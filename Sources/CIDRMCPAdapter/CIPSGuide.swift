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

// Compile the pinned guide into the executable so resource reads need no files or network access.
enum CIPSGuide {
    static let uri = "routeobjects://routeobjects-mcp/guides/cips-v1"
    static let name = "cips-v1"
    static let title = "CIPS: interpreting address and prefix calculations"
    static let description =
        "Offline guide to the four CIDR tools, informed by draft-munro-cips-00. Explains semantic forms and the calculator's limits."

    static let text = """
        # CIPS guide v1 for routeobjects-mcp

        This guide applies the terminology of Contextual IP Prefix Semantics
        (CIPS), by Craig A. Munro, RouteObjects, to this calculator. Its source is
        draft-munro-cips-00, published 2026-10-03, intended status Informational:

        - [Published HTML](https://www.ietf.org/archive/id/draft-munro-cips-00.html)
        - [Plain text](https://www.ietf.org/archive/id/draft-munro-cips-00.txt)

        The Internet-Draft is work in progress, not an IETF standard or evidence
        of IETF consensus. This guide is an application explanation, not a copy
        of the draft or a claim of complete CIPS support. Guide version v1 is
        independent of the tools' domain-envelope schemaVersion "1".

        ## Choose the semantic form first

        CIPS distinguishes an address, a canonical prefix, an address with
        prefix context, and a prefix selector. A selector can carry a relation
        and prefix-length bounds; its base prefix alone does not preserve it.
        A field's declared meaning determines the form. Slash notation and
        whether trailing bits are zero cannot determine that meaning alone.

        In a prefix-typed field, clearing insignificant bits canonicalizes
        that prefix. Converting a complete address with prefix context to its
        containing network is instead a projection that loses address bits.
        The calculator exposes that projection separately so the original
        contextual address remains available.

        ## Inputs and explicit conversion

        For cidr_inspect, select kind deliberately:

        - "address": one bare IPv4 or IPv6 literal, such as "192.0.2.129".
          A slash is rejected. The result has an addressCount of "1".
        - "address_with_prefix": a complete address and associated length,
          such as "192.0.2.129/24". The address and length are retained.
        - "network": a prefix whose non-prefix bits are zero. An explicit
          length is required, even for a singleton network such as /32 or /128.

        Thus "192.0.2.0/24" with kind "address_with_prefix" remains an address
        with context even though its last octet is zero. The same text with
        kind "network" requests a network. Do not infer an interface, route,
        allocation, or permission from either input.

        Network input defaults to networkMode "require_canonical":
        "192.0.2.129/24" produces host_bits_set. With networkMode "normalize",
        it produces "192.0.2.0/24" and host_bits_normalized. This mode is allowed
        only with kind "network"; neither address kind accepts networkMode.
        IPv6 spelling normalization alone does not produce that diagnostic.
        Original validated input spelling is retained in the result envelope.

        All literals use strict parsing. Whitespace is not trimmed. Padded
        IPv4 octets, names, ports, brackets and IPv6 zone identifiers are not
        accepted. IPv4-mapped IPv6 stays IPv6. No DNS lookup is implicit.

        ## The four calculation tools

        1. cidr_inspect reports an address, contextual address, or network.
           Example: {"kind":"address_with_prefix","value":"192.0.2.129/24"}
           retains address "192.0.2.129", canonical "192.0.2.129/24" and
           prefixLength 24. Its separate network record is "192.0.2.0/24",
           from "192.0.2.0" to "192.0.2.255", with addressCount "256".

        2. cidr_contains distinguishes bare-address membership from containment
           of an entire network. Container "192.0.2.0/25" with target
           {"kind":"network","value":"192.0.2.0/24"} returns contains false:
           the /24 extends outside the /25 although their first addresses match.
           The basis is "network_containment". A bare-address target instead
           uses "address_membership". Contextual targets are rejected.

        3. cidr_relation compares two canonical networks of the same family.
           Left "192.0.2.0/25" and right "192.0.2.128/25" return relation
           "disjoint", overlaps false and adjacent true. Equal networks return
           "equal"; containment labels mean proper containment. Numeric
           adjacency alone does not establish that two prefixes can merge.

        4. cidr_summarize_range returns a minimal, exact cover of an inclusive
           interval without enumerating its addresses. Start "192.0.2.1" and
           end "192.0.2.6" produce addressCount "6", prefixCount 4 and:
           ["192.0.2.1/32","192.0.2.2/31","192.0.2.4/31","192.0.2.6/32"].
           Reversed endpoints fail by default. Explicit orderPolicy "normalize"
           reorders them and reports endpoints_reordered. Covers are never
           silently truncated. A single IPv6 interval needs at most 254 prefixes.

        Containment and relation require aligned network operands; they do not
        silently normalize host bits. Cross-family comparisons fail with
        family_mismatch rather than converting mapped IPv6 into IPv4.

        ## Counts and operational limits

        Counts are total address cardinalities, serialized as decimal strings.
        IPv4 /31 and /32 have "2" and "1"; IPv6 /127 and /128 have "2" and "1".
        The IPv6 network "::/0" has exactly
        "340282366920938463463374607431768211456" addresses. Preserve the string;
        do not convert it through floating-point JSON numbers. These are not
        usable-host counts, and the calculator does not subtract two addresses.

        An address cover describes exactly which addresses are included. It
        does not establish route aggregation safety, equivalent routing policy,
        forwarding behavior, reachability, allocation ownership or authorization.
        Mathematical containment does not prove that an announcement is valid.

        Prefix selectors, more-specific length bounds, policy evaluation and
        longest-prefix route lookup are unsupported. The tools do not represent
        VRFs, tenants, interface scope, route attributes, provenance or validity
        periods. They do not inspect IRR records, validate RPKI, authorize an
        origin AS, authenticate a peer or configure a device. The caller must
        preserve any such context outside these calculation inputs and results.

        This offline guide adds explanatory context, not another calculation
        tool. Successful and domain-error calls keep the existing envelope:
        schemaVersion, input, result, diagnostics and error. Domain errors have
        result null and a stable error code; malformed arguments are protocol
        errors. Check error codes and declared semantics before acting on a result.
        """
}
