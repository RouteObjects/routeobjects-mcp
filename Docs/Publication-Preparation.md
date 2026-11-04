# Publication preparation

November 3, 2026 (America/New_York; raw logs use November 4 UTC).
The preparation sections below retain their pre-publication evidence. The later
[published-pin verification](#published-sdk-pin-verification) records the actual
maintenance commit and subsequent consumer checks.

The initial preparation change prepared the build and review tooling for source
publication without creating an SDK commit, publishing a repository or claiming
a new release. The four
tools, input/output schemas, domain results and CIPS resource content are unchanged.

## Reviewed SDK selection at the preparation snapshot

`SDKSelection.json` records the released baseline and independently approved
maintenance source/lock digests. Its `maintenance.revision` was deliberately null
while the patch remained uncommitted. The development build mode requires the
baseline HEAD, the exact reviewed source/lock hashes and an explicitly selected
SwiftPM edit. Stable but unreviewed source is rejected before compilation.

The immutable mode requires an exact maintenance revision in three places:
the `maintenanceSDKRevision` literal in `Package.swift`, the selection record,
and the SDK entry of the complete `Package.resolved`. The pin must reference the
RouteObjects fork; it must not be a branch, tag, placeholder or the unpatched
baseline revision. The verifier checks manifest/selection agreement before
invoking Swift. The literal belongs in the manifest because SwiftPM does not
invalidate a cached manifest merely when an arbitrary JSON file it read changes.

Pinned mode uses `--force-resolved-versions`, enables the patched server without
a development environment variable, and rejects SDK edits, local path overrides,
dirty checkouts, incorrect checkout URLs/HEADs and source/lock mismatches.
Configuration never automatically removes a caller's existing edit. All nine
dependency pins remain required; duplicate or changed entries are rejected.
Failed configuration/build attempts restore the canonical lock. Failed rebuilds
cannot issue a new build receipt.

Receipts distinguish the upstream baseline from the actual SDK revision and
record the selection mode, maintenance status and selection-record digest.
Archives include the exact selection record. Pinned fixtures record
`uncommittedMaintenancePatch: false`; development builds record `true`. Neither
mode automatically makes an archive release-ready.

## Explicit publication inventory

`Scripts/make-review-bundle.py` now requires an explicit reviewed manifest and a
fresh output directory. It verifies repository bases, empty indexes, exact
path/hash/size/mode records and safe regular-file paths before writing a patch.
The SDK's full tree is checked independently from its selected changed-file delta.

Unrelated tracked changes and excluded posting documents cannot enter the patch
through Git-status discovery. The two approved correction records are retained
when selected by the manifest. Existing outputs, symlinks, unsafe paths, stale
hashes, changed bases, staged changes and unsupported deletion inventories fail
explicitly. The script accepts SwiftPM versioned manifests such as `Package@swift-6.0.swift`
and extension sources such as `Data+Extensions.swift`; a dedicated regression
covers both legitimate paths. It makes no commits and stages nothing.

The current publication review selects only the consumer and SDK maintenance
fork. NetClaw's existing 35-file contribution remains a separate review.

## Verification

The complete packaging/tooling suite contains **52 passing tests** on native
macOS ARM64 and native Linux x86-64 (Ubuntu 24.04, Python 3.12.3 on Linux).
It includes 13 provenance tests, 24 SDK-selection/bootstrap/archive tests, and
15 review-bundle tests. These use real driver subprocesses with isolated fake
Git/compiler processes; no test creates a real commit or fetches a repository.
Review patches also pass real Git reverse-application checks.

The regressions cover a future non-baseline SDK revision, manifest/JSON mismatch,
source/lock/checkout drift, edits and overrides, duplicate/missing pins, locked
bootstrap, failed-build receipt invalidation, selection-bound archives and the
exact SDK publication-file boundary. One regression exposed a duplicate-pin
validation gap; the driver now rejects it before receipt issuance.

Five additional checks compiled actual SwiftPM manifests in temporary copies:
baseline, development, pinned, rejected pinned override, then baseline again.
They verify dependency/compile-flag selection and cache invalidation without
resolving the synthetic pinned revision. An initial JSON-only selection attempt
exposed the cache problem and was replaced by the manifest-literal design above.

The current development source also passed native macOS ARM64 Debug and Release
verification: **39 Swift tests and 30 subprocess checks in each configuration**.
The explicit Release build produced a new selection-bound receipt. Configure and
build steps retained the complete canonical lock.

Current compiled-input identities:

- Application: `572671d750caa1972f05b29c59a9566326d419d522c74e020a297582d22623b9`.
- SDK: `d4a82bbb1e207cfe598c8e68d1d7831bb00308353fb8a1bdcdab7c58b2f0a9ab`.
- Consumer lock: `6fa402a47daaeab25c9bfa873a00e5d4bc440357b287f4025d93596f36ff0675`.

The SDK production delta in this preparation is a comment correction only:
the finite default control-response budget is no longer described as preserving
all upstream defaults. Current SDK documentation points to the correct source
identity and uses the checked-out source/tests for reproduction, without requiring
excluded historical patch files. Previous SDK logs retain their original hashes.

Earlier [native Linux x86-64](Native-Linux-X86-64-Verification.md) and ARM64 archive
results remain evidence for those exact artifacts. The new Linux run qualifies
the Python tooling; it is not a new Swift binary/archive qualification. No old
archive or execution result is relabeled with the new application/SDK digests.

## Publication actions identified at the preparation snapshot

1. Review the exact SDK delta and source boundary, then separately authorize its
   signed commit and publication to the intended maintenance fork.
2. Put that actual immutable revision in the manifest, selection record and lock;
   preserve the other eight dependency pins and refresh the reviewed identities.
3. Qualify a clean consumer checkout against the real published revision, then
   review the refreshed source manifest before committing/pushing the consumer.
4. Complete the intended repository naming/fork setup. No remote mutation is part
   of this local tooling change.

The immutable path is regression-tested with synthetic revisions, not yet
qualified against a real published maintenance commit. Native Intel macOS,
minimum-macOS-15 execution and final release archives remain separate distribution
qualifications. Caller `AbortSignal`, full Linux SDK-suite and July 2026 protocol
limitations remain as previously documented. No new tool or protocol support is
claimed.

## Published SDK pin verification

The RouteObjects maintenance fork is now published at signed commit
[`10cb175661ab095abfc73cf293a0c79af244e61e`](https://github.com/RouteObjects/swift-sdk/commit/10cb175661ab095abfc73cf293a0c79af244e61e)
on `routeobjects/pilot`, with parent `a0ae212ebf6eab5f754c3129608bc5557637e605`
(released SDK 0.12.1). Local SSH signature verification passes and GitHub reports
the signature as verified. The commit contains the reviewed 24-file delta in a
122-file full tree. It retains upstream history, attribution and licenses. This
is a RouteObjects maintenance commit, not a new official SDK release.

The consumer selects the actual revision in `Package.swift`, `SDKSelection.json`
and `Package.resolved`. Normal SwiftPM resolution in a fresh allowlisted workspace
preserved all other eight complete pin records and the existing `originHash`.
Subsequent locked configuration verifies the fork URL, exact checkout revision,
clean SDK state and independently approved source/lock hashes. No edited dependency
or local SDK override was used. The main development workspace has also been
configured and rebuilt against this immutable pin.

| Native environment | Results against the published pin |
| --- | --- |
| macOS ARM64, Apple Swift 6.3.3 | Debug and Release each pass 39 Swift tests and 30 independent subprocess checks; 52 tooling tests pass |
| Linux x86-64, Swift 6.2.4 and 6.3.3 | Each toolchain passes 39 Swift tests and 30 independent subprocess checks in both Debug and Release; all 52 tooling cases pass |

The Linux run verifies the unchanged 65-file transferred candidate and complete
lock after each compiler environment. The 52 tooling cases were repeated under
both environments; they are 52 unique cases, not 104 distinct tests. Collected
Linux evidence hashes were verified after transfer. These are native executable
checks, not new archive or Linux NetClaw deployment qualifications.

Successful explicit Release builds produce receipts with the actual maintenance
revision, `selectionMode: pinned` and `uncommittedMaintenancePatch: false`.
The compiled-input identities for these checks are:

- Application: `99c75d8296d23a590dcca4d7a7881739d51d5d7bf5eff622e525d5b27e9e9a85`.
- SDK: `d4a82bbb1e207cfe598c8e68d1d7831bb00308353fb8a1bdcdab7c58b2f0a9ab`.
- Consumer lock: `c1cb3a374a1cb171dbfa6332793fedca318fc45fd58c138beaaab801c89393c9`.

The pinned macOS Release binary also passes seven NetClaw import/helper cases,
six ordinary runtime tool cases, three resource cases and native configuration
resolution using Node 22.23.4 and OpenClaw 2026.7.1-2. These checks use fresh owned
state and an unchanged cached runtime import closure; they do not install a full
agent, invoke a model or change the live demonstration. Binary SHA-256:
`98dce235e9c5c925975d2770047c095ac0faa71e0770598b944139b1ac432184`.

All runtime source files and `CONTRACTS.md` are unchanged from the preceding
review. Historical archives and execution logs retain their original identities.
This follow-up does not claim final archive qualification, native Intel macOS,
minimum-macOS-15 execution, full Linux SDK HTTP/OAuth test-target verification,
caller `AbortSignal` support or July 2026 protocol conformance. No MCP repository
commit, push, tag or release is part of this SDK publication and pinning action.
