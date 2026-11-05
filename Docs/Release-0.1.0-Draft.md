# RouteObjects MCP 0.1.0 release draft

Publication plan, November 4, 2026: experimental prerelease tag `0.1.0` targets
the published application source at
[`8595fae93803083b6146d04356b1bd02f0d8bfe0`](https://github.com/RouteObjects/routeobjects-mcp/commit/8595fae93803083b6146d04356b1bd02f0d8bfe0),
with SDK maintenance revision
[`10cb175661ab095abfc73cf293a0c79af244e61e`](https://github.com/RouteObjects/swift-sdk/commit/10cb175661ab095abfc73cf293a0c79af244e61e).
Prepared archives retain their original packaging-time `releaseReady: false`
metadata; that immutable record is not a live publication or approval flag.
The four selected native archives are qualified within their recorded scopes.
This document describes the publication plan rather than asserting release
availability; tag creation and asset upload are separate operations.

The later signed workflow-only commit
[`9c5313ffc39a95f6e3c9e734bdc96dfb00477516`](https://github.com/RouteObjects/routeobjects-mcp/commit/9c5313ffc39a95f6e3c9e734bdc96dfb00477516)
produced the 66-file baseline for the November 4 documentation review. The
five-document follow-up modifies README, the acceptance matrix and this draft,
and adds the qualification report and [distribution guide](Pilot-Distribution.md),
producing a 68-file tree when applied to that baseline. These are review-snapshot
counts, not a statement about live branch state. The earlier three-document/67-file
review is historical. Qualification and planned tag `0.1.0` retain the unchanged
65-file `8595fae` product snapshot. Later documentation on `main` and standalone
attachments do not change the tagged source, archived documents or binaries.

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
publication tooling. Its later published-pin section records the real immutable
SDK selection and clean pinned builds. The [published-source qualification](Published-Source-Qualification.md)
adds exact archive identities and the latest scoped results.

## Included

- Four offline IPv4/IPv6 tools with explicit address, address-with-prefix and network semantics.
- Exact decimal cardinalities and minimal inclusive range covers without address enumeration.
- Independent domain types and JSON Schemas, complete JSON text alongside structured MCP results.
- Bounded stdio input/output, serialized writes, bounded redacted stderr diagnostics, isolated signal-source ownership and a process shutdown deadline.
- Bundled CIPS guide, semantic tool descriptions and NetClaw skill based on draft-munro-cips-00; the draft is not an IETF standard.
- Opt-in NetClaw component alongside the existing subnet calculator, with explicit checksum/version imports into installation-owned paths.
- Test fixtures and scoped platform/client evidence, separated into current renamed-build results and historical Inspector/chat/archive records.

## Selected qualified artifacts and distribution decision

The [pilot distribution plan](Pilot-Distribution.md) selects exactly the new
macOS ARM64 and Intel CI archives plus the qualified Linux ARM64 and x86-64
archives. It provides their original filenames, archive/executable checksums,
OS/toolchain scopes, local stdio setup and NetClaw checksum/version import.
The plan is experimental prerelease tag `0.1.0` at `8595fae`, using those
unchanged bytes: signed
source commits, the recorded ad-hoc ARM64 linker signature and unsigned Intel
binary, without a Developer ID or notarization claim. The [planned release
location](https://github.com/RouteObjects/routeobjects-mcp/releases/tag/0.1.0)
and asset locations in the distribution guide do not assert present availability.
Existing archives retain immutable packaging metadata, including
`releaseReady: false`; later documentation is supplied separately.

A separate new Intel CI archive passes native macOS 15.7.9 qualification with
Apple Swift 6.2.3: 39 Swift tests and 30 subprocess checks in each Debug/Release
configuration, all 52 tooling cases and 30 extracted-archive checks. Its archive
SHA-256 is `53760c4938264f91b263ff462bceb6237c507fe4563001e76a54144257fcf42e`;
the exact downloaded binary also passes NetClaw 7/6/3 helper/tool/resource cases,
configuration resolution and timeout recovery locally under Rosetta on ARM64
macOS 26.7.1. This is not native Intel NetClaw integration.

A separately authorized ARM64 retry now passes on native macOS 15.8.2 with
Apple Swift 6.2.3 and Xcode 26.2: 39 Swift tests and 30 subprocess checks in
each Debug/Release configuration, all 52 tooling cases and 30 extracted-archive
checks. Its new archive SHA-256 is
`0bc482660ace98204c1ebf350544d47fed052813474767d3a3c56bfb7b359b43`.
The first two ARM attempts ended without acquiring a runner; the successful
third attempt produces new evidence and leaves those failures in the record.
The [qualification report](Published-Source-Qualification.md#native-arm64-macos-1582-ci-artifact)
records the exact new artifact and source identities. The same new ARM64 bytes
also pass seven import/helper, six ordinary runtime tool and three CIPS resource
cases, configuration resolution and timeout recovery natively on macOS 26.7.1.
That NetClaw result is separate from CI execution on 15.8.2; it does not establish
macOS 15 NetClaw execution. Read-only signature verification succeeds for the
new ARM64 executable's ad-hoc linker signature, without a Developer ID or
notarization claim. Caller `AbortSignal` forwarding remains unsupported.

The declared minimum remains macOS 15. Native macOS 15 source/archive coverage
now includes both architectures at their recorded point releases; exact 15.0,
a machine without Xcode and native Intel NetClaw execution are not established.
Earlier native ARM64 macOS 26.7.1 archive and NetClaw results retain their own
identities. The authorized retry is complete; this review authorizes no further
CI run.

The new Intel CI executable is unsigned (`codesign --verify --strict` exits 1).
Developer ID signing/notarization is a separate distribution-policy choice,
not an implementation requirement for the source pilot.

The earlier four archives built from source `8595fae` and SDK `10cb175` each pass all 30
subprocess checks against the build output and again after extraction on macOS
ARM64, macOS x86-64, Linux ARM64 and Linux x86-64. macOS ARM64 and both Linux
architectures run natively; macOS x86-64 uses Rosetta and does not qualify a
native Intel Mac. Each of the three native archive executables also passes
seven NetClaw import/helper cases, six ordinary runtime tool cases, three
resource cases, configuration resolution and timeout notification/recovery.
Linux x86-64 reuses the audited fixture with earlier catalog metadata; later
metadata-only source-link changes are checked separately in the local checkout.
These checks preserve the four tools and contracts.

Fresh published-source Linux ARM64 checks additionally pass 39 Swift tests and
30 subprocess checks in Debug and Release on both Swift 6.2.4 and 6.3.3, with
52 tooling cases per toolchain. The fresh Linux x86-64 run qualifies its Swift
6.3.3 static distribution build and extracted archive; its earlier complete
Debug/Release matrix remains separate evidence.

Both macOS archives retain the published 65-file source snapshot's packaged
documents. Their checks cover receipt/lock identity, all nine dependency pins
and 38 packaged source/dependency files. This documentation follow-up does not
rewrite those archives. The ARM64 executable has an ad-hoc signature and passes
`codesign --verify`; the x86-64 executable is unsigned and verification exits 1.
Neither result establishes Developer ID signing or notarization.

The Linux distribution executables use receipted static-Swift and linker-strip
options without post-build mutation. Their extracted-archive tests run in
isolated native no-Swift runtimes; system glibc/libcurl prerequisites remain.
Linux ARM64 packaging ran on macOS after the native image lacked `file`, so its
unchanged `BUILD-INFO` correctly says `executionEvidence: not-run`; the separate
native extraction checks establish runtime evidence. Exact artifact hashes and
fixture limits are in the published-source qualification report.

The following earlier qualification remains tied to its original builds:

Renamed Linux ARM64 Swift 6.2.4 and 6.3.3 builds each pass 38 Swift tests and 29
subprocess checks in Debug/Release. macOS ARM64 Debug and Release each pass 38/29,
with a Release build receipt. All 13 packaging-driver tests passed.
Later native Linux x86-64 runs include the two test-only acceptance additions:
all 39 Swift tests and 30 subprocess methods pass in Debug/Release on both Swift
6.2.4 and 6.3.3. The original ARM64 counts are not retroactively changed. See the
[native x86-64 report](Native-Linux-X86-64-Verification.md) for exact artifact and
runtime evidence. A renamed model-driven chat is not yet claimed.

The earlier Linux ARM64 Release build uses the wrapper's Linux Release-only
`--linker-strip-all` option with `--static-swift-stdlib`. Its actual linker command
is receipted; the unchanged binary is 60,292,776 bytes, fits NetClaw's unchanged
64 MiB import limit, and passed 29 subprocess checks. Final clean-runtime/archive
checks also passed without Swift installed. A new native Linux x86-64 archive
with a 61,898,488-byte executable passed the expanded 30-method harness after
clean extraction in an isolated native runtime without Swift. Those were local development artifacts at that earlier qualification snapshot.
The current selection instead uses the immutable-source artifacts identified
in the distribution plan; this historical paragraph does not require rebuilding
those already qualified bytes.
Post-receipt stripping invalidates the receipt.

The renamed Release integration passed 7 native import/helper cases and 6
ordinary-runtime calls covering all four tools, plus timeout cancellation/recovery.
Native Linux ARM64 and x86-64 also passed three CIPS resource checks each.
The new x86-64 run used its exact newly qualified archive executable.
The existing chat registration is healthy with the new name; no new model turn
was executed. Caller `AbortSignal` forwarding remains a host limitation.

## Dependency and artifact identity

Direct dependencies are exact swift-cidr 0.8.1, MCP Swift SDK 0.12.1 baseline,
swift-log 1.6.2 and swift-system 1.4.0. The complete `Package.resolved` records all
nine transitive/direct packages. `Package.swift`, `SDKSelection.json` and the
lock select published RouteObjects SDK maintenance revision
`10cb175661ab095abfc73cf293a0c79af244e61e`; pinned mode rejects local overrides.
The [published-pin verification](Publication-Preparation.md#published-sdk-pin-verification)
records clean native macOS ARM64 and Linux x86-64 Debug/Release results and
compiled-input identities. This is a maintenance fork, not an official SDK
release. New archives require a validated build receipt binding the executable,
compiled inputs, SDK revision, locks, toolchain and target; `BUILD-INFO.json`
derives its build identity from that receipt. Unsupported post-build changes
such as stripping invalidate the receipt. Preserve every third-party license
and upstream attribution.

## Publication checks for this plan

1. Review this documentation follow-up and any later source/test diffs separately; preserve the published source identities and SDK patch ledger.
2. Review the exact four-archive selection, checksums, receipts and proposed experimental distribution policy in [Pilot-Distribution.md](Pilot-Distribution.md). Native artifact qualification, the SDK fork publication, exact consumer pin and initial 65-file source publication are complete within the recorded scopes.
3. Preserve the selected qualified bytes and their native evidence: macOS ARM64 15.8.2, macOS Intel 15.7.9, Ubuntu 24.04 ARM64 and Ubuntu 24.04.5 x86-64. Any later binary change is a new artifact. Do not expand NetClaw or WSL2 claims beyond the recorded scope.
4. Include the recorded extracted-archive checks, dependency inventory, checksums and OS runtime prerequisites with the distribution review. The macOS deployment target is 15; actual native checks include the new ARM64 15.8.2 and Intel 15.7.9 artifacts, with earlier ARM64 26.7.1 evidence retained separately, not exact 15.0. Xcode remains installed on CI. Ubuntu 24.04 requires libcurl4t64 and does not require a Swift installation for the bundled-runtime binary.
5. For the separate NetClaw proposal, agree contribution scope and a specification number with its maintainer before preparing its upstream PR. This pilot does not reserve a NetClaw specification number; the RouteObjects release locations above are planned locations.
6. Confirm tag `0.1.0` targets application commit `8595fae93803083b6146d04356b1bd02f0d8bfe0`, with the GitHub release marked as an experimental prerelease. Keep the later documentation commit separate, and require explicit authorization for tag creation and release publication. Developer ID/notarization can remain a separate optional step; signed source commits do not imply signed binaries. No credentials or private application material belong in either public repository.

## Deferred

Native Windows, musl distribution, protected Hermes, HTTP serving, MCPB packaging, a RouteObjects agent runtime and additional tools are outside 0.1.0. Host-driven model selection was demonstrated in the pre-rename NetClaw chat; it does not add model orchestration to this server. MCP 2026-07-28 is not implemented; historical Inspector legacy/fallback evidence remains scoped to its tested build, and modern-only negotiation is expected to fail.
