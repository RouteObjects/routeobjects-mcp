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

#if canImport(Darwin)
    import Darwin
#elseif canImport(Glibc)
    import Glibc
#else
    import Musl
#endif

/// One process owner for termination signals. Dispositions deliberately remain ignored
/// after stopping: a repeated signal must not interrupt final logging or process exit.
/// This is an executable lifecycle component, not a general-purpose signal subscription.
actor TerminationSignalBridge {
    enum State: Sendable { case idle, starting, running, stopping, stopped }
    enum Failure: Error {
        case alreadyStarted
        case installation(Int32)
    }

    nonisolated let events: AsyncStream<Int32>
    private let continuation: AsyncStream<Int32>.Continuation
    private let signalNumbers: [Int32]
    private let queue: DispatchQueue
    private var sources: [any DispatchSourceSignal] = []
    private var remainingRegistrations = 0
    private var startWaiter: CheckedContinuation<Void, Never>?
    private var remainingCancellations = 0
    private var stopWaiters: [CheckedContinuation<Void, Never>] = []
    private(set) var state = State.idle

    init(
        signalNumbers: [Int32] = [SIGINT, SIGTERM],
        queue: DispatchQueue = DispatchQueue(label: "com.routeobjects.routeobjects-mcp.signals")
    ) {
        self.signalNumbers = signalNumbers
        self.queue = queue
        (events, continuation) = AsyncStream.makeStream(bufferingPolicy: .bufferingOldest(1))
    }

    func start() async throws {
        guard state == .idle else { throw Failure.alreadyStarted }
        try Task.checkCancellation()
        var ignored = sigaction()
        #if canImport(Darwin)
            ignored.__sigaction_u.__sa_handler = SIG_IGN
        #else
            ignored.__sigaction_handler.sa_handler = SIG_IGN
        #endif
        sigemptyset(&ignored.sa_mask)
        for number in signalNumbers {
            guard sigaction(number, &ignored, nil) == 0 else {
                throw Failure.installation(errno)
            }
        }
        state = .starting
        remainingRegistrations = signalNumbers.count
        let continuation = continuation
        for number in signalNumbers {
            let source = DispatchSource.makeSignalSource(signal: number, queue: queue)
            // Only Sendable values cross this callback boundary. The first observed signal
            // finishes the bounded stream; Unix signals are not an ordered event log.
            source.setEventHandler {
                continuation.yield(number)
                continuation.finish()
            }
            source.setCancelHandler { [weak self] in
                // One callback per source, after its final event handler has returned.
                guard let self else { return }
                Task { await self.sourceCancelled() }
            }
            source.setRegistrationHandler { [weak self] in
                guard let self else { return }
                Task { await self.sourceRegistered() }
            }
            sources.append(source)
            source.resume()
        }
        if sources.isEmpty {
            state = .running
        } else {
            // Callers may send a signal as soon as start returns, without timing sleeps.
            await withCheckedContinuation { startWaiter = $0 }
        }
        try Task.checkCancellation()
        guard state == .running else { throw CancellationError() }
    }

    /// Returns only after every source reports cancellation, after its event handler. Cancelling
    /// a caller does not abandon cleanup; all concurrent callers share the same teardown.
    func stop() async {
        switch state {
        case .stopped:
            return
        case .stopping:
            break
        case .idle, .starting, .running:
            state = .stopping
            continuation.finish()
            remainingCancellations = sources.count
            guard remainingCancellations > 0 else {
                state = .stopped
                return
            }
            for source in sources { source.cancel() }
        }
        await withCheckedContinuation { stopWaiters.append($0) }
    }

    private func sourceRegistered() {
        remainingRegistrations -= 1
        guard remainingRegistrations == 0, state == .starting else { return }
        state = .running
        startWaiter?.resume()
        startWaiter = nil
    }

    private func sourceCancelled() {
        remainingCancellations -= 1
        guard remainingCancellations == 0 else { return }
        sources.removeAll()
        state = .stopped
        startWaiter?.resume()
        startWaiter = nil
        let waiters = stopWaiters
        stopWaiters.removeAll()
        for waiter in waiters { waiter.resume() }
    }
}
