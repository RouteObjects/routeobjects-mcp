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

import CIDR
import Foundation

/// The complete v1 tool list. These identifiers are independent of the MCP SDK.
public enum CIDRTool: String, CaseIterable, Sendable {
    case inspect = "cidr_inspect"
    case contains = "cidr_contains"
    case relation = "cidr_relation"
    case summarizeRange = "cidr_summarize_range"

    public var title: String {
        switch self {
        case .inspect: "Inspect an address or network"
        case .contains: "Test address or network containment"
        case .relation: "Compare two networks"
        case .summarizeRange: "Summarize an inclusive address range"
        }
    }

    public var description: String {
        // Describe semantic choices before a client calls the unchanged deterministic contracts.
        switch self {
        case .inspect:
            "Inspect an IPv4/IPv6 literal using its declared meaning. kind=address requires a bare address. kind=address_with_prefix preserves the complete address and prefix length (192.0.2.129/24 stays .129/24) and separately reports the containing network. kind=network requires an aligned prefix by default; networkMode=normalize explicitly permits clearing host bits and reports a diagnostic when those bits change. Do not infer the kind from slash notation alone or normalize an interface address silently. Counts are exact decimal strings for total address coverage, not usable hosts. No DNS, zone identifiers, prefix selectors or operational-context validation. CIPS background: draft-munro-cips-00."
        case .contains:
            "Test bare address membership or whole-network containment within an aligned, same-family IPv4/IPv6 container. Select target.kind=address or network explicitly. A /25 does not contain a /24 just because their first address matches; equal networks contain one another. Network inputs must already be aligned; address-with-prefix targets and implicit normalization are unsupported. The returned basis distinguishes address_membership from network_containment. This mathematical result does not decide route-filter matching, ROA validity, reachability or permission to access a device."
        case .relation:
            "Compare two aligned, same-family IPv4/IPv6 networks. Return equality, proper left/right containment or disjointness, plus overlap and numeric adjacency without address-space wraparound. Preserve operand order. Adjacent networks need not combine into one prefix. Equal address coverage or prefix bits does not establish the same route, allocation, tenant or policy object; VRF, authority and other operational context are outside this calculation. No implicit normalization or prefix-selector evaluation."
        case .summarizeRange:
            "Return the minimal exact CIDR cover of an inclusive IPv4/IPv6 address interval without enumerating addresses. Both endpoints must be bare addresses in the same family. Reversed endpoints fail unless orderPolicy=normalize explicitly requests sorting, which reports a diagnostic. The sorted prefixes cover every address exactly once with no gaps or extra coverage; cardinality is an exact decimal string. This is address-set summarization, not permission to aggregate route filters, ACL rules, allocations or ROAs whose context may differ. Complete covers are never silently truncated."
        }
    }
}

/// A malformed tool argument object. Adapters map this to invalid-params semantics.
public struct ToolInputError: Error, Sendable, Equatable, CustomStringConvertible {
    public let message: String

    public init(message: String) { self.message = message }
    public var description: String { message }
}

/// Pure, bounded calculations and transport-independent JSON contracts.
public enum CIDRToolCore {
    public static let maxArgumentBytes = 8 * 1024
    public static let maxPrefixes = 256

    /// Executes one tool. Shape errors throw; valid-shaped domain failures return an error envelope.
    public static func execute(tool: String, arguments: JSONValue) throws -> JSONValue {
        guard let identifier = CIDRTool(rawValue: tool) else {
            throw ToolInputError(message: "Unknown tool.")
        }
        // Validate all shapes before calculation so lexical domain errors can safely echo bounded input.
        let request = try Request(tool: identifier, arguments: arguments)
        guard try JSONEncoder().encode(arguments).count <= maxArgumentBytes else {
            throw ToolInputError(message: "Tool arguments exceed the encoded size limit.")
        }
        do {
            let calculation = try calculate(request)
            return envelope(
                input: arguments, result: calculation.result, diagnostics: calculation.diagnostics, error: .null)
        } catch let failure as DomainFailure {
            return envelope(input: arguments, result: .null, diagnostics: [], error: failure.json)
        }
    }

    private static func envelope(
        input: JSONValue, result: JSONValue, diagnostics: [JSONValue], error: JSONValue
    ) -> JSONValue {
        [
            "schemaVersion": "1", "input": input, "result": result,
            "diagnostics": .array(diagnostics), "error": error,
        ]
    }

    private static func calculate(_ request: Request) throws -> Calculation {
        switch request {
        case .inspect(let kind, let text, let normalize):
            let address = try parse(text, prefix: kind != .address, field: "/value")
            switch address {
            case .v4(let value): return try inspect(value, kind: kind, normalize: normalize)
            case .v6(let value): return try inspect(value, kind: kind, normalize: normalize)
            }
        case .contains(let container, let targetKind, let target):
            let left = try parse(container, prefix: true, field: "/container")
            let right = try parse(target, prefix: targetKind == .network, field: "/target/value")
            switch (left, right) {
            case (.v4(let left), .v4(let right)): return try contains(left, target: right, kind: targetKind)
            case (.v6(let left), .v6(let right)): return try contains(left, target: right, kind: targetKind)
            default: throw DomainFailure.familyMismatch(field: "/target/value")
            }
        case .relation(let leftText, let rightText):
            let left = try parse(leftText, prefix: true, field: "/left")
            let right = try parse(rightText, prefix: true, field: "/right")
            switch (left, right) {
            case (.v4(let left), .v4(let right)): return try relation(left, right)
            case (.v6(let left), .v6(let right)): return try relation(left, right)
            default: throw DomainFailure.familyMismatch(field: "/right")
            }
        case .summarize(let startText, let endText, let normalize):
            let start = try parse(startText, prefix: false, field: "/start")
            let end = try parse(endText, prefix: false, field: "/end")
            switch (start, end) {
            case (.v4(let start), .v4(let end)): return try summarize(start, end, normalize: normalize)
            case (.v6(let start), .v6(let end)): return try summarize(start, end, normalize: normalize)
            default: throw DomainFailure.familyMismatch(field: "/end")
            }
        }
    }

    private static func parse(_ text: String, prefix: Bool, field: String) throws -> AnyIPAddress {
        guard text.contains("/") == prefix, let value = AnyIPAddress(text, policy: .strict) else {
            throw DomainFailure(
                code: prefix ? "invalid_cidr" : "invalid_address", field: field,
                message: prefix
                    ? "Expected a strict address literal with a valid prefix length."
                    : "Expected a strict bare address literal."
            )
        }
        return value
    }

    private static func aligned<F: IPAddressFamily>(_ address: IPAddress<F>, field: String) throws -> IPNetwork<F> {
        let network = address.network
        // IPNetwork always masks host bits, even with strict parsing; check original storage first.
        guard address.address == network.prefix else {
            throw DomainFailure(code: "host_bits_set", field: field, message: "Network input contains host bits.")
        }
        return network
    }

    private static func inspect<F: IPAddressFamily>(
        _ address: IPAddress<F>, kind: InspectKind, normalize: Bool
    ) throws -> Calculation {
        var fields: [String: JSONValue] = ["kind": .string(kind.rawValue), "family": family(F.self)]
        var diagnostics: [JSONValue] = []
        switch kind {
        case .address:
            fields["canonical"] = .string(address.addressLiteral)
            fields["address"] = .string(address.addressLiteral)
            fields["addressCount"] = "1"
        case .addressWithPrefix:
            fields["canonical"] = .string(address.description)
            fields["address"] = .string(address.addressLiteral)
            fields["prefixLength"] = .integer(Int64(address.prefixBits))
            fields["network"] = try networkRecord(address.network)
        case .network:
            let network = normalize ? address.network : try aligned(address, field: "/value")
            fields["canonical"] = .string(network.description)
            fields["network"] = try networkRecord(network)
            if address.address != network.prefix {
                diagnostics.append(
                    diagnostic(
                        "host_bits_normalized", field: "/value",
                        message: "Host bits were cleared to the network boundary.")
                )
            }
        }
        return Calculation(result: .object(fields), diagnostics: diagnostics)
    }

    private static func contains<F: IPAddressFamily>(
        _ container: IPAddress<F>, target: IPAddress<F>, kind: TargetKind
    ) throws -> Calculation {
        let network = try aligned(container, field: "/container")
        let canonical: String
        let contained: Bool
        switch kind {
        case .address:
            // Bare parsing supplies host-length context, so hierarchical containment is raw address membership here.
            contained = network.contains(address: target)
            canonical = target.addressLiteral
        case .network:
            let targetNetwork = try aligned(target, field: "/target/value")
            contained = network.contains(subnet: targetNetwork)
            canonical = targetNetwork.description
        }
        return Calculation(result: [
            "family": family(F.self), "container": .string(network.description),
            "target": ["kind": .string(kind.rawValue), "value": .string(canonical)],
            "basis": .string(kind == .address ? "address_membership" : "network_containment"),
            "contains": .bool(contained),
        ])
    }

    private static func relation<F: IPAddressFamily>(_ left: IPAddress<F>, _ right: IPAddress<F>) throws -> Calculation
    {
        let first = try aligned(left, field: "/left")
        let second = try aligned(right, field: "/right")
        let relationship: String
        if first == second {
            relationship = "equal"
        } else if first.contains(subnet: second) {
            relationship = "left_contains_right"
        } else if second.contains(subnet: first) {
            relationship = "right_contains_left"
        } else {
            relationship = "disjoint"
        }
        let firstRange = IPAddressRange(covering: first)
        let secondRange = IPAddressRange(covering: second)
        return Calculation(result: [
            "family": family(F.self), "left": .string(first.description), "right": .string(second.description),
            "relation": .string(relationship), "overlaps": .bool(firstRange.overlaps(secondRange)),
            "adjacent": .bool(firstRange.isAdjacent(to: secondRange)),
        ])
    }

    private static func summarize<F: IPAddressFamily>(
        _ start: IPAddress<F>, _ end: IPAddress<F>, normalize: Bool
    ) throws -> Calculation {
        let reversed = start.address > end.address
        guard !reversed || normalize else {
            throw DomainFailure(
                code: "reversed_range", field: "/end", message: "Range end precedes start under strict ordering.")
        }
        let lower = reversed ? end : start
        let upper = reversed ? start : end
        guard let range = IPAddressRange(lowerBound: lower, upperBound: upper) else {
            throw DomainFailure.internalFailure
        }
        // Summarize by integer bounds, never by enumerating the potentially full IPv6 address space.
        let prefixes = IPNetwork<F>.summarize(from: lower, to: upper)
        guard !prefixes.isEmpty, prefixes.count <= maxPrefixes else {
            throw DomainFailure(
                code: "limit_exceeded", field: nil, message: "Range cover exceeds the supported result bound.")
        }
        return Calculation(
            result: [
                "family": family(F.self), "start": .string(lower.addressLiteral), "end": .string(upper.addressLiteral),
                "addressCount": .string(try cardinality(range)), "prefixCount": .integer(Int64(prefixes.count)),
                "prefixes": .array(prefixes.map { .string($0.description) }),
            ],
            diagnostics: reversed
                ? [
                    diagnostic(
                        "endpoints_reordered", field: "/orderPolicy",
                        message: "Endpoints were reordered into ascending address order.")
                ] : []
        )
    }

    private static func networkRecord<F: IPAddressFamily>(_ network: IPNetwork<F>) throws -> JSONValue {
        [
            "cidr": .string(network.description), "prefixLength": .integer(Int64(network.prefixBits)),
            "firstAddress": .string(network.first.addressLiteral), "lastAddress": .string(network.last.addressLiteral),
            "addressCount": .string(try cardinality(IPAddressRange(covering: network))),
        ]
    }

    private static func cardinality<F: IPAddressFamily>(_ range: IPAddressRange<F>) throws -> String {
        if let count = range.rangeSizeIfRepresentable { return String(count) }
        // 2^128 is one beyond UInt128.max; only the verified complete IPv6 range gets this value.
        guard F.bitWidth == 128, range.lowerBound.address == 0, range.upperBound.address == F.Storage.max else {
            throw DomainFailure.internalFailure
        }
        return "340282366920938463463374607431768211456"
    }

    private static func family<F: IPAddressFamily>(_ family: F.Type) -> JSONValue {
        .string(F.ianaValue == AF.V4.ianaValue ? "ipv4" : "ipv6")
    }

    private static func diagnostic(_ code: String, field: String, message: String) -> JSONValue {
        ["code": .string(code), "field": .string(field), "message": .string(message)]
    }
}

private enum InspectKind: String {
    case address
    case addressWithPrefix = "address_with_prefix"
    case network
}

private enum TargetKind: String {
    case address
    case network
}

private struct Calculation {
    let result: JSONValue
    var diagnostics: [JSONValue] = []
}

private struct DomainFailure: Error {
    let code: String
    let field: String?
    let message: String

    var json: JSONValue {
        ["code": .string(code), "field": field.map(JSONValue.string) ?? .null, "message": .string(message)]
    }

    static func familyMismatch(field: String) -> Self {
        Self(code: "family_mismatch", field: field, message: "Both operands must use the same address family.")
    }

    static let internalFailure = Self(
        code: "internal_error", field: nil, message: "The calculation could not be completed.")
}

private enum Request {
    case inspect(InspectKind, String, normalize: Bool)
    case contains(String, TargetKind, String)
    case relation(String, String)
    case summarize(String, String, normalize: Bool)

    init(tool: CIDRTool, arguments: JSONValue) throws {
        let object = try Self.object(arguments, field: "")
        switch tool {
        case .inspect:
            let kindText = try Self.choice(object, key: "kind", values: ["address", "address_with_prefix", "network"])
            guard let kind = InspectKind(rawValue: kindText) else { throw ToolInputError(message: "Invalid kind.") }
            try Self.fields(object, required: ["kind", "value"], optional: kind == .network ? ["networkMode"] : [])
            let text = try Self.literal(object, key: "value")
            let mode = try Self.choice(
                object, key: "networkMode", values: ["require_canonical", "normalize"], default: "require_canonical")
            self = .inspect(kind, text, normalize: mode == "normalize")
        case .contains:
            try Self.fields(object, required: ["container", "target"])
            let container = try Self.literal(object, key: "container")
            let target = try Self.object(object["target"] ?? .null, field: "/target")
            try Self.fields(target, required: ["kind", "value"], field: "/target")
            let kindText = try Self.choice(target, key: "kind", values: ["address", "network"], field: "/target")
            guard let kind = TargetKind(rawValue: kindText) else {
                throw ToolInputError(message: "Invalid target kind.")
            }
            self = .contains(container, kind, try Self.literal(target, key: "value", field: "/target"))
        case .relation:
            try Self.fields(object, required: ["left", "right"])
            self = .relation(try Self.literal(object, key: "left"), try Self.literal(object, key: "right"))
        case .summarizeRange:
            try Self.fields(object, required: ["start", "end"], optional: ["orderPolicy"])
            let start = try Self.literal(object, key: "start")
            let end = try Self.literal(object, key: "end")
            let policy = try Self.choice(
                object, key: "orderPolicy", values: ["strict", "normalize"], default: "strict")
            self = .summarize(start, end, normalize: policy == "normalize")
        }
    }

    private static func object(_ value: JSONValue, field: String) throws -> [String: JSONValue] {
        guard case .object(let object) = value else {
            throw ToolInputError(message: "Expected an object at \(field.isEmpty ? "/" : field).")
        }
        return object
    }

    private static func fields(
        _ object: [String: JSONValue], required: Set<String>, optional: Set<String> = [], field: String = ""
    ) throws {
        guard required.isSubset(of: Set(object.keys)), Set(object.keys).isSubset(of: required.union(optional)) else {
            throw ToolInputError(message: "Missing or unknown fields at \(field.isEmpty ? "/" : field).")
        }
    }

    private static func literal(_ object: [String: JSONValue], key: String, field: String = "") throws -> String {
        guard case .string(let text) = object[key], !text.isEmpty, text.utf8.count <= 64,
            text.utf8.allSatisfy({ $0 < 128 })
        else {
            throw ToolInputError(message: "Expected 1–64 ASCII characters at \(field)/\(key).")
        }
        return text
    }

    private static func choice(
        _ object: [String: JSONValue], key: String, values: Set<String>, default fallback: String? = nil,
        field: String = ""
    ) throws -> String {
        guard let value = object[key] else {
            if let fallback { return fallback }
            throw ToolInputError(message: "Missing field \(field)/\(key).")
        }
        guard case .string(let text) = value, values.contains(text) else {
            throw ToolInputError(message: "Invalid selection at \(field)/\(key).")
        }
        return text
    }
}
