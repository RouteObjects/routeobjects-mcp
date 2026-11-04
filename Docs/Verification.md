# Pilot verification and release gates

> Historical verification record: these results describe the `swift-cidr-mcp` builds identified below. The project is being renamed to `routeobjects-mcp`; this record is not new-name qualification. See [naming migration](Naming-Migration.md) for current evidence.

The current source includes the four [publication-review corrections](Review-Corrections.md).
That report identifies the corrected source and its new regression runs. The
candidate-3 results below are historical; none of its archives is a current release
candidate. Their source and binary identities have not been relabeled.

The current working tree additionally includes the bundled CIPS guide and semantic
description/skill update. [CIPS-Guide-Verification.md](CIPS-Guide-Verification.md)
records its separate source-build checks. The candidate-3 archives and review
patch predate this addition and remain unchanged; their historical qualification
does not certify the new resource.

This is a local 0.1.0 pilot. The first native qualification snapshot is retained under `artifacts/iteration-1`; independent review subsequently found lifecycle/batch gaps, so those archives are historical evidence. The later historical candidate is `artifacts/candidate-3`, using SDK source SHA-256 `f54aafb2b2a2f2babcaf414a03fa31bdc0c430f825867e967c24cc9711ff306b`. The consumer's public repository exists, but no source commit, tag, release or download asset has been published. The SDK base is released 0.12.1 at `a0ae212ebf6eab5f754c3129608bc5557637e605`, with an explicitly edited maintenance checkout. A reviewed immutable SDK dependency revision is required before publication.

## Reproducible development checks

```sh
./Scripts/configure-pilot.sh ../swift-sdk
python3 Scripts/build-pilot.py test
python3 Scripts/build-pilot.py test --configuration release
.venv/bin/python Tests/Compatibility/test_stdio.py --binary .build/release/swift-cidr-mcp
```

The build wrapper verifies all nine canonical baseline pins, the edited SDK base revision and path, unchanged non-SDK resolutions, and a stable SDK source digest during each build. It restores the full canonical `Package.resolved`. SwiftPM's normal editable mode drops the SDK pin from its generated lock, while `--force-resolved-versions` silently discards the edit; that flag is appropriate only for a stock released-SDK build. A bare build with a stock SDK is not qualified to run this pilot's bounded lifecycle and fails closed at startup.

## Historical candidate-3 evidence

| Surface | Evidence |
|---|---|
| Native macOS ARM64, Apple Swift 6.3.3 / Xcode 26.6.0 | 28 Swift Testing tests pass in Debug and Release. |
| Native Linux ARM64, Swift 6.3.3 / Ubuntu Noble / OrbStack | 28 Swift Testing tests pass in Debug and Release; static Swift-runtime build succeeds. |
| Independent subprocess harness | 19 tests pass in Debug and Release on both native platforms, using `jsonschema 4.25.1`. |
| Inspector 2.13.0 / Node 22.23.4 | CLI, Web and TUI results and commands are recorded in [Inspector-Verification.md](Inspector-Verification.md). |
| NetClaw | Component/catalog/installer contracts, unchanged helper, real binary import, and native OpenClaw config/discovery/tool calls pass; scope in [NetClaw.md](NetClaw.md). |
| SDK maintenance patch | Full native macOS suite: 573 tests / 44 suites. Focused native Linux suite: 28 tests / 5 suites. |

Candidate 3 moves the canonical schemas into the replaceable `CIDRMCPAdapter`, as specified by the approved target boundaries. Complete parsed tool definitions, input schemas and output schemas compare equal to candidate 2. Application source SHA-256 is `fc5eb9a70cdca3fe9128d8515979e266ea137d8e2ce04208ad0b34601009a4f3`; the SDK source is unchanged. Candidate-2 evidence remains historical and is not relabeled as a new run.

The 17 core tests cover every IPv4/IPv6 prefix length, strict parsing, context, normalization, containment, relation boundaries, 528 interval covers, full-family cardinalities, and worst-case 62/254-prefix covers. Eleven adapter tests cover envelope equality, error flags, fragmented pipes, concurrent frame integrity, exact input/output boundaries, output rejection, descriptor restoration, input-EOF ownership and SDK-log redaction. The subprocess suite independently checks schemas and both result representations, malformed/domain errors, four negotiated revisions, batch eligibility/limits, concurrency, cancellation recovery, fragmented/oversized/incomplete input, EOF/signals, stderr pressure and stdout stalls. The final harness also checks malformed request IDs, valid members within mixed legacy batches, and notification-only silence; it verifies null error IDs for messages without a valid correlation ID.

The earlier candidate-2 test-only supplement expanded the adapter selection to **11 tests**,
all passing in Debug and Release on both native ARM64 platforms. It proves the
exact 16-KiB inbound and 64-KiB outbound acceptance/rejection boundaries with real
pipes. The strengthened stderr probe pre-fills a pipe to observed `EAGAIN` before
launch, then verifies successful protocol calls and EOF while it remains full.
It passed against both unchanged candidate-2 Release artifacts. That supplemented the
original 25-test/19-test full runs without retrospectively changing their
counts. Candidate 3 now runs all 28 Swift tests and the strengthened 19-test
process suite in Debug and Release on both native ARM64 hosts. Exact commands and hashes are in
`artifacts/candidate-2/evidence/acceptance-gap-closure/README.md`.

There is no July 2026 conformance claim. Negotiated 2024-11-05 and 2025-03-26 retain batch support; 2025-06-18 and 2025-11-25 reject batches. The Inspector's modern-only negotiation is an expected incompatibility; legacy and automatic fallback are the supported paths.

The deterministic tools finish too quickly to prove cancellation ordering through elapsed-time guesses. SDK tests and independent review regressions use gated handlers and blocked delivery to cover early and running cancellation, queued cancellation, duplicate outstanding IDs, overload, retained capacity, batch completion and cleanup. Request cancellation and completed cleanup are distinct assertions.

## Distribution

`Scripts/archive-pilot.py` prepares a local archive, checksum, dependency inventory and third-party licenses only after validating the receipt from `Scripts/build-pilot.py build`. `BUILD-INFO.json` uses that receipt's build-time identity and labels every archive `releaseReady: false`; `BUILD-RECEIPT.json` preserves the validated record. It never publishes or signs an artifact. Archive smoke tests must use an extracted archive in a clean runtime environment and verify the architecture before making a native claim. Historical Linux distribution copies used GNU `strip --strip-unneeded`; the corrected archiver rejects any post-build byte change, including stripping, until a separate transformation receipt is designed. Bundled runtime licenses/notices accompany the SwiftPM licenses.

Four archives are prepared. The x86-64 archives pass 19 subprocess checks under Rosetta/emulation; Linux x86-64 also passes 28 Swift tests. Native x86-64 remains unqualified, and the macOS x86-64 Swift Testing runner is unavailable on this ARM host. Details are in [X86-64-Verification.md](X86-64-Verification.md). Native x86-64 qualification, WSL2 evidence, model-driven agent acceptance if claimed, signed release engineering and reviewed immutable SDK publication remain separate gates. No native Windows, musl, protected Hermes, HTTP hosting or MCPB qualification is claimed. Linux requires the documented libcurl runtime; bundling Swift does not make the executable fully static.

## SDK collaboration

Independent comparisons tested #266 at `044e2b31f11714901a2b4a0b2f6f73098a757aca`, #298 at `206bc64c04ebec4b2af0a7f82ca0c5fbd91bdc19`, and main at `727175f35c8a0554d9d61c372d4d0da48ebc8b91` on native macOS and Linux ARM64. They confirm the scoped frame-serialization and early-cancellation improvements. The tested #298 snapshot returns from `stop()` before cooperative cleanup completes and leaves active work after input EOF in those scenarios. Tested main includes #297 but reproduces frame interleaving. These findings are scoped tests, not complete PR certification. The SDK checkout's `verification/routeobjects-pilot/README.md` records exact revisions, fixtures, commands, hashes and limitations.

The pre-posting check on 2026-11-02 found #298 at newer head `bc2e1cf6aa2ca585d11ca6e752e0d1e699b88ae4`. It has not been executed in this verification effort. A read-only comparison found its dispatch/stop/EOF paths unchanged; that inspection is not a new test result. The [#266 verification comment](https://github.com/modelcontextprotocol/swift-sdk/pull/266#issuecomment-6578317796), [#298 support/evidence comment](https://github.com/modelcontextprotocol/swift-sdk/pull/298#issuecomment-6578364439) and separate [resource-control proposal #319](https://github.com/modelcontextprotocol/swift-sdk/issues/319) were posted through the explicitly authorized signed-in browser on 2026-11-02. Maintainer feedback and API agreement remain pending; posting approval is no longer a blocker for these contributions.

The maintenance patch changes only the shared Server production source. The pilot uses its own bounded serialized transport, so stock `StdioTransport` is not silently patched. Resource-control proposals remain separate from the correctness contributions. The tested baseline's full Linux SDK suite was blocked by pre-existing URLProtocol test-helper concurrency diagnostics; selected tests do not establish full-suite Linux success, and no failure claim is made about the newer #298 head or its CI.

This contribution-status update follows candidate-3 packaging. The existing archives retain their build-time documentation snapshot and unchanged source/binary identities; no archive was repacked for the posting-status change.

## Rollback

Keep unrelated workspace work intact. Stop only the pilot process; remove its explicit MCP registration/component selection and its installer-owned artifact through NetClaw's normal ownership mechanism. For development, remove only the SwiftPM SDK edit (`swift package unedit swift-sdk`) and unset `SWIFT_CIDR_MCP_SDK_PATH`. The public manifest continues to pin the released SDK baseline; bounded server startup then fails explicitly. Review and revert only the listed pilot paths, without resetting another repository's branch or untracked work.
