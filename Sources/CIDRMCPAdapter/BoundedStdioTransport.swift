//===----------------------------------------------------------------------===//
//
// This source file is part of the routeobjects-mcp project.
//
// Copyright (c) 2026 Craig A. Munro
//
// Licensed under the Apache License, Version 2.0.
// See the LICENSE file for details.
//
// SPDX-License-Identifier: Apache-2.0
//
//===----------------------------------------------------------------------===//

import Foundation
import Logging
import MCP
import SystemPackage

#if canImport(Darwin)
    import Darwin
#elseif canImport(Glibc)
    import Glibc
#else
    import Musl
#endif

public enum StdioFailure: Error, Sendable {
    case disconnected, inputLimit, outputLimit, queueLimit, stalledWrite, incompleteFrame
    case system(Int32)
}

/// A bounded byte transport. Request admission belongs to the SDK's server lifecycle.
public actor BoundedStdioTransport: Transport {
    public nonisolated let logger: Logger
    public static let maximumInputBytes = 16 * 1024
    public static let maximumOutputBytes = 64 * 1024
    private let input: FileDescriptor
    private let output: FileDescriptor
    private let inputClosed: AsyncStream<Void>
    private let inputClosedContinuation: AsyncStream<Void>.Continuation
    private var unread = Data()
    private var unreadOffset = 0
    private var connected = false
    private var finished = false
    private var reader: Task<Data?, any Error>?
    private var writer: Task<Void, Never>?
    private var queue: [PendingWrite] = []
    private var flags: [DescriptorFlags] = []
    public private(set) var terminalFailure: StdioFailure?

    private struct PendingWrite {
        let bytes: Data
        let completion: CheckedContinuation<Void, any Error>
    }

    private struct DescriptorFlags {
        let descriptor: Int32
        let original: Int32
        let device: UInt64
        let inode: UInt64
    }

    public init(input: FileDescriptor = .standardInput, output: FileDescriptor = .standardOutput, logger: Logger) {
        self.input = input
        self.output = output
        self.logger = logger
        (inputClosed, inputClosedContinuation) = AsyncStream.makeStream()
    }

    public func connect() async throws {
        guard !connected, !finished else { throw StdioFailure.disconnected }
        do {
            flags.append(try configure(input))
            flags.append(try configure(output))
        } catch {
            restoreFlags()
            throw error
        }
        connected = true
    }

    public func receive() -> AsyncThrowingStream<Data, any Error> {
        // Pull one frame per consumer iteration. No eager queue can discard cancellation notifications.
        AsyncThrowingStream(unfolding: { try await self.nextFrame() })
    }

    /// Allows the process owner to start its shutdown deadline before SDK cleanup completes.
    public func waitUntilInputClosed() async {
        for await _ in inputClosed {}
    }

    private func nextFrame() async throws -> Data? {
        guard connected, !finished else { return nil }
        guard reader == nil else { throw StdioFailure.queueLimit }
        let operation = Task { try await readFrame() }
        reader = operation
        defer { reader = nil }
        return try await withTaskCancellationHandler {
            try await operation.value
        } onCancel: {
            operation.cancel()
        }
    }

    public func send(_ data: Data) async throws {
        try Task.checkCancellation()
        guard connected else { throw terminalFailure ?? .disconnected }
        guard data.count < Self.maximumOutputBytes else { throw StdioFailure.outputLimit }
        guard queue.count < 12 else {
            fail(.queueLimit)
            throw StdioFailure.queueLimit
        }
        var frame = data
        frame.append(10)
        // Only the writer task touches stdout. Actor reentrancy during EAGAIN cannot splice another frame.
        try await withCheckedThrowingContinuation { completion in
            queue.append(PendingWrite(bytes: frame, completion: completion))
            if writer == nil { writer = Task { await writeFrames() } }
        }
    }

    public func disconnect() async {
        connected = false
        finished = true
        inputClosedContinuation.finish()
        let activeReader = reader
        let activeWriter = writer
        activeReader?.cancel()
        activeWriter?.cancel()
        failQueued(.disconnected)
        _ = try? await activeReader?.value
        await activeWriter?.value
        reader = nil
        writer = nil
        restoreFlags()
    }

    private func configure(_ descriptor: FileDescriptor) throws -> DescriptorFlags {
        let fd = descriptor.rawValue
        let original = fcntl(fd, F_GETFL)
        var identity = stat()
        guard original >= 0, fstat(fd, &identity) == 0 else { throw StdioFailure.system(errno) }
        guard fcntl(fd, F_SETFL, original | O_NONBLOCK) >= 0 else { throw StdioFailure.system(errno) }
        return DescriptorFlags(
            descriptor: fd, original: original,
            device: UInt64(truncatingIfNeeded: identity.st_dev), inode: UInt64(truncatingIfNeeded: identity.st_ino))
    }

    private func restoreFlags() {
        for item in flags.reversed() {
            var identity = stat()
            // Restore only our unchanged descriptor, after owned reads/writes have stopped.
            guard fstat(item.descriptor, &identity) == 0,
                UInt64(truncatingIfNeeded: identity.st_dev) == item.device,
                UInt64(truncatingIfNeeded: identity.st_ino) == item.inode,
                fcntl(item.descriptor, F_GETFL) == (item.original | O_NONBLOCK)
            else { continue }
            _ = fcntl(item.descriptor, F_SETFL, item.original)
        }
        flags.removeAll()
    }

    private func readFrame() async throws -> Data? {
        var buffer = [UInt8](repeating: 0, count: 4096)
        var pending = Data()
        do {
            while connected && !Task.isCancelled {
                while unreadOffset < unread.count {
                    let byte = unread[unreadOffset]
                    unreadOffset += 1
                    if byte == 10 {
                        if !pending.isEmpty { return pending }
                    } else {
                        guard pending.count + 1 < Self.maximumInputBytes else { throw StdioFailure.inputLimit }
                        pending.append(byte)
                    }
                }
                unread.removeAll(keepingCapacity: true)
                unreadOffset = 0
                do {
                    let count = try buffer.withUnsafeMutableBytes { try input.read(into: $0) }
                    if count == 0 {
                        guard pending.isEmpty else { throw StdioFailure.incompleteFrame }
                        finished = true
                        inputClosedContinuation.finish()
                        return nil
                    }
                    unread.append(contentsOf: buffer.prefix(count))
                } catch let failure as Errno where failure == .resourceTemporarilyUnavailable || failure == .interrupted
                {
                    try await Task.sleep(for: .milliseconds(2))
                }
            }
            return nil
        } catch is CancellationError { return nil } catch {
            let failure = error as? StdioFailure ?? .system(errno)
            fail(failure)
            throw failure
        }
    }

    private func writeFrames() async {
        while connected && !queue.isEmpty {
            let item = queue.removeFirst()
            do {
                try await writeCompleteFrame(item.bytes)
                item.completion.resume()
            } catch {
                item.completion.resume(throwing: error)
                // A partial frame cannot be followed by another response after failure.
                fail(error as? StdioFailure ?? .disconnected)
                break
            }
        }
        writer = nil
    }

    private func writeCompleteFrame(_ bytes: Data) async throws {
        let clock = ContinuousClock()
        var progressDeadline = clock.now.advanced(by: .seconds(5))
        var offset = 0
        while offset < bytes.count {
            try Task.checkCancellation()
            guard connected else { throw StdioFailure.disconnected }
            do {
                let count = try bytes.withUnsafeBytes { raw in
                    try output.write(UnsafeRawBufferPointer(rebasing: raw[offset...]))
                }
                if count > 0 {
                    offset += count
                    progressDeadline = clock.now.advanced(by: .seconds(5))
                } else if clock.now >= progressDeadline {
                    throw StdioFailure.stalledWrite
                } else {
                    try await Task.sleep(for: .milliseconds(2))
                }
            } catch let failure as Errno where failure == .resourceTemporarilyUnavailable || failure == .interrupted {
                guard clock.now < progressDeadline else { throw StdioFailure.stalledWrite }
                try await Task.sleep(for: .milliseconds(2))
            }
        }
    }

    private func fail(_ error: StdioFailure) {
        if terminalFailure == nil { terminalFailure = error }
        connected = false
        finished = true
        inputClosedContinuation.finish()
        reader?.cancel()
        failQueued(error)
    }

    private func failQueued(_ error: StdioFailure) {
        let pending = queue
        queue.removeAll()
        for item in pending { item.completion.resume(throwing: error) }
    }
}
