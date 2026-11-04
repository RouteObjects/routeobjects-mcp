# Native Linux x86-64 verification

Qualification date: November 3, 2026 (America/New_York; command logs extend into
November 4 UTC). The renamed four-tool pilot passed native Intel Linux source,
clean-archive and scoped NetClaw integration checks. This closes the earlier
SSH-blocked Linux x86-64 qualification gap. No production source, schemas,
tool/result contracts or dependency pins changed for this run.

The native Intel Linux environment runs Ubuntu 24.04.5. The Swift compiler targets
`x86_64-unknown-linux-gnu`, and the tested executables are x86-64 ELF binaries.
These runs used native execution, without Rosetta or AMD64 emulation. They are
Linux results and do not qualify an Intel Mac or the macOS 15 minimum runtime.

## Source and test matrix

| Native toolchain | Debug | Release |
| --- | --- | --- |
| Swift 6.2.4 | 39 Swift tests and 30 subprocess methods passed. | 39 Swift tests and 30 subprocess methods passed. |
| Swift 6.3.3 | 39 Swift tests and 30 subprocess methods passed. | 39 Swift tests and 30 subprocess methods passed. |

The expanded inventory includes the canonical range-cover oracle's host-bit
mutation check and independent JSON Schema coverage of all four relation results
in both IP families. The original ARM64 runs retain their recorded 38/29 counts;
their later focused acceptance tests are described in the
[qualification follow-up](Qualification-Followup.md#acceptance-test-audit).

The controlled wrapper validated the complete dependency locks and SDK identity.
Both locks and all input source files remained unchanged. The compiled application
source digest is
`64920883272eaa168c45f0b32463b84ce1534f95222540a01b201d1cfb5678b4`;
the maintenance SDK source digest is
`b8084e9769c9b48027db6e2ec2d8a29718102449476423e4d7e4e47fd80332c1`.
These identify compiled inputs, not immutable published revisions or the later
edited report files.

For each toolchain, the command sequence used the isolated reviewed SDK checkout
and a Python environment with test-only `jsonschema 4.25.1`. Public command shapes
are shown below; `SDK_CHECKOUT` denotes that checkout, not a new dependency pin.

```sh
python3 Scripts/build-pilot.py --sdk-path "$SDK_CHECKOUT" test --configuration debug
python3 Tests/Compatibility/test_stdio.py --binary .build/debug/routeobjects-mcp -v
python3 Scripts/build-pilot.py --sdk-path "$SDK_CHECKOUT" test --configuration release
python3 Scripts/build-pilot.py --sdk-path "$SDK_CHECKOUT" build --configuration release
python3 Tests/Compatibility/test_stdio.py --binary .build/release/routeobjects-mcp -v
```

## Native distribution artifact

Swift 6.3.3 built a separate Linux Release distribution executable using the
controlled wrapper's `--static-swift-stdlib --linker-strip-all` options. The actual
linker invocation is recorded in its build receipt. No post-receipt stripping or
other binary mutation occurred.

| Item | Recorded identity |
| --- | --- |
| Archive | `routeobjects-mcp-0.1.0-pilot-linux-x86_64.tar.gz` |
| Archive SHA-256 | `daa0bc4af0dd501405400d318d06e4f872158317098854525dfcf1212807491a` |
| Archive size | 23,529,829 bytes. |
| Executable SHA-256 | `77ba6ae7cccf7291b09631c5bf3dae82a96350361a95e935365f290ead8455a0` |
| Executable size | 61,898,488 bytes; below NetClaw's unchanged 64 MiB import/ownership bound. |
| Build receipt SHA-256 | `a6f6d2f3cd69adc0ba948147e7738fbe21184326578bce70b779bd12fb0ab995` |
| Release state | Development review artifact, `releaseReady: false`. |

All 30 subprocess methods passed after fresh extraction in a native clean Ubuntu
runtime with no Swift installation. The probe used fresh user, mount, PID and
network namespaces, a read-only root filesystem/input, and owned writable test
output. No host home, source checkout or Swift installation was mounted into the
runtime. Python 3.12.3 and `jsonschema 4.25.1` supplied the independent validator;
glibc and libcurl supplied the documented system runtime prerequisites.

The probe verified archive/receipt/executable/lock identities, all nine dependency
pins and license directories, the native ELF architecture, CLI version and absence
of dynamic Swift-library dependencies. The network-isolated clean-runtime result
is distinct from the ordinary NetClaw checks below.

The earlier emulated Linux archive remains unchanged at SHA-256
`1d2823be740253193d4e045731897e390edc9e76e3fccbe64d952be5725f8dbc`.
Its 29+29 subprocess results remain emulation evidence for those exact bytes;
the new native result does not retroactively qualify that archive. Each archive
retains the source-documentation snapshot packaged at its creation. This report
was not inserted into either archive after qualification.

## Native NetClaw import and ordinary runtime

The exact new archive executable passed:

- Seven installation-owned import/helper cases, including checksum/version,
  ownership/resume and the four-tool semantic probes.
- Six ordinary-runtime calls spanning all four tools.
- Three CIPS resource checks: discovery, the current guide URI and rejection of
  the old URI.
- Timeout cancellation/recovery, with the existing caller-`AbortSignal` behavior
  explicitly recorded as `UNSUPPORTED_BY_RUNTIME`.

These checks used native Node 22.23.4 and the cached OpenClaw 2026.7.1-2 import
closure, the canonical NetClaw registration/launcher, and normal unprivileged
user execution. `HOME` stayed unchanged; dedicated state/configuration locations
scoped the test. This NetClaw run did not use a network namespace and does not
inherit the clean-runtime network-isolation claim.

An initial qualification attempt failed the installer's `unsafe_parent` check:
temporary-directory permissions and namespace user mapping did not meet the
ownership requirements. That failure was retained. Correcting only the temporary
directory permissions and using normal-user execution allowed the unchanged
checks to pass; no installer rule or product code was weakened.

The timeout fixture withholds an already completed response. It establishes
timeout notification and subsequent-call recovery, not cancellation of active
server computation. The exercised MCP/configuration path is qualified; no clean
Linux npm installation, optional native modules, complete gateway/service
deployment or new model-selected chat is claimed.

## Remaining boundaries

The SDK remains the reviewed-source maintenance checkout based on released
0.12.1, with the existing adapter-owned bounded stdio transport. The supported
protocol claim remains the four legacy revisions through `2025-11-25`; this is
not July 2026 conformance or full SDK/PR verification.

Native Intel Mac and minimum-macOS 15 execution remain unqualified. WSL2, native
Windows, musl, protected Hermes, HTTP hosting and MCPB remain outside this pilot's
claims. Publication still requires exact source/SDK review, immutable revisions,
and a final release rebuild with fresh artifact qualification. NetClaw maintainer
coordination and publication authorization remain separate. No sending, staging,
commits, pushes or releases were performed by this qualification.
