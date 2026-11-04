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
import Synchronization
import SystemPackage

#if canImport(Darwin)
    import Darwin
#elseif canImport(Glibc)
    import Glibc
#else
    import Musl
#endif

/// Bounded diagnostics independent of the MCP stdout writer.
public final class JSONLogSink: Sendable {
    private struct State: Sendable {
        var records: [Data] = []
        var dropped = 0
        var closing = false
    }
    private let state = Mutex(State())
    private let worker = Mutex<Task<Void, Never>?>(nil)
    private let descriptor: FileDescriptor
    private let initialFlags: Int32

    public init(descriptor: FileDescriptor = .standardError) throws {
        self.descriptor = descriptor
        initialFlags = fcntl(descriptor.rawValue, F_GETFL)
        guard initialFlags >= 0, fcntl(descriptor.rawValue, F_SETFL, initialFlags | O_NONBLOCK) >= 0 else {
            throw StdioFailure.system(errno)
        }
    }

    public func start() {
        worker.withLock { task in
            guard task == nil else { return }
            task = Task { await drain() }
        }
    }

    public func record(level: Logger.Level, label: String, message: String, metadata: Logger.Metadata) {
        var object: [String: Any] = [
            "timestamp": Date().formatted(.iso8601), "level": level.rawValue,
            "component": label, "event": label == BuildInfo.name ? String(message.prefix(128)) : "sdk_diagnostic",
        ]
        // SDK diagnostics can contain raw messages; only bounded operational metadata crosses this sink.
        let allowed: Set<String> = [
            "tool", "requestId", "durationMs", "errorCode", "protocolVersion", "version", "sdkBaseline",
        ]
        for (key, value) in metadata where allowed.contains(key) {
            object[key] = String(value.description.prefix(128))
        }
        guard var bytes = try? JSONSerialization.data(withJSONObject: object, options: [.sortedKeys]), bytes.count < 512
        else { return }
        bytes.append(10)
        state.withLock { state in
            guard !state.closing else { return }
            guard state.records.count < 64 else {
                state.dropped += 1
                return
            }
            state.records.append(bytes)
        }
    }

    public func finish() async {
        state.withLock { $0.closing = true }
        let task = worker.withLock { $0 }
        await task?.value
        if fcntl(descriptor.rawValue, F_GETFL) == (initialFlags | O_NONBLOCK) {
            _ = fcntl(descriptor.rawValue, F_SETFL, initialFlags)
        }
    }

    private func drain() async {
        while !Task.isCancelled {
            let next: (Data?, Bool) = state.withLock { state in
                if !state.records.isEmpty { return (state.records.removeFirst(), false) }
                if state.dropped > 0 {
                    let count = state.dropped
                    state.dropped = 0
                    let line =
                        "{\"level\":\"warning\",\"component\":\"routeobjects-mcp\",\"event\":\"logs_dropped\",\"count\":\(count)}\n"
                    return (Data(line.utf8), false)
                }
                return (nil, state.closing)
            }
            if next.1 { return }
            guard let data = next.0 else {
                do { try await Task.sleep(for: .milliseconds(5)) } catch { return }
                continue
            }
            let deadline = ContinuousClock.now.advanced(by: .milliseconds(100))
            var offset = 0
            while offset < data.count && !Task.isCancelled {
                guard ContinuousClock.now < deadline else {
                    state.withLock {
                        $0.records.removeAll()
                        $0.closing = true
                        $0.dropped = 0
                    }
                    return
                }
                do {
                    let count = try data.withUnsafeBytes { raw in
                        try descriptor.write(UnsafeRawBufferPointer(rebasing: raw[offset...]))
                    }
                    offset += count
                    if count == 0 { try await Task.sleep(for: .milliseconds(2)) }
                } catch let failure as Errno where failure == .resourceTemporarilyUnavailable || failure == .interrupted
                {
                    if ContinuousClock.now >= deadline {
                        // Stop this sink after a partial/blocked record; never concatenate later JSON onto it.
                        state.withLock {
                            $0.records.removeAll()
                            $0.closing = true
                            $0.dropped = 0
                        }
                        return
                    }
                    do { try await Task.sleep(for: .milliseconds(2)) } catch { return }
                } catch { return }
            }
        }
    }
}

public struct JSONLogHandler: LogHandler {
    public var metadata: Logger.Metadata = [:]
    public var logLevel: Logger.Level
    private let label: String
    private let sink: JSONLogSink

    public init(label: String, sink: JSONLogSink, level: Logger.Level = .info) {
        self.label = label
        self.sink = sink
        logLevel = level
    }

    public subscript(metadataKey key: String) -> Logger.Metadata.Value? {
        get { metadata[key] }
        set { metadata[key] = newValue }
    }

    public func log(
        level: Logger.Level, message: Logger.Message, metadata: Logger.Metadata?, source: String,
        file: String, function: String, line: UInt
    ) {
        sink.record(
            level: level, label: label, message: message.description,
            metadata: self.metadata.merging(metadata ?? [:], uniquingKeysWith: { _, new in new }))
    }
}
