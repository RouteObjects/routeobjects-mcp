<h1 align="left">
  <img src="Docs/Assets/routeobjects-mcp.png" alt="swift-cidr icon" width="75" height="75" valign="middle">
  &nbsp;CIDR
</h1>

RouteObjects MCP provides explicit networking operations for AI agents. The initial pilot offers four local, deterministic IPv4/IPv6 tools backed by [`swift-cidr`](https://github.com/RouteObjects/swift-cidr). It keeps bare addresses, addresses carrying prefix context, and canonical networks distinct. Additional RouteObjects capabilities will be introduced through separately defined tool contracts.

**Experimental 0.1.0 pilot.** The publication plan selects an experimental GitHub prerelease tagged `0.1.0` at application commit [`8595fae93803083b6146d04356b1bd02f0d8bfe0`](https://github.com/RouteObjects/routeobjects-mcp/commit/8595fae93803083b6146d04356b1bd02f0d8bfe0). Four selected native macOS/Linux archives have scoped qualification evidence. See the [pilot distribution plan](Docs/Pilot-Distribution.md) for exact artifacts, checksums, local setup and the distinction between the tagged build source and later documentation. Check the [repository releases](https://github.com/RouteObjects/routeobjects-mcp/releases) for availability; this plan does not assert that a release or its assets have been published. The complete lockfile selects the RouteObjects SDK maintenance fork at published commit [`10cb175661ab095abfc73cf293a0c79af244e61e`](https://github.com/RouteObjects/swift-sdk/commit/10cb175661ab095abfc73cf293a0c79af244e61e), based on released MCP Swift SDK **0.12.1**. `SDKSelection.json` records that immutable revision and the independently approved SDK source/lock hashes. This is a RouteObjects maintenance revision, not an official SDK release. [Published-pin verification](Docs/Publication-Preparation.md#published-sdk-pin-verification) records the actual clean-checkout results; earlier local-edit results remain historical evidence.

## Tools

| Tool | Purpose |
|---|---|
| `cidr_inspect` | Inspect an address, address with prefix context, or network; normalize host bits only when requested. |
| `cidr_contains` | Test address membership or containment of an entire network. |
| `cidr_relation` | Compare aligned networks for equality, containment, overlap and adjacency. |
| `cidr_summarize_range` | Compute a minimal inclusive range cover without enumerating addresses. |

All tools are read-only, deterministic and offline. They accept IP literals; they do not resolve hostnames or connect to devices. Counts are exact decimal strings, including IPv6 `/0`. See [CONTRACTS.md](CONTRACTS.md) for the public contract. Tools return one domain envelope as both `structuredContent` and complete JSON text for older clients.

## Bundled CIPS guide

The executable includes an offline Markdown resource at
`routeobjects://routeobjects-mcp/guides/cips-v1`, based on Craig A. Munro's
[draft-munro-cips-00](https://www.ietf.org/archive/id/draft-munro-cips-00.html)
(3 October 2026). The draft is work in progress, not an IETF standard.
The guide explains the semantic choices behind the four tools; it adds no
calculation tool and changes no input schema or result contract.

Resource-aware clients can discover it with `resources/list` and retrieve it with
`resources/read`. Hosts control whether resource text enters model context, so
essential guidance also appears in tool descriptions and the NetClaw skill.
See [CIPS guide integration](Docs/CIPS-Guide.md) for examples and compatibility.

## Local development

Requires Swift tools 6.2 or later, Swift language mode 6, macOS 15 or glibc Linux. Qualified Ubuntu 24.04 archives bundle the Swift runtime and require the system `libcurl.so.4` runtime (`libcurl4t64` on Ubuntu 24.04). See the [native x86-64 report](Docs/Native-Linux-X86-64-Verification.md) and [ARM64 follow-up](Docs/Qualification-Followup.md) for exact previously qualified artifact identities; later source/tooling changes do not relabel those archives. Operators provision runtime prerequisites; neither the binary nor NetClaw installs packages. Python runs the build/verification scripts; its schema validator is test-only. SwiftPM fetches the pinned SDK from the public fork. No sibling SDK checkout is required.

```sh
./Scripts/configure-pilot.sh
python3 Scripts/verify-dependencies.py
python3 Scripts/build-pilot.py test
python3 Scripts/build-pilot.py test --configuration release
python3 Scripts/build-pilot.py build --configuration release
.build/release/routeobjects-mcp --version
```

`Scripts/verify-dependencies.py` verifies all nine dependency pins, the selected fork URL and commit, a clean SDK checkout, and the independently approved SDK source/lock hashes. Configure and build use locked resolution and reject duplicate or changed pins. Pinned mode enables the patched server automatically and rejects local SDK overrides. When migrating an earlier development workspace, remove its `ROUTEOBJECTS_MCP_SDK_PATH` environment variable and explicitly retire its SwiftPM edit, or use a fresh checkout; configuration never removes an edit automatically.

The reviewed SDK commit appears in both the `maintenanceSDKRevision` literal in `Package.swift` and `SDKSelection.json`, with the same exact revision and fork URL in `Package.resolved`. The verifier checks agreement before invoking Swift. Keeping the revision literal in the manifest ensures SwiftPM invalidates its manifest cache when the pin changes. The [publication preparation report](Docs/Publication-Preparation.md) distinguishes earlier fixture-tested tooling from the subsequent [published-pin verification](Docs/Publication-Preparation.md#published-sdk-pin-verification). The SDK-independent `CIDRToolCore` has no MCP dependency. `CIDRMCPAdapter` owns protocol schemas, SDK conversion, bounded stdio and lifecycle. The executable owns startup and process signals.

Test-only schema validation:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r Tests/Compatibility/requirements.txt
```

See the [naming migration](Docs/Naming-Migration.md) for current qualification and [historical verification](Docs/Verification.md) for earlier build evidence. No July 2026 MCP conformance is claimed.

The [publication-review corrections](Docs/Review-Corrections.md) cover malformed
tool parameters, mixed legacy batches, SDK startup ownership and archive provenance.
The four tool definitions and result contracts are unchanged.

## Running

Use an absolute executable path in your MCP client:

```json
{"mcpServers":{"routeobjects-mcp":{"command":"/absolute/path/routeobjects-mcp","args":[]}}}
```

No arguments (or `--stdio`) starts the server. `--help` and `--version` are human-facing commands. In server mode stdout contains only newline-delimited JSON-RPC. Diagnostics are bounded JSON lines on stderr; ordinary logs omit raw arguments, addresses, results and SDK message text.

The pilot limits arguments to 8 KiB, inbound frames to 16 KiB, complete outbound frames to 64 KiB including LF, executing requests to 4, queued requests to 8, protocol batches to 8 items and returned CIDRs to 256. A stalled writer is closed after 5 seconds without progress. Cancellation notifications remain available under request saturation. Up to 64 bounded protocol-error replies (including the active write) use a separate writer queue so an overload reply cannot block cancellation reception; exhausting this queue closes the connection. An incomplete output frame causes connection termination before any later frame can be written. A full range cover is never truncated.

The application logger keeps at most 64 records of at most 512 bytes including LF. It drops whole queued diagnostics under pressure and stops its sink after a 100 ms blocked write; MCP output and shutdown do not depend on a stderr reader.

## NetClaw

The experimental local integration is opt-in under component `routeobjects`, server `routeobjects-mcp`, and executable override `ROUTEOBJECTS_MCP_BIN`. It preserves the existing subnet calculator and existing profile defaults. The installer requires a locally supplied executable with an explicit SHA-256 and expected version, then copies it into an installation-owned location. It does not install Swift or system packages. See [NetClaw integration](Docs/NetClaw.md).

## Distribution and license

Apache-2.0. Third-party licenses and source revisions accompany every prepared archive. The selected four archives have native evidence: macOS ARM64 on 15.8.2, macOS x86-64 on 15.7.9, Linux ARM64 on Ubuntu 24.04 and Linux x86-64 on Ubuntu 24.04.5. macOS 15 remains the minimum; exact 15.0 execution is not claimed. The new macOS CI archives and qualified Linux archives are identified by hash in the [distribution plan](Docs/Pilot-Distribution.md), with complete boundaries in [published-source qualification](Docs/Published-Source-Qualification.md). The selection identifies exact qualified bytes; the installer does not download them automatically. Native Windows, musl, WSL2, protected Hermes, HTTP hosting and MCPB remain outside this pilot.

After configuring the selected SDK, build an executable with `python3 Scripts/build-pilot.py build --configuration release`
before packaging it. A successful explicit build writes a sibling
`routeobjects-mcp.build-receipt.json`; `Scripts/archive-pilot.py` requires that receipt
and verifies the executable, compiled inputs, SDK revision, dependency locks and
target. A copied executable can use `--receipt /path/to/its/receipt.json`. Receipts
are unsigned integrity records, not signatures. Post-build stripping, signing or other
modification of receipted bytes is rejected; post-build transformations need a separately
defined provenance step before they can be distributed. The selected, already qualified archives retain their original
`releaseReady: false` packaging metadata. That immutable field records their
build-time candidate status, not live publication or approval state. No
repackaging or rebuild is needed merely to update documentation. A later change to binary
bytes would need its own matching provenance and qualification.

Linux distribution builds use `--static-swift-stdlib --linker-strip-all` with the
Release build command. The latter removes symbols during linking, is restricted
to Linux Release builds, and is recorded in the build receipt. This keeps the
qualified executable within NetClaw's 64 MiB import limit without changing bytes
after the receipt is issued.

## Review tooling

The review bundler requires an explicit reviewed path/hash/mode manifest and a
fresh output directory. It does not discover a publication allowlist from Git
status, stage files, or include excluded posting documents. SDK full-tree
validation is separate from its changed-file patch.

```sh
python3 Scripts/make-review-bundle.py --manifest /absolute/reviewed-manifest.json --output /absolute/fresh-review-directory
python3 -m unittest discover -s Tests/Packaging -v
```

The manifest is review input, not part of the distributed product. Keep private
review material outside public repositories.
