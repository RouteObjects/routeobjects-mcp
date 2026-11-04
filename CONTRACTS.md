# routeobjects-mcp tool contracts

Contract version **1** exposes four deterministic operations backed by the public
`CIDR` library. The tools perform address and prefix mathematics. They do not
resolve names, contact network services, enumerate a network, or decide whether
an operation is authorized.

The server publishes JSON Schemas through `tools/list`. Schemas validate object
shape; handlers additionally validate literal grammar, address family, prefix
alignment, and relationships between fields. Objects reject unknown fields.
Defaults are applied by the handler without adding them to the echoed input.

## Literal and numeric rules

- Input literal fields contain 1–64 ASCII characters. Inputs are not trimmed.
- An **address** is a bare IPv4 or IPv6 literal, without a slash.
- An **address with prefix** has exactly one slash and an unsigned, unpadded
  decimal prefix length: 0–32 for IPv4 or 0–128 for IPv6. Its host bits are retained.
- A **network** is an address with prefix whose host bits are zero. Network
  alignment is numeric: uppercase and expanded IPv6 spelling are accepted.
- Strict parsing rejects padded IPv4 octets, including dotted IPv6 tails. Names,
  scope identifiers such as `%eth0`, brackets, URLs and address/port wrappers are
  not accepted. A valid unbracketed IPv6 literal is always interpreted as an
  address, never split into an address and port.
- IPv4-mapped IPv6 remains IPv6. For example, `::ffff:192.0.2.1` is displayed as
  `::ffff:c000:201`. It is not implicitly converted into an IPv4 address.
- Different address families produce `family_mismatch` in binary operations.
- Every cardinality is a positive decimal **string**, including small counts.
  Prefix lengths and the number of returned prefixes are JSON integers.

Counts mean all addresses covered by a prefix or interval. No generic
`usableHosts` convention is inferred. `/31`, `/32`, `/127` and `/128` have counts
`"2"`, `"1"`, `"2"` and `"1"`. IPv4 `/0` has `"4294967296"` addresses; IPv6 `/0`
has `"340282366920938463463374607431768211456"` addresses, exactly 2^128.

## Shared output

A network record contains exactly these fields:

| Field | Meaning |
| --- | --- |
| `cidr` | Canonically formatted, aligned network string. |
| `prefixLength` | Integer valid for the enclosing result's family. |
| `firstAddress` | Bare first address, without prefix context. |
| `lastAddress` | Bare last address, without prefix context. |
| `addressCount` | Exact decimal-string total cardinality. |

Every successful or domain-error response has this domain envelope:

| Field | Meaning |
| --- | --- |
| `schemaVersion` | Constant string `"1"`. |
| `input` | Original validated argument object, including original spelling and omitted defaults. |
| `result` | Tool-specific result on success; `null` on a domain error. |
| `diagnostics` | Ordered `{code, field, message}` array describing explicit normalization; otherwise empty. |
| `error` | `null` on success; otherwise `{code, field, message}`. |

Diagnostic fields are JSON Pointers into the input. Error fields are JSON Pointers
or `null` for a failure that does not identify one input field. Clients should use
the stable codes, rather than branching on explanatory messages. Calculation
results contain no timestamps, timings, process identifiers or generated IDs.

The MCP result contains the same envelope in `structuredContent` and in one JSON
text content block. Domain failures set `isError: true`; successful results set
it to false. The complete text copy supports clients that do not consume
structured content.

## `cidr_inspect`

Required arguments are `kind` and `value`:

| `kind` | `value` | Optional arguments |
| --- | --- | --- |
| `address` | Bare address. | None. |
| `address_with_prefix` | Address with prefix; preserve host bits. | None. |
| `network` | Address with prefix. | `networkMode`: `require_canonical` (default) or `normalize`. |

`networkMode` is forbidden for both address kinds. The default network mode
rejects host bits with `host_bits_set`. Explicit normalization clears host bits
and emits `host_bits_normalized` at `/value` only when bits changed. Formatting
an IPv6 spelling does not emit that diagnostic.

Every result has `kind`, `family` (`ipv4` or `ipv6`) and `canonical`:

- `address` additionally has the bare `address` and `addressCount: "1"`.
- `address_with_prefix` additionally has the bare `address`, `prefixLength` and
  a projected `network` record. Projection does not alter the contextual address.
- `network` additionally has its `network` record.

Example domain response:

```json
{
  "schemaVersion": "1",
  "input": {"kind": "address_with_prefix", "value": "192.0.2.129/24"},
  "result": {
    "kind": "address_with_prefix",
    "family": "ipv4",
    "canonical": "192.0.2.129/24",
    "address": "192.0.2.129",
    "prefixLength": 24,
    "network": {
      "cidr": "192.0.2.0/24",
      "prefixLength": 24,
      "firstAddress": "192.0.2.0",
      "lastAddress": "192.0.2.255",
      "addressCount": "256"
    }
  },
  "diagnostics": [],
  "error": null
}
```

## `cidr_contains`

Required arguments are a canonical `container` network and
`target: {kind: "address" | "network", value: string}`. Address targets must be
bare; network targets must already be aligned. Contextual targets and implicit
normalization are not supported. Both operands must have the same family.

The result contains `family`, canonical `container`, canonical tagged `target`,
`basis` (`address_membership` or `network_containment`) and `contains` (boolean).

Network containment means the **whole target network** fits inside the
container. `192.0.2.0/25` does not contain `192.0.2.0/24`, despite sharing its first
address. Equal networks contain one another. Boundary addresses are included.

## `cidr_relation`

Required arguments are canonical networks `left` and `right`, of the same
family. There are no optional arguments; operand order is preserved.

The result contains `family`, canonical `left` and `right`, `relation`, `overlaps`
and `adjacent`. The relation is one of:

- `equal`;
- `left_contains_right`;
- `right_contains_left`;
- `disjoint`.

Containment labels mean **proper** containment. Equality is checked first.
Aligned CIDR networks of one family are nested or disjoint; they cannot partially
overlap. `overlaps` is true for equality or containment. `adjacent` is true only
for disjoint intervals that touch numerically, without wrapping the maximum
address to zero. Adjacency does not imply that one prefix can represent the union.

For `192.0.2.0/25` and `192.0.2.128/26`, the result is `disjoint`, with
`overlaps: false` and `adjacent: true`.

## `cidr_summarize_range`

Required arguments are bare same-family addresses `start` and `end`.
`orderPolicy` optionally selects `strict` (default) or `normalize`. Strict mode
rejects reversed endpoints. Normalization sorts reversed endpoints and emits
`endpoints_reordered` at `/orderPolicy`.

The result contains `family`, ordered canonical `start` and `end`, exact
`addressCount`, integer `prefixCount`, and a `prefixes` array of canonical
networks. The minimal cover is sorted by starting address and contains every
address in the inclusive interval exactly once, with no gaps or extra coverage.
Equal endpoints produce a single host prefix.

`192.0.2.1` through `192.0.2.6` produces count `"6"` and:

```json
["192.0.2.1/32", "192.0.2.2/31", "192.0.2.4/31", "192.0.2.6/32"]
```

The result cap is 256 prefixes. A single interval needs at most 62 IPv4 prefixes
or 254 IPv6 prefixes, so complete covers fit without pagination or truncation.
The implementation uses integer prefix arithmetic rather than address iteration.

## Failures and bounds

Missing/unknown fields, wrong JSON types, invalid enum selections and violations
of literal-field length/ASCII bounds are argument-shape failures. They map to
JSON-RPC invalid-params errors rather than a domain envelope. Unknown tool names
are also invalid parameters.

Correctly shaped calls can return these domain codes:

| Code | Meaning |
| --- | --- |
| `invalid_address` | Invalid bare literal, including unwanted prefix context. |
| `invalid_cidr` | Invalid address-with-prefix text or missing prefix. |
| `host_bits_set` | Network alignment was required but host bits were present. |
| `family_mismatch` | Operands use different address families. |
| `reversed_range` | Strict range order was violated. |
| `limit_exceeded` | A supported calculation/result bound was exceeded. |
| `internal_error` | An unexpected calculation failure, with sanitized detail. |

Encoded tool arguments are limited to 8 KiB. The transport independently bounds
wire frames and complete MCP results; see the deployment documentation. Schema
version 1 has no batch calculation arguments, address previews or neighboring
network operation. JSON-RPC batch-envelope support, when available for a
negotiated protocol revision, does not change these four domain contracts.
