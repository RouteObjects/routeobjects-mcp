# Implementation review

Current status, November 3, 2026: **RouteObjects MCP** is the permanent product and
executable identity. The four-tool implementation, bundled CIPS guide, semantic
descriptions/NetClaw skill, isolated signal bridge, and publication-review fixes
are present. Tool names and result contracts are unchanged. Publication and
installable release qualification remain incomplete.

The [publication-preparation report](Publication-Preparation.md) records the later
build-selection and review-tooling changes, their regression results and current
input identities. The four tools and contracts are unchanged. Earlier archives
retain their exact tested source/SDK identities and are not recertified by those
tooling checks.

The [naming qualification report](Naming-Migration.md) records the earlier
platform and integration status. Renamed Linux ARM64 runs passed 38 Swift tests
and 29 subprocess checks per configuration on Swift 6.2.4 and 6.3.3. Renamed
macOS ARM64 Debug and Release each passed 38/29. NetClaw component, catalog,
installer and runtime-isolation checks passed. The renamed Release passed 7
native import/helper cases and 6 ordinary-runtime calls spanning all four tools,
plus timeout cancellation/recovery. Packaging-driver tests passed all 13 cases. Fresh
native Linux x86-64 runs now pass the expanded 39 Swift tests and 30 subprocess
checks in Debug/Release on both Swift 6.2.4 and 6.3.3. Its new archive passes 30
checks in a native clean runtime without Swift, plus 7 NetClaw import/helper
cases, 6 runtime calls, 3 CIPS resource checks and timeout recovery. The
[native report](Native-Linux-X86-64-Verification.md) identifies the exact artifact
and scope; the earlier ARM64 38/29 runs remain separately recorded.

The receipted Linux ARM64 and native x86-64 distribution binaries use controlled
linker-time stripping and are 60,292,776 and 61,898,488 bytes respectively. Both
fit the unchanged 64 MiB NetClaw import bound and passed their separately recorded
clean-runtime/archive and import checks. No post-receipt stripping is permitted.
Final immutable-release packaging remains required; all prepared development
artifacts retain `releaseReady: false`.

## Implementation boundaries

1. `routeobjects-mcp`: SDK-independent calculations/contracts, replaceable adapter,
   executable, locked baseline, bounded I/O/logging, signal ownership, tests,
   CIPS guide, Inspector support, and receipted archive/review scripts.
2. `swift-sdk`: released 0.12.1 baseline with existing production changes confined
   to `Server.swift`; lifecycle/cancellation/resource controls and their focused
   tests. Stock `StdioTransport` remains unchanged. The tested maintenance source
   has no reviewed immutable published revision yet.
3. `netclaw`: optional `routeobjects` component with `routeobjects-mcp` registration,
   `ROUTEOBJECTS_MCP_*` bindings, ownership-aware binary import, skill, docs, and
   contract tests. Existing calculator, profile membership, and protected Hermes
   policy are preserved. Its existing experimental branch name is historical;
   the naming work does not imply a remote branch or repository rename.

## Review and publication inventory

Use the freshly reviewed explicit path/hash/mode manifest. The corrected
`Scripts/make-review-bundle.py` consumes that manifest and validates its selected
files instead of deriving publication scope from every untracked path. Older
bundles and candidate-3 `paths.json` remain historical snapshots. The primary
publication review covers this package and the SDK maintenance fork; NetClaw
retains its separate integration review. Exclude local evidence/logs, archives,
caches, duplicated patches, temporary aliases, and private material. A review
patch is not authorization to stage or commit untracked files.

## Historical candidate-3 tests and evidence

- Native ARM64 macOS and Linux: 28 Swift tests in Debug and Release; 19 independent process tests, including all four negotiated revisions.
- Candidate 3 places schemas in the adapter as planned. All complete tool definitions compare equal to candidate 2. Its 28-test runs include the 11 adapter tests, exact frame boundaries and measured stderr saturation.
- SDK: 573 native macOS tests, 28 focused native Linux tests, plus independent gated regressions that exposed and verified the corrected lifecycle/batch cases.
- NetClaw: 10 new component fixtures, 9 catalog tests, 277 existing installer tests with declared skips, reconciliation/generated checks, 404 HUD tests and production build, real binary import/resume, and native OpenClaw config/discovery/runtime success/error calls.
- Inspector 2.13.0 / Node 22.23.4: final Release CLI/TUI/Web pass, including the exact IPv6 `/0` count in all three clients. Modern-only negotiation fails as expected.
- Four checksummed archives with dependency/runtime notices are under `artifacts/candidate-3`. Native ARM64 archives are qualified on the recorded hosts. Both x86-64 candidate-3 archives have translated/emulated process evidence; that snapshot did not have native x86-64 qualification. Later native Linux x86-64 source tests are recorded separately and do not retroactively qualify those archives. `ARTIFACTS.json` lists hashes and execution status.

See [Verification.md](Verification.md), platform reports and the NetClaw/SDK evidence ledgers for exact scope and limitations.
The [acceptance matrix](Acceptance-Matrix.md) maps the approved plan to evidence
and names the remaining gates; it is not an all-green release checklist.

## Verification and rollback

Use `Scripts/configure-pilot.sh` and `Scripts/build-pilot.py`, then the independent
subprocess harness. The wrapper checks the canonical lock and actual SDK
selection, including reviewed source/lock hashes. Development mode retains the
release baseline and an explicit local checkout. Pinned mode requires matching
manifest/selection revisions and forbids a local SDK override; the actual
maintenance revision remains unset until a reviewed commit exists. Build receipts bind the executable to its compiled
inputs and command; regenerate and requalify when build options or bytes change.
Linux's bundled Swift runtime still needs documented glibc/libcurl prerequisites.

Rollback uses path-specific source restoration and the installer's ownership
machinery while preserving unrelated work. Do not repurpose `HOME` for tests or
assume a working-directory change isolates service setup. Use task-specific state
and configuration paths with service hooks disabled for scoped runtime checks;
complete service installation requires its own explicitly qualified environment.

## Remaining review gates

- The future immutable selection path is implemented, but a real reviewed SDK
  commit and its clean-checkout qualification are still required. Signed commits, remote repository naming,
  publication, signing/notarization, tags and releases remain reviewed actions.
- Qualify every newly named archive, its checksum/dependency inventory and actual
  installer path from the reviewed immutable release inputs. Native macOS
  x86-64, minimum macOS 15 runtime and WSL2 remain unqualified. No native Windows,
  musl, protected Hermes, HTTP or MCPB claim is made.
- The model-selected chat is verified for the pre-rename build, including the
  initial validation failures and recovery. The existing chat registration now
  uses the renamed server and reports healthy/ready without altering auth, models
  or history; no new model turn was executed. Full service setup remains separate.
  Renamed Release timeout recovery passed but does not prove caller `AbortSignal`
  forwarding or server-active cancellation.
- Prior SDK contributions were posted with explicit authorization: [#266
  verification](https://github.com/modelcontextprotocol/swift-sdk/pull/266#issuecomment-6578317796),
  [#298 evidence](https://github.com/modelcontextprotocol/swift-sdk/pull/298#issuecomment-6578364439),
  and [resource controls #319](https://github.com/modelcontextprotocol/swift-sdk/issues/319).
  Those reports retain their exact tested revisions; neither posting nor unrelated
  CI results establish complete PR verification or upstream API acceptance.

See the [acceptance matrix](Acceptance-Matrix.md) for the remaining release gates.
