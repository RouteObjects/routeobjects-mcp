# MCP Inspector qualification

> Historical verification record: these results describe the `swift-cidr-mcp` builds identified below. The project is being renamed to `routeobjects-mcp`; this record is not new-name qualification. See [naming migration](Naming-Migration.md) for current evidence.

## Current candidate 3

The adapter schema relocation was requalified on 2026-11-02 against Release SHA-256
`a4f93ae67087b468a6661e3b2a22c3240d15685c52a651dcabf53e9e0b02d35e`.
All four complete tool definitions and input/output schemas equal candidate 2 as
parsed JSON. Inspector 2.13.0 / Node 22.23.4 passed all 20 legacy/auto CLI cases;
modern-only was the expected incompatibility. Actual CLI negotiation traces
show `2025-11-25` in both supported modes, including auto discovery rejection
and fallback, with per-run timings in candidate-3 evidence.

In the in-app browser, all four forms and valid calls, visible domain error,
sanitized stderr Console, automatic fallback and modern-only rejection passed.
Auto Web and legacy TUI each preserved the exact `2^128` string with equal text
and structured content. TUI discovery listed four tools. Current UI evidence is
in `.verification/inspector-candidate-3/`; CLI and sanitized negotiation reports
are under `artifacts/candidate-3/evidence/`. The test tab and owned processes were
closed. Earlier TUI four-form/error checks below remain explicitly older evidence.

## Candidate 2 and earlier qualification history

Local development evidence, 2026-11-01–02 (America/New_York). This is native macOS
arm64 evidence for `swift-cidr-mcp 0.1.0`, not a public release, Linux/Windows
qualification, or deployment of a NetClaw agent.

## Pinned client and isolated session

- Inspector: `@modelcontextprotocol/inspector` **2.13.0**.
- Node: **22.23.4**, native Darwin arm64.
- Server: Debug and final Release executables built with the explicitly selected local Swift SDK
  checkout based on **0.12.1**. Its local SDK changes are lifecycle/resource
  controls in `Server.swift`; stock `StdioTransport` is unchanged. The bounded,
  serialized stdio transport belongs to this package's `CIDRMCPAdapter`.
  The SDK changes are not yet a published dependency.
- CLI/Web/TUI used a read-only `--config` with `legacy`, `auto`, and `modern`
  entries. No user catalog, provider account, model call, device, or remote MCP
  server was used.
- Inspector state and logs were redirected below ignored `.verification/`.
  Secret storage was `memory`, token persistence `none`, automatic browser launch
  disabled. Web bound to `127.0.0.1` with authentication enabled; its token was
  retained in a mode-0600 log and never printed or placed in the browser URL.
  The browser loaded the clean loopback URL, whose page supplies its API token.

The server remains a stdio subprocess. The Inspector's localhost HTTP service is
the testing UI, not an HTTP transport added to `swift-cidr-mcp`.

## Observed results

| Client | Check | Result |
| --- | --- | --- |
| CLI, legacy and auto | `tools/list --strict` | PASS: four expected tools; discovery validation succeeds. |
| CLI, legacy and auto | Inspect `192.0.2.129/24` as `address_with_prefix` | PASS: address `.129` retained; network `192.0.2.0/24`; text and structured content agree. |
| CLI, legacy and auto | Inspect network `::/0` | PASS: exact decimal string `340282366920938463463374607431768211456`. |
| CLI, legacy and auto | Inspect `not-an-address` as address | PASS: `isError: true`, `invalid_address`, Inspector exit **5**. |
| CLI, legacy and auto | `cidr_contains`, `cidr_relation`, `cidr_summarize_range`, valid and invalid inputs | PASS: whole-network containment, proper containment relation, four-prefix `.1`–`.6` cover; family mismatch/reversed range return exact codes and exit **5**. |
| CLI, modern only | Discovery | EXPECTED INCOMPATIBILITY: exit **1**, pinned `2026-07-28` not offered through `server/discover`. |
| TUI, legacy | All four tools' forms and calls | PASS after the schema presentation correction below. |
| TUI, legacy | Address kind supplied slash notation | PASS: tool error displayed; context call succeeds when the explicit contextual kind is selected. |
| TUI, auto | Connection and discovery | PASS: four tools. Tool execution in this mode is covered by CLI; it was not repeated in TUI. |
| TUI, modern only | Connection | EXPECTED INCOMPATIBILITY: connection enters error state. |
| Web, legacy, Safari | All four tools' forms and calls | PASS: context inspect; address membership; `/24` versus `/25` relation; inclusive `.0` through `.255` range. |
| Web, legacy, Safari | `not-an-address` | PASS: visible **Tool Error**, structured `invalid_address`, `result: null`. |
| Web, auto | Connection and discovery | PASS: failed modern discovery falls back to `2025-11-25`, four tools available. |
| Web, modern only | Connection | EXPECTED INCOMPATIBILITY: explicit pinned-version negotiation error, no fallback. |

Web visibly displayed matching text and structured results for the context call:
`address: 192.0.2.129`, `canonical: 192.0.2.129/24`, network `192.0.2.0/24`, count
`"256"`. The optional `networkMode` was left unset. The four Web calls used the
schema-updated Debug binary, SHA-256
`b019f7afbaf56c0bb1670a5d07222d8a12555d530be57b88629e1d273666517b`.
The repeated CLI matrix and TUI inspect/range calls used the same binary.
Initial TUI relation/contains calls used Debug SHA-256
`f0b750b029ac89703702752736025a3760be11e9fd65aa8f46918084fca62ec6`;
only inspect's schema presentation changed between those builds.

After the final SDK lifecycle/resource fixes, the complete CLI matrix passed
again against the Release binary, SHA-256
`d1a8882e075cc5597ba040efad5e6f7afb094af2bff79b4246dcd935525aacff`.
Legacy and auto passed all eight cases; modern-only remained the expected
incompatibility. A final TUI legacy connection and contextual inspect call also
passed against those exact Release bytes: the form omitted `networkMode`, the
request retained `192.0.2.129/24`, and the visible result retained address `.129`,
network `192.0.2.0/24` and count `"256"`. The final TUI process was stopped.
Evidence is retained in `.verification/inspector-final-release/`.

The final CLI supplement adds valid and invalid fixtures for the other three
tools, closing the every-tool requirement rather than inferring it from inspect.
All **20 legacy/auto cases** pass against the same Release SHA; modern-only is the
21st, expected-incompatibility case. Results are retained separately under
`.verification/inspector-final-all-tools/`; earlier eight-case counts remain
historical evidence for their original runs.

A narrow transparent-stdio relay also records the actual CLI negotiation without
changing production code. Both legacy and automatic mode received
`protocolVersion: "2025-11-25"`. Automatic mode sent `server/discover`, received
error `-32600`, then initialized successfully and listed four tools. Observed
launch-to-initialization times were 239.993 ms (legacy) and 249.281 ms (auto);
complete CLI runs took 347.516 ms and 337.823 ms respectively. Auto's probe lasted
43.528 ms and its error-to-fallback interval was 7.238 ms. These single-run timings
include relay overhead and are not performance benchmarks. Reproduce with
`Tests/Inspector/qualify_negotiation.py`; sanitized wire events, exact commands,
fixture hashes and timings are under
`artifacts/candidate-2/evidence/inspector-negotiation/`.

The final Web Console supplement visibly displayed JSON-line `server_started`
and `tool_completed` stderr records during a successful relation call. Those log
records contain bounded event/tool/timing metadata and no raw prefix inputs or
result body. The returned prefixes remain visible only in the tool result pane.
`web-stderr-console.txt` records the observed DOM in the same supplement directory;
the direct subprocess harness remains the independent proof of stream separation.

The final Release Web matrix was then repeated in the in-app browser on
2026-11-02. All four legacy forms/calls and the visible `invalid_address` Tool
Error passed against the same Release SHA above. Automatic mode first reported
the expected `server/discover` error, then connected using `2025-11-25` and
discovered four tools. Its network `::/0` call displayed the exact string
`340282366920938463463374607431768211456` in both text and structured results.
Modern-only mode visibly failed with the pinned `2026-07-28` negotiation error
and no fallback. This final run used the in-app browser; the Safari rows retain
their earlier Debug provenance.

A separate final Release TUI `::/0` call also displayed the exact cardinality in
both representations. The TUI's saved JSON result independently compares equal
after parsing its text content, with `isError: false`. The screenshot, sanitized
modern-only snapshot, TUI transcript/result, and `interactive-summary.json` are
retained in `.verification/inspector-final-release/`. The test tab was closed and
both owned Inspector processes were stopped. No authentication token is part of
the shared evidence.

Inspector's protocol pane labels a successful JSON-RPC `tools/call` response
`OK` even when the result's `isError` is true. Its tool result panel correctly
renders that case as **Tool Error**. A transport response alone is not a success
assertion for the domain operation.

## Schema presentation correction

The initial inspect schema had its fields only inside root `oneOf` alternatives.
Inspector 2.13.0's TUI rendered an empty form, sent `{}`, and received the expected
invalid-params response. The server now declares shared field metadata at the
root while retaining the restrictive alternatives. Both TUI and Web now expose
`kind`, `value`, and optional `networkMode`; the contextual call works without
injecting an inappropriate network-mode default.

The TUI represents nested `cidr_contains.target` as a JSON text field. Enter
`{"kind":"address","value":"192.0.2.1"}` there. Inspector converts a field whose
schema type is `object` from JSON text to an object before RPC; the raw form view
can still show the entered string. The Web client renders nested kind/value
controls. Neither behavior requires weakening the server's typed object input.

## Reproduce

Use an already built server and the pinned Node/Inspector installations; these
scripts do not download dependencies or start a model:

```sh
python3 Tests/Inspector/qualify_cli.py
python3 Tests/Inspector/launch_tui.py
python3 Tests/Inspector/launch_web.py
```

`qualify_cli.py --help` accepts explicit binary, Node, Inspector package and output
paths. Its default output is `.verification/inspector-session`; the schema-update
repeat used `.verification/inspector-session-schema-update`. Each CLI case saves
JSON/stdout and stderr plus a sanitized summary recording the binary checksum.
The interactive launchers use the default session's generated config; pass
`--session-dir` to select another CLI output directory, such as a final artifact
qualification. That config determines the exact server executable launched.

In the TUI, `c` connects, `t` selects Tools, Tab moves focus, arrows select, Enter
opens or edits a field and submits. Leave `networkMode` unset for address kinds.
For a recorded macOS terminal session, use:

```sh
script -q .verification/inspector-session/tui.txt python3 Tests/Inspector/launch_tui.py
```

Open only the clean URL printed by the Web launcher. Do not copy its private log
to shared evidence. Close the test browser tab and terminate the launcher after
testing; it terminates its owned Inspector process group. The qualification run
closed its test tab, disconnected all server sessions, and stopped the owned Web
and TUI processes.

These checks cover this tool contract and client interaction. They do not assert
support for the modern-only MCP protocol, remote HTTP transport, OAuth, all MCP
capabilities, or every Inspector feature. See the official
[Inspector documentation](https://modelcontextprotocol.io/docs/2026-07-28/tools/inspector),
[CLI configuration](https://modelcontextprotocol.io/docs/2026-07-28/tools/inspector/configuration),
[TUI guide](https://modelcontextprotocol.io/docs/2026-07-28/tools/inspector/tui), and
[Web guide](https://modelcontextprotocol.io/docs/2026-07-28/tools/inspector/web).
