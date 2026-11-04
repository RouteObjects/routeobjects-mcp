# Native Linux ARM64 pilot verification

> Historical verification record: these results describe the `swift-cidr-mcp` builds identified below. The project is being renamed to `routeobjects-mcp`; this record is not new-name qualification. See [naming migration](Naming-Migration.md) for current evidence.

Verified on 2026-11-02 for local candidate 3 of `0.1.0-pilot`. The schema definitions now reside in `CIDRMCPAdapter`, matching the approved target boundary. This required a new binary and qualification. Candidate-2 evidence remains preserved; no result below is inferred merely from its earlier tests. No public release or other-platform qualification is established here.

## Environment and source identity

Compilation and execution used native ARM64 Linux in OrbStack on an ARM64 host, without CPU emulation. The build container reported `aarch64`, kernel `7.2.12-orbstack-00394-gbecdd6130068`, and Swift 6.3.3 targeting `aarch64-unknown-linux-gnu`.

| Input | Identity |
| --- | --- |
| Build image | `swift@sha256:1038d54c80063f5cdfabc4560990c30af64b5de8ebf28161deb22ca4ad5db866` |
| Runtime base | `ubuntu@sha256:fe81560990fae86dc4743202b2cb4d3df98d0bcf949173cecef15ce1127ef852` (Ubuntu 24.04 ARM64) |
| Prepared clean runtime | `sha256:8a4d8b173ccca18be4ecc6b9d0317a4a6ac68c1a8b85e4746e9175dc26a619a1` |
| CIDR | `0.8.1`, revision `f8d8077191342e58e4f593531d3e7cfb7625988e` |
| SDK baseline | `0.12.1`, revision `a0ae212ebf6eab5f754c3129608bc5557637e605`, plus uncommitted maintenance patch |
| SDK source SHA-256 | `f54aafb2b2a2f2babcaf414a03fa31bdc0c430f825867e967c24cc9711ff306b` |
| MCP source SHA-256 | `fc5eb9a70cdca3fe9128d8515979e266ea137d8e2ce04208ad0b34601009a4f3` |

The source digests cover root `Package*.swift` and all `Sources` files, sorted by relative path; each entry hashes its UTF-8 path, NUL, file bytes and NUL. They identify production sources, not tests or documentation. Only public package/SDK source was copied into the temporary qualification directory. The existing isolated dependency cache was reused. The wrapper verified the edited SDK identity, unchanged non-SDK pins and source digest, and restored the complete canonical nine-pin lock after every build.

## Observed results before packaging

| Check | Result |
| --- | --- |
| Debug Swift Testing | 28 passed |
| Release Swift Testing | 28 passed |
| Debug subprocess compatibility | 19 passed |
| Release subprocess compatibility | 19 passed |
| Release build with `--static-swift-stdlib` | Passed |
| Exact stripped distribution binary, build container | 19 compatibility tests passed |
| Complete parsed tool catalog versus candidate 2 | Identical, including every schema and metadata field |
| Actual NetClaw import/helper in clean runtime, no Swift, networking disabled | Passed: ownership/resume/revision/mode 0700, discovery, context, full IPv6 count and error exit |
| Network syscall audit on exact stripped binary | 26 representative checks passed; no IPv4/IPv6 or DNS connection/send attempts |

The 28 Swift tests include exact frame boundaries: 16,383 payload bytes plus LF accepted inbound, first 16,384-byte payload rejected before delimiter/EOF, 65,535 payload bytes plus LF accepted outbound, and the next payload size rejected before writing. The 19-test process harness uses independent `jsonschema==4.25.1`, checks four protocol revisions, schemas and text/structured equivalence, strict/domain errors, batch/correlation/admission behavior, concurrency, fragmented input, EOF/signals and stalled output. Its strengthened stderr test measured `EAGAIN` at 65,536 bytes before server launch, then completed calls and EOF without draining that pipe. Gated SDK tests provide active cancellation/cleanup ordering evidence; the process harness's cancellation notification checks recovery. See [Verification.md](Verification.md).

The whole parsed four-tool catalog matched candidate 2, with canonical JSON SHA-256 `9bd9b38a97f36a73a6292e50e0f770f4a677fc6c53584689df0d22554557fa88`. The schema relocation therefore preserved the advertised JSON contract in this comparison.

## Runtime and distribution binary

| Item | Value |
| --- | --- |
| Distributed executable SHA-256 | `44ec5f7bd949479c5ad047f076626c9dadae6102778fce4194682f128dd9ce60` |
| Distributed executable bytes | `60,280,488` |
| Original static-runtime build SHA-256 | `8a3beb69953e79d6ef57f954e8a5ef6ec4402597e5ae44872cf1d2923d169661` |
| Original bytes | `82,459,400` |
| Format | ARM aarch64 ELF64 PIE, dynamically linked, stripped |
| Transformation | GNU strip 2.42 `--strip-unneeded` on a copy |

The exact stripped copy fits NetClaw's unchanged 64 MiB ownership limit. Its full 19-test suite passed after stripping. The original build was preserved. Dynamic linkage includes libcurl and standard Linux libraries; it is not a fully static executable. `ldd` found no missing libraries or dynamic Swift, Foundation, Dispatch or Blocks runtime. Successful clean-runtime import/helper execution used no Swift installation.

The prepared Ubuntu runtime includes `libcurl4t64` 8.5.0-2ubuntu10.16 and glibc 2.39-0ubuntu8.9. Python 3.12 and jsonschema are qualification tooling, not server prerequisites. Installation does not add Swift or system packages automatically. The static link still emits Swift Foundation's pre-existing `mktemp` warning; this work did not modify or audit that dependency implementation.

## Network audit

The exact distribution binary ran under `strace 6.8 -ff -e trace=network` in the pinned disposable audit image `sha256:ef1eeb417d28edfd134b67affa22a24b94db387e9a44b8e4f23fd4b092285995`. Ordinary Docker bridge networking was configured; no extra capabilities or ports were added. Only the server and its children/threads were traced, not Python or the validator. The binary hash was verified before execution.

All 26 checks passed under negotiated MCP 2025-11-25, covering all four tools over IPv4/IPv6, normalization, worst-case range cover, hostname rejection, domain/shape errors, malformed IDs/JSON, recovery and EOF. Ten trace logs recorded zero `AF_INET`/`AF_INET6` events and no IP/DNS connection/send attempts. Two Unix-domain operations occurred: a datagram socket and a failed `/dev/log` connect (`ENOENT`). They are recorded separately; no absence-of-all-sockets claim is made.

This is evidence for these inputs and exact bytes, not every possible execution. The audit preceded packaging. Independent archive extraction must match the same binary hash to associate these results with the packaged executable.

## Reproduction and archive verification

Build commands use the preserved nine-pin wrapper:

```sh
./Scripts/configure-pilot.sh /path/to/sdk
python3 Scripts/build-pilot.py --sdk-path /path/to/sdk test --configuration debug
python3 Scripts/build-pilot.py --sdk-path /path/to/sdk test --configuration release
python3 Scripts/build-pilot.py --sdk-path /path/to/sdk build --configuration release --static-swift-stdlib
```

Use `Tests/Compatibility/test_stdio.py` with the exact selected binary and pinned validator. After packaging, verify the archive checksum, extract it in the clean runtime without Swift/networking, assert the executable hash above, run `--version` and `ldd`, and repeat the 19-test process suite. Archive checksums and postpackaging results are retained beside the artifact, avoiding a self-referential archive hash in this included report.

Evidence lives under `artifacts/candidate-3/evidence/linux-arm64`: source/binary identities, build/test log, schema comparison, NetClaw import and network audit. The manifest records `releaseReady:false` and the uncommitted SDK patch. Signing, immutable SDK publication/pinning and release remain separate reviewed actions. No native x86-64, WSL, Windows or musl claim follows from this ARM64 run.
