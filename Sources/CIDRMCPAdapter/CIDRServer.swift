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

public enum CIDRServer {
    public static func make(logger: Logger) async throws -> Server {
        #if ROUTEOBJECTS_PATCHED_SDK
            let configuration = Server.Configuration(
                strict: true, maxConcurrentRequests: 4, maxQueuedRequests: 8,
                maxBatchItems: 8, maxResponseBytes: 65_535, maxPendingControlResponses: 64)
        #else
            let configuration = Server.Configuration.strict
        #endif
        let server = Server(
            name: BuildInfo.name, version: BuildInfo.version,
            // Essential semantics accompany discovery; reading the optional guide is not required for correctness.
            instructions:
                "Deterministic IPv4/IPv6 calculations. Choose address, address_with_prefix, or network from the caller's declared meaning, not slash notation alone. Preserve contextual host bits; normalize a network only when requested. Counts describe total address coverage, not usable hosts. Containment and range covers do not establish routing policy, reachability or authorization. No DNS or network access. Optional CIPS guide: \(CIPSGuide.uri), based on draft-munro-cips-00 (work in progress).",
            capabilities: .init(
                resources: .init(subscribe: false, listChanged: false), tools: .init(listChanged: false)),
            configuration: configuration)
        // A fixed in-binary resource preserves single-executable installation and never resolves arbitrary URIs.
        let guide = Resource(
            name: CIPSGuide.name, uri: CIPSGuide.uri, title: CIPSGuide.title,
            description: CIPSGuide.description, mimeType: "text/markdown", size: CIPSGuide.text.utf8.count)
        await server.withMethodHandler(ValidatedMethod<ListResources>.self) { raw in
            let parameters = try raw.decode(ListResources.Parameters.self, errorMessage: "Invalid resource parameters.")
            guard parameters.cursor == nil else { throw MCPError.invalidParams("Unknown resource cursor.") }
            return .init(resources: [guide])
        }
        await server.withMethodHandler(ValidatedMethod<ListResourceTemplates>.self) { raw in
            let parameters = try raw.decode(
                ListResourceTemplates.Parameters.self, errorMessage: "Invalid resource parameters.")
            guard parameters.cursor == nil else { throw MCPError.invalidParams("Unknown resource-template cursor.") }
            return .init(templates: [])
        }
        await server.withMethodHandler(ValidatedMethod<ReadResource>.self) { raw in
            let parameters = try raw.decode(ReadResource.Parameters.self, errorMessage: "Invalid resource parameters.")
            guard parameters.uri == CIPSGuide.uri else {
                throw MCPError.serverError(code: -32002, message: "Resource not found.")
            }
            return .init(contents: [.text(CIPSGuide.text, uri: CIPSGuide.uri, mimeType: "text/markdown")])
        }
        let tools = try CIDRTool.allCases.map { tool in
            Tool(
                name: tool.rawValue, title: tool.title, description: tool.description,
                inputSchema: try sdkValue(CIDRToolSchemas.inputSchema(for: tool)),
                annotations: .init(
                    readOnlyHint: true, destructiveHint: false, idempotentHint: true, openWorldHint: false),
                outputSchema: try sdkValue(CIDRToolSchemas.outputSchema(for: tool)))
        }
        await server.withMethodHandler(ListTools.self) { _ in .init(tools: tools) }
        await server.withMethodHandler(ValidatedMethod<CallTool>.self) { raw in
            // Validate the outer call shape inside the handler so SDK decoding cannot misclassify it as -32603.
            let parameters = try raw.decode(CallTool.Parameters.self, errorMessage: "Invalid tool parameters.")
            // Unknown caller-controlled names are excluded from logs, including error diagnostics.
            guard let tool = CIDRTool(rawValue: parameters.name) else {
                throw MCPError.invalidParams("Unknown tool.")
            }
            let clock = ContinuousClock()
            let start = clock.now
            do {
                try Task.checkCancellation()
                let arguments = try JSONDecoder().decode(
                    JSONValue.self, from: JSONEncoder().encode(parameters.arguments ?? [:]))
                let envelope = try CIDRToolCore.execute(tool: tool.rawValue, arguments: arguments)
                try Task.checkCancellation()
                let result = try result(envelope)
                let elapsed = start.duration(to: clock.now).components
                let milliseconds = elapsed.seconds * 1000 + elapsed.attoseconds / 1_000_000_000_000_000
                logger.info(
                    "tool_completed",
                    metadata: [
                        "tool": .string(tool.rawValue), "durationMs": .string(String(milliseconds)),
                        "errorCode": .string(envelope["error"]?["code"]?.stringValue ?? "none"),
                    ])
                return result
            } catch let error as ToolInputError {
                throw MCPError.invalidParams(error.message)
            }
        }
        return server
    }

    static func sdkValue(_ value: JSONValue) throws -> MCP.Value {
        try JSONDecoder().decode(MCP.Value.self, from: JSONEncoder().encode(value))
    }

    /// Both wire representations originate from exactly the same domain envelope.
    static func result(_ envelope: JSONValue) throws -> CallTool.Result {
        let encoder = JSONEncoder()
        encoder.outputFormatting = [.sortedKeys, .withoutEscapingSlashes]
        let data = try encoder.encode(envelope)
        return CallTool.Result(
            content: [.text(text: String(decoding: data, as: UTF8.self), annotations: nil, _meta: nil)],
            structuredContent: Optional.some(try JSONDecoder().decode(MCP.Value.self, from: data)),
            isError: envelope["error"] != .null)
    }
}

// SDK 0.12.1 maps parameter-decoding failures to internal errors. Decode resource and tool
// parameters in the adapter handler so malformed input gets -32602, with no SDK or tool-contract change.
private enum ValidatedMethod<M: MCP.Method>: MCP.Method {
    static var name: String { M.name }
    typealias Parameters = RawMethodParameters
    typealias Result = M.Result
}

private struct RawMethodParameters: NotRequired, Hashable, Codable, Sendable {
    let value: MCP.Value

    init() { value = .object([:]) }

    init(from decoder: Decoder) throws { value = try MCP.Value(from: decoder) }

    func encode(to encoder: Encoder) throws { try value.encode(to: encoder) }

    func decode<T: Decodable>(_ type: T.Type, errorMessage: String) throws -> T {
        do {
            return try JSONDecoder().decode(type, from: JSONEncoder().encode(value))
        } catch {
            throw MCPError.invalidParams(errorMessage)
        }
    }
}
