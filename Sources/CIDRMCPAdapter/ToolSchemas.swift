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

// Presentation schemas belong to the replaceable MCP adapter, outside deterministic domain operations.
enum CIDRToolSchemas {
    /// JSON Schema for argument shape. Literal grammar and numeric alignment are domain validation.
    static func inputSchema(for tool: CIDRTool) -> JSONValue {
        let schema: JSONValue
        switch tool {
        case .inspect:
            schema = [
                "type": "object",
                // Form clients discover fields at the root; oneOf still enforces each kind's exact contract.
                "properties": [
                    "kind": Schema.selection(["address", "address_with_prefix", "network"]),
                    "value": Schema.literal,
                    "networkMode": Schema.selection(["require_canonical", "normalize"]),
                ],
                "required": ["kind", "value"],
                "additionalProperties": false,
                "oneOf": .array([
                    Schema.object(["kind": Schema.constant("address"), "value": Schema.literal]),
                    Schema.object(["kind": Schema.constant("address_with_prefix"), "value": Schema.literal]),
                    Schema.object(
                        [
                            "kind": Schema.constant("network"), "value": Schema.literal,
                            "networkMode": Schema.selection(
                                ["require_canonical", "normalize"], default: "require_canonical"),
                        ], optional: ["networkMode"]
                    ),
                ]),
            ]
        case .contains:
            schema = Schema.object([
                "container": Schema.literal,
                "target": Schema.object(["kind": Schema.selection(["address", "network"]), "value": Schema.literal]),
            ])
        case .relation:
            schema = Schema.object(["left": Schema.literal, "right": Schema.literal])
        case .summarizeRange:
            schema = Schema.object(
                [
                    "start": Schema.literal, "end": Schema.literal,
                    "orderPolicy": Schema.selection(["strict", "normalize"], default: "strict"),
                ], optional: ["orderPolicy"]
            )
        }
        return Schema.dialect(schema)
    }

    /// JSON Schema for the complete success/error envelope, including the specific tool's result.
    static func outputSchema(for tool: CIDRTool) -> JSONValue {
        let resultVariants = ["ipv4", "ipv6"].flatMap { resultSchemas(for: tool, family: $0) }
        let input = inputSchema(for: tool)
        let success = Schema.object([
            "schemaVersion": Schema.constant("1"), "input": input,
            "result": ["oneOf": .array(resultVariants)],
            "diagnostics": Schema.array(Schema.diagnostic, maximum: 1), "error": ["type": "null"],
        ])
        let failure = Schema.object([
            "schemaVersion": Schema.constant("1"), "input": input, "result": ["type": "null"],
            "diagnostics": Schema.array(Schema.diagnostic, maximum: 0), "error": Schema.error,
        ])
        // Disjoint success/error branches prohibit accidental success payloads on an error response.
        return Schema.dialect(["type": "object", "oneOf": .array([success, failure])])
    }

    private static func resultSchemas(for tool: CIDRTool, family: String) -> [JSONValue] {
        let network = Schema.network(family: family)
        let familySchema = Schema.constant(family)
        let cidr = Schema.canonicalCIDR(family: family)
        let address = Schema.canonicalAddress(family: family)
        switch tool {
        case .inspect:
            return [
                Schema.object([
                    "kind": Schema.constant("address"), "family": familySchema, "canonical": address,
                    "address": address, "addressCount": Schema.constant("1"),
                ]),
                Schema.object([
                    "kind": Schema.constant("address_with_prefix"), "family": familySchema, "canonical": cidr,
                    "address": address, "prefixLength": Schema.prefixLength(family: family), "network": network,
                ]),
                Schema.object([
                    "kind": Schema.constant("network"), "family": familySchema, "canonical": cidr, "network": network,
                ]),
            ]
        case .contains:
            // Tie the result basis to its target tag, rather than permitting contradictory combinations.
            return [
                Schema.object([
                    "family": familySchema, "container": cidr,
                    "target": Schema.object(["kind": Schema.constant("address"), "value": address]),
                    "basis": Schema.constant("address_membership"), "contains": ["type": "boolean"],
                ]),
                Schema.object([
                    "family": familySchema, "container": cidr,
                    "target": Schema.object(["kind": Schema.constant("network"), "value": cidr]),
                    "basis": Schema.constant("network_containment"), "contains": ["type": "boolean"],
                ]),
            ]
        case .relation:
            let common: [String: JSONValue] = ["family": familySchema, "left": cidr, "right": cidr]
            return [
                Schema.object(
                    common.merging(
                        [
                            "relation": Schema.selection(["equal", "left_contains_right", "right_contains_left"]),
                            "overlaps": ["const": true], "adjacent": ["const": false],
                        ], uniquingKeysWith: { _, new in new })),
                Schema.object(
                    common.merging(
                        [
                            "relation": Schema.constant("disjoint"), "overlaps": ["const": false],
                            "adjacent": ["type": "boolean"],
                        ], uniquingKeysWith: { _, new in new })),
            ]
        case .summarizeRange:
            return [
                Schema.object([
                    "family": familySchema, "start": address, "end": address, "addressCount": Schema.cardinality,
                    "prefixCount": [
                        "type": "integer", "minimum": 1, "maximum": .integer(Int64(CIDRToolCore.maxPrefixes)),
                    ],
                    "prefixes": Schema.array(cidr, minimum: 1, maximum: CIDRToolCore.maxPrefixes),
                ])
            ]
        }
    }
}

private enum Schema {
    static let literal: JSONValue = [
        "type": "string", "minLength": 1, "maxLength": 64, "pattern": "^[\\u0000-\\u007f]+$",
        "description": "1–64 ASCII characters. Strict IP literal grammar is validated by the tool; no DNS or trimming.",
    ]
    static let cardinality: JSONValue = [
        "type": "string", "pattern": "^[1-9][0-9]*$", "minLength": 1, "maxLength": 39,
    ]
    static let diagnostic: JSONValue = object([
        "code": selection(["host_bits_normalized", "endpoints_reordered"]),
        "field": ["type": "string", "pattern": "^/"], "message": ["type": "string", "minLength": 1],
    ])
    static let error: JSONValue = object([
        "code": selection([
            "invalid_address", "invalid_cidr", "host_bits_set", "family_mismatch", "reversed_range", "limit_exceeded",
            "internal_error",
        ]),
        "field": ["anyOf": [["type": "string", "pattern": "^/"], ["type": "null"]]],
        "message": ["type": "string", "minLength": 1],
    ])

    static func dialect(_ schema: JSONValue) -> JSONValue {
        guard case .object(var fields) = schema else { return schema }
        fields["$schema"] = "https://json-schema.org/draft/2020-12/schema"
        return .object(fields)
    }

    static func object(_ properties: [String: JSONValue], optional: Set<String> = []) -> JSONValue {
        [
            "type": "object", "properties": .object(properties), "additionalProperties": false,
            "required": .array(properties.keys.filter { !optional.contains($0) }.sorted().map(JSONValue.string)),
        ]
    }

    static func selection(_ values: [String], default fallback: String? = nil) -> JSONValue {
        var result: [String: JSONValue] = ["type": "string", "enum": .array(values.map(JSONValue.string))]
        if let fallback { result["default"] = .string(fallback) }
        return .object(result)
    }

    static func constant(_ value: String) -> JSONValue { ["type": "string", "const": .string(value)] }

    static func array(_ items: JSONValue, minimum: Int = 0, maximum: Int) -> JSONValue {
        ["type": "array", "items": items, "minItems": .integer(Int64(minimum)), "maxItems": .integer(Int64(maximum))]
    }

    static func prefixLength(family: String) -> JSONValue {
        ["type": "integer", "minimum": 0, "maximum": .integer(family == "ipv4" ? 32 : 128)]
    }

    static func canonicalAddress(family: String) -> JSONValue {
        [
            "type": "string", "minLength": 1, "maxLength": 39,
            "pattern": .string(family == "ipv4" ? "^[0-9]+(\\.[0-9]+){3}$" : "^[0-9a-f:]+$"),
            "description": .string("Canonical bare \(family) literal; numeric grammar is enforced by CIDR."),
        ]
    }

    static func canonicalCIDR(family: String) -> JSONValue {
        [
            "type": "string", "minLength": 3, "maxLength": 43,
            "pattern": .string(
                family == "ipv4" ? "^[0-9]+(\\.[0-9]+){3}/(0|[1-9][0-9]?)$" : "^[0-9a-f:]+/(0|[1-9][0-9]{0,2})$"),
            "description": .string(
                "Canonical \(family) CIDR text; address bits and family prefix bounds are enforced by CIDR."),
        ]
    }

    static func network(family: String) -> JSONValue {
        object([
            "cidr": canonicalCIDR(family: family), "prefixLength": prefixLength(family: family),
            "firstAddress": canonicalAddress(family: family), "lastAddress": canonicalAddress(family: family),
            "addressCount": cardinality,
        ])
    }
}
