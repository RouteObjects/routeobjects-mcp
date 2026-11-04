# Bundled CIPS guide

The server exposes one static Markdown resource:

```text
routeobjects://routeobjects-mcp/guides/cips-v1
```

Its content is compiled into `CIDRMCPAdapter` from `CIPSGuide.swift`. Installation
still needs only the executable. Reading the guide performs no file lookup, DNS
resolution or download. Unknown URIs are rejected; the URI is an identifier, not
a general fetch endpoint.

The guide is an application explanation based on Craig A. Munro, RouteObjects,
**Contextual IP Prefix Semantics**, [draft-munro-cips-00, 3 October 2026](https://www.ietf.org/archive/id/draft-munro-cips-00.html).
That Internet-Draft is work in progress, with intended Informational status; it is
not an RFC, IETF standard or evidence of IETF consensus. This guide uses the
published revision 00, not an unpublished working draft, and does not claim
complete CIPS support. Guide revision `v1` is independent of domain-envelope
`schemaVersion: "1"`.

## Meaning before calculation

`192.0.2.129/24` with `kind: "address_with_prefix"` retains the complete address and
length and separately reports `192.0.2.0/24`. With `kind: "network"`, the same text
fails canonical validation unless the caller explicitly selects
`networkMode: "normalize"`. Clearing non-prefix bits in a prefix-typed field is
canonicalization; replacing an address with its containing network is a projection
that loses address identity. Slash notation alone does not decide the field's
meaning, even when its trailing bits happen to be zero.

The guide also explains whole-network containment, exact cardinalities rather
than usable-host counts, adjacency, and minimal interval covers. Address-set
calculations do not establish routing-policy equivalence, ROA validity,
reachability or permission to access a device. Prefix selectors and operational
context such as VRFs, authority and validity periods remain outside these tools.

## MCP surface

The server advertises `resources` with `subscribe: false` and `listChanged: false`.
The resource is immutable for the running binary. There are no subscriptions,
resource templates, prompts or additional calculation tools.

```json
{"jsonrpc":"2.0","id":2,"method":"resources/list"}
{"jsonrpc":"2.0","id":3,"method":"resources/read","params":{"uri":"routeobjects://routeobjects-mcp/guides/cips-v1"}}
```

Send these after MCP initialization. Reads return one `text/markdown` content
item. Listing reports its UTF-8 byte size. Unknown URIs produce JSON-RPC error
`-32002`; malformed read parameters and unsupported pagination cursors produce
`-32602`. `resources/templates/list` returns an empty list. Unsupported methods
remain `-32601`. No caller-supplied URI is echoed in the not-found message.

The existing SDK 0.12.1 resource APIs provide this surface. No SDK patch,
dependency or protocol upgrade is needed. The resource uses the existing request,
batch and transport bounds. Eight ordinary-ID reads fit one legacy batch frame;
unusually large correlation IDs remain subject to the complete-frame bound.
The server does not truncate Markdown to fit a response.

## Client behavior and unchanged contracts

The four tool names, input/output schemas, annotations, domain envelopes, error
codes and deterministic operations are unchanged. Each call still returns one
complete JSON text representation equivalent to `structuredContent`; guide text
is not appended to results. Essential semantic instructions are repeated in the
short tool descriptions, within the pinned OpenClaw catalog's 1,200-character
description limit.

MCP hosts choose when to read resources and whether to include them in model
context. Resource advertisement is not proof that an agent has read the guide.
NetClaw's unchanged helper supports tool discovery/calls; its skill therefore
contains the essential rules independently and treats resource access as optional.
Inspector can browse the guide directly. A future model-driven evaluation should
measure tool-kind selection and interpretation rather than assuming that adding
documentation changes reasoning behavior.

The resource is tested with the four existing negotiated revisions:
2024-11-05, 2025-03-26, 2025-06-18 and 2025-11-25. Legacy revisions retain batch
handling; the later two reject protocol batches. There is no July 2026 protocol
conformance claim. See [CIPS verification](CIPS-Guide-Verification.md) for the
current source build's evidence, separate from older prepared archives.
