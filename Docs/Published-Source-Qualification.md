# Published source and artifact qualification

Qualification snapshot: November 4, 2026. The four-tool source pilot is public.
The publication plan selects experimental prerelease tag `0.1.0` at application
commit `8595fae`; qualification does not itself establish release availability.
The exact published 65-file tree remains the source of the artifacts below and
the planned tag target. The later signed workflow-only commit
[`9c5313ffc39a95f6e3c9e734bdc96dfb00477516`](https://github.com/RouteObjects/routeobjects-mcp/commit/9c5313ffc39a95f6e3c9e734bdc96dfb00477516)
produced the 66-file baseline for the documentation review. The original
three-document follow-up described a 67-file candidate. Adding the
[pilot distribution guide](Pilot-Distribution.md) and updating README/release
wording makes five documentation paths and a 68-file tree against that baseline.
Those counts identify review snapshots rather than live branch state. Later
documentation commits and standalone attachments alter neither the tagged
build-source snapshot nor any executable or contract.

## Immutable inputs

| Input | Identity |
| --- | --- |
| Consumer source | [`8595fae93803083b6146d04356b1bd02f0d8bfe0`](https://github.com/RouteObjects/routeobjects-mcp/commit/8595fae93803083b6146d04356b1bd02f0d8bfe0) |
| SDK maintenance fork | [`10cb175661ab095abfc73cf293a0c79af244e61e`](https://github.com/RouteObjects/swift-sdk/commit/10cb175661ab095abfc73cf293a0c79af244e61e), based on released SDK 0.12.1 |
| Application compiled-input SHA-256 | `99c75d8296d23a590dcca4d7a7881739d51d5d7bf5eff622e525d5b27e9e9a85` |
| SDK source SHA-256 | `d4a82bbb1e207cfe598c8e68d1d7831bb00308353fb8a1bdcdab7c58b2f0a9ab` |
| Complete dependency-lock SHA-256 | `c1cb3a374a1cb171dbfa6332793fedca318fc45fd58c138beaaab801c89393c9` |

`Package.swift`, `SDKSelection.json` and the complete nine-package lock agree on
the published SDK revision. The maintenance production delta is confined to
shared `Server.swift`; the application's adapter owns bounded stdio. Upstream
attribution and licenses are retained. This is not an official SDK release.

The earlier [published-pin verification](Publication-Preparation.md#published-sdk-pin-verification)
passed 39 Swift tests and 30 independent subprocess checks in Debug and Release
on native macOS ARM64 and native Linux x86-64; Linux covered Swift 6.2.4 and 6.3.3.
All 52 tooling cases passed. These source checks retain their original logs and
are separate from the newly packaged artifact checks below.

Fresh source checks on native Linux ARM64 now pass 39 Swift tests and 30
subprocess checks in Debug and Release on both Swift 6.2.4 and 6.3.3. All 52
tooling cases pass per toolchain; these are repeated executions of the same
52 cases. The new Linux x86-64 run covers the Swift 6.3.3 static distribution
build and archive, not a rerun of its earlier complete source matrix.

## Earlier four-archive snapshot

| Artifact | Execution and result | Boundary |
| --- | --- | --- |
| macOS ARM64 | Native macOS 26.7.1: 30 subprocess checks against the build output and the same 30 after extraction; seven NetClaw import/helper cases, six runtime tool cases and three resource cases pass | Restricted environment and fresh extraction on the existing host; not a fresh VM or minimum-OS test |
| macOS x86-64 | Rosetta on ARM64 macOS 26.7.1: 30 subprocess checks against the build output and the same 30 after extraction | Translated execution only for these earlier bytes; the new native Intel CI archive below has a separate identity |
| Linux ARM64 | Native Ubuntu 24.04/glibc 2.39 on OrbStack: 30 static distribution subprocess checks and the same 30 after extraction; seven NetClaw helper, six runtime tool and three resource cases pass | Network-disabled native containers; runtime roots/archive mounts read-only and fresh owned state |
| Linux x86-64 | Native Intel Linux with Swift 6.3.3: 30 static distribution subprocess checks and the same 30 after extraction; seven NetClaw helper, six runtime tool and three resource cases pass | Extracted-archive checks use a no-Swift runtime in fresh user/mount/PID/network namespaces; NetClaw uses the existing audited fixture and does not claim network isolation |

Each macOS archive matches 38 packaged source/dependency files and all nine
dependency pins. Build receipts select the exact SDK revision without an
uncommitted maintenance patch. The archive metadata retains the original
packaging-time `releaseReady: false` value, which does not track live publication
or approval state. The hashes below identify this earlier evidence snapshot;
selection for the `0.1.0` publication plan is recorded separately below. Packaged
documents retain their original source snapshot.
Both Linux archives also match all 27 packaged files drawn from the published
source tree and all 11 dependency license/notice files. Their nine dependency
pins and receipts agree with the immutable inputs above.

| Local archive | Archive SHA-256 | Executable SHA-256 / size |
| --- | --- | --- |
| `routeobjects-mcp-0.1.0-pilot-macos-arm64.tar.gz` | `662bb3bb4f57c62fe557d6915775342b7d18bd8be11027eef0e64059e50c9b29` | `fb8994910678c272781daf796342a908dcf6d5e253351d19c6d52c13050a2f44` / 6,036,416 bytes |
| `routeobjects-mcp-0.1.0-pilot-macos-x86_64.tar.gz` | `2307ea36f4cc8b397008f41160df69552bc01ca8c0659cfbc4f94ee6d94d79cd` | `1a7ca8873fab82a98dc796d198030bd81be3349a4b8475305518d0538cd5daaf` / 6,147,520 bytes |
| `routeobjects-mcp-0.1.0-pilot-linux-arm64.tar.gz` | `c79ea9c886bace2aa5f5ad822345242d0491362539c70a8e2a123d08212ac6a7` | `fd538a78380087939925b698123575b1b00c1ae0e5944795d830a492b659876c` / 60,292,776 bytes |
| `routeobjects-mcp-0.1.0-pilot-linux-x86_64.tar.gz` | `ba06dcdfa53424dda6def2ea527a8b89aafdd06f2fd66a94d309b09d38567764` | `58410bf6366157f8141e9837328a071bf536115a1099718ddb3b898db7b18f6b` / 61,898,488 bytes |

The macOS ARM64 executable is ad-hoc signed and `codesign --verify` exits 0. The
macOS x86-64 executable is unsigned and verification exits 1. Neither macOS
archive is Developer ID signed or notarized. The Mach-O deployment target is macOS 15; runtime testing
on macOS 26.7.1 does not establish minimum-macOS-15 compatibility.

Both Linux executables were built with receipted `--static-swift-stdlib` and
linker `--strip-all`; no post-build stripping occurred. They run without Swift
installed, while glibc/libcurl and their system dependencies remain required.
The Linux ARM64 image lacked `file`, so packaging ran on macOS against the same
untouched source snapshot and native executable. Its `BUILD-INFO` honestly
retains `executionEvidence: not-run` for that packaging step; the separate
native extracted-archive tests establish execution. No artifact metadata was
rewritten to turn the packaging step into a native runtime claim.

## Native Intel macOS 15.7.9 CI artifact

The [Intel job](https://github.com/RouteObjects/routeobjects-mcp/actions/runs/41856078163/job/126664994965)
builds source `8595fae` and SDK `10cb175` using Apple Swift 6.2.3, Xcode 26.2
(17C52), on native x86-64 macOS 15.7.9 (24G830). Receipt host, translation probe,
raw job logs and the thin x86-64 Mach-O agree. Independent evidence checks match
all 65 source files, nine dependency pins, 11 license/notice files, the uploaded
artifact digest and all 31 downloaded artifact files. All nine recorded job
steps succeeded; the only warnings were four SwiftPM `--skip-update` deprecations.

Both Debug and Release pass 39 Swift tests and 30 subprocess checks; all 52
tooling cases and 30 extracted-archive checks pass. Extracted execution used
restricted `PATH` and denied network access; Xcode remained installed. This
qualifies the new artifact below on 15.7.9, not exact 15.0, a no-Xcode deployment,
or the earlier archive bytes. The separate ARM64 macOS 15.8.2 artifact below
has its own successful job, binary and receipt identities.

| New CI artifact | Identity |
| --- | --- |
| Archive | `routeobjects-mcp-0.1.0-pilot-macos-x86_64.tar.gz` |
| Archive SHA-256 | `53760c4938264f91b263ff462bceb6237c507fe4563001e76a54144257fcf42e` |
| Executable SHA-256 / size | `fe1e8613a10f6ce75650717cc6ff90f74cc39dc72455dc06eebbed5900dd7299` / 6,153,016 bytes |
| Build receipt SHA-256 | `bd4cd653a35c761f8d916de6cc347eb4543cbe1ae4d4a01b000457ff2b24950b` |

The exact downloaded executable additionally passes seven installation-owned
NetClaw import/helper cases, six ordinary runtime tool cases, three resource
cases, configuration resolution and timeout recovery locally under Rosetta on
ARM64 macOS 26.7.1. The unchanged 1,806-file cached runtime closure and all 82
NetClaw/runner inputs were verified. `HOME` was retained and no model or service
was invoked. Native Intel CLI/archive evidence and translated NetClaw evidence
remain separate claims; native Intel NetClaw execution is not established.
Caller `AbortSignal` is still unsupported. The artifact retains its immutable
packaging-time `releaseReady: false` field; CI artifact upload is not release publication, signing or
notarization qualification.
Read-only signature inspection of these exact Intel bytes reports unsigned;
`codesign --verify --strict` and signature description both exit 1. Developer ID
signing/notarization remain a separate distribution-policy decision, not an
implementation requirement for the source pilot.

## Native ARM64 macOS 15.8.2 CI artifact

The declared minimum remains **macOS 15**. A separately authorized job retry
in [run 41856078163](https://github.com/RouteObjects/routeobjects-mcp/actions/runs/41856078163)
now passes as [ARM64 job 126752039275](https://github.com/RouteObjects/routeobjects-mcp/actions/runs/41856078163/job/126752039275),
attempt 3. It builds the same immutable source `8595fae` and SDK `10cb175`
with Apple Swift 6.2.3 and Xcode 26.2 on native ARM64 macOS **15.8.2**.

Both Debug and Release pass **39 Swift tests and 30 subprocess checks**;
all **52 tooling cases** and **30 extracted-archive checks** pass. Artifact
content checks match the source manifest, nine dependency pins, eleven
license/notice files, archive contents and build receipt. The downloaded ZIP
matches the GitHub artifact digest and contains 31 verified files.

| New ARM64 CI artifact | Identity |
| --- | --- |
| Archive | `routeobjects-mcp-0.1.0-pilot-macos-arm64.tar.gz` |
| Archive SHA-256 | `0bc482660ace98204c1ebf350544d47fed052813474767d3a3c56bfb7b359b43` |
| Executable SHA-256 / size | `9dae199cebd499084b7f7ca69163dc01154f99d21a1f2380a64c05fdbd867833` / 6,051,136 bytes |
| Build receipt SHA-256 | `be9f0aa948d0ba566a7fd04fdea90d63fca7cc7d435e81880608e07470bd2b31` |
| GitHub artifact ID | `13349267500` |
| Download ZIP SHA-256 | `42cba9dfa51ccdb05dff4022ae1bd6ed04dad41a7e42d29404b030797760116b` |

This closes the ARM64 macOS 15 source/CLI/archive evidence gap for these new
bytes on **15.8.2**. Xcode remained installed; exact macOS 15.0 execution,
no-Xcode deployment and Developer ID signing/notarization are not established.
The artifact retains packaging-time `releaseReady: false` metadata. The earlier macOS 26.7.1 ARM64
archive and its NetClaw tests retain their own binary identity.

The exact downloaded ARM64 binary separately passes seven installation-owned
import/helper cases, six ordinary runtime tool cases, three CIPS resource cases,
configuration resolution and timeout recovery natively on macOS **26.7.1**, using
Node 22.23.4 and OpenClaw 2026.7.1-2. All 1,806 cached runtime files and 82
NetClaw/runner inputs remain unchanged. No model call, service installation,
source/fixture change or `HOME` change occurred. This establishes NetClaw
behavior for the new bytes on 26.7.1, separately from the native CI
source/CLI/archive checks on 15.8.2; macOS 15 NetClaw execution is not claimed.
Caller `AbortSignal` remains unsupported, and timeout recovery uses the
withheld-completed-response fixture rather than active-server cancellation.
Read-only `codesign --verify --strict` succeeds with an ad-hoc linker signature;
Developer ID signing and notarization remain unclaimed.

The first two ARM64 attempts ended without acquiring a runner, executing steps
or producing an artifact. Their capacity failures remain historical evidence;
they are not retroactively changed into passing tests. The owner subsequently
authorized the one additional job retry reported here. That retry is complete;
no further CI run is authorized by this review. No source, workflow, dependency,
minimum-version or tool-contract change was needed for the passing run.

## NetClaw scope and SDK limits

The fresh macOS ARM64 archive passed real installation-owned import/resume and
native configuration resolution using Node 22.23.4 and OpenClaw 2026.7.1-2. The seven
helper, six ordinary runtime tool and three resource cases used the exact
extracted binary above and an unchanged, previously audited 1,806-file cached
runtime closure. Fresh owned state was used; the caller's `HOME` was retained.
No model call, service installation or live-chat change was part of this run.

Both native Linux archive executables independently pass the same 7/6/3
import/runtime/resource checks and configuration resolution with Node 22.23.4
and OpenClaw 2026.7.1-2. Linux ARM64 uses the current experimental integration in
network-disabled containers. Linux x86-64 reuses the previously audited
2,132-file fixture, retaining its earlier catalog metadata; 18 reviewed
integration paths match the earlier manifest. It does not qualify the later
metadata-only source-URL/catalog edits, which have separate local catalog and
component checks. No fresh full NetClaw upload, model call or service installation
is claimed. Initial x86-64 fixture-directory permission failures are retained in
the evidence; only newly owned test-directory permissions were corrected before
the successful rerun, without weakening importer checks.

Timeout emitted the matching cancellation notification and a later call
succeeded. That fixture withheld an already-completed server response; it does
not prove cancellation of active server work. OpenClaw still does not forward a
pre-aborted caller `AbortSignal`. These limits are separate from the SDK lifecycle
tests and do not imply full upstream PR or HTTP/OAuth-suite verification.

Supported protocol claims remain limited to `2024-11-05`, `2025-03-26`,
`2025-06-18` and `2025-11-25`, including applicable March batch behavior. There is
no MCP July 2026 conformance claim. Earlier Inspector and model-selected chat
results remain tied to their tested builds; this archive run does not repeat them.

Native macOS 15 source/CLI/archive qualification is complete for the separate
ARM64 15.8.2 and Intel 15.7.9 CI artifacts. Their scopes do not extend to exact
macOS 15.0, no-Xcode deployment, native Intel NetClaw execution or WSL2. The new
ARM64 binary separately passes native NetClaw checks on macOS 26.7.1; macOS 15
NetClaw execution is not claimed. Earlier ARM64 NetClaw results retain their
original artifact identity.
Developer ID signing/notarization, final release review, NetClaw maintainer scope
agreement and publication actions are separate gates. A fresh full NetClaw/npm
installation and complete service/gateway deployment are not claimed by these
scoped MCP runtime checks. The four tools and [result contracts](../CONTRACTS.md)
are unchanged; private Engine/Claw material remains outside this repository.

## Selected distribution review set

The [pilot distribution guide](Pilot-Distribution.md) selects the new native macOS
CI ARM64/x86-64 archives and the published-source Linux ARM64/x86-64 archives
identified in this report for experimental prerelease tag `0.1.0` at build-source
commit `8595fae`. The publication plan includes a combined exact-asset manifest
and checksum list as separate attachments. The selected archives retain their
original bytes, embedded documents, receipts and packaging-time
`releaseReady: false` metadata; this field does not describe live approval or
availability. Qualification is complete within the recorded scopes. Planned
release URLs and later documentation commits do not change that evidence or
assert that publication has occurred.
