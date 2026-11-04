# Qualification follow-up — November 3, 2026

The renamed pilot now has fresh Inspector Web/TUI evidence, native Linux ARM64
NetClaw import/runtime checks, a real generated-catalog check, a macOS x86-64
archive exercised through Rosetta, and a Linux x86-64 archive tested under
emulation on ARM64. A subsequent [native Linux x86-64 run](Native-Linux-X86-64-Verification.md)
passed the expanded source matrix, a new clean-runtime archive and scoped NetClaw
integration. The four tools, schemas, result contracts,
production source and dependency pins are unchanged. Publication remains pending.

This report and the current [acceptance matrix](Acceptance-Matrix.md) supersede
stale pending rows in earlier documentation. Existing archives, their manifests,
and embedded documentation retain their packaging snapshots and checksums. These
new report bytes were not retroactively added to those archives. Final release
packaging from reviewed immutable source/SDK revisions is still required.

## Client and integration results

| Scope | Observed result | Qualification limit |
| --- | --- | --- |
| Inspector 2.13.0 Web, Node 22.23.4 | Two actual `cidr_inspect` form calls passed: contextual IPv4 address preservation and exact IPv6 `2^128`, with text/structured equality. New CIPS resource discovery/read, automatic fallback, legacy discovery and expected modern-only incompatibility passed. | Web calls exercised these two inspection cases; separate CLI evidence covers all four tools. |
| Inspector 2.13.0 TUI, Node 22.23.4 | Two actual legacy-mode TUI calls passed the same context/count checks and saved text/structured equality. Automatic discovery and expected modern-only incompatibility passed. | This was a real terminal UI session; automatic mode was tested for discovery, not an additional tool-call suite. |
| NetClaw catalog generation | Unmodified `node scripts/build-catalog.mjs --check` passed against the current catalog and all 240 skill documents, using exact locked YAML 2.9.1 in an isolated copy. | No source-tree/global dependency installation or generator change was needed. |
| Native Linux ARM64 import/helper | Checksum-pinned archive executable imported into installation ownership; version, 0700 mode, revision, resume and all seven unchanged helper cases passed. | Focused component/ownership check; full setup-engine/service deployment remains separate. |
| Native Linux ARM64 ordinary runtime | Six calls spanning all four tools, three CIPS resource checks, and deterministic timeout/cancellation/recovery passed through actual config resolution, canonical launcher and the installed executable. | OpenClaw 2026.7.1-2 still ignores caller `AbortSignal`. The timeout relay held an already completed response, so it does not prove cancellation of server-active work. |

Linux integration used native Node 22.23.4 with the cached, unmodified OpenClaw
MCP session JavaScript, MCP JavaScript SDK 1.29.0 and TypeBox 1.3.3. Runs used a
network-disabled native ARM64 runtime. `HOME` was unchanged; dedicated state and
configuration paths scoped the runtime. This qualifies the exercised MCP/config
path, with no claim about a clean Linux npm installation, optional native modules,
full gateway/HUD deployment or model execution. No new AI chat turn was run.

## Artifact evidence

The tested macOS ARM64 archive (`aae466…`) passed all 29 subprocess checks after
fresh extraction on native macOS 26.7.1 with a restricted environment. The current
reviewed archive (`c549bc…`) changes only `README.md`: archive-member comparison
confirmed identical executable, build receipt, lock, libraries, licenses and
resources. Its executable evidence is therefore the prior extracted-archive run
plus this explicit parity check, not a claim that the new archive hash was the
input to that run.

The Linux ARM64 archive passed all 29 checks after fresh extraction in a native
runtime without Swift installed; its dependency inventory and nine license
directories were verified. It also passed the import/runtime checks above.

A new thin macOS x86-64 Release binary passed 29 subprocess checks, followed by
29 more against a fresh archive extraction with verified receipt, lock and nine
license directories. Execution was **Rosetta on ARM64**, confirmed by
`sysctl.proc_translated=1`; it does not establish native Intel Mac qualification.
The encoded deployment target is macOS 15, whose runtime remains untested.

The Linux x86-64 Release used the actual AMD64 Swift 6.3.3 compiler in a
`linux/amd64` container on an ARM64 OrbStack host. All 13 packaging-driver tests,
29 Release-binary subprocess checks and 29 fresh extracted-archive checks passed.
The latter used a network-disabled clean runtime without Swift, verifying the
archive checksum, executable, receipt, nine pins and nine license directories.
This is **emulated AMD64 execution**; it adds no native Debug/full Swift-test-matrix
or Linux x86-64 NetClaw integration claim. The later native result has its own
archive identity and report below.
The archive's documents came from its frozen packaging snapshot before these
final report updates.

| Archive | SHA-256 | Execution evidence |
| --- | --- | --- |
| macOS ARM64 — current reviewed archive | `c549bc81e5c6c56f490ead26cb5d3ad9f442b3af1719d0210ac2b708869b4e80` | Only README differs from the tested archive below; executable/receipt/lock/libraries/licenses/resources match. |
| macOS ARM64 — prior directly tested archive | `aae466233a7b4ab65aeee94668a9e7e7b3da74a77c670ec335fdd8790208c763` | 29 checks after fresh extraction on native ARM64; restricted environment, not a fresh VM. |
| Linux ARM64 | `30fd591150a079f338e2b2a4792ff6f44b395dbde97a9e5a44ec3c14e180516f` | Native ARM64 clean runtime without Swift. |
| macOS x86-64 | `7752687344aa03d8dcccad2a36228280a7f92b017c2cf61e8a63649286f34070` | Rosetta only; native Intel pending. |
| Linux x86-64 — earlier emulated archive | `1d2823be740253193d4e045731897e390edc9e76e3fccbe64d952be5725f8dbc` | Emulated AMD64 on ARM64; 29 checks before and 29 after extraction. This archive was not retroactively qualified natively. |
| Linux x86-64 — new native archive | `daa0bc4af0dd501405400d318d06e4f872158317098854525dfcf1212807491a` | 30 checks after clean extraction on native Intel Linux without Swift; separately passed scoped NetClaw import/runtime checks. |

All use compiled application source digest
`64920883272eaa168c45f0b32463b84ce1534f95222540a01b201d1cfb5678b4`
and the existing maintenance SDK source digest
`b8084e9769c9b48027db6e2ec2d8a29718102449476423e4d7e4e47fd80332c1`.
These are source identities, not immutable published revisions. The Linux ARM64
binary is 60,292,776 bytes; the earlier emulated Linux x86-64 binary is 61,898,488 bytes with SHA-256
`9bec2648785ae0e5bf8fb736385b95ca21f69650ed07a6df6a49ab9a898e9025`.
Both fit NetClaw's unchanged 64 MiB ownership/import bound. Their static Swift
runtime and linker-time stripping are receipted build steps; no post-build
mutation was used. The new native Linux x86-64 executable is also 61,898,488 bytes,
with SHA-256 `77ba6ae7cccf7291b09631c5bf3dae82a96350361a95e935365f290ead8455a0`;
its independent receipt and clean-runtime evidence are in the
[native report](Native-Linux-X86-64-Verification.md). Archives remain `releaseReady: false`.

## SDK partial-write supplement

Separate scratch tests exercised [SDK PR #266](https://github.com/modelcontextprotocol/swift-sdk/pull/266)
at `044e2b31f11714901a2b4a0b2f6f73098a757aca` and historical main
`727175f35c8a0554d9d61c372d4d0da48ebc8b91` with the recorded #266 transport
integration, retaining #297 cleanup. This is not current-main runtime verification.

Four real pipe peer-close runs passed: each SDK variant on native macOS ARM64
and Linux ARM64 rejected active, queued and later sends with `EPIPE` after partial
output. In two native Linux runs, a controlled one-shot `EIO` after a proven
partial write exposed a framing failure: the queued caller reported success while
its frame followed an unfinished earlier frame, producing invalid JSON. Each run
failed its framing assertion. This synthetic fault model is distinct from the
real peer-close result and is not a claim about naturally observed incidence.

The existing RouteObjects bounded transport passed the analogous native Linux
injected-fault test: queued/later sends failed and no later frame followed the
partial prefix. No production fix was needed for this case. These scoped results
do not fully verify #266, #297, all error paths or the SDK. The existing author
retains ownership of the upstream framing work; follow-up discussion is separate
from this report.

## Current #298 revision

The current [#298](https://github.com/modelcontextprotocol/swift-sdk/pull/298)
head `bc2e1cf6aa2ca585d11ca6e752e0d1e699b88ae4` was rechecked before testing.
All 67 tests in the five existing cancellation/HTTP/context suites passed on
native macOS ARM64 with Apple Swift 6.3.3 and native Linux ARM64 with Swift 6.3.3.
The exact upstream production source, manifest and eight-pin lockfile were
unchanged; all eight resolved revisions matched on both platforms.

The separate three-test lifecycle selection produced **one pass and two
failures** on each host. Cancellation before handler registration passed;
stop-completion and EOF-cleanup assertions still failed. This replaces the older
source-comparison-only observation for this head, without claiming full SDK,
Swift 6.1, x86-64 or July 2026 qualification. It does not settle the HTTP design
choices. The existing pilot dependency and maintenance source are unchanged.

## Acceptance-test audit

Two test-only gaps were closed after the original qualification runs. The range
cover oracle now compares each emitted CIDR literal with canonical output before
checking coverage; a deliberately host-bit-set mutation proves the oracle rejects
text that network parsing would otherwise normalize. A new subprocess case checks
all four relation results in both IPv4 and IPv6 through independent `jsonschema
4.25.1` validation and text/structured equality.

Native macOS ARM64 and Linux ARM64 with Swift 6.3.3 each passed the 18 affected
core tests and the new subprocess method's eight cases. This focused follow-up
does not claim a rerun of the entire now-39 Swift-test or 30-method subprocess
inventory. Existing native Release binaries were used for the schema check;
production source, schemas, contracts and dependency pins are unchanged. No new
archive qualification follows from these test-only changes.

The subsequent native Linux x86-64 run executed the complete expanded inventory:
39 Swift tests and 30 subprocess methods in both Debug and Release on Swift 6.2.4
and 6.3.3. Its separately built native archive passed all 30 subprocess methods
after clean extraction. This closes the Linux x86-64 gate without changing the
scope of the earlier focused ARM64 or emulated runs.

## Remaining gates

- Native Intel Mac and minimum-macOS 15 runtime execution remain unqualified.
- Complete NetClaw service deployment and maintainer contribution/specification
  coordination remain separate work.
- Review and publish an immutable SDK dependency, then rebuild/requalify the final
  release with its reviewed source, documentation, inventories and manifests.
- WSL2, native Windows, musl, protected Hermes, HTTP hosting and MCPB remain outside
  the current claims. Supported protocols remain the four legacy SDK revisions;
  no July 2026 conformance is claimed.

No commits, pushes, releases or outbound messages were performed by this follow-up.
