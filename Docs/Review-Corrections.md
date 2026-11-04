# Publication-review corrections — 2026-11-02

> Historical verification record: these results describe the `swift-cidr-mcp` builds identified below. The project is being renamed to `routeobjects-mcp`; this record is not new-name qualification. See [naming migration](Naming-Migration.md) for current evidence.

The four findings from the final source review are corrected. This is still an
uncommitted integration pilot using the local SDK maintenance checkout. No
immutable SDK pin, source publication, tag or release is claimed by this report.

## Changes

| Finding | Correction | Regression evidence |
|---|---|---|
| Invalid members discard valid legacy batch calls | SDK batch decoding classifies each malformed member independently and retains valid requests and notifications | Scalar, missing-method and nested-array cases under both legacy revisions; valid results and IDs survive, valid notifications stay silent, and later calls recover |
| Concurrent startup or shutdown can invalidate a suspended start | The SDK reserves its single startup attempt before suspension and checks stop/cancellation before installing the receive loop; failed and late connections are disconnected | Gated concurrent-start, stop-during-connect, cancellation-ignoring connect, and failed-connect tests |
| Archive metadata can describe source that did not build its executable | Successful explicit builds issue receipts; the archiver validates the executable, compiled inputs, SDK revision, dependency locks and selected target, then verifies copied bytes | Stale executable/input rejection, failed-build invalidation, absent/malformed receipts, target mismatch and copy-boundary replacement tests |
| Malformed outer `tools/call` parameters return `-32603` | The adapter decodes outer parameters inside its validated handler and returns `-32602` | Missing/wrongly typed names and parameters across all four protocol revisions; valid-call recovery and unchanged domain-error envelopes |

The wire regressions failed against the preserved pre-fix executable. The five new
SDK tests (six parameterized cases) also failed before the production correction,
then passed against the corrected source. Existing resource/cancellation tests
remain in the passing SDK selections.

## Contracts preserved

Exactly `cidr_inspect`, `cidr_contains`, `cidr_relation`, and
`cidr_summarize_range` remain available. Complete discovered tool definitions,
including both schemas, compare equal to the pre-fix server. Representative
success/domain-failure wire results also compare equal. `CONTRACTS.md`, the
SDK-independent core, schema source, CIPS guide and canonical dependency lock
retain their pre-fix hashes. No fifth tool, input field or result field was added.

## Current source verification

| Environment | Checks |
|---|---|
| Native macOS ARM64, Apple Swift 6.3.3 | Consumer: 30 Swift tests in Debug and Release; 24 subprocess tests in each configuration |
| Native Linux ARM64, Swift 6.3.3 | Consumer: 30 Swift tests in Debug and Release; 24 subprocess tests in each configuration |
| SDK, native macOS ARM64 | Full suite: 578 tests / 44 suites; focused lifecycle/resource/wire selection: 27 tests / 4 suites |
| SDK, native Linux ARM64 | Focused selection: 33 tests / 5 suites, including the release's existing stdio tests |
| Packaging scripts | 11 isolated subprocess regressions; native macOS explicit Release build issues and validates a real receipt |

Linux uses cached image
`swift@sha256:1038d54c80063f5cdfabc4560990c30af64b5de8ebf28161deb22ca4ad5db866`
on native ARM64, with test-only `jsonschema 4.25.1`. The focused SDK selection is
the six-file selection documented in the maintenance ledger; it is not a full
Linux SDK test-target result. Existing HTTP/OAuth helper compilation limitations
remain. Native Intel, minimum macOS 15, WSL2 and newer protocol support were not
qualified by these runs. The SDK's Swift 6.1 minimum was not tested.

| Compiled source identity | SHA256 |
|---|---|
| Application manifest/source | `b1a35e86ad5925aa682b03d70a72cd9bd1889465da90f6a800dd50646d08cf93` |
| SDK manifest/source | `b8084e9769c9b48027db6e2ec2d8a29718102449476423e4d7e4e47fd80332c1` |
| SDK baseline revision | `a0ae212ebf6eab5f754c3129608bc5557637e605` |

Source hashes use sorted `Package*.swift` and `Sources` file paths and bytes,
with NUL separators. They identify uncommitted source; they are not Git pins.
The SDK's `verification/routeobjects-pilot/review-corrections.json` records its
test/source identities and scoped evidence. Raw logs remain local evidence.

## Reproduce

```sh
python3 Scripts/build-pilot.py test --configuration debug
python3 Scripts/build-pilot.py test --configuration release
.venv/bin/python Tests/Compatibility/test_stdio.py --binary .build/debug/swift-cidr-mcp
.venv/bin/python Tests/Compatibility/test_stdio.py --binary .build/release/swift-cidr-mcp
python3 -m unittest discover -s Tests/Packaging -p 'test_*.py' -v
python3 Scripts/build-pilot.py build --configuration release
python3 Scripts/archive-pilot.py --binary .build/release/swift-cidr-mcp \
  --platform macos-arm64 --execution native --output artifacts/review-corrections
```

Configure the explicit SDK edit first, as documented in the README, and select the
actual platform/execution mode for archiving. Use a fresh output directory.
The example's native macOS claim is appropriate only on a matching host.

## Build receipts and remaining gates

Only a successful explicit `build-pilot.py build` creates a receipt; `test` does
not certify a distributable executable. A failed rebuild invalidates its previous
receipt. The complete canonical lock is restored after SwiftPM's editable-mode
resolution, and both application and SDK inputs must stay unchanged across the
build. Build-time compiler metadata is preserved in the receipt;
`compilerDefaultTarget` describes the compiler driver's default, while `target`
and `requestedArchitecture` describe the requested package architecture/platform.
It does not claim to measure the executable's minimum OS.

The archiver cannot mint a missing receipt. It validates the receipt and copied
executable, carries `BUILD-RECEIPT.json`, and derives `BUILD-INFO.json` from the
validated build record. Receipts are unsigned local integrity records, not
cryptographic attestations. Stripping, signing and other byte transformations
currently invalidate the receipt and need a separate designed provenance step.

The SDK remains single-start, including failed or cancelled startup attempts.
A transport that ignores cancellation can keep its caller suspended until connect
returns. The correction prevents it from installing a receive loop afterward and
disconnects a late connection; it does not forcibly terminate arbitrary transport
code. Process deadlines remain the host's responsibility.

An approved immutable SDK revision and matching consumer dependency/verifier
update remain necessary before an installable release. Fresh platform archives,
clean-runtime checks and NetClaw runtime qualification must use those exact
approved inputs. Candidate-3 archives and historical Inspector/NetClaw results
were not relabeled as verification of this corrected executable. Publication,
tags, release assets and sending the NetClaw proposal remain separate actions.
