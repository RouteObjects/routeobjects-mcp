# RouteObjects MCP 0.1.0 release draft

Status: local integration pilot; unpublished. All prepared archives carry `releaseReady: false` until the SDK dependency can be pinned to a reviewed immutable revision and the intended publication checks are complete.

The permanent executable/server name is `routeobjects-mcp`, with NetClaw component
`routeobjects`. The four [publication-review corrections](Review-Corrections.md),
CIPS guide and isolated signal bridge are implemented with regressions. The four
tool names and result contracts are unchanged. [Current naming qualification](Naming-Migration.md)
records fresh platform checks; historical candidate-3 archives and old-name chat
results remain tied to their original builds.

The subsequent [publication preparation](Publication-Preparation.md) adds reviewed
SDK source selection, matching manifest/revision checks and explicit-manifest
review bundles. That tooling has its own regression evidence and input identity;
previous native archives are not rewritten or relabeled as builds of the new
publication tooling. No maintenance commit is selected or published yet.

## Included

- Four offline IPv4/IPv6 tools with explicit address, address-with-prefix and network semantics.
- Exact decimal cardinalities and minimal inclusive range covers without address enumeration.
- Independent domain types and JSON Schemas, complete JSON text alongside structured MCP results.
- Bounded stdio input/output, serialized writes, bounded redacted stderr diagnostics, isolated signal-source ownership and a process shutdown deadline.
- Bundled CIPS guide, semantic tool descriptions and NetClaw skill based on draft-munro-cips-00; the draft is not an IETF standard.
- Opt-in NetClaw component alongside the existing subnet calculator, with explicit checksum/version imports into installation-owned paths.
- Test fixtures and scoped platform/client evidence, separated into current renamed-build results and historical Inspector/chat/archive records.

## Current qualification and packaging gate

Renamed Linux ARM64 Swift 6.2.4 and 6.3.3 builds each pass 38 Swift tests and 29
subprocess checks in Debug/Release. macOS ARM64 Debug and Release each pass 38/29,
with a Release build receipt. All 13 packaging-driver tests passed.
Later native Linux x86-64 runs include the two test-only acceptance additions:
all 39 Swift tests and 30 subprocess methods pass in Debug/Release on both Swift
6.2.4 and 6.3.3. The original ARM64 counts are not retroactively changed. See the
[native x86-64 report](Native-Linux-X86-64-Verification.md) for exact artifact and
runtime evidence. A renamed model-driven chat is not yet claimed.

The final Linux ARM64 Release build uses the wrapper's Linux Release-only
`--linker-strip-all` option with `--static-swift-stdlib`. Its actual linker command
is receipted; the unchanged binary is 60,292,776 bytes, fits NetClaw's unchanged
64 MiB import limit, and passed 29 subprocess checks. Final clean-runtime/archive
checks also passed without Swift installed. A new native Linux x86-64 archive
with a 61,898,488-byte executable passed the expanded 30-method harness after
clean extraction in an isolated native runtime without Swift. Both are local
development artifacts; final immutable-release packaging remains required.
Post-receipt stripping invalidates the receipt.

The renamed Release integration passed 7 native import/helper cases and 6
ordinary-runtime calls covering all four tools, plus timeout cancellation/recovery.
Native Linux ARM64 and x86-64 also passed three CIPS resource checks each.
The new x86-64 run used its exact newly qualified archive executable.
The existing chat registration is healthy with the new name; no new model turn
was executed. Caller `AbortSignal` forwarding remains a host limitation.

## Dependency and artifact identity

Direct dependencies are exact swift-cidr 0.8.1, MCP Swift SDK 0.12.1 baseline, swift-log 1.6.2 and swift-system 1.4.0. The complete `Package.resolved` records all nine transitive/direct packages. Development uses a reviewed-source maintenance candidate via explicit editable mode; the source remains uncommitted. `SDKSelection.json` contains the approved source and lock digests with maintenance revision `null`; `Package.swift` retains matching literal `nil`. Pinned mode is implemented for a future exact maintenance commit, with local overrides rejected, but its fixture tests do not establish a real published dependency. New archives require a validated build receipt binding the executable, compiled inputs, SDK revision, locks, toolchain and target; `BUILD-INFO.json` derives its build identity from that receipt. Unsupported post-build changes such as stripping invalidate the receipt. Preserve every third-party license and upstream attribution.

## Before publication

1. Review the source/test diffs and the separate SDK patch ledger. Resolve any review findings.
2. Approve signed commits and publication of the minimal SDK fork revision, then set that exact revision in `SDKSelection.json` and the manifest literal, update the canonical lock, and qualify a clean pinned checkout. Refresh the reviewed file hashes before consumer publication. Rebuild and requalify release artifacts from the approved commits.
3. For downloadable release artifacts, qualify every advertised architecture natively. Cross-compilation or translated/emulated execution is recorded separately and does not satisfy a native execution claim. WSL2 needs its own evidence.
4. Verify clean-environment archive launch, dependency inventory, checksums and intended OS runtime prerequisites. macOS minimum deployment target is 15; the available native runtime test host is newer. Ubuntu 24.04 requires libcurl4t64 and does not require a Swift installation for the bundled-runtime binary.
5. Agree NetClaw contribution scope/specification number with its maintainer, then review the PR/release contents. No number or public asset URL is reserved by this pilot.
6. Review signing/notarization and tag/release authorization as separate actions. No credentials or private application material belong in either public repository.

## Deferred

Native Windows, musl distribution, protected Hermes, HTTP serving, MCPB packaging, a RouteObjects agent runtime and additional tools are outside 0.1.0. Host-driven model selection was demonstrated in the pre-rename NetClaw chat; it does not add model orchestration to this server. MCP 2026-07-28 is not implemented; historical Inspector legacy/fallback evidence remains scoped to its tested build, and modern-only negotiation is expected to fail.
