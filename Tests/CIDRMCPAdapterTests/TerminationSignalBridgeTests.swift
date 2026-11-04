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

import Dispatch
import Foundation
import Testing

@testable import CIDRMCPAdapter

#if canImport(Darwin)
    import Darwin
#else
    import Glibc
#endif

private enum SignalTestFailure: Error { case system, timeout, startup }

/// Linux libdispatch retains process-wide signal machinery after source cancellation.
/// Installing SIG_IGN for a later independent bridge overwrites that handler. Exercise
/// each process-owned lifetime in a fresh test runner instead of changing production policy.
private func runInSignalProcess(_ test: String, argument: String = "") async throws -> Bool {
    #if os(Linux)
        let key = "ROUTEOBJECTS_MCP_SIGNAL_TEST"
        let identity = test + ":" + argument
        if let selected = ProcessInfo.processInfo.environment[key] {
            if selected == identity, let path = ProcessInfo.processInfo.environment[key + "_MARKER"] {
                try Data(identity.utf8).write(to: URL(fileURLWithPath: path))
            }
            return selected != identity
        }
        let marker = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        defer { try? FileManager.default.removeItem(at: marker) }
        let child = Process()
        child.executableURL = URL(fileURLWithPath: CommandLine.arguments[0])
        child.arguments = ["--testing-library", "swift-testing", "--filter", "TerminationSignalBridgeTests/" + test]
        var environment = ProcessInfo.processInfo.environment
        environment[key] = identity
        environment[key + "_MARKER"] = marker.path
        child.environment = environment
        try child.run()
        defer {
            if child.isRunning { _ = kill(child.processIdentifier, SIGKILL) }
        }
        let deadline = ContinuousClock.now.advanced(by: .seconds(10))
        while child.isRunning {
            guard ContinuousClock.now < deadline else { throw SignalTestFailure.timeout }
            try await Task.sleep(for: .milliseconds(10))
        }
        #expect(child.terminationReason == .exit)
        #expect(child.terminationStatus == 0)
        #expect(try String(contentsOf: marker, encoding: .utf8) == identity)
        return true
    #else
        return false
    #endif
}

/// Tests reserve SIGUSR1/SIGUSR2, leaving the test runner's termination signals alone.
private struct SavedSignalDispositions {
    private var first = sigaction()
    private var second = sigaction()

    init() throws {
        guard sigaction(SIGUSR1, nil, &first) == 0, sigaction(SIGUSR2, nil, &second) == 0 else {
            throw SignalTestFailure.system
        }
    }

    mutating func restore() {
        _ = sigaction(SIGUSR1, &first, nil)
        _ = sigaction(SIGUSR2, &second, nil)
    }
}

private actor TestGate {
    private(set) var isOpen = false
    private var waiters: [CheckedContinuation<Void, Never>] = []

    func wait() async {
        guard !isOpen else { return }
        await withCheckedContinuation { waiters.append($0) }
    }

    func release() {
        isOpen = true
        for waiter in waiters { waiter.resume() }
        waiters.removeAll()
    }
}

private func waitForState(
    _ state: TerminationSignalBridge.State, of bridge: TerminationSignalBridge
) async throws {
    let deadline = ContinuousClock.now.advanced(by: .seconds(3))
    while await bridge.state != state {
        guard ContinuousClock.now < deadline else { throw SignalTestFailure.timeout }
        try await Task.sleep(for: .milliseconds(1))
    }
}

private func nextSignal(_ events: AsyncStream<Int32>) async -> Int32? {
    await withTaskGroup(of: Int32?.self) { group in
        group.addTask {
            var iterator = events.makeAsyncIterator()
            return await iterator.next()
        }
        group.addTask {
            do { try await Task.sleep(for: .seconds(3)) } catch { return nil }
            return nil
        }
        let value = await group.next() ?? nil
        group.cancelAll()
        return value
    }
}

@Suite(.serialized, .timeLimit(.minutes(1)))
struct TerminationSignalBridgeTests {
    @Test func deliversOnlyFirstObservedSignal() async throws {
        if try await runInSignalProcess("deliversOnlyFirstObservedSignal") { return }
        var dispositions = try SavedSignalDispositions()
        defer { dispositions.restore() }
        let bridge = TerminationSignalBridge(signalNumbers: [SIGUSR1, SIGUSR2])
        try await bridge.start()
        #expect(kill(getpid(), SIGUSR1) == 0)
        #expect(await nextSignal(bridge.events) == SIGUSR1)
        #expect(kill(getpid(), SIGUSR2) == 0)
        #expect(await nextSignal(bridge.events) == nil)
        await bridge.stop()
        #expect(await bridge.state == .stopped)
    }

    @Test func stopWaitsForDispatchAndSurvivesCallerCancellation() async throws {
        if try await runInSignalProcess("stopWaitsForDispatchAndSurvivesCallerCancellation") { return }
        var dispositions = try SavedSignalDispositions()
        defer { dispositions.restore() }
        let queue = DispatchQueue(label: "signal-test.cancellation")
        let bridge = TerminationSignalBridge(signalNumbers: [SIGUSR1, SIGUSR2], queue: queue)
        try await bridge.start()
        queue.suspend()
        let first = Task {
            await bridge.stop()
            #expect(await bridge.state == .stopped)
        }
        do {
            try await waitForState(.stopping, of: bridge)
            first.cancel()
            let second = Task {
                await bridge.stop()
                #expect(await bridge.state == .stopped)
            }
            // Dispatch cannot run either cancellation callback while its queue is suspended.
            #expect(await bridge.state == .stopping)
            queue.resume()
            await first.value
            await second.value
            await bridge.stop()
            #expect(await bridge.state == .stopped)
        } catch {
            queue.resume()
            await first.value
            await bridge.stop()
            throw error
        }
    }

    @Test func stoppedBridgeCannotRestart() async throws {
        if try await runInSignalProcess("stoppedBridgeCannotRestart") { return }
        let bridge = TerminationSignalBridge(signalNumbers: [])
        await bridge.stop()
        await bridge.stop()
        await #expect(throws: TerminationSignalBridge.Failure.self) { try await bridge.start() }
        #expect(await nextSignal(bridge.events) == nil)
    }

    @Test func failedInstallationCanBeStopped() async throws {
        if try await runInSignalProcess("failedInstallationCanBeStopped") { return }
        let bridge = TerminationSignalBridge(signalNumbers: [SIGKILL])
        await #expect(throws: TerminationSignalBridge.Failure.self) { try await bridge.start() }
        await bridge.stop()
        #expect(await bridge.state == .stopped)
        #expect(await nextSignal(bridge.events) == nil)
    }

    @Test func startupFailureRetiresSignalSources() async throws {
        if try await runInSignalProcess("startupFailureRetiresSignalSources") { return }
        var dispositions = try SavedSignalDispositions()
        defer { dispositions.restore() }
        let bridge = TerminationSignalBridge(signalNumbers: [SIGUSR1])
        let never = AsyncStream<Void>.makeStream().stream
        let stopped = TestGate()
        await #expect(throws: SignalTestFailure.self) {
            try await CommandLineServer.serve(
                signals: bridge, start: { throw SignalTestFailure.startup },
                waitUntilCompleted: { Issue.record("Failed startup must not enter completion wait") },
                waitUntilInputClosed: { for await _ in never {} },
                stop: { await stopped.release() })
        }
        #expect(await stopped.isOpen)
        #expect(await bridge.state == .stopped)
    }

    @Test func stopDuringRegistrationRetiresSourcesAndReleasesStarter() async throws {
        if try await runInSignalProcess("stopDuringRegistrationRetiresSourcesAndReleasesStarter") { return }
        var dispositions = try SavedSignalDispositions()
        defer { dispositions.restore() }
        let queue = DispatchQueue(label: "signal-test.registration")
        queue.suspend()
        let bridge = TerminationSignalBridge(signalNumbers: [SIGUSR1], queue: queue)
        let starter = Task { try await bridge.start() }
        do {
            try await waitForState(.starting, of: bridge)
            let stopper = Task { await bridge.stop() }
            try await waitForState(.stopping, of: bridge)
            queue.resume()
            await #expect(throws: CancellationError.self) { try await starter.value }
            await stopper.value
            #expect(await bridge.state == .stopped)
        } catch {
            queue.resume()
            await bridge.stop()
            _ = try? await starter.value
            throw error
        }
    }

    @Test func cancellationDuringRegistrationRunsOwnedShutdown() async throws {
        if try await runInSignalProcess("cancellationDuringRegistrationRunsOwnedShutdown") { return }
        var dispositions = try SavedSignalDispositions()
        defer { dispositions.restore() }
        let queue = DispatchQueue(label: "signal-test.registration-cancellation")
        queue.suspend()
        let bridge = TerminationSignalBridge(signalNumbers: [SIGUSR1], queue: queue)
        let never = AsyncStream<Void>.makeStream().stream
        let stopped = TestGate()
        let server = Task {
            try await CommandLineServer.serve(
                signals: bridge,
                start: { Issue.record("Cancelled registration must not start the server") },
                waitUntilCompleted: {
                    Issue.record("Cancelled registration must not enter completion wait")
                },
                waitUntilInputClosed: { for await _ in never {} },
                stop: { await stopped.release() })
        }
        do {
            try await waitForState(.starting, of: bridge)
            server.cancel()
            try await waitForState(.stopping, of: bridge)
            #expect(await stopped.isOpen)
            queue.resume()
            await #expect(throws: CancellationError.self) { try await server.value }
            #expect(await bridge.state == .stopped)
        } catch {
            queue.resume()
            server.cancel()
            _ = try? await server.value
            throw error
        }
    }
    @Test(arguments: ["signal", "eof", "parentCancellation"])
    func shutdownInterruptsStartupAndJoinsItsCleanup(trigger: String) async throws {
        if try await runInSignalProcess("shutdownInterruptsStartupAndJoinsItsCleanup", argument: trigger) { return }
        var dispositions = try SavedSignalDispositions()
        defer { dispositions.restore() }
        let bridge = TerminationSignalBridge(signalNumbers: [SIGUSR1])
        let enteredStartup = TestGate()
        let releaseStartup = TestGate()
        let startupCleaned = TestGate()
        let eof = AsyncStream<Void>.makeStream()
        let server = Task {
            try await CommandLineServer.serve(
                signals: bridge,
                start: {
                    await enteredStartup.release()
                    // Deliberately ignore task cancellation until the shutdown owner releases us.
                    await releaseStartup.wait()
                    await startupCleaned.release()
                    try Task.checkCancellation()
                },
                waitUntilCompleted: { Issue.record("Interrupted startup must not enter completion wait") },
                waitUntilInputClosed: { for await _ in eof.stream {} },
                stop: { await releaseStartup.release() })
        }
        await enteredStartup.wait()
        switch trigger {
        case "signal": #expect(kill(getpid(), SIGUSR1) == 0)
        case "eof": eof.continuation.finish()
        default: server.cancel()
        }
        if trigger == "parentCancellation" {
            await #expect(throws: CancellationError.self) { try await server.value }
        } else {
            try await server.value
        }
        #expect(await startupCleaned.isOpen)
        #expect(await bridge.state == .stopped)
    }
}
