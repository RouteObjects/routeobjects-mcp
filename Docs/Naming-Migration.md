# RouteObjects MCP naming and qualification

The permanent public identity is `RouteObjects/routeobjects-mcp`. The name is
being established before source publication so consumers can configure one
stable server as additional RouteObjects capabilities are developed.

| Surface | Identity |
| --- | --- |
| Repository/package | `RouteObjects/routeobjects-mcp` / `routeobjects-mcp` |
| Executable and MCP server name | `routeobjects-mcp` |
| Recommended client registration key | `routeobjects-mcp` |
| NetClaw component | `routeobjects` |
| Executable override | `ROUTEOBJECTS_MCP_BIN` |
| Installer settings | `ROUTEOBJECTS_MCP_SOURCE`, `ROUTEOBJECTS_MCP_SHA256`, `ROUTEOBJECTS_MCP_VERSION` |
| Development SDK selector | `ROUTEOBJECTS_MCP_SDK_PATH` |
| Bundled guide | `routeobjects://routeobjects-mcp/guides/cips-v1` |

The four tool names remain `cidr_inspect`, `cidr_contains`, `cidr_relation`,
and `cidr_summarize_range`. Their inputs, result envelopes, error codes,
limits, and schema version are unchanged. The executable target is named
`RouteObjectsMCP`; the independent `CIDRToolCore` and replaceable
`CIDRMCPAdapter` retain their boundaries.

This is one server and one product. `cidrmerge`, `asroutes`, and RPSL operations
are possible future capabilities, not additional tools in this release.

## Local pilot migration

Existing experimental client registrations must change their executable path,
server key, and override names together. Hosts that qualify tool names by server
will change from `swift-cidr-mcp__cidr_inspect` to
`routeobjects-mcp__cidr_inspect`, for example. The pre-publication pilot does not
advertise permanent legacy aliases or register both identities simultaneously.

The repository directory is now `routeobjects-mcp`. A temporary local filesystem
alias keeps earlier development/demo paths resolvable while those clients are
migrated. This alias is outside the repository and is not a distributed feature.
Existing GitHub repository/remote changes require separate review; a new public
repository URL in documentation does not establish that it has been published.

## Current qualification — November 3, 2026

The four-tool source is renamed; publication remains pending. The CIPS guide,
semantic descriptions, isolated signal bridge, and their regression tests are
already included. These additions are not deferred release work. The
[qualification follow-up](Qualification-Followup.md) records completed client,
Linux runtime and artifact checks. Existing archives retain their original
packaging documentation; this source report does not change archive contents.
The later [native Linux x86-64 verification](Native-Linux-X86-64-Verification.md)
closes that platform's source, clean-archive and scoped NetClaw qualification gap
for the source snapshot recorded there. The subsequent
[publication-preparation report](Publication-Preparation.md) owns the new
SDK-selection/build/review-tooling checks and current input identities. The table
below retains the earlier executions; it does not relabel their binaries or
archives as builds of the later publication tooling.

| Scope | Renamed-build result | Remaining limit |
| --- | --- | --- |
| Native macOS ARM64, Apple Swift 6.3.3 | Debug and Release each passed 38 Swift tests and 29 subprocess checks; Release build receipt recorded. | Minimum macOS 15 runtime was not exercised. |
| Native Linux ARM64, Swift 6.2.4 and 6.3.3 | Each toolchain passed 38 Swift tests and 29 subprocess checks in both Debug and Release. | These source checks do not qualify a packaged archive. |
| Linux ARM64 distribution binary/archive | The receipted 60,292,776-byte binary passed 29 subprocess checks, then all 29 after fresh archive extraction in a native clean runtime without Swift. Native NetClaw import/helper and ordinary-runtime checks also passed. | The archive remains a development snapshot with `releaseReady: false`; final immutable-release packaging remains required. |
| Linux x86-64 emulated artifact | Actual AMD64 Swift 6.3.3 compiler on ARM64 emulation: 13 packaging tests, 29 Release-binary checks and 29 clean extracted-archive checks passed. | No Debug/full Swift-test-matrix or x86-64 NetClaw integration claim. |
| Native Linux x86-64 | On native Intel Ubuntu 24.04.5, Swift 6.2.4 and 6.3.3 each passed all 39 Swift tests and 30 subprocess checks in Debug/Release. The new native archive passed 30 clean-runtime checks without Swift and scoped NetClaw import/runtime checks. | This later run includes the two test-only acceptance additions; older ARM64 38/29 results retain their original scope. Native Linux does not qualify macOS Intel. |
| macOS x86-64 archive | Cross-built thin x86-64 binary passed 29 checks before and 29 after fresh archive extraction through Rosetta. | Native Intel Mac and minimum-macOS 15 runtime remain unqualified. |
| NetClaw component/catalog/installer | Existing 11 component/9 catalog/277 installer tests (32 skips) and 5 isolation checks passed. The unchanged generator also passed against all 240 skills using locked YAML 2.9.1. Native Linux ARM64 and x86-64 each passed 7 helper cases, 6 runtime calls, 3 resource checks and timeout recovery. | Full service setup remains unqualified; caller `AbortSignal` remains unsupported by the recorded OpenClaw runtime. |
| Packaging driver | 13 tests passed; macOS/Linux ARM64 extracted-artifact checks passed. The current reviewed macOS ARM64 archive differs only in README, with executable/receipt/lock/library/license/resource parity verified. The earlier macOS/Linux x86-64 archives passed translated/emulated checks; a separately identified new Linux x86-64 archive passed 30 native clean-runtime checks. | Exact archive identities are in the [follow-up](Qualification-Followup.md#artifact-evidence) and [native x86-64 report](Native-Linux-X86-64-Verification.md). Final immutable-release packaging remains required. |
| Inspector 2.13.0 / Node 22.23.4 | CLI: 20 tool/discovery and 6 resource checks passed. Fresh Web/TUI sessions each made two real `cidr_inspect` calls with exact-count/context and text/structured equality checks; legacy/automatic discovery and expected modern-only incompatibility passed. Web also read the new CIPS resource. | All-four-tool execution is covered by CLI; Web/TUI coverage is the scoped pair of inspection calls. |
| Live demo registration | Existing chat registration hot-reloaded to the new identity; health/readiness endpoints returned 200. Authentication, model configuration and history were preserved. | No new model turn was executed; the recorded model-selected demonstration remains pre-rename evidence. |

The earlier native Linux source snapshot is
`64920883272eaa168c45f0b32463b84ce1534f95222540a01b201d1cfb5678b4`;
its SDK source digest was
`b8084e9769c9b48027db6e2ec2d8a29718102449476423e4d7e4e47fd80332c1`.
The macOS Release receipt identifies binary SHA-256
`53a97a6c16dd5989908b51cb64933f47402cbbd62834c91792256422ca2a9138`
(6,034,800 bytes). These are compiled-source/binary identities, not immutable Git
revisions or hashes of subsequently edited documentation. Local command logs and build receipts retain
the exact snapshot/toolchain/binary relationship.

The unstripped Linux binary exceeded NetClaw's 64 MiB executable-import limit.
The final Linux Release build uses `Scripts/build-pilot.py` with
`--static-swift-stdlib --linker-strip-all`; the wrapper restricts the latter to
Linux Release builds and records the actual `-Xlinker --strip-all` invocation in
the receipt. Its SHA-256 is
`e3c66ba4c1e106970820f1c4db2379f63d98f9d6c06f56555f5c714e4ebcc2bb`
and size is 60,292,776 bytes, closing the executable-size gate without changing
the import limit or shared ownership rules. The same receipted binary passed 29
clean-runtime checks and 29 checks after fresh archive extraction. The later
[qualification follow-up](Qualification-Followup.md) adds native Linux NetClaw
import/runtime evidence. Stripping or otherwise mutating bytes after their build
receipt is issued invalidates that receipt.

The renamed Release runtime also passed timeout cancellation/recovery. The
pre-aborted caller limitation remains: this OpenClaw materialized API does not
forward caller `AbortSignal`. Its timeout fixture does not establish cancellation
of server-active work; separate SDK lifecycle tests cover their own scope.

## Historical evidence

Earlier Inspector reports, candidate-3 archives, SDK verification and the recorded AI chat retain
the `swift-cidr-mcp` identity and exact hashes they actually tested. They establish
the predecessor's behavior; they do not certify a newly named archive or client
registration. Earlier native Linux x86-64 runs passed 38 Swift tests and 29
subprocess checks per Debug/Release configuration on Swift 6.2.4 and 6.3.3. Native
macOS x86-64 and WSL2 remain separate gaps.

The pre-rename OpenClaw 2026.7.1-2 / GPT-5.6 Sol chat selected all four tools and
explained their results. Four initial empty-argument attempts failed client
validation; four valid MCP calls then succeeded without intervention. The cause
of those initial failures remains unresolved. A renamed model-driven demo remains
pending; no full NetClaw deployment claim follows from the scoped chat.

The SDK remains the released 0.12.1 baseline with explicit, uncommitted
shared-server maintenance changes and an adapter-owned bounded stdio transport.
No dependency pins or SDK production code were changed by the naming migration.
Later publication preparation adds reviewed-source and future pinned selection
modes, with no real immutable revision selected. Its SDK source digest changes
only because of the clarified default-limit comment; the recorded native archive
SDK hash above remains historical. The four tools and contracts are unchanged.
Publication still requires reviewed immutable source/dependency revisions and
qualified artifacts. There is no July 2026 MCP conformance claim.
