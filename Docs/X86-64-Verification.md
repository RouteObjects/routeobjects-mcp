# Candidate 3 x86_64 pilot evidence — native qualification UNQUALIFIED

> Historical verification record: these results describe the `swift-cidr-mcp` builds identified below. The project is being renamed to `routeobjects-mcp`; this record is not new-name qualification. See [naming migration](Naming-Migration.md) for current evidence.

Both x86_64 artifacts remain **UNQUALIFIED for native x86_64 execution**. These checks used an ARM64 host: Rosetta for macOS and an explicitly selected `linux/amd64` container for Linux. Passing emulated execution does not establish native Intel/AMD behavior. These are unsigned, unpublished local pilot artifacts with `releaseReady: false` and an uncommitted SDK maintenance patch.

## Source identity

Verified 2026-11-02. Sources were copied into isolated temporary directories; builds reused the separate x86_64 `.build` caches. Candidate 2 archives and evidence were preserved. The candidate-3 change moves unchanged protocol JSON schemas into the MCP adapter boundary. Fresh SDK clones retained the public release baseline and received only the reviewed source overlay. Host Git configuration, credentials, and private projects were not copied.

| Input | SHA-256 / revision |
|---|---|
| Application source | `fc5eb9a70cdca3fe9128d8515979e266ea137d8e2ce04208ad0b34601009a4f3` |
| SDK source | `f54aafb2b2a2f2babcaf414a03fa31bdc0c430f825867e967c24cc9711ff306b` |
| SDK release baseline | `0.12.1`, `a0ae212ebf6eab5f754c3129608bc5557637e605` |

The source digest algorithm hashes root `Package*.swift` files and all files under `Sources`, sorted by relative path, as UTF-8 relative path + NUL + file bytes + NUL. These hashes exclude documentation and test files. The build wrapper verified the nine-pin graph and SDK edit identity, then restored the complete canonical `Package.resolved` after SwiftPM's editable build.

## macOS x86_64

The executable was cross-compiled with Apple Swift 6.3.3 / Xcode 26.6.0 and executed through Rosetta on macOS 26.7.1 (`25G241`), ARM64 hardware. A translated x86_64 process reported `sysctl.proc_translated = 1`; the sandbox-limited first probe is retained separately from the successful read.

| Check | Result |
|---|---|
| Release x86_64 build | Passed |
| Real-process compatibility harness | 19 passed under Rosetta |
| Swift Testing bundle compilation | Candidate 2 compiled successfully; not repeated for candidate 3 |
| Swift Testing execution | Unavailable with the installed ARM-only SwiftPM testing helper; no candidate-3 pass claimed |
| Native x86_64 execution | **UNQUALIFIED** |

The installed `swift` and `swiftpm-testing-helper` binaries are arm64-only. The helper cannot load the x86_64 test bundle. Launching the universal XCTest runner reports zero tests and is not counted as a Swift Testing pass. No custom test loader or additional toolchain was introduced. The 19 subprocess checks execute the actual x86_64 MCP executable, including CIDR arithmetic, wire validation, concurrency, cancellation, and process lifecycle checks.

The executable is 6,065,872 bytes, SHA-256 `2539106128287a6916ed92cc937aeaf123c533848988951dbe3a9804f397817a`. No other macOS version or native x86_64 host has been qualified.

## Linux x86_64

Docker was explicitly requested to run `linux/amd64` on the ARM64 host. The guest reported `Linux x86_64` and Swift 6.3.3 targeting `x86_64-unknown-linux-gnu`; those guest labels do not make execution native.

| Input | Identity |
|---|---|
| Official Swift build base | `swift@sha256:2b618f16484669041d2fb8d7e16a9bc14f1774830eb167f04958074db71b43f4` |
| Prepared verification image | `sha256:e27f3dfa0a9300bc497965f93fba8633eba278466a4e0d3b70b73f99bd6a512a` |
| Clean Ubuntu 24.04 base | `ubuntu@sha256:78d4744ead1f5b19b04d0df558ab182a5300903900755e515b2ca4d10eb2044d` |
| Prepared runtime image without Swift | `sha256:6fa17c670e4c6f0275f0cb7a82def61d8c462b66b33e5e8e513fef840d736703` |

| Check | Result |
|---|---|
| Release Swift Testing | 28 passed under emulation |
| Release `--static-swift-stdlib` build | Passed |
| Exact stripped distribution executable | 19 subprocess checks passed under emulation |
| Exact distribution executable in clean Ubuntu, no Swift, networking disabled | 19 subprocess checks passed under emulation |
| Runtime linkage | No missing libraries; no dynamic Swift/Foundation/Dispatch runtime |
| Native x86_64 execution | **UNQUALIFIED** |

Only a distribution copy was processed with `strip --strip-unneeded`; the unstripped build output was preserved. The distributed ELF x86-64 executable is **61,857,528 bytes (58.99 MiB)**, below the existing 64 MiB NetClaw executable ceiling. Its SHA-256 is `995a8ef5be617272c063daa7de87ba810b9eab5b14b1a3dec0534c851b49de15`. The archive must contain these exact stripped bytes.

Static Swift runtime linking does not make the executable fully static. Ubuntu's `libcurl4t64` and its standard-library dependencies are required. The clean runtime has no Swift installation and uses `--network none` for the tests. Python 3.12 with `jsonschema==4.25.1` is test tooling, not an MCP runtime requirement. The observed static Foundation link warning about `mktemp` was not modified by this work.

## Packaging and repeatability

The archives are named `swift-cidr-mcp-0.1.0-pilot-macos-x86_64.tar.gz` and `swift-cidr-mcp-0.1.0-pilot-linux-x86_64.tar.gz`. Their manifests record `executionEvidence: emulated`, the source and binary hashes, complete dependency inventory, and `releaseReady: false`; notices and licenses are included. Native qualification remains UNQUALIFIED regardless of archive availability.

For macOS, configure the isolated SDK edit and use `python3 Scripts/build-pilot.py --sdk-path /absolute/sdk build --configuration release --arch x86_64`. Run the independent subprocess harness against the resulting x86_64 executable. The installed unit-test runner limitation above still applies.

For Linux, use the pinned AMD64 Swift image, configure the SDK edit, run `build-pilot.py test --configuration release`, then `build-pilot.py build --configuration release --static-swift-stdlib`. Copy the executable, strip that copy, check its size, and execute the 19-test harness against the stripped copy. Archive it with `--execution emulated`; verify checksum, extract, and repeat the same harness in the prepared Ubuntu runtime with networking disabled.

## Candidate history and evidence

Candidate 2 archives and their original manifests remain under `artifacts/candidate-2/`; their source identity was `74192cf2ed713e3b0cbbec09d837112ef39f198f9521fc300def228f98306da6`. Candidate 3 uses the new application identity above and the unchanged reviewed SDK source. No SDK suites were rerun for this adapter-only change.

Candidate-3 build/runtime evidence is in `.verification/x86_64-v3/` and will accompany its archives under `artifacts/candidate-3/evidence/x86_64/`. The initial scratch sync caught SwiftPM's temporary omission of the edited SDK pin from the root lockfile; both dependency guards refused before compilation. The exact nine-pin lock from the preserved candidate-2 archive was restored in the scratch copies and matched the root's restored canonical lock byte-for-byte. The guarded refusals are retained as setup evidence, not failed compilation or qualification.

Archive extraction checks and final archive checksums are recorded after packaging. The build and runtime results above describe the exact preserved distribution binaries. Native x86_64 execution remains UNQUALIFIED, and no archive is published.
