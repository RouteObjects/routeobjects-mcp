# CIPS guide source-build verification

> Historical verification record: these results describe the `swift-cidr-mcp` builds identified below. The project is being renamed to `routeobjects-mcp`; this record is not new-name qualification. See [naming migration](Naming-Migration.md) for current evidence.

Recorded 2026-11-02 for the uncommitted CIPS guide addition. This report supplements
the existing pilot evidence; candidate-3 archives were not rebuilt or relabeled.
No SDK source, dependency lock, calculation contract, staging or commit changed.

## Scope and build identity

- Native macOS 26.7.1 (25G241), ARM64; Apple Swift 6.3.3, Xcode 26.6.0.
- Release executable SHA-256:
  `46995b0e6594589b272dccde8fda6528b7b281885e0cc0acfd1370df4de52d2e`.
- Unchanged maintenance SDK source SHA-256:
  `f54aafb2b2a2f2babcaf414a03fa31bdc0c430f825867e967c24cc9711ff306b`.
- Compiled guide: 6,009 UTF-8 bytes, SHA-256
  `26cdf7cce0debb455f76f2f6f73fc8ab746a127a5c03f891ac7debfecf01c336`.
- Source: published `draft-munro-cips-00`, 3 October 2026. The guide identifies
  authorship, revision and work-in-progress status and makes no full CIPS claim.

The guide is a fixed `text/markdown` MCP resource at
`routeobjects://swift-cidr-mcp/guides/cips-v1`. Essential meaning is also present
in tool descriptions and the NetClaw skill. Nothing is appended to tool results.

## Checks

| Surface | Evidence |
| --- | --- |
| Swift Testing | 30 tests pass in both Debug and Release: the existing 28 plus SDK-encoded guide batch size and NetClaw description length checks. |
| Independent process harness | 22 tests pass in both configurations, using `jsonschema 4.25.1`. All four negotiated revisions retain the existing four-tool schema/result checks. |
| Resource behavior | Discovery, exact URI/MIME/UTF-8 size, stable complete reads, empty templates, malformed parameters/cursors, unknown URIs and unsupported methods pass. Normal calls still work afterward. |
| Standalone executable | Copying only the executable to a temporary directory and starting it there successfully reads the guide; no adjacent resource bundle or source file is needed. |
| Batch and frame bounds | Eight guide reads succeed in November 2024/March 2025 batches. Later revisions reject batches. A valid inbound batch with long correlation IDs exceeds the outbound bound and returns eight correlated limit errors without truncated Markdown; the connection remains usable. |
| Inspector CLI | Pinned Inspector 2.13.0 / Node 22.23.4: all 20 existing legacy/auto tool cases pass, modern-only incompatibility remains expected, and six new legacy/auto resource list/read/template checks pass. |
| Contract parity | All four parsed tool definitions compare equal to candidate 3 after removing descriptions. Eighteen complete success/error tool responses compare equal, including both content representations. Schemas and calculation/validation code are unchanged. |
| NetClaw unchanged helper | Seven checks pass: discovery, contextual address, IPv6 full count, contains, relation, range and domain failure. Parsed results match Inspector. |
| NetClaw source integration | Nine catalog tests, ten swift-cidr fixtures, metadata, generated catalog parity, catalog/docs reconciliation and coverage checks pass. Skill hash and generated fingerprint are refreshed; profile membership and HUD environment map are unchanged. |
| Formatting and dependencies | Changed Swift files pass strict `swift format` lint. Both original lockfile hashes remain equal; the build wrapper verifies the unchanged SDK source digest. |

The malformed-parameter regression initially exposed SDK 0.12.1 mapping a
resource parameter decoding failure to `-32603`. A private adapter method wrapper
now validates the new resource parameters inside the handler and returns
`-32602`. Resource result types still come from the SDK. This does not modify
shared SDK behavior or any existing tool input/result contract.

## Reproduce

From the package root, with the existing qualified local SDK selection and
test dependencies:

```sh
python3 Scripts/build-pilot.py test
python3 Scripts/build-pilot.py test --configuration release
.venv/bin/python Tests/Compatibility/test_stdio.py --binary .build/debug/swift-cidr-mcp
.venv/bin/python Tests/Compatibility/test_stdio.py --binary .build/release/swift-cidr-mcp
python3 Tests/Inspector/qualify_cli.py --binary .build/release/swift-cidr-mcp --output .verification/cips-guide/inspector
python3 Tests/Inspector/qualify_resources.py --output .verification/cips-guide/inspector
```

Raw logs, parsed Inspector outputs, contract parity and NetClaw checks are under
`.verification/cips-guide/`. The focused incremental unified diff is
`.verification/cips-guide/review/cips-guide.patch`, with its exact path allowlist.
It excludes prior pilot work, local logs, caches and private architecture material.

## Manual view and limits

For an already connected Inspector, disconnect and reconnect its server so it
starts the newly built executable. Select **Resources**, then the CIPS guide and
read it. The existing loopback demo remains available; its earlier connection
may still be running the old executable until reconnected.

Web re-verification was blocked by the browser-control connection reporting
`browser.user is unavailable`. No new Web or TUI result is claimed; CLI resource
reads succeeded. No model-driven improvement is inferred from documentation or
resource availability. Hosts still decide what enters model context.

These new checks are native macOS ARM64 source-build evidence. They do not
extend the older Linux, Intel, clean-runtime or archive evidence to this changed
binary. Release archives need rebuilding and their normal qualification before
distribution. No July 2026 protocol, resource subscription, HTTP, MCPB or new
tool support is introduced.

## Review and rollback

Nothing is staged or committed. Review the incremental patch, then use
`git apply --reverse --check` from the broad workspace root before a selective
rollback. Reverse only this patch after confirming no later edits overlap; do
not reset either repository or remove the earlier untracked pilot. Rebuild and
reconnect the local executable after reverting. The original files are retained
under `.verification/cips-guide/before/` for review.
