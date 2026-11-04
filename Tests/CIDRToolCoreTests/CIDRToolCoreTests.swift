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
import CIDRToolCore
import Foundation
import Testing

@Suite("Deterministic CIDR tool contracts")
struct CIDRToolCoreTests {
    @Test("Contextual addresses preserve host bits and expose a separate network")
    func contextualAddress() throws {
        let input: JSONValue = ["kind": "address_with_prefix", "value": "192.0.2.129/24"]
        let response = try call(.inspect, input)
        #expect(response["input"] == input)
        #expect(response["schemaVersion"] == "1")
        #expect(response["error"] == .null)
        #expect(response["diagnostics"] == [])
        #expect(
            response["result"] == [
                "kind": "address_with_prefix", "family": "ipv4", "canonical": "192.0.2.129/24",
                "address": "192.0.2.129", "prefixLength": 24,
                "network": [
                    "cidr": "192.0.2.0/24", "prefixLength": 24, "firstAddress": "192.0.2.0",
                    "lastAddress": "192.0.2.255", "addressCount": "256",
                ],
            ])
    }

    @Test("Network normalization is explicit and only changed host bits produce a diagnostic")
    func networkNormalization() throws {
        try expectError(
            .inspect, ["kind": "network", "value": "192.0.2.129/24"], code: "host_bits_set", field: "/value")
        let normalized = try call(.inspect, ["kind": "network", "value": "192.0.2.129/24", "networkMode": "normalize"])
        #expect(normalized["result"]?["canonical"] == "192.0.2.0/24")
        #expect(normalized["diagnostics"]?.arrayValue?.first?["code"] == "host_bits_normalized")
        #expect(normalized["diagnostics"]?.arrayValue?.first?["field"] == "/value")
        let aligned = try call(.inspect, ["kind": "network", "value": "192.0.2.0/24", "networkMode": "normalize"])
        #expect(aligned["diagnostics"] == [])
        let spelling = try call(.inspect, ["kind": "network", "value": "2001:0DB8:0000:0000::/64"])
        #expect(spelling["result"]?["canonical"] == "2001:db8::/64")
        #expect(spelling["diagnostics"] == [])
    }

    @Test("A bare address has singleton cardinality without manufacturing prefix text")
    func bareAddress() throws {
        let result = try call(.inspect, ["kind": "address", "value": "2001:0DB8::1"])["result"]
        #expect(
            result == [
                "kind": "address", "family": "ipv6", "canonical": "2001:db8::1",
                "address": "2001:db8::1", "addressCount": "1",
            ])
    }

    @Test("Every IPv4 and IPv6 prefix length has exact arithmetic cardinality")
    func everyPrefixCount() throws {
        for prefix in 0...32 {
            let expected = String(UInt64(1) << (32 - prefix))
            let response = try call(.inspect, ["kind": "network", "value": .string("0.0.0.0/\(prefix)")])
            #expect(response["result"]?["network"]?["addressCount"] == .string(expected))
            #expect(response["result"]?["network"]?["prefixLength"] == .integer(Int64(prefix)))
        }
        for prefix in 0...128 {
            let expected =
                prefix == 0 ? "340282366920938463463374607431768211456" : String(UInt128(1) << (128 - prefix))
            let response = try call(.inspect, ["kind": "network", "value": .string("::/\(prefix)")])
            #expect(response["result"]?["network"]?["addressCount"] == .string(expected))
            #expect(response["result"]?["network"]?["prefixLength"] == .integer(Int64(prefix)))
        }
    }

    @Test("Strict literal parsing rejects padded octets, scopes, names, wrappers and prefix context")
    func invalidBareLiterals() throws {
        let literals = [
            "192.000.2.1", "192.0.2.256", "127.1", "0xc0000201", "192.0.2.1/32",
            "::ffff:192.000.2.1", "fe80::1%en0", "fe80::1%3", "[::1]", "[::1]:80",
            "192.0.2.1:80", "example.com", " 192.0.2.1", "192.0.2.1 ", "\n::1", "::1\n",
        ]
        for literal in literals {
            try expectError(
                .inspect, ["kind": "address", "value": .string(literal)], code: "invalid_address", field: "/value")
        }
    }

    @Test("CIDR parsing requires exactly one valid family-specific prefix")
    func invalidCIDRLiterals() throws {
        for literal in [
            "192.0.2.1", "192.0.2.0/024", "192.0.2.0/+24", "192.0.2.0/-1", "192.0.2.0/33", "::/129", "::/00",
            "::/64/64", "::/",
        ] {
            try expectError(
                .inspect, ["kind": "network", "value": .string(literal)], code: "invalid_cidr", field: "/value")
        }
    }

    @Test("Mapped IPv6 is retained as IPv6 without collapsing address families")
    func mappedIPv6() throws {
        let mapped = try call(.inspect, ["kind": "address", "value": "::ffff:192.0.2.1"])
        #expect(mapped["result"]?["family"] == "ipv6")
        #expect(mapped["result"]?["canonical"] == "::ffff:c000:201")
        try expectError(
            .contains, ["container": "192.0.2.0/24", "target": ["kind": "address", "value": "::ffff:192.0.2.1"]],
            code: "family_mismatch", field: "/target/value"
        )
        let contained = try call(
            .contains,
            ["container": "::ffff:c000:200/120", "target": ["kind": "address", "value": "::ffff:192.0.2.1"]])
        #expect(contained["result"]?["contains"] == true)
    }

    @Test("Containment checks the entire target network and treats equal networks as contained")
    func networkContainment() throws {
        for (container, target, expected) in [
            ("192.0.2.0/25", "192.0.2.0/24", false),
            ("192.0.2.0/24", "192.0.2.128/25", true),
            ("192.0.2.0/24", "192.0.2.0/24", true),
            ("192.0.2.0/25", "192.0.2.128/25", false),
            ("::/0", "ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff/128", true),
        ] {
            let response = try call(
                .contains, ["container": .string(container), "target": ["kind": "network", "value": .string(target)]])
            #expect(response["result"]?["contains"] == .bool(expected))
            #expect(response["result"]?["basis"] == "network_containment")
        }
        try expectError(
            .contains, ["container": "192.0.2.1/24", "target": ["kind": "address", "value": "192.0.2.2"]],
            code: "host_bits_set", field: "/container")
        try expectError(
            .contains, ["container": "192.0.2.0/24", "target": ["kind": "network", "value": "192.0.2.129/25"]],
            code: "host_bits_set", field: "/target/value")
    }

    @Test("Address membership includes boundary addresses and rejects contextual targets")
    func addressMembership() throws {
        for (address, expected) in [("192.0.2.0", true), ("192.0.2.127", true), ("192.0.2.128", false)] {
            let response = try call(
                .contains, ["container": "192.0.2.0/25", "target": ["kind": "address", "value": .string(address)]])
            #expect(response["result"]?["contains"] == .bool(expected))
            #expect(response["result"]?["basis"] == "address_membership")
        }
        try expectError(
            .contains, ["container": "192.0.2.0/24", "target": ["kind": "address", "value": "192.0.2.1/32"]],
            code: "invalid_address", field: "/target/value")
        #expect(throws: ToolInputError.self) {
            try call(
                .contains,
                ["container": "192.0.2.0/24", "target": ["kind": "address_with_prefix", "value": "192.0.2.1/24"]])
        }
    }

    @Test("Relations distinguish equal, proper containment and adjacency without wraparound")
    func relations() throws {
        let fixtures: [(String, String, String, Bool, Bool)] = [
            ("192.0.2.0/24", "192.0.2.0/24", "equal", true, false),
            ("192.0.2.0/24", "192.0.2.0/25", "left_contains_right", true, false),
            ("192.0.2.0/25", "192.0.2.0/24", "right_contains_left", true, false),
            ("192.0.2.0/25", "192.0.2.128/26", "disjoint", false, true),
            ("192.0.2.0/26", "192.0.2.128/26", "disjoint", false, false),
            ("255.255.255.255/32", "0.0.0.0/32", "disjoint", false, false),
            ("ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff/128", "::/128", "disjoint", false, false),
            ("2001:0DB8:0000::/32", "2001:db8::/32", "equal", true, false),
        ]
        for (left, right, relation, overlaps, adjacent) in fixtures {
            let result = try call(.relation, ["left": .string(left), "right": .string(right)])["result"]
            #expect(result?["relation"] == .string(relation))
            #expect(result?["overlaps"] == .bool(overlaps))
            #expect(result?["adjacent"] == .bool(adjacent))
        }
        try expectError(.relation, ["left": "0.0.0.0/0", "right": "::/0"], code: "family_mismatch", field: "/right")
        try expectError(
            .relation, ["left": "192.0.2.1/24", "right": "192.0.2.0/24"], code: "host_bits_set", field: "/left")
    }

    @Test("Range summary is minimal, inclusive, sorted and normalizes only on request")
    func rangeSummary() throws {
        let input: JSONValue = ["start": "192.0.2.1", "end": "192.0.2.6"]
        let response = try call(.summarizeRange, input)
        #expect(response["input"] == input)
        #expect(
            response["result"] == [
                "family": "ipv4", "start": "192.0.2.1", "end": "192.0.2.6", "addressCount": "6", "prefixCount": 4,
                "prefixes": ["192.0.2.1/32", "192.0.2.2/31", "192.0.2.4/31", "192.0.2.6/32"],
            ])
        try expectError(
            .summarizeRange, ["start": "192.0.2.6", "end": "192.0.2.1"], code: "reversed_range", field: "/end")
        let normalizedInput: JSONValue = ["start": "192.0.2.6", "end": "192.0.2.1", "orderPolicy": "normalize"]
        let normalized = try call(.summarizeRange, normalizedInput)
        #expect(normalized["input"] == normalizedInput)
        #expect(normalized["result"] == response["result"])
        #expect(normalized["diagnostics"]?.arrayValue?.first?["code"] == "endpoints_reordered")
        #expect(normalized["diagnostics"]?.arrayValue?.first?["field"] == "/orderPolicy")
        let unchanged = try call(.summarizeRange, ["start": "::1", "end": "::2", "orderPolicy": "normalize"])
        #expect(unchanged["diagnostics"] == [])
        try expectError(.summarizeRange, ["start": "::1/128", "end": "::2"], code: "invalid_address", field: "/start")
        try expectError(.summarizeRange, ["start": "192.0.2.1", "end": "::2"], code: "family_mismatch", field: "/end")
    }

    @Test("Full and singleton ranges retain exact cardinality at overflow boundaries")
    func fullAndSingletonRanges() throws {
        let full = try call(.summarizeRange, ["start": "::", "end": "ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff"])
        #expect(full["result"]?["addressCount"] == "340282366920938463463374607431768211456")
        #expect(full["result"]?["prefixes"] == ["::/0"])
        #expect(full["result"]?["prefixCount"] == 1)
        for (address, prefix) in [
            ("255.255.255.255", "255.255.255.255/32"),
            ("ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff", "ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff/128"),
        ] {
            let singleton = try call(.summarizeRange, ["start": .string(address), "end": .string(address)])
            #expect(singleton["result"]?["addressCount"] == "1")
            #expect(singleton["result"]?["prefixes"] == .array([.string(prefix)]))
        }
    }

    @Test("Worst-case covers fit within the cap and independently conserve address count")
    func worstCaseRanges() throws {
        let v4 = try call(.summarizeRange, ["start": "0.0.0.1", "end": "255.255.255.254"])
        #expect(v4["result"]?["prefixCount"] == 62)
        #expect(v4["result"]?["addressCount"] == "4294967294")
        try assertCover(v4, from: UInt32(1), to: UInt32.max - 1, family: AF.V4.self)
        let v6 = try call(.summarizeRange, ["start": "::1", "end": "ffff:ffff:ffff:ffff:ffff:ffff:ffff:fffe"])
        #expect(v6["result"]?["prefixCount"] == 254)
        #expect(v6["result"]?["addressCount"] == "340282366920938463463374607431768211454")
        try assertCover(v6, from: UInt128(1), to: UInt128.max - 1, family: AF.V6.self)
        let encoded = try JSONEncoder().encode(v6)
        // The adapter adds its own envelope and text copy; the largest domain cover leaves ample room.
        #expect(encoded.count * 2 < 60 * 1024)
    }

    @Test("All bounded endpoint pairs have exact coverage with no mergeable siblings")
    func boundedRangeProperties() throws {
        for start in UInt32(0)...31 {
            for end in start...31 {
                let response = try call(
                    .summarizeRange, ["start": .string("0.0.0.\(start)"), "end": .string("0.0.0.\(end)")])
                try assertCover(response, from: start, to: end, family: AF.V4.self)
            }
        }
    }

    @Test("Cover validation rejects emitted host bits that network parsing would erase")
    func coverValidationRejectsHostBits() throws {
        let response = try call(.summarizeRange, ["start": "0.0.0.0", "end": "0.0.0.3"])
        try assertCover(response, from: UInt32(0), to: UInt32(3), family: AF.V4.self)

        var envelope = try #require(response.objectValue)
        var result = try #require(response["result"]?.objectValue)
        result["prefixes"] = ["0.0.0.1/30"]
        envelope["result"] = .object(result)
        #expect(throws: CoverValidationError.self) {
            try assertCover(.object(envelope), from: UInt32(0), to: UInt32(3), family: AF.V4.self)
        }
    }

    @Test("Shape violations throw without manufacturing a successful domain envelope")
    func shapeErrors() {
        let fixtures: [(CIDRTool, JSONValue)] = [
            (.inspect, .null), (.inspect, []), (.inspect, ["kind": "address"]),
            (.inspect, ["kind": "address", "value": true]), (.inspect, ["kind": "address", "value": 1]),
            (.inspect, ["kind": "address", "value": ""]), (.inspect, ["kind": "address", "value": "é"]),
            (.inspect, ["kind": "address", "value": .string(String(repeating: "a", count: 65))]),
            (.inspect, ["kind": "address", "value": "::1", "extra": true]),
            (.inspect, ["kind": "address", "value": "::1", "networkMode": "normalize"]),
            (.inspect, ["kind": "address_with_prefix", "value": "::1/64", "networkMode": "normalize"]),
            (.inspect, ["kind": "network", "value": "::/0", "networkMode": "forgiving"]),
            (.contains, ["container": "::/0", "target": "::1"]),
            (.contains, ["container": "::/0", "target": ["kind": "address", "value": "::1", "extra": false]]),
            (.relation, ["left": "::/0", "right": "::/0", "normalize": true]),
            (.summarizeRange, ["start": "::1", "end": "::2", "orderPolicy": false]),
        ]
        for (tool, input) in fixtures {
            #expect(throws: ToolInputError.self) { try call(tool, input) }
        }
        #expect(throws: ToolInputError.self) { try CIDRToolCore.execute(tool: "unregistered_tool", arguments: [:]) }
    }

    @Test("Domain envelopes are deterministic, exactly shaped and JSON round-trippable")
    func envelopeIdentity() throws {
        let input: JSONValue = ["kind": "address_with_prefix", "value": "2001:0DB8::129/64"]
        let first = try call(.inspect, input)
        let second = try call(.inspect, input)
        #expect(first == second)
        #expect(
            Set(try #require(first.objectValue).keys) == ["schemaVersion", "input", "result", "diagnostics", "error"])
        #expect(try JSONDecoder().decode(JSONValue.self, from: JSONEncoder().encode(first)) == first)
        let failure = try call(.inspect, ["kind": "address", "value": "example.com"])
        #expect(failure["result"] == .null)
        #expect(failure["diagnostics"] == [])
        #expect(failure["error"]?["code"] == "invalid_address")
        #expect(try JSONDecoder().decode(JSONValue.self, from: JSONEncoder().encode(failure)) == failure)
    }

    @Test("JSON values distinguish boolean, integer and string boundary types")
    func jsonValueTypes() throws {
        #expect(try JSONDecoder().decode(JSONValue.self, from: Data("true".utf8)) == .bool(true))
        #expect(try JSONDecoder().decode(JSONValue.self, from: Data("1".utf8)) == .integer(1))
        #expect(try JSONDecoder().decode(JSONValue.self, from: Data("1.5".utf8)) == .number(1.5))
        #expect(try JSONDecoder().decode(JSONValue.self, from: Data("\"1\"".utf8)) == .string("1"))
        #expect(throws: EncodingError.self) { try JSONEncoder().encode(JSONValue.number(.infinity)) }
    }

    private func call(_ tool: CIDRTool, _ arguments: JSONValue) throws -> JSONValue {
        try CIDRToolCore.execute(tool: tool.rawValue, arguments: arguments)
    }

    private func expectError(_ tool: CIDRTool, _ arguments: JSONValue, code: String, field: String) throws {
        let response = try call(tool, arguments)
        #expect(response["input"] == arguments)
        #expect(response["result"] == .null)
        #expect(response["error"]?["code"] == .string(code))
        #expect(response["error"]?["field"] == .string(field))
        #expect(response["diagnostics"] == [])
    }

    private enum CoverValidationError: Error {
        case noncanonicalLiteral(String)
    }

    private func canonicalCoverNetwork<F: IPAddressFamily>(
        _ literal: String, family: F.Type
    ) throws -> IPNetwork<F> {
        let network = try #require(IPNetwork<F>(literal, policy: .strict))
        // CHANGE: Check emitted text because the network parser masks host bits even under strict parsing.
        guard literal == network.description else {
            throw CoverValidationError.noncanonicalLiteral(literal)
        }
        return network
    }

    private func assertCover<F: IPAddressFamily>(
        _ response: JSONValue, from lower: F.Storage, to upper: F.Storage, family: F.Type
    ) throws {
        let text = try #require(response["result"]?["prefixes"]?.arrayValue)
        let networks = try text.map { value in
            let literal = try #require(value.stringValue)
            return try canonicalCoverNetwork(literal, family: family)
        }
        #expect(networks.first?.first.address == lower)
        #expect(networks.last?.last.address == upper)
        #expect(response["result"]?["prefixCount"] == .integer(Int64(networks.count)))
        var total: UInt128 = 0
        for (index, network) in networks.enumerated() {
            let exponent = F.bitWidth - network.prefixBits
            // These fixtures exclude the full IPv6 space, so this independent sum fits UInt128.
            total += UInt128(1) << exponent
            guard index > 0 else { continue }
            let previous = networks[index - 1]
            #expect(previous.last.address < network.first.address)
            #expect(previous.last.address + 1 == network.first.address)
            if previous.prefixBits == network.prefixBits, previous.prefixBits > 0 {
                let parentBits = previous.prefixBits - 1
                let mask = parentBits == 0 ? F.Storage.zero : F.Storage.max << (F.bitWidth - parentBits)
                #expect(previous.prefix & mask != network.prefix & mask)
            }
        }
        let expected = UInt128(upper) - UInt128(lower) + 1
        #expect(total == expected)
        #expect(response["result"]?["addressCount"] == .string(String(expected)))
    }
}
