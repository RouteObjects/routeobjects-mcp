# Approved-plan completion audit

Audit date: November 3, 2026. The renamed four-tool pilot is implemented; the
full publication/release objective is **not complete**. The CIPS guide, semantic
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

## Current requirement and evidence mapping

| Approved requirement | Current result | Remaining action |
| --- | --- | --- |
| Separate consumer/SDK repositories and private boundary | Public product is `routeobjects-mcp`; no private Engine/Claw dependency. Core, adapter and executable boundaries remain intact. | Review the fresh explicit publication path/hash allowlist and immutable SDK revision. |
| Swift tools 6.2, language 6, macOS 15; Apache-2.0; 0.1.0 | Manifest/license/CLI retain these settings. Renamed Linux ARM64 and x86-64 tested with Swift 6.2.4 and 6.3.3; macOS ARM64 with Apple Swift 6.3.3. | Native Intel Mac and minimum-macOS 15 runtime qualification remain separate. |
| Exactly four tools and unchanged results | `cidr_inspect`, `cidr_contains`, `cidr_relation`, `cidr_summarize_range`; [standalone contracts](../CONTRACTS.md). Schema ownership stays in the adapter; domain code imports no MCP. | Preserve contracts through future SDK or tool additions. |
| Strict literals, normalization, address context, whole-network containment, family handling, exact counts and minimal covers | Existing fixtures cover these semantics, `2^128`, worst-case covers, and no enumeration/truncation. Renamed Linux ARM64 Debug/Release passes 38 Swift and 29 subprocess tests per toolchain/configuration. | Record fresh results for every additional advertised platform. |
| One envelope, equal text/structured output, stable errors and independent schemas | The harness uses `jsonschema 4.25.1` and verifies representation equality, domain errors, malformed requests and protocol-specific batches. The added relation matrix raises its inventory from 29 to 30 methods; all 30 pass in the new native Linux x86-64 runs. | Keep archived-build validation separate from source test results. |
| Input/output/resource limits; bounded stderr and clean stdout | 8 KiB arguments, 16 KiB inbound, 64 KiB complete outbound, 4 executing/8 queued, batch 8, 256 returned CIDRs and five-second stalled-I/O/shutdown limits remain. Bounded transport/logging, isolated signal ownership and regressions are implemented. | Preserve narrower test claims; these limits do not make the adapter a general streaming JSON encoder. |
| Native source/build checks | Renamed macOS ARM64 and Linux ARM64 each pass 38 Swift + 29 subprocess in their original Debug/Release runs; Linux ran both Swift 6.2.4 and 6.3.3. After two test additions, native Linux x86-64 passed all 39 Swift + 30 subprocess tests in Debug/Release on both toolchains. [Exact scope](Native-Linux-X86-64-Verification.md). | The focused ARM64 acceptance follow-up does not relabel the older full 38/29 runs as 39/30. Native Intel Mac and minimum-macOS 15 remain unqualified. |
| Minimal necessary SDK maintenance and attribution | Existing delta is confined to shared `Server.swift`; stock transport unchanged. Adapter owns bounded stdio. Naming did not change the SDK digest; the later comment-only default-limit clarification has a separately recorded source identity. | Replace editable uncommitted maintenance source with a reviewed immutable revision or qualified official release; preserve patch ledger and licenses. |
| Complete lock and actual compiled identity | Nine baseline pins remain in development mode. `SDKSelection.json` records reviewed SDK source/lock hashes; its maintenance revision is null and must agree with the manifest literal. Pinned-mode checks are implemented, but no published revision is selected. Earlier packaging-driver evidence is 13 passing tests; [publication preparation](Publication-Preparation.md) records the new tooling regressions and build identities. | A source digest does not substitute for an immutable published Git revision. Post-receipt binary mutation invalidates its receipt. |
| Opt-in ordinary NetClaw component | Permanent component `routeobjects`, registration/executable `routeobjects-mcp`, overrides `ROUTEOBJECTS_MCP_*`. Four tools, calculator and existing profile membership preserved. | Coordinate upstream scope/specification number with maintainer. |
| NetClaw component/catalog/installer | 11 component fixtures, 9 catalog tests, 277 installer tests with 32 declared skips and 5 isolation checks pass. The actual unchanged generator passed against all 240 skills with locked YAML 2.9.1. Native Linux ARM64 and x86-64 each passed 7 import/helper cases, 6 runtime calls, 3 resource checks and timeout cancellation/recovery. | Caller `AbortSignal` remains unsupported. The Linux MCP/config path is qualified, not a clean Linux npm installation or complete service/gateway deployment. `HOME` stayed unchanged. |
| Pinned/checksummed installation ownership | Explicit version/checksum import and ownership controls remain. The 60,292,776-byte Linux binary passed clean-runtime/extracted-archive checks and actual native NetClaw import/resume within the unchanged 64 MiB bound. | Rebuild/requalify final immutable-release artifacts; no automatic Swift/system-package installation or post-receipt mutation. |
| Four legacy protocol revisions, including applicable March batches | Harness covers `2024-11-05`, `2025-03-26`, `2025-06-18`, `2025-11-25`; applicable batch behavior retained. | No July 2026 MCP conformance claim. |
| Inspector 2.13.0 / Node 22.23.4 | Renamed CLI: 20 tool/discovery and 6 resource checks passed. Fresh Web/TUI each executed two inspection calls covering context, exact IPv6 count and representation equality; legacy/automatic discovery and expected modern-only incompatibility passed. Web read the new CIPS guide. | CLI covers all four tools; Web/TUI claims remain limited to their actual inspection calls and discovery checks. [Current report](Qualification-Followup.md); [older report](Inspector-Verification.md) remains historical. |
| Model-selected tools and explanations | Pre-rename OpenClaw 2026.7.1-2 / GPT-5.6 Sol chat selected all four tools, then explained their results. Four initial empty-argument calls failed client validation before four valid calls succeeded. The existing registration now hot-reloads the renamed identity with healthy/ready endpoints. | No new model turn was executed. Initial argument-failure cause remains unresolved; no full NetClaw deployment claim. |
| Native archives, clean runtime and inventory | macOS/Linux ARM64 extracted-artifact checks passed all 29 cases; Linux used a clean runtime without Swift. The current reviewed macOS ARM64 archive differs only in README from its directly tested predecessor; runtime members and receipt/lock/license parity match. A new native Linux x86-64 archive passed all 30 checks after extraction in a network-isolated clean runtime without Swift, then scoped NetClaw import/runtime checks. The earlier Linux emulated archive and macOS Rosetta archive retain their separate 29+29 results. | Native Intel Mac, minimum macOS 15 and WSL2 remain gaps. Existing archives retain their packaging documents; final immutable-release packaging remains required. Native Linux evidence does not qualify the macOS Intel artifact. |
| Partial-write failure supplement | Four real peer-close runs passed on native macOS/Linux ARM64 across exact #266 and historical-main+#266. Two synthetic one-shot EIO runs exposed an SDK framing assertion failure; the existing bounded pilot passed the analogous Linux test. [Scope and revisions](Qualification-Followup.md#sdk-partial-write-supplement). | Synthetic EIO and real EPIPE evidence are distinct. This verifies one fault model, not all failure paths or complete upstream PR correctness; no production change or duplicate fix was made. |
| Reviewed commits, remote naming, publication and releases | No staging, commits, pushes, remote rename, tags or releases are performed by publication preparation. Prepared development artifacts remain `releaseReady: false`. | Review exact contents and authorize publication separately. |

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

Required outstanding work includes native Intel Mac and minimum-macOS 15
execution, exact publication review,
immutable SDK selection, and final release packaging/qualification for every
advertised artifact. NetClaw maintainer coordination,
repository publication and release authorization remain separate actions. Native
Intel Mac and minimum-OS checks govern advertised distribution claims; they do not
prevent publication of a clearly labeled source pilot. The
pre-rename model-driven demonstration is completed scoped evidence; WSL2, native
Windows, musl, protected Hermes, HTTP hosting and MCPB must not inherit claims
from it or from this stdio pilot.

Complete NetClaw service/gateway deployment remains unqualified. It is separate
from the approved pilot's ordinary MCP runtime and installer-integration
requirements, which have scoped native evidence; it is not an additional
prerequisite for this opt-in stdio contribution.
