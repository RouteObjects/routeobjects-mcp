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

#if canImport(Darwin)
    import Darwin
#elseif canImport(Glibc)
    import Glibc
#else
    import Musl
#endif

public enum CommandLineServer {
    public static func run() async {
        let arguments = Array(CommandLine.arguments.dropFirst())
        if arguments == ["--version"] {
            print("\(BuildInfo.name) \(BuildInfo.version)")
            return
        }
        if arguments == ["--help"] || arguments == ["-h"] {
            print(
                """
                routeobjects-mcp 0.1.0
                Usage: routeobjects-mcp [--stdio | --help | --version]
                Four deterministic CIDR tools over local MCP stdio.
                Server mode reserves stdout for JSON-RPC; diagnostics are JSON lines on stderr.
                This pilot requires the reviewed RouteObjects SDK maintenance patch.
                """)
            return
        }
        signal(SIGPIPE, SIG_IGN)
        guard let sink = try? JSONLogSink() else { exit(1) }
        sink.start()
        LoggingSystem.bootstrap { JSONLogHandler(label: $0, sink: sink) }
        let logger = Logger(label: BuildInfo.name)
        guard arguments.isEmpty || arguments == ["--stdio"] else {
            logger.error("invalid_command_line")
            await sink.finish()
            exit(64)
        }
        // A stock SDK build may run contract tests, but cannot silently claim bounded request lifecycle.
        guard BuildInfo.usesDevelopmentSDK else {
            logger.error(
                "patched_sdk_required", metadata: ["sdkBaseline": .string(BuildInfo.sdkBaseline)])
            await sink.finish()
            exit(78)
        }
        let transport = BoundedStdioTransport(logger: Logger(label: "mcp.transport"))
        do {
            let server = try await CIDRServer.make(logger: logger)
            try await serve(
                signals: TerminationSignalBridge(),
                start: {
                    try await server.start(transport: transport)
                    logger.info(
                        "server_started",
                        metadata: [
                            "version": .string(BuildInfo.version), "sdkBaseline": .string(BuildInfo.sdkBaseline),
                        ])
                },
                waitUntilCompleted: { await server.waitUntilCompleted() },
                waitUntilInputClosed: { await transport.waitUntilInputClosed() },
                stop: {
                    // Release blocked I/O before awaiting SDK task cleanup.
                    await transport.disconnect()
                    await server.stop()
                })
            if await transport.terminalFailure != nil {
                logger.error("transport_failed")
                await sink.finish()
                exit(1)
            }
            logger.info("server_stopped")
            await sink.finish()
        } catch {
            logger.error("server_failed")
            await transport.disconnect()
            await sink.finish()
            exit(1)
        }
    }

    /// Coordinates startup and shutdown without tying signal ownership to stream lifetime.
    /// Internal closures let tests hold startup/cleanup at explicit suspension points.
    static func serve(
        signals: TerminationSignalBridge,
        start: @escaping @Sendable () async throws -> Void,
        waitUntilCompleted: @escaping @Sendable () async -> Void,
        waitUntilInputClosed: @escaping @Sendable () async -> Void,
        stop: @escaping @Sendable () async -> Void
    ) async throws {
        let outcome = await withTaskGroup(of: Result<Void, any Error>.self) { group in
            group.addTask {
                do {
                    try Task.checkCancellation()
                    try await signals.start()
                    try await start()
                    await waitUntilCompleted()
                    return .success(())
                } catch { return .failure(error) }
            }
            group.addTask {
                for await _ in signals.events { break }
                return .success(())
            }
            group.addTask {
                await waitUntilInputClosed()
                return .success(())
            }
            let outcome = await group.next() ?? .success(())
            // Keep the deadline alive through child-task joins, including startup that
            // ignores cancellation. Requesting cancellation is not completed teardown.
            let shutdownDeadline = Task {
                do { try await Task.sleep(for: .seconds(5)) } catch { return }
                exit(70)
            }
            group.cancelAll()
            await stop()
            await signals.stop()
            while await group.next() != nil {}
            shutdownDeadline.cancel()
            return outcome
        }
        try outcome.get()
        try Task.checkCancellation()
    }
}
