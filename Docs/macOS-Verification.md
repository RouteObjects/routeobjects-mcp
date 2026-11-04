# macOS pilot verification

> Historical verification record: these results describe the `swift-cidr-mcp` builds identified below. The project is being renamed to `routeobjects-mcp`; this record is not new-name qualification. See [naming migration](Naming-Migration.md) for current evidence.

The native host is Apple Silicon, macOS 26.7.1, Apple Swift 6.3.3/Xcode 26.6.0. The executable's `LC_BUILD_VERSION` has minimum macOS 15.0; runtime execution on macOS 15 itself has not been tested here. Its linked Swift libraries and frameworks are OS paths; no Xcode-private dynamic library dependency is required to launch it.

Candidate 3 source SHA-256: `fc5eb9a70cdca3fe9128d8515979e266ea137d8e2ce04208ad0b34601009a4f3`. SDK source SHA-256: `f54aafb2b2a2f2babcaf414a03fa31bdc0c430f825867e967c24cc9711ff306b`, based on 0.12.1 with an uncommitted maintenance patch. The Release binary SHA-256 is `a4f93ae67087b468a6661e3b2a22c3240d15685c52a651dcabf53e9e0b02d35e`.

- Debug and Release each pass 28 Swift Testing tests and 19 independent subprocess compatibility tests.
- The candidate-3 Release executable passes the real NetClaw import/resume/hash/mode checks, unchanged helper, and isolated real OpenClaw 2026.7.1-2 configuration/discovery/native-runtime success/error calls.
- Inspector 2.13.0 on Node 22.23.4 passes candidate-3 Release CLI legacy/auto cases, TUI exact IPv6 `/0` count (earlier contextual-form evidence is retained separately), and Web four-tool forms/error/automatic fallback. Web and TUI preserve the full `2^128` decimal string; modern-only negotiation is the expected incompatibility. See [Inspector-Verification.md](Inspector-Verification.md) for exact browser and build provenance.
- The archive includes all nine SwiftPM dependency licenses, supplemental runtime notices and `BUILD-INFO.json`. Its checksum is in the adjacent `.sha256` file. The archive smoke check extracts its own executable, verifies the recorded checksum, and runs all 19 compatibility tests with a temporary HOME/TMPDIR and PATH restricted to `/usr/bin:/bin`; the post-packaging result log is retained beside the artifact. This is an isolated process environment on the existing host, not a fresh macOS VM.

Native evidence is retained under `artifacts/candidate-3/evidence/macos-arm64`. The archive and its sidecar are under `artifacts/candidate-3`. No signing, notarization, tag or publication has occurred. x86-64/Rosetta evidence is separate and does not establish native Intel execution.
