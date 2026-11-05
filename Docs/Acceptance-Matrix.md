# Approved-plan completion audit

Audit date: November 4, 2026. The four-tool source pilot is published at
[`8595fae93803083b6146d04356b1bd02f0d8bfe0`](https://github.com/RouteObjects/routeobjects-mcp/commit/8595fae93803083b6146d04356b1bd02f0d8bfe0),
selecting the published SDK maintenance revision
[`10cb175661ab095abfc73cf293a0c79af244e61e`](https://github.com/RouteObjects/swift-sdk/commit/10cb175661ab095abfc73cf293a0c79af244e61e).
The source pilot and native qualification of the four selected archives are
complete within the recorded scopes. The publication plan selects experimental
prerelease tag `0.1.0` at application commit `8595fae`; this technical audit does
not establish release availability. The CIPS guide, semantic
descriptions, isolated signal bridge, and their regression tests are included.
The [naming qualification report](Naming-Migration.md) separates fresh checks
from pre-rename historical evidence. The [November 3 follow-up](Qualification-Followup.md)
records the completed Web/TUI, Linux runtime, generated-catalog, archive and
partial-write checks. Earlier archives and embedded documents retain their
packaging snapshots; the current source reports do not rewrite those artifacts.
The later [native Linux x86-64 report](Native-Linux-X86-64-Verification.md)
records the expanded 39/30 source matrix, clean archive and scoped NetClaw checks.
The subsequent [publication preparation](Publication-Preparation.md) adds reviewed
SDK selection and explicit-manifest review tooling. Its input identities and
regressions are separate from the earlier native archive snapshots below; those
archives are retained unchanged.

The [published-source qualification](Published-Source-Qualification.md) records
macOS/Linux archive checks and separate native macOS 15 CI artifacts: Intel
on 15.7.9 and ARM64 on 15.8.2. Intel NetClaw integration was checked locally
under Rosetta; the new ARM64 binary separately passes native NetClaw checks on
macOS 26.7.1. One separately authorized ARM64 job retry passed after the
first two attempts failed to acquire runners; native ARM64 macOS 15 source and
archive evidence is now complete for those new bytes. The declared minimum
stays macOS 15. The earlier native macOS 26.7.1 ARM64 evidence remains tied to
its own archive. Native Linux ARM64 also has a full Debug/Release source matrix
on Swift 6.2.4 and 6.3.3. The signed workflow-only commit
[`9c5313ffc39a95f6e3c9e734bdc96dfb00477516`](https://github.com/RouteObjects/routeobjects-mcp/commit/9c5313ffc39a95f6e3c9e734bdc96dfb00477516)
adds one file to the 65-file application snapshot, producing a 66-file review
baseline. The five-document follow-up changes README, this audit, the release
draft, the qualification report and the [distribution guide](Pilot-Distribution.md).
Applied to baseline `9c5313f`, its three modified and two added paths produce a
68-file documentation tree. These counts describe the November 4 review, not
live branch state. The earlier three-document/67-file review is historical.
The planned `0.1.0` tag and all binaries retain the 65-file `8595fae` build source;
the later documentation commit does not change that tag target or those bytes.

## Current requirement and evidence mapping

| Approved requirement | Current result | Remaining action |
| --- | --- | --- |
| Separate consumer/SDK repositories and private boundary | The 65-file product source snapshot and separate SDK revision are published; the later one-file CI workflow produced the 66-file review baseline `9c5313f`. No private Engine/Claw dependency; core, adapter and executable boundaries remain intact. | Keep the five-document/68-file review snapshot and any later publication allowlist tied to their exact baselines. |
| Swift tools 6.2, language 6, macOS 15; Apache-2.0; 0.1.0 | Manifest/license/CLI retain these settings. Linux ARM64/x86-64 tested with Swift 6.2.4 and 6.3.3; macOS ARM64 with Apple Swift 6.3.3. New native CI passes on Intel macOS 15.7.9 and ARM64 macOS 15.8.2 with Apple Swift 6.2.3. | macOS 15 remains the minimum. These point-release results do not establish exact macOS 15.0, no-Xcode deployment or native Intel NetClaw integration. |
| Exactly four tools and unchanged results | `cidr_inspect`, `cidr_contains`, `cidr_relation`, `cidr_summarize_range`; [standalone contracts](../CONTRACTS.md). Schema ownership stays in the adapter; domain code imports no MCP. | Preserve contracts through future SDK or tool additions. |
| Strict literals, normalization, address context, whole-network containment, family handling, exact counts and minimal covers | Existing fixtures cover these semantics, `2^128`, worst-case covers, and no enumeration/truncation. Renamed Linux ARM64 Debug/Release passes 38 Swift and 29 subprocess tests per toolchain/configuration. | Record fresh results for every additional advertised platform. |
| One envelope, equal text/structured output, stable errors and independent schemas | The harness uses `jsonschema 4.25.1` and verifies representation equality, domain errors, malformed requests and protocol-specific batches. The added relation matrix raises its inventory from 29 to 30 methods; all 30 pass in the new native Linux x86-64 runs. | Keep archived-build validation separate from source test results. |
| Input/output/resource limits; bounded stderr and clean stdout | 8 KiB arguments, 16 KiB inbound, 64 KiB complete outbound, 4 executing/8 queued, batch 8, 256 returned CIDRs and five-second stalled-I/O/shutdown limits remain. Bounded transport/logging, isolated signal ownership and regressions are implemented. | Preserve narrower test claims; these limits do not make the adapter a general streaming JSON encoder. |
| Native source/build checks | Original renamed macOS/Linux ARM64 results remain 38 Swift + 29 subprocess checks. Later [published-pin checks](Publication-Preparation.md#published-sdk-pin-verification) passed 39/30 in Debug/Release on macOS ARM64 and Linux x86-64. Linux ARM64 now passes 39/30 Debug/Release on Swift 6.2.4 and 6.3.3 plus 52 tooling cases per toolchain. New native Intel macOS 15.7.9 and ARM64 macOS 15.8.2 CI each pass 39/30 in Debug/Release plus 52 tooling cases. | Preserve original test identities. Fresh Linux x86-64 distribution adds 30+30 process checks, not another full source matrix. Exact macOS 15.0 remains unqualified. |
| Minimal necessary SDK maintenance and attribution | Published maintenance commit `10cb175661ab095abfc73cf293a0c79af244e61e` derives from SDK 0.12.1. Production delta is confined to shared `Server.swift`; stock transport is unchanged and the adapter owns bounded stdio. Upstream history, attribution and licenses are retained. | Replace carried changes with a qualified official release when available; preserve the patch ledger and removal conditions. |
| Complete lock and actual compiled identity | `Package.swift`, `SDKSelection.json` and the complete nine-package `Package.resolved` select the actual published SDK revision. Pinned-mode checks reject local overrides and verify source/lock identity. [Publication preparation](Publication-Preparation.md#published-sdk-pin-verification) records clean pinned builds and 52 tooling cases. | Keep receipts tied to exact compiled inputs, locks, toolchain and target. Post-receipt binary mutation invalidates its receipt. |
| Opt-in ordinary NetClaw component | Permanent component `routeobjects`, registration/executable `routeobjects-mcp`, overrides `ROUTEOBJECTS_MCP_*`. Four tools, calculator and existing profile membership preserved. | Coordinate upstream scope/specification number with maintainer. |
| NetClaw component/catalog/installer | Historical scope: 11 component fixtures, 9 catalog tests, 277 installer tests with 32 declared skips and 5 isolation checks; generator checked all 240 skills with locked YAML 2.9.1. Fresh published-source macOS ARM64, Linux ARM64 and native Linux x86-64 archive executables each pass 7 import/helper, 6 runtime and 3 resource cases, configuration resolution and timeout notification/recovery. | Linux x86-64 reused the audited fixture with earlier catalog metadata; later metadata-only source-link edits are checked locally. Caller `AbortSignal` remains unsupported; the timeout fixture holds a completed response, not active server work. No clean npm installation or complete service/gateway deployment is claimed. |
| Pinned/checksummed installation ownership | Archive executables pass installation-owned import/resume: earlier macOS ARM64 6,036,416 bytes, new CI ARM64 6,051,136 bytes, Linux ARM64 60,292,776 bytes and Linux x86-64 61,898,488 bytes, within the unchanged 64 MiB bound. Explicit version/checksum and ownership controls remain. | Preserve qualified bytes through release review; no automatic Swift/system-package installation or post-receipt mutation. |
| Four legacy protocol revisions, including applicable March batches | Harness covers `2024-11-05`, `2025-03-26`, `2025-06-18`, `2025-11-25`; applicable batch behavior retained. | No July 2026 MCP conformance claim. |
| Inspector 2.13.0 / Node 22.23.4 | Renamed CLI: 20 tool/discovery and 6 resource checks passed. Fresh Web/TUI each executed two inspection calls covering context, exact IPv6 count and representation equality; legacy/automatic discovery and expected modern-only incompatibility passed. Web read the new CIPS guide. | CLI covers all four tools; Web/TUI claims remain limited to their actual inspection calls and discovery checks. [Current report](Qualification-Followup.md); [older report](Inspector-Verification.md) remains historical. |
| Model-selected tools and explanations | Pre-rename OpenClaw 2026.7.1-2 / GPT-5.6 Sol chat selected all four tools, then explained their results. Four initial empty-argument calls failed client validation before four valid calls succeeded. The existing registration now hot-reloads the renamed identity with healthy/ready endpoints. | No new model turn was executed. Initial argument-failure cause remains unresolved; no full NetClaw deployment claim. |
| Native archives, clean runtime and inventory | The earlier four-archive snapshot remains unchanged: each build output/extracted archive passes 30 checks, with macOS x86-64 under Rosetta. Separate native Intel macOS 15.7.9 and ARM64 macOS 15.8.2 CI archives each pass all 30 extracted checks; the Intel bytes also pass local Rosetta NetClaw 7/6/3 checks, while the new ARM64 bytes pass those checks natively on macOS 26.7.1. Source documents, nine dependency pins and licenses match the recorded inputs. | Native macOS 15 source/CLI/archive evidence and macOS 26.7.1 NetClaw evidence remain distinct; macOS 15 NetClaw execution is not claimed. Exact macOS 15.0 and WSL2 remain gaps. CI had Xcode installed. Earlier macOS signing results remain tied to their original bytes; Developer ID/notarization and release authorization remain separate. Linux ARM64 host packaging retains honest `executionEvidence: not-run` and separate native execution evidence. |
| Partial-write failure supplement | Four real peer-close runs passed on native macOS/Linux ARM64 across exact #266 and historical-main+#266. Two synthetic one-shot EIO runs exposed an SDK framing assertion failure; the existing bounded pilot passed the analogous Linux test. [Scope and revisions](Qualification-Followup.md#sdk-partial-write-supplement). | Synthetic EIO and real EPIPE evidence are distinct. This verifies one fault model, not all failure paths or complete upstream PR correctness; no production change or duplicate fix was made. |
| Reviewed commits, remote naming, publication and releases | The SDK fork, 65-file product source and later signed one-file workflow are published at the exact revisions above. Four exact qualified archives are selected in the [distribution plan](Pilot-Distribution.md); all retain immutable packaging-time `releaseReady: false` metadata. CI evidence upload is not a release or tag. | The publication plan targets experimental prerelease tag `0.1.0` at `8595fae`, separately from the later documentation commit. Release publication, registry submission and maintainer outreach remain separate actions. |

## Historical SDK contribution and qualification audit

The rows below preserve the recorded November 2 SDK findings. Revisions and
third-party status here are historical evidence, not a live upstream-status
check. Source changes and CI activity after those snapshots require new review.

| Approved requirement | Recorded result | Limitation |
| --- | --- | --- |
| #266 first verification deliverable, exact release/main/#266/#298 comparisons | Real pipes, measured capacity, payload/newline/JSON checks and native macOS/Linux evidence exist. Supplemental queue-entry barriers and cancellation/read/disconnect tests run on both native hosts. The pre-posting check retained main `727175f3` and #266 `044e2b31`; #298 had advanced from tested `206bc64c` to untested `bc2e1cf6`. | At this November 2 snapshot, mid-write fault injection was unverified. The [November 3 supplement](Qualification-Followup.md#sdk-partial-write-supplement) covers one controlled fault model; neither report certifies the full PR. |
| #266 cancellation, blocked output and #297 interaction | #266 and main+#266 both emit the frame of a provably queued cancelled caller. #266 alone leaves sends blocked after disconnect; main+#266 retires them without peer draining and ends the tracked read task. Existing descriptor reuse/flag tests pass with that scratch integration. [Evidence and limitations posted](https://github.com/modelcontextprotocol/swift-sdk/pull/266#issuecomment-6578317796). | Await author/maintainer feedback; do not describe the PR as fully verified or open a duplicate framing fix. An independent #297 parent comparison is not claimed. |
| #298 useful lifecycle verification, separate HTTP design | Selected upstream tests and independent early-cancellation/cleanup/EOF probes ran on both native hosts at `206bc64c`. The [posted comment](https://github.com/modelcontextprotocol/swift-sdk/pull/298#issuecomment-6578364439) distinguishes that tested snapshot from newer untested `bc2e1cf6`. Source comparison found the dispatch/stop/EOF paths unchanged. HTTP design is not copied or endorsed. | Await maintainer feedback; execute appropriate tests before claiming runtime qualification of the newer head. |
| Separate resource-control API proposal, defaults discussion | [Proposal #319](https://github.com/modelcontextprotocol/swift-sdk/issues/319) posted separately from correctness comments on 2026-11-02. Local defaults and compatibility costs are explicit. | Maintainer discussion/agreement on contracts and defaults remains pending. Posting does not establish upstream acceptance. |
| SDK full/relevant scopes | Historical full native macOS suite and selected native Linux lifecycle/resource tests passed at the recorded snapshots. | The then-tested full Linux target encountered pre-existing URLProtocol test-helper concurrency diagnostics. Selected consumer tests and unrelated CI do not establish full SDK-suite verification. |

[Verification.md](Verification.md), platform reports, [CIPS guide verification](CIPS-Guide-Verification.md),
and [review corrections](Review-Corrections.md) retain their original build
identities and test counts. Candidate-3 archives predate later source changes and
the naming migration. Earlier native Linux x86-64 source tests passed on Swift
6.2.4 and 6.3.3; this does not retroactively qualify candidate-3 Intel archives or
the newly named executable.

Historical OpenClaw timeout cancellation/recovery emitted a matching notification
and a later call succeeded, but caller `AbortSignal` was not forwarded by that
runtime. Its timeout fixture held an already completed response; it did not prove
server-active cancellation. These limits remain separate from SDK lifecycle tests.

## Completion rule

The reviewed source publication, immutable SDK selection and native
qualification of the four [selected archives](Pilot-Distribution.md) are complete
within their recorded scopes. The experimental prerelease plan uses tag `0.1.0`
at application commit `8595fae` and selects the
exact new macOS CI archives and qualified Linux archives, retaining original
names, receipts and packaging-time `releaseReady: false` metadata. That field
is not a live publication or approval flag. Signed source commits, an
ad-hoc ARM64 linker signature and an unsigned Intel binary are described
explicitly; Developer ID/notarization is an optional separate distribution
decision, not a new implementation prerequisite. Publication authorization and
availability remain outside this technical audit.
Native Intel macOS 15.7.9 and ARM64 macOS 15.8.2
source/CLI/archive checks are complete for the new CI bytes. The Intel NetClaw
checks ran under Rosetta; the new ARM64 binary separately passes native NetClaw
checks on macOS 26.7.1. This does not establish macOS 15 NetClaw execution. Earlier
ARM64 results retain their original artifact identity. The minimum stays
macOS 15; the separately authorized ARM64 retry is complete and no additional
CI run is authorized by
this review. Exact macOS 15.0 execution is not claimed. Prepared native Linux
ARM64/x86-64 archive and scoped NetClaw qualification are complete.
NetClaw maintainer coordination
and release authorization remain separate actions. Platform/OS checks govern
advertised distribution claims; they do not
prevent use of the already published, clearly labeled source pilot. The
pre-rename model-driven demonstration is completed scoped evidence; WSL2, native
Windows, musl, protected Hermes, HTTP hosting and MCPB must not inherit claims
from it or from this stdio pilot.

Complete NetClaw service/gateway deployment remains unqualified. It is separate
from the approved pilot's ordinary MCP runtime and installer-integration
requirements, which have scoped native evidence; it is not an additional
prerequisite for this opt-in stdio contribution.
