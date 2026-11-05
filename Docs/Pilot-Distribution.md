# Experimental pilot distribution

This guide records the publication plan for the initial four-tool RouteObjects
MCP pilot: **experimental GitHub prerelease tag `0.1.0`**, targeting application
commit `8595fae93803083b6146d04356b1bd02f0d8bfe0`. The selected archives have
native qualification evidence. Each retains its original `0.1.0-pilot` name,
embedded executable version `0.1.0`, and packaging-time `releaseReady: false`
metadata. That immutable field does not track live publication or approval state.

The [release page](https://github.com/RouteObjects/routeobjects-mcp/releases/tag/0.1.0)
and asset links below are planned locations, not claims of present availability.
Check the [repository releases](https://github.com/RouteObjects/routeobjects-mcp/releases)
for publication status. Neither this guide nor the installer downloads anything
automatically.

All four are built from application commit
[`8595fae93803083b6146d04356b1bd02f0d8bfe0`](https://github.com/RouteObjects/routeobjects-mcp/commit/8595fae93803083b6146d04356b1bd02f0d8bfe0)
and published SDK maintenance revision
[`10cb175661ab095abfc73cf293a0c79af244e61e`](https://github.com/RouteObjects/swift-sdk/commit/10cb175661ab095abfc73cf293a0c79af244e61e),
based on MCP Swift SDK 0.12.1. Their bundled documentation is the original
65-file source snapshot. This guide and the later qualification documents
postdate that snapshot and are maintained separately from the archives. The
planned tag and its source archive remain at `8595fae`; a later documentation
commit on `main` and standalone release attachments do not change those inputs. See [artifact qualification](Published-Source-Qualification.md)
for the complete provenance and runtime boundaries.

## Selected artifacts and supported scope

| Target | Archive filename | Native runtime evidence | Build toolchain |
| --- | --- | --- | --- |
| macOS ARM64 | [routeobjects-mcp-0.1.0-pilot-macos-arm64.tar.gz](https://github.com/RouteObjects/routeobjects-mcp/releases/download/0.1.0/routeobjects-mcp-0.1.0-pilot-macos-arm64.tar.gz) | macOS 15.8.2; separate NetClaw checks on 26.7.1 | Apple Swift 6.2.3 / Xcode 26.2 |
| macOS x86-64 | [routeobjects-mcp-0.1.0-pilot-macos-x86_64.tar.gz](https://github.com/RouteObjects/routeobjects-mcp/releases/download/0.1.0/routeobjects-mcp-0.1.0-pilot-macos-x86_64.tar.gz) | macOS 15.7.9; NetClaw checks use Rosetta on 26.7.1 | Apple Swift 6.2.3 / Xcode 26.2 |
| Linux ARM64 | [routeobjects-mcp-0.1.0-pilot-linux-arm64.tar.gz](https://github.com/RouteObjects/routeobjects-mcp/releases/download/0.1.0/routeobjects-mcp-0.1.0-pilot-linux-arm64.tar.gz) | Ubuntu 24.04 / glibc 2.39 | Swift 6.3.3 |
| Linux x86-64 | [routeobjects-mcp-0.1.0-pilot-linux-x86_64.tar.gz](https://github.com/RouteObjects/routeobjects-mcp/releases/download/0.1.0/routeobjects-mcp-0.1.0-pilot-linux-x86_64.tar.gz) | Ubuntu 24.04.5 | Swift 6.3.3 |

**macOS 15 remains the minimum.** The recorded point releases establish the
tested scope; exact macOS 15.0, macOS 15 NetClaw execution and native Intel
NetClaw execution are not claimed. CI had Xcode installed, so a no-Xcode
deployment is not established. The new macOS CI archives replace the older
macOS candidates in this selection; the older bytes and their historical
results are preserved separately.

Linux archives bundle the Swift runtime, but still require the documented
glibc/system runtime and `libcurl.so.4` (`libcurl4t64` on Ubuntu 24.04).
Operators provision these prerequisites. Neither this executable nor the
NetClaw component installs Swift or system packages. Linux ARM64 packaging
occurred on macOS with execution marked `not-run`; the same executable was
independently built and tested natively on Linux, including after extraction.

This pilot does not claim WSL2, native Windows, musl, protected Hermes, HTTP
hosting, OAuth or MCPB support. It uses local stdio and the four protocol
revisions through `2025-11-25`; MCP July 2026 conformance is not claimed.

## Verify and extract an explicitly supplied archive

Obtain the chosen archive through an explicitly reviewed handoff or, once
published, its planned release location above. These are the expected SHA-256
values for the selected immutable files:

```text
0bc482660ace98204c1ebf350544d47fed052813474767d3a3c56bfb7b359b43  routeobjects-mcp-0.1.0-pilot-macos-arm64.tar.gz
53760c4938264f91b263ff462bceb6237c507fe4563001e76a54144257fcf42e  routeobjects-mcp-0.1.0-pilot-macos-x86_64.tar.gz
c79ea9c886bace2aa5f5ad822345242d0491362539c70a8e2a123d08212ac6a7  routeobjects-mcp-0.1.0-pilot-linux-arm64.tar.gz
ba06dcdfa53424dda6def2ea527a8b89aafdd06f2fd66a94d309b09d38567764  routeobjects-mcp-0.1.0-pilot-linux-x86_64.tar.gz
```

The archive checksum verifies the compressed file. NetClaw instead pins the
**extracted executable** checksum:

| Target | Executable SHA-256 |
| --- | --- |
| macOS ARM64 | `9dae199cebd499084b7f7ca69163dc01154f99d21a1f2380a64c05fdbd867833` |
| macOS x86-64 | `fe1e8613a10f6ce75650717cc6ff90f74cc39dc72455dc06eebbed5900dd7299` |
| Linux ARM64 | `fd538a78380087939925b698123575b1b00c1ae0e5944795d830a492b659876c` |
| Linux x86-64 | `58410bf6366157f8141e9837328a071bf536115a1099718ddb3b898db7b18f6b` |

For example, with the macOS ARM64 archive in the current directory, this block
checks the archive before extraction, creates a new directory without
overwriting an existing installation, then checks the executable before running
its version command:

```sh
(
  set -eu
  ro_archive="routeobjects-mcp-0.1.0-pilot-macos-arm64.tar.gz"
  printf '%s  %s\n' \
    '0bc482660ace98204c1ebf350544d47fed052813474767d3a3c56bfb7b359b43' \
    "$ro_archive" | shasum -a 256 -c -
  ro_extract_dir="$PWD/routeobjects-mcp-pilot-macos-arm64"
  mkdir -m 700 "$ro_extract_dir"
  tar -xzf "$ro_archive" -C "$ro_extract_dir"
  ro_binary="$ro_extract_dir/routeobjects-mcp-0.1.0-pilot-macos-arm64/bin/routeobjects-mcp"
  printf '%s  %s\n' \
    '9dae199cebd499084b7f7ca69163dc01154f99d21a1f2380a64c05fdbd867833' \
    "$ro_binary" | shasum -a 256 -c -
  "$ro_binary" --version
  printf 'MCP executable: %s\n' "$ro_binary"
)
```

Expected version: `routeobjects-mcp 0.1.0`. For another target, substitute its
filename, extraction-directory suffix and both hashes above. On Linux use
`sha256sum -c -` in place of `shasum -a 256 -c -`. Retain the extracted licenses,
build information and receipt with the executable. Receipts are integrity
records, not signatures; changing the binary invalidates its recorded identity.

## Configure a local MCP client

Use the absolute verified executable path in the client's stdio configuration:

```json
{
  "mcpServers": {
    "routeobjects-mcp": {
      "command": "/absolute/retained/directory/bin/routeobjects-mcp",
      "args": ["--stdio"]
    }
  }
}
```

The client starts and owns the process. No arguments also selects stdio;
`--help` and `--version` are human-facing commands. Stdout is reserved for MCP
JSON-RPC and bounded diagnostics go to stderr. No HTTP listener, model API,
credentials, DNS resolution or device connection is required by these four
offline tools. Client configuration formats may differ; this is the common
`mcpServers` form, not qualification of every local or cloud agent.

## Import into the experimental NetClaw component

This requires the reviewed NetClaw integration fork; it is not an already
accepted upstream component. Select `routeobjects` explicitly in selected
setup and provide all three settings:

| Setting | Value |
| --- | --- |
| `ROUTEOBJECTS_MCP_SOURCE` | Absolute path to the verified extracted executable, at most 64 MiB |
| `ROUTEOBJECTS_MCP_SHA256` | Its exact lowercase executable SHA-256 from the table above |
| `ROUTEOBJECTS_MCP_VERSION` | `0.1.0` |

Setup verifies the checksum before execution, imports the bytes to the selected
home's `.setup/prefix/bin/routeobjects-mcp` with owner-only permissions, and
checks `--version`. It generates `ROUTEOBJECTS_MCP_BIN` for that owned path.
It refuses unrelated or changed destination files. Updating the pin is an
explicit installation change; there is no automatic download or upgrade.

For a development smoke check from the experimental NetClaw checkout, point
the override at the verified executable:

```sh
export ROUTEOBJECTS_MCP_BIN="/absolute/retained/directory/bin/routeobjects-mcp"
python3 scripts/mcp-call.py --component routeobjects --list-tools
python3 scripts/mcp-call.py --component routeobjects cidr_inspect \
  '{"kind":"address_with_prefix","value":"192.0.2.129/24"}'
```

Expect four tools and an inspection that retains `192.0.2.129/24` as address
context, reporting the containing network separately. The helper is a smoke
check; successful calls discard stderr, so it does not replace independent
transport qualification. See [NetClaw integration](NetClaw.md) and
[current evidence](Published-Source-Qualification.md) for runtime limitations.
The tested OpenClaw runtime does not forward caller `AbortSignal`; its timeout
fixture demonstrates notification/recovery after withholding a completed
response, not cancellation of active server work.

## Experimental distribution policy

The publication plan uses an explicitly labeled experimental prerelease at tag
`0.1.0`, targeting `8595fae`, with these exact qualified bytes. The source and SDK commits are signed. The new
macOS ARM64 binary has an ad-hoc linker signature; the Intel binary is unsigned.
Neither carries Developer ID signing or notarization, and downloaded/quarantined
installation is not qualified. Acceptance for controlled experimental use is a
distribution decision; this guide does not alter macOS security controls.

Developer ID signing/notarization can be a separate later distribution step.
It is not a prerequisite added to the implemented pilot. No archive is renamed,
repacked, signed or changed by this plan. Planned locations and qualification
records do not themselves grant approval for tag creation, upload, registry
listing or a message to the NetClaw maintainer; those are separate actions.
