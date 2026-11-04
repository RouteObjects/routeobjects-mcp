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

import CIDRToolCore
import Foundation
import Logging
import MCP
import SystemPackage
import Testing

@testable import CIDRMCPAdapter

#if canImport(Darwin)
    import Darwin
#else
    import Glibc
#endif

private func pipePair() throws -> (FileDescriptor, FileDescriptor) {
    var values: [Int32] = [0, 0]
    guard pipe(&values) == 0 else { throw StdioFailure.system(errno) }
    return (FileDescriptor(rawValue: values[0]), FileDescriptor(rawValue: values[1]))
}

private func discardLogger() -> Logger {
    Logger(label: "test", factory: { _ in SwiftLogNoOpLogHandler() })
}

private func boundedPipeWrite(_ data: Data, to descriptor: FileDescriptor) async throws {
    let deadline = ContinuousClock.now.advanced(by: .seconds(5))
    var offset = 0
    while offset < data.count {
        try Task.checkCancellation()
        guard ContinuousClock.now < deadline else { throw StdioFailure.stalledWrite }
        do {
            offset += try data.withUnsafeBytes { bytes in
                try descriptor.write(UnsafeRawBufferPointer(rebasing: bytes[offset...]))
            }
        } catch let error as Errno
            where error == .resourceTemporarilyUnavailable || error == .interrupted
        {
            try await Task.sleep(for: .milliseconds(1))
        }
    }
}

private func boundedPipeRead(_ count: Int, from descriptor: FileDescriptor) async throws -> Data {
    let deadline = ContinuousClock.now.advanced(by: .seconds(5))
    var result = Data()
    var buffer = [UInt8](repeating: 0, count: 997)
    while result.count < count {
        try Task.checkCancellation()
        guard ContinuousClock.now < deadline else { throw StdioFailure.stalledWrite }
        do {
            let received = try buffer.withUnsafeMutableBytes { try descriptor.read(into: $0) }
            guard received > 0 else { throw StdioFailure.incompleteFrame }
            result.append(contentsOf: buffer.prefix(received))
        } catch let error as Errno
            where error == .resourceTemporarilyUnavailable || error == .interrupted
        {
            try await Task.sleep(for: .milliseconds(1))
        }
    }
    return result
}

@Test func sameEnvelopeForBothRepresentations() throws {
    let envelope = try CIDRToolCore.execute(
        tool: "cidr_inspect", arguments: ["kind": "network", "value": "::/0"])
    let result = try CIDRServer.result(envelope)
    let structured = try #require(result.structuredContent)
    guard case .text(let text, _, _) = result.content[0] else {
        Issue.record("Missing text")
        return
    }
    #expect(try JSONDecoder().decode(JSONValue.self, from: Data(text.utf8)) == envelope)
    #expect(
        try JSONDecoder().decode(JSONValue.self, from: JSONEncoder().encode(structured)) == envelope)
    #expect(result.isError == false)
}

@Test func domainFailureHasErrorFlag() throws {
    let envelope = try CIDRToolCore.execute(
        tool: "cidr_inspect", arguments: ["kind": "network", "value": "192.0.2.1/24"])
    #expect(try CIDRServer.result(envelope).isError == true)
}

@Test func fragmentedInputAndFlagRestoration() async throws {
    let (input, feed) = try pipePair()
    let (drain, output) = try pipePair()
    defer {
        try? input.close()
        try? feed.close()
        try? drain.close()
        try? output.close()
    }
    let beforeInput = fcntl(input.rawValue, F_GETFL)
    let beforeOutput = fcntl(output.rawValue, F_GETFL)
    let transport = BoundedStdioTransport(input: input, output: output, logger: discardLogger())
    try await transport.connect()
    let consumer = Task { () throws -> [Data] in
        var received: [Data] = []
        for try await data in await transport.receive() {
            received.append(data)
            if received.count == 2 { break }
        }
        return received
    }
    for part in ["{\"x\":", "1}\n{\"y\":2", "}\n"] {
        try Array(part.utf8).withUnsafeBytes { _ = try feed.writeAll($0) }
    }
    #expect(try await consumer.value == [Data("{\"x\":1}".utf8), Data("{\"y\":2}".utf8)])
    await transport.disconnect()
    #expect(fcntl(input.rawValue, F_GETFL) == beforeInput)
    #expect(fcntl(output.rawValue, F_GETFL) == beforeOutput)
}

@Test func concurrentFramesRemainIntact() async throws {
    let (input, feed) = try pipePair()
    let (drain, output) = try pipePair()
    defer {
        try? input.close()
        try? feed.close()
        try? drain.close()
        try? output.close()
    }
    let transport = BoundedStdioTransport(input: input, output: output, logger: discardLogger())
    try await transport.connect()
    _ = fcntl(drain.rawValue, F_SETFL, O_NONBLOCK)
    let payloads = (0..<8).map {
        Data("{\"id\":\($0),\"body\":\"\(String(repeating: String($0), count: 48_000))\"}".utf8)
    }
    let reader = Task { () throws -> [Data] in
        var bytes = Data()
        var buffer = [UInt8](repeating: 0, count: 997)
        let deadline = ContinuousClock.now.advanced(by: .seconds(10))
        while bytes.filter({ $0 == 10 }).count < payloads.count {
            guard ContinuousClock.now < deadline else { throw StdioFailure.stalledWrite }
            do {
                let count = try buffer.withUnsafeMutableBytes { try drain.read(into: $0) }
                bytes.append(contentsOf: buffer.prefix(count))
            } catch let error as Errno where error == .resourceTemporarilyUnavailable {
                try await Task.sleep(for: .milliseconds(1))
            }
        }
        return bytes.split(separator: 10).map { Data($0) }
    }
    try await withThrowingTaskGroup(of: Void.self) { group in
        for payload in payloads { group.addTask { try await transport.send(payload) } }
        try await group.waitForAll()
    }
    let frames = try await reader.value
    #expect(Set(frames) == Set(payloads))
    for frame in frames { #expect(try JSONSerialization.jsonObject(with: frame) is [String: Any]) }
    await transport.disconnect()
}

@Test func oversizedOutboundRejectedBeforeWriting() async throws {
    let (input, feed) = try pipePair()
    let (drain, output) = try pipePair()
    defer {
        try? input.close()
        try? feed.close()
        try? drain.close()
        try? output.close()
    }
    let transport = BoundedStdioTransport(input: input, output: output, logger: discardLogger())
    try await transport.connect()
    await #expect(throws: StdioFailure.self) {
        try await transport.send(Data(repeating: 120, count: 65_536))
    }
    try await transport.send(Data("{}".utf8))
    var buffer = [UInt8](repeating: 0, count: 8)
    let count = try buffer.withUnsafeMutableBytes { try drain.read(into: $0) }
    #expect(Array(buffer.prefix(count)) == Array("{}\n".utf8))
    await transport.disconnect()
}

@Test func exactInboundFrameBoundaryIncludesNewline() async throws {
    let (input, feed) = try pipePair()
    let (drain, output) = try pipePair()
    defer {
        try? input.close()
        try? feed.close()
        try? drain.close()
        try? output.close()
    }
    _ = fcntl(feed.rawValue, F_SETFL, O_NONBLOCK)
    let transport = BoundedStdioTransport(input: input, output: output, logger: discardLogger())
    try await transport.connect()
    let deadline = Task {
        do {
            try await Task.sleep(for: .seconds(5))
            await transport.disconnect()
        } catch {}
    }
    defer { deadline.cancel() }
    // Exactly 16 KiB includes LF; the immediately following frame must remain intact.
    let payload = Data("{\"x\":\"\(String(repeating: "x", count: 16_375))\"}".utf8)
    #expect(payload.count == 16_383)
    let producer = Task { try await boundedPipeWrite(payload + Data("\n{}\n".utf8), to: feed) }
    do {
        var iterator = await transport.receive().makeAsyncIterator()
        #expect(try await iterator.next() == payload)
        #expect(try await iterator.next() == Data("{}".utf8))
        try await producer.value
        await transport.disconnect()
    } catch {
        producer.cancel()
        await transport.disconnect()
        _ = try? await producer.value
        throw error
    }
}

@Test func firstOversizedInboundPayloadIsRejected() async throws {
    let (input, feed) = try pipePair()
    let (drain, output) = try pipePair()
    defer {
        try? input.close()
        try? feed.close()
        try? drain.close()
        try? output.close()
    }
    _ = fcntl(feed.rawValue, F_SETFL, O_NONBLOCK)
    let transport = BoundedStdioTransport(input: input, output: output, logger: discardLogger())
    try await transport.connect()
    let deadline = Task {
        do {
            try await Task.sleep(for: .seconds(5))
            await transport.disconnect()
        } catch {}
    }
    defer { deadline.cancel() }
    // The first disallowed payload must fail before any further bytes or delimiter are required.
    let producer = Task { try await boundedPipeWrite(Data(repeating: 120, count: 16_384), to: feed) }
    do {
        var iterator = await transport.receive().makeAsyncIterator()
        do {
            _ = try await iterator.next()
            Issue.record("The first oversized inbound payload was accepted")
        } catch StdioFailure.inputLimit {
            // Expected before a newline or EOF is supplied.
        }
        try await producer.value
        await transport.disconnect()
    } catch {
        producer.cancel()
        await transport.disconnect()
        _ = try? await producer.value
        throw error
    }
}

@Test func exactOutboundFrameBoundaryIncludesNewline() async throws {
    let (input, feed) = try pipePair()
    let (drain, output) = try pipePair()
    defer {
        try? input.close()
        try? feed.close()
        try? drain.close()
        try? output.close()
    }
    _ = fcntl(drain.rawValue, F_SETFL, O_NONBLOCK)
    let transport = BoundedStdioTransport(input: input, output: output, logger: discardLogger())
    try await transport.connect()
    let deadline = Task {
        do {
            try await Task.sleep(for: .seconds(5))
            await transport.disconnect()
        } catch {}
    }
    defer { deadline.cancel() }
    // Exercise the last allowed frame, not only smaller frames and oversize rejection.
    let payload = Data("{\"x\":\"\(String(repeating: "x", count: 65_527))\"}".utf8)
    #expect(payload.count == 65_535)
    let reader = Task { try await boundedPipeRead(65_536, from: drain) }
    do {
        try await transport.send(payload)
        let frame = try await reader.value
        #expect(frame == payload + Data([10]))
        #expect(try JSONSerialization.jsonObject(with: frame) is [String: Any])
        await transport.disconnect()
    } catch {
        reader.cancel()
        await transport.disconnect()
        _ = try? await reader.value
        throw error
    }
}

@Test func loggingRedactsSDKMessagesAndArguments() async throws {
    let (drain, output) = try pipePair()
    defer {
        try? drain.close()
        try? output.close()
    }
    let sink = try JSONLogSink(descriptor: output)
    sink.start()
    sink.record(
        level: .error, label: "mcp.server", message: "secret 192.0.2.42",
        metadata: ["arguments": "secret", "tool": "cidr_inspect"])
    await sink.finish()
    var buffer = [UInt8](repeating: 0, count: 4096)
    let count = try buffer.withUnsafeMutableBytes { try drain.read(into: $0) }
    let data = Data(buffer.prefix(count))
    let line = String(decoding: data, as: UTF8.self)
    #expect(!line.contains("secret"))
    #expect(!line.contains("192.0.2.42"))
    #expect(line.hasSuffix("\n"))
    #expect(try JSONSerialization.jsonObject(with: data) is [String: Any])
}

@Test func inputEOFNotifiesProcessOwner() async throws {
    let (input, feed) = try pipePair()
    let (drain, output) = try pipePair()
    defer {
        try? input.close()
        try? drain.close()
        try? output.close()
    }
    let transport = BoundedStdioTransport(input: input, output: output, logger: discardLogger())
    try await transport.connect()
    let owner = Task { await transport.waitUntilInputClosed() }
    try feed.close()
    var frames = 0
    for try await _ in await transport.receive() { frames += 1 }
    await owner.value
    #expect(frames == 0)
    #expect(await transport.terminalFailure == nil)
    await transport.disconnect()
}
