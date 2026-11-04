#!/usr/bin/env python3
"""Independent, deadline-bounded qualification of the real stdio executable.

Run with a built maintenance-SDK executable; this harness does not build or install it.
"""

# Copyright (c) 2026 Craig A. Munro
# SPDX-License-Identifier: Apache-2.0

import argparse
import copy
import json
import os
from pathlib import Path
import queue
import select
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
import unittest

from jsonschema import Draft202012Validator, ValidationError


PROTOCOLS = ("2024-11-05", "2025-03-26", "2025-06-18", "2025-11-25")
TOOL_NAMES = {"cidr_inspect", "cidr_contains", "cidr_relation", "cidr_summarize_range"}
GUIDE_URI = "routeobjects://routeobjects-mcp/guides/cips-v1"
BINARY = Path(".build/debug/routeobjects-mcp").resolve()
DEADLINE = 6.0


def encoded(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8") + b"\n"


def request(identifier, method, params=None):
    value = {"jsonrpc": "2.0", "id": identifier, "method": method}
    if params is not None:
        value["params"] = params
    return value


def tool_request(identifier, name="cidr_inspect", arguments=None):
    if arguments is None:
        arguments = {"kind": "address", "value": "192.0.2.1"}
    return request(identifier, "tools/call", {"name": name, "arguments": arguments})


class MCPProcess:
    """Owns one subprocess and drains each output stream independently."""

    def __init__(self, read_stderr=True, stderr_fd=None, stdout_fd=None, binary=None, cwd=None):
        if stderr_fd is not None and read_stderr:
            raise ValueError("An external stderr descriptor must have its own capture owner")
        self.process = subprocess.Popen(
            [str(binary or BINARY), "--stdio"], stdin=subprocess.PIPE,
            stdout=subprocess.PIPE if stdout_fd is None else stdout_fd,
            stderr=subprocess.PIPE if stderr_fd is None else stderr_fd, bufsize=0, cwd=cwd,
        )
        self.messages = queue.Queue()
        self.logs = queue.Queue()
        self.frames = []
        self.stderr = bytearray()
        self.read_errors = []
        self.pending = {}
        self.next_id = 100
        self.tools = {}
        self.threads = [] if stdout_fd is not None else [threading.Thread(target=self._stdout, daemon=True)]
        if read_stderr:
            self.threads.append(threading.Thread(target=self._stderr, daemon=True))
        for thread in self.threads:
            thread.start()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        if self.process.poll() is None:
            self.process.kill()
        self.process.wait(timeout=DEADLINE)
        for thread in self.threads:
            thread.join(timeout=1)
        for stream in (self.process.stdin, self.process.stdout, self.process.stderr):
            if stream is not None and not stream.closed:
                stream.close()

    def _stdout(self):
        pending = bytearray()
        try:
            while data := os.read(self.process.stdout.fileno(), 4096):
                pending.extend(data)
                while b"\n" in pending:
                    frame, _, pending = pending.partition(b"\n")
                    if not frame:
                        raise AssertionError("Empty stdout frame is not a JSON-RPC message")
                    if len(frame) + 1 > 65536:
                        raise AssertionError("Output frame exceeded 64 KiB")
                    value = json.loads(frame)
                    self.frames.append(bytes(frame))
                    self.messages.put(value)
                if len(pending) > 65536:
                    raise AssertionError("Unterminated stdout exceeded the output bound")
            if pending:
                raise AssertionError("Stdout ended inside a JSON frame")
        except Exception as failure:
            self.read_errors.append(failure)
            self.messages.put(failure)
        finally:
            self.messages.put(EOFError("Server stdout closed"))

    def _stderr(self):
        pending = bytearray()
        try:
            while data := os.read(self.process.stderr.fileno(), 4096):
                if len(self.stderr) + len(data) > 1024 * 1024:
                    raise AssertionError("Test diagnostic capture exceeded 1 MiB")
                self.stderr.extend(data)
                pending.extend(data)
                while b"\n" in pending:
                    line, _, pending = pending.partition(b"\n")
                    self.logs.put(json.loads(line))
            if pending:
                raise AssertionError("Stderr ended inside a JSON log record")
        except Exception as failure:
            self.read_errors.append(failure)
            self.logs.put(failure)
        finally:
            self.logs.put(EOFError("Server stderr closed"))

    def wait_for_log(self, event):
        deadline = time.monotonic() + DEADLINE
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise AssertionError(f"Timed out waiting for {event}")
            try:
                value = self.logs.get(timeout=remaining)
            except queue.Empty as failure:
                raise AssertionError(f"Timed out waiting for {event}") from failure
            if isinstance(value, Exception):
                raise value
            if value.get("event") == event:
                return value

    def wait_for_exit(self, expected=0):
        status = self.process.wait(timeout=DEADLINE)
        for thread in self.threads:
            thread.join(timeout=1)
        if status != expected:
            raise AssertionError(f"Unexpected process exit {status}: {self.stderr.decode(errors='replace')}")
        if self.read_errors:
            raise AssertionError(f"Stream capture failures: {self.read_errors}")

    def raw(self, data):
        view = memoryview(data)
        while view:
            written = os.write(self.process.stdin.fileno(), view)
            view = view[written:]

    def send(self, value):
        self.raw(encoded(value))

    def receive(self, timeout=DEADLINE):
        try:
            value = self.messages.get(timeout=timeout)
        except queue.Empty as failure:
            raise AssertionError("Timed out waiting for a complete JSON-RPC frame") from failure
        if isinstance(value, Exception):
            raise value
        return value

    def response(self, identifier):
        if identifier in self.pending:
            return self.pending.pop(identifier)
        deadline = time.monotonic() + DEADLINE
        while time.monotonic() < deadline:
            value = self.receive(timeout=max(0.01, deadline - time.monotonic()))
            if not isinstance(value, dict):
                raise AssertionError("Unexpected batch response to an individual request")
            if "id" not in value:
                continue
            if value["id"] == identifier:
                return value
            if value["id"] in self.pending:
                raise AssertionError("Duplicate response ID")
            self.pending[value["id"]] = value
        raise AssertionError("Response deadline expired")

    def rpc(self, method, params=None):
        identifier = self.next_id
        self.next_id += 1
        self.send(request(identifier, method, params))
        return self.response(identifier)

    def initialize(self, protocol="2025-11-25", fragment=False):
        message = request(1, "initialize", {
            "protocolVersion": protocol, "capabilities": {},
            "clientInfo": {"name": "contract-π", "version": "1.0"},
        })
        if fragment:
            data = encoded(message)
            split = data.index("π".encode("utf-8")) + 1
            self.raw(data[:split])
            time.sleep(0.02)
            self.raw(data[split:])
        else:
            self.send(message)
        response = self.response(1)
        if response.get("result", {}).get("protocolVersion") != protocol:
            raise AssertionError(f"Unexpected negotiated protocol: {response}")
        self.send({"jsonrpc": "2.0", "method": "notifications/initialized"})
        return response

    def discover(self):
        response = self.rpc("tools/list")
        self.tools = {tool["name"]: tool for tool in response["result"]["tools"]}
        if set(self.tools) != TOOL_NAMES:
            raise AssertionError("Discovery did not return exactly the four contract tools")
        for tool in self.tools.values():
            Draft202012Validator.check_schema(tool["inputSchema"])
            Draft202012Validator.check_schema(tool["outputSchema"])
        return self.tools

    def call(self, name, arguments):
        return self.rpc("tools/call", {"name": name, "arguments": arguments})

    def domain(self, name, arguments, error=None):
        definition = self.tools[name]
        Draft202012Validator(definition["inputSchema"]).validate(arguments)
        wire = self.call(name, arguments)
        if "error" in wire:
            raise AssertionError(f"Unexpected protocol error: {wire}")
        result = wire["result"]
        if len(result["content"]) != 1 or result["content"][0]["type"] != "text":
            raise AssertionError("Expected one complete text representation")
        envelope = result["structuredContent"]
        if json.loads(result["content"][0]["text"]) != envelope:
            raise AssertionError("Text result differs from structured content")
        Draft202012Validator(definition["outputSchema"]).validate(envelope)
        if envelope["input"] != arguments:
            raise AssertionError("The tool did not preserve original arguments")
        if bool(result.get("isError", False)) != (error is not None):
            raise AssertionError("Tool isError does not match the domain outcome")
        if error is not None and envelope["error"]["code"] != error:
            raise AssertionError(f"Unexpected domain error: {envelope}")
        return envelope

    def eof(self, expected=0):
        self.process.stdin.close()
        self.wait_for_exit(expected)


class StdioContracts(unittest.TestCase):
    def test_all_protocols_schemas_and_four_tools(self):
        for protocol in PROTOCOLS:
            with self.subTest(protocol=protocol), MCPProcess() as client:
                initialization = client.initialize(protocol)
                self.assertEqual(initialization["result"]["serverInfo"]["name"], "routeobjects-mcp")
                self.assertEqual(set(initialization["result"]["capabilities"]), {"tools", "resources"})
                client.discover()
                inspect = client.domain("cidr_inspect", {"kind": "address_with_prefix", "value": "192.0.2.129/24"})
                self.assertEqual(inspect["result"]["canonical"], "192.0.2.129/24")
                self.assertEqual(inspect["result"]["network"]["cidr"], "192.0.2.0/24")
                contains = client.domain("cidr_contains", {"container": "192.0.2.0/25", "target": {"kind": "network", "value": "192.0.2.0/24"}})
                self.assertFalse(contains["result"]["contains"])
                relation = client.domain("cidr_relation", {"left": "192.0.2.0/25", "right": "192.0.2.128/26"})
                self.assertEqual(relation["result"]["relation"], "disjoint")
                self.assertTrue(relation["result"]["adjacent"])
                summary = client.domain("cidr_summarize_range", {"start": "192.0.2.1", "end": "192.0.2.6"})
                self.assertEqual(summary["result"]["prefixes"], ["192.0.2.1/32", "192.0.2.2/31", "192.0.2.4/31", "192.0.2.6/32"])
                client.eof()

    def test_relation_result_variants_match_output_schema(self):
        # CHANGE: Domain-only relation tests cannot establish the adapter's output-schema agreement.
        families = [
            ("ipv4", "192.0.2.0/24", "192.0.2.0/25", "198.51.100.0/24"),
            ("ipv6", "2001:db8::/48", "2001:db8::/64", "2001:db8:2::/48"),
        ]
        with MCPProcess() as client:
            client.initialize()
            client.discover()
            for family, parent, child, separate in families:
                variants = [
                    (parent, parent, "equal", True),
                    (parent, child, "left_contains_right", True),
                    (child, parent, "right_contains_left", True),
                    (parent, separate, "disjoint", False),
                ]
                for left, right, relation, overlaps in variants:
                    with self.subTest(family=family, relation=relation):
                        envelope = client.domain("cidr_relation", {"left": left, "right": right})
                        self.assertEqual(envelope["result"], {
                            "family": family, "left": left, "right": right,
                            "relation": relation, "overlaps": overlaps, "adjacent": False,
                        })
            client.eof()

    def test_bundled_cips_resource_across_protocols(self):
        # CHANGE: Resource guidance is additive and must not replace the four calculation contracts.
        for protocol in PROTOCOLS:
            with self.subTest(protocol=protocol), MCPProcess() as client:
                initialization = client.initialize(protocol)["result"]
                self.assertEqual(initialization["capabilities"]["resources"],
                                 {"subscribe": False, "listChanged": False})
                self.assertIn(GUIDE_URI, initialization["instructions"])
                listing = client.rpc("resources/list")["result"]
                self.assertNotIn("nextCursor", listing)
                self.assertEqual(len(listing["resources"]), 1)
                resource = listing["resources"][0]
                self.assertEqual(resource["uri"], GUIDE_URI)
                self.assertEqual(resource["mimeType"], "text/markdown")
                content = client.rpc("resources/read", {"uri": GUIDE_URI})["result"]["contents"]
                self.assertEqual(len(content), 1)
                self.assertEqual(content[0]["uri"], GUIDE_URI)
                self.assertEqual(content[0]["mimeType"], "text/markdown")
                text = content[0]["text"]
                self.assertEqual(resource["size"], len(text.encode("utf-8")))
                self.assertIn("draft-munro-cips-00", text)
                self.assertIn("192.0.2.129/24", text)
                self.assertEqual(client.rpc("resources/read", {"uri": GUIDE_URI})["result"]["contents"], content)
                self.assertEqual(client.rpc("resources/templates/list")["result"], {"resourceTemplates": []})
                for method in ("resources/list", "resources/templates/list"):
                    self.assertEqual(client.rpc(method, {"cursor": "unknown"})["error"]["code"], -32602)
                    self.assertEqual(client.rpc(method, {"cursor": 42})["error"]["code"], -32602)
                for uri in ("file:///private/no-read", "https://example.invalid/no-fetch",
                            GUIDE_URI + "?other=1", GUIDE_URI.replace("cips-v1", "cips-v2")):
                    error = client.rpc("resources/read", {"uri": uri})
                    self.assertEqual(error["error"]["code"], -32002)
                    self.assertNotIn(uri, json.dumps(error))
                for params in (None, {}, {"uri": 42}, [], "invalid"):
                    self.assertEqual(client.rpc("resources/read", params)["error"]["code"], -32602)
                self.assertEqual(client.rpc("resources/subscribe", {"uri": GUIDE_URI})["error"]["code"], -32601)
                self.assertEqual(client.rpc("prompts/list")["error"]["code"], -32601)
                client.discover()
                client.domain("cidr_inspect", {"kind": "address_with_prefix", "value": "192.0.2.129/24"})
                client.eof()

    def test_guide_is_embedded_in_standalone_binary(self):
        # CHANGE: The NetClaw installer copies only the executable; no source or SwiftPM resource bundle may be needed.
        with tempfile.TemporaryDirectory(prefix="swift-cidr-guide-") as directory:
            binary = Path(directory) / "routeobjects-mcp"
            shutil.copy2(BINARY, binary)
            with MCPProcess(binary=binary, cwd=directory) as client:
                client.initialize()
                contents = client.rpc("resources/read", {"uri": GUIDE_URI})["result"]["contents"]
                self.assertIn("draft-munro-cips-00", contents[0]["text"])
                self.assertEqual(sorted(p.name for p in Path(directory).iterdir()), ["routeobjects-mcp"])
                client.eof()

    def test_resource_batches_honor_size_and_revision(self):
        for protocol in PROTOCOLS:
            with self.subTest(protocol=protocol), MCPProcess() as client:
                client.initialize(protocol)
                client.send([request(i, "resources/read", {"uri": GUIDE_URI}) for i in range(10, 18)])
                message = client.receive()
                if protocol in ("2024-11-05", "2025-03-26"):
                    self.assertIsInstance(message, list)
                    self.assertEqual({item["id"] for item in message}, set(range(10, 18)))
                    texts = [item["result"]["contents"][0]["text"] for item in message]
                    self.assertEqual(len(set(texts)), 1)
                    self.assertIn("draft-munro-cips-00", texts[0])
                    self.assertLessEqual(len(encoded(message)), 65536)
                    # CHANGE: Valid large IDs can push a complete guide batch over its response bound.
                    # Require correlated errors, not truncated Markdown, and keep the connection usable.
                    identifiers = ["r" * 1900 + str(i) for i in range(8)]
                    oversized = copy.deepcopy(message)
                    for item, identifier in zip(oversized, identifiers):
                        item["id"] = identifier
                    self.assertGreater(len(encoded(oversized)), 65536)
                    batch = [request(i, "resources/read", {"uri": GUIDE_URI}) for i in identifiers]
                    self.assertLessEqual(len(encoded(batch)), 16384)
                    client.send(batch)
                    rejected = client.receive()
                    self.assertEqual({item["id"] for item in rejected}, set(identifiers))
                    self.assertTrue(all(item["error"]["code"] == -32000 and "result" not in item
                                        for item in rejected))
                else:
                    self.assertEqual(message["error"]["code"], -32600)
                self.assertIn("result", client.rpc("resources/read", {"uri": GUIDE_URI}))
                client.eof()

    def test_exact_ipv6_and_normalization(self):
        with MCPProcess() as client:
            client.initialize()
            client.discover()
            full = client.domain("cidr_inspect", {"kind": "network", "value": "::/0"})
            self.assertEqual(full["result"]["network"]["addressCount"], str(2**128))
            normalized = client.domain("cidr_inspect", {"kind": "network", "value": "192.0.2.129/24", "networkMode": "normalize"})
            self.assertEqual(normalized["diagnostics"][0]["code"], "host_bits_normalized")
            contextual = client.domain("cidr_inspect", {"kind": "address_with_prefix", "value": "2001:0DB8::1/64"})
            self.assertEqual(contextual["result"]["canonical"], "2001:db8::1/64")
            self.assertEqual(contextual["diagnostics"], [])
            reordered = client.domain("cidr_summarize_range", {"start": "::2", "end": "::1", "orderPolicy": "normalize"})
            self.assertEqual(reordered["result"]["addressCount"], "2")
            self.assertEqual(reordered["diagnostics"][0]["code"], "endpoints_reordered")
            worst = client.domain("cidr_summarize_range", {"start": "::1", "end": "ffff:ffff:ffff:ffff:ffff:ffff:ffff:fffe"})
            self.assertEqual(worst["result"]["prefixCount"], 254)
            self.assertEqual(worst["result"]["addressCount"], str(2**128 - 2))
            client.eof()

    def test_domain_errors_recover(self):
        fixtures = [
            ("cidr_inspect", {"kind": "address", "value": "192.000.2.1"}, "invalid_address"),
            ("cidr_inspect", {"kind": "address", "value": "fe80::1%eth0"}, "invalid_address"),
            ("cidr_inspect", {"kind": "network", "value": "::/129"}, "invalid_cidr"),
            ("cidr_inspect", {"kind": "network", "value": "192.0.2.1/24"}, "host_bits_set"),
            ("cidr_contains", {"container": "192.0.2.0/24", "target": {"kind": "address", "value": "::ffff:192.0.2.1"}}, "family_mismatch"),
            ("cidr_relation", {"left": "::/0", "right": "0.0.0.0/0"}, "family_mismatch"),
            ("cidr_summarize_range", {"start": "::2", "end": "::1"}, "reversed_range"),
        ]
        with MCPProcess() as client:
            client.initialize()
            client.discover()
            for tool, arguments, error in fixtures:
                with self.subTest(tool=tool, error=error):
                    envelope = client.domain(tool, arguments, error)
                    self.assertIsNone(envelope["result"])
                    self.assertEqual(envelope["diagnostics"], [])
            client.domain("cidr_inspect", {"kind": "address", "value": "::1"})
            client.eof()

    def test_argument_shapes_match_schemas(self):
        fixtures = [
            ("cidr_inspect", {"kind": "address", "value": True}),
            ("cidr_inspect", {"kind": "address", "value": 1}),
            ("cidr_inspect", {"kind": "address", "value": ""}),
            ("cidr_inspect", {"kind": "address", "value": "é"}),
            ("cidr_inspect", {"kind": "address", "value": "a" * 65}),
            ("cidr_inspect", {"kind": "address", "value": "::1", "networkMode": "normalize"}),
            ("cidr_inspect", {"kind": "address", "value": "::1", "extra": True}),
            ("cidr_contains", {"container": "::/0", "target": {"kind": "address_with_prefix", "value": "::1/128"}}),
            ("cidr_contains", {"container": "::/0", "target": {"kind": "address", "value": "::1", "extra": True}}),
            ("cidr_relation", {"left": "::/0"}),
            ("cidr_summarize_range", {"start": "::1", "end": "::2", "orderPolicy": "sort"}),
        ]
        with MCPProcess() as client:
            client.initialize()
            client.discover()
            for tool, arguments in fixtures:
                with self.subTest(tool=tool, arguments=arguments):
                    with self.assertRaises(ValidationError):
                        Draft202012Validator(client.tools[tool]["inputSchema"]).validate(arguments)
                    self.assertEqual(client.call(tool, arguments)["error"]["code"], -32602)
            self.assertEqual(client.call("unknown_tool", {})["error"]["code"], -32602)
            self.assertEqual(client.rpc("not_a_method")["error"]["code"], -32601)
            client.domain("cidr_inspect", {"kind": "address", "value": "::1"})
            client.eof()

    def test_malformed_outer_tool_parameters_recover(self):
        # CHANGE: Exercise SDK parameter decoding, before the tool's argument-schema validation runs.
        fixtures = [
            None,  # Missing params must still be an invalid-parameters response.
            {},
            {"name": 7, "arguments": {}},
            {"name": False, "arguments": {}},
            {"name": None, "arguments": {}},
            {"name": "cidr_inspect", "arguments": []},
            {"name": "cidr_inspect", "arguments": 7},
            {"name": "cidr_inspect", "arguments": "192.0.2.1"},
            [],
            "cidr_inspect",
            {"name": "unknown_tool", "arguments": {}},
        ]
        for protocol in PROTOCOLS:
            with self.subTest(protocol=protocol), MCPProcess() as client:
                client.initialize(protocol)
                client.discover()
                for parameters in fixtures:
                    with self.subTest(parameters=parameters):
                        response = client.rpc("tools/call", parameters)
                        self.assertEqual(response["error"]["code"], -32602)
                        self.assertNotIn("result", response)
                        client.domain("cidr_inspect", {"kind": "address", "value": "::1"})
                # A well-shaped call with a domain failure keeps the existing isError/result envelope.
                client.domain("cidr_inspect", {"kind": "network", "value": "192.0.2.1/24"}, "host_bits_set")
                client.eof()

    def test_output_schema_rejects_wrong_envelope_and_result_types(self):
        with MCPProcess() as client:
            client.initialize()
            client.discover()
            good = client.domain("cidr_inspect", {"kind": "network", "value": "::/0"})
            schema = Draft202012Validator(client.tools["cidr_inspect"]["outputSchema"])
            wrong_count = copy.deepcopy(good)
            wrong_count["result"]["network"]["addressCount"] = 2**128
            wrong_error = copy.deepcopy(good)
            wrong_error["error"] = {"code": "internal_error", "field": None, "message": "bad"}
            extra = copy.deepcopy(good)
            extra["result"]["network"]["extra"] = True
            wrong_prefix = copy.deepcopy(good)
            wrong_prefix["result"]["network"]["prefixLength"] = True
            for invalid in (wrong_count, wrong_error, extra, wrong_prefix):
                with self.assertRaises(ValidationError):
                    schema.validate(invalid)
            client.eof()

    def test_fragmented_utf8_and_multiple_frames(self):
        with MCPProcess() as client:
            client.initialize(fragment=True)
            client.raw(encoded(tool_request(10)) + encoded(tool_request(11, arguments={"kind": "address", "value": "::1"})))
            self.assertEqual(client.response(10)["result"]["structuredContent"]["result"]["family"], "ipv4")
            self.assertEqual(client.response(11)["result"]["structuredContent"]["result"]["family"], "ipv6")
            client.eof()

    def test_malformed_json_recovers(self):
        with MCPProcess() as client:
            client.initialize()
            client.raw(b"{not-json}\n")
            malformed = client.receive()
            self.assertEqual(malformed["error"]["code"], -32700)
            self.assertIsNone(malformed["id"])
            self.assertIn("result", client.call("cidr_inspect", {"kind": "address", "value": "::1"}))
            client.eof()

    def test_malformed_request_ids_are_errors_and_never_invoke_tools(self):
        with MCPProcess() as client:
            client.initialize()
            for identifier in (None, True, False, 1.5, [], {}):
                with self.subTest(identifier=identifier):
                    client.send(tool_request(identifier))
                    message = client.receive()
                    self.assertEqual(message["error"]["code"], -32600)
                    self.assertIsNone(message["id"])
                    self.assertNotIn("result", message)
            # CHANGE: Preserve legitimate integer/string IDs while rejecting malformed IDs before dispatch.
            for identifier in (0, -1, ""):
                client.send(request(identifier, "ping"))
                message = client.response(identifier)
                self.assertEqual(message["id"], identifier)
                self.assertIn("result", message)
            client.eof()
            records = [json.loads(line) for line in client.stderr.splitlines()]
            self.assertFalse(any(record["event"] == "tool_completed" for record in records))

    def test_malformed_batch_members_preserve_valid_members(self):
        for protocol in ("2024-11-05", "2025-03-26"):
            with self.subTest(protocol=protocol), MCPProcess() as client:
                client.initialize(protocol)
                batch = [request(identifier, "ping") for identifier in (None, True, 1.5, [], {})]
                batch.extend([request(77, "ping"), {"jsonrpc": "2.0", "method": "notifications/initialized"}])
                client.send(batch)
                message = client.receive()
                self.assertIsInstance(message, list)
                self.assertEqual(len(message), 6)
                valid = [item for item in message if item["id"] == 77]
                self.assertEqual(len(valid), 1)
                self.assertIn("result", valid[0])
                invalid = [item for item in message if item["id"] is None]
                self.assertEqual(len(invalid), 5)
                self.assertTrue(all(item["error"]["code"] == -32600 for item in invalid))
                self.assertIn("result", client.rpc("ping"))
                client.eof()

    def test_invalid_batch_shapes_preserve_tool_results(self):
        # CHANGE: Invalid IDs alone missed whole-batch failure on other malformed member shapes.
        invalid_members = [42, {"jsonrpc": "2.0", "id": 7}, [request(8, "ping")]]
        for protocol in ("2024-11-05", "2025-03-26"):
            with self.subTest(protocol=protocol), MCPProcess() as client:
                client.initialize(protocol)
                client.discover()
                arguments = {"container": "192.0.2.0/24", "target": {"kind": "address", "value": "198.51.100.1"}}
                expected = client.domain("cidr_contains", arguments)
                for invalid_member in invalid_members:
                    with self.subTest(invalid_member=invalid_member):
                        client.send([
                            tool_request(77, "cidr_contains", arguments),
                            invalid_member,
                            {"jsonrpc": "2.0", "method": "notifications/initialized"},
                        ])
                        response = client.receive()
                        self.assertIsInstance(response, list)
                        self.assertEqual(len(response), 2)  # The valid notification has no response.
                        valid = [item for item in response if item["id"] == 77]
                        invalid = [item for item in response if item["id"] is None]
                        self.assertEqual(len(valid), 1)
                        self.assertEqual(len(invalid), 1)
                        self.assertEqual(invalid[0]["error"]["code"], -32600)
                        result = valid[0]["result"]
                        self.assertFalse(result["isError"])
                        self.assertEqual(result["structuredContent"], expected)
                        self.assertEqual(json.loads(result["content"][0]["text"]), expected)
                        client.domain("cidr_contains", arguments)
                client.eof()

    def test_notification_only_batches_are_silent_and_empty_batches_are_errors(self):
        notification = {"jsonrpc": "2.0", "method": "notifications/cancelled", "params": {"requestId": 9999}}
        for initialized in (False, True):
            for count in (1, 8, 9):
                with self.subTest(initialized=initialized, count=count), MCPProcess() as client:
                    if initialized:
                        client.initialize("2025-03-26")
                    client.send([notification] * count)
                    self.assertIn("result", client.rpc("ping"))
                    self.assertIn("result", client.rpc("ping"))
                    client.eof()
                    self.assertEqual(client.pending, {})
                    # CHANGE: Count every captured frame after EOF so a stray notification error cannot hide.
                    self.assertEqual(len(client.frames), 3 if initialized else 2)
        with MCPProcess() as client:
            client.initialize("2025-03-26")
            client.send([])
            message = client.receive()
            self.assertIsInstance(message, dict)
            self.assertEqual(message["error"]["code"], -32600)
            self.assertIsNone(message["id"])
            self.assertIn("result", client.rpc("ping"))
            client.eof()

    def test_oversized_unterminated_and_incomplete_frames_terminate(self):
        for data in (b"x" * 16384, b'{"jsonrpc":"2.0"'):
            with self.subTest(length=len(data)), MCPProcess() as client:
                client.raw(data)
                client.eof(expected=1)

    def test_concurrent_requests_have_complete_frames_and_unique_ids(self):
        with MCPProcess() as client:
            client.initialize()
            client.discover()
            identifiers = list(range(1000, 1040))
            client.raw(b"".join(encoded(tool_request(i)) for i in identifiers))
            successes = 0
            for identifier in identifiers:
                message = client.response(identifier)
                if "error" in message:
                    self.assertEqual(message["error"]["code"], -32000)
                else:
                    successes += 1
                    envelope = message["result"]["structuredContent"]
                    Draft202012Validator(client.tools["cidr_inspect"]["outputSchema"]).validate(envelope)
                    self.assertEqual(json.loads(message["result"]["content"][0]["text"]), envelope)
            self.assertGreater(successes, 0)
            self.assertEqual(client.pending, {})
            self.assertIn("result", client.call("cidr_inspect", {"kind": "address", "value": "::1"}))
            client.eof()
            actual = [json.loads(frame).get("id") for frame in client.frames if isinstance(json.loads(frame), dict)]
            for identifier in identifiers:
                self.assertEqual(actual.count(identifier), 1)

    def test_batch_support_is_protocol_gated(self):
        for protocol in PROTOCOLS:
            with self.subTest(protocol=protocol), MCPProcess() as client:
                client.initialize(protocol)
                client.send([tool_request(10), {"jsonrpc": "2.0", "method": "notifications/initialized"}, tool_request(11)])
                message = client.receive()
                if protocol in ("2024-11-05", "2025-03-26"):
                    self.assertIsInstance(message, list)
                    self.assertEqual({item["id"] for item in message}, {10, 11})
                    self.assertTrue(all("result" in item for item in message))
                else:
                    self.assertIsInstance(message, dict)
                    self.assertEqual(message["error"]["code"], -32600)
                self.assertIn("result", client.call("cidr_inspect", {"kind": "address", "value": "::1"}))
                client.eof()

    def test_batch_limit_rejects_whole_envelope(self):
        with MCPProcess() as client:
            client.initialize("2025-03-26")
            client.send([tool_request(i) for i in range(20, 29)])
            message = client.receive()
            self.assertIsInstance(message, dict)
            self.assertEqual(message["error"]["code"], -32000)
            self.assertIn("result", client.call("cidr_inspect", {"kind": "address", "value": "::1"}))
            client.eof()

    def test_cancellation_notification_preserves_later_calls(self):
        with MCPProcess() as client:
            client.initialize()
            client.send({"jsonrpc": "2.0", "method": "notifications/cancelled", "params": {"requestId": 9999, "reason": "test"}})
            self.assertIn("result", client.call("cidr_inspect", {"kind": "address", "value": "::1"}))
            client.eof()

    def test_termination_signals_stop_idle_process(self):
        for number in (signal.SIGINT, signal.SIGTERM):
            with self.subTest(signal=number), MCPProcess() as client:
                client.initialize()
                client.process.send_signal(number)
                client.wait_for_exit()
                self.assertFalse(client.process.stdin.closed, "Signal must terminate without stdin EOF")

    def test_termination_signals_before_initialize(self):
        for number in (signal.SIGINT, signal.SIGTERM):
            with self.subTest(signal=number), MCPProcess() as client:
                client.wait_for_log("server_started")
                client.process.send_signal(number)
                client.wait_for_exit()
                self.assertEqual(client.frames, [])

    def test_termination_signals_with_incomplete_input(self):
        for number in (signal.SIGINT, signal.SIGTERM):
            with self.subTest(signal=number), MCPProcess() as client:
                client.initialize()
                client.raw(b'{"jsonrpc":"2.0","id":2,"method":')
                client.process.send_signal(number)
                client.wait_for_exit()
                self.assertFalse(client.process.stdin.closed)
                self.assertEqual(len(client.frames), 1, "An unfinished input frame has no response")

    def test_repeated_termination_signals_preserve_graceful_exit(self):
        with MCPProcess() as client:
            client.initialize()
            # Unix may coalesce these signals; only one orderly shutdown is required.
            for number in (signal.SIGTERM, signal.SIGINT) * 16:
                try:
                    os.kill(client.process.pid, number)
                except ProcessLookupError:
                    break
            client.wait_for_exit()

    @staticmethod
    def fill_pipe(output):
        os.set_blocking(output, False)
        filled = 0
        # Observe EAGAIN rather than assuming an operating system's pipe capacity.
        for chunk in (b"x" * 512, b"x"):
            while True:
                try:
                    filled += os.write(output, chunk)
                except BlockingIOError:
                    break
                if filled >= 4 * 1024 * 1024:
                    raise AssertionError("Pressure fixture exceeded its bounded capacity")
        if not filled:
            raise AssertionError("Pressure fixture wrote no bytes")
        try:
            os.write(output, b"x")
        except BlockingIOError:
            return filled
        raise AssertionError("Pressure fixture did not establish EAGAIN")

    def test_termination_signals_with_stderr_pressure(self):
        for number in (signal.SIGINT, signal.SIGTERM):
            with self.subTest(signal=number):
                drain, output = os.pipe()
                try:
                    filled = self.fill_pipe(output)
                    with MCPProcess(read_stderr=False, stderr_fd=output) as client:
                        os.close(output)
                        output = None
                        client.initialize()
                        client.process.send_signal(number)
                        client.wait_for_exit()
                    captured = bytearray()
                    while chunk := os.read(drain, 4096):
                        captured.extend(chunk)
                    self.assertEqual(captured, b"x" * filled)
                finally:
                    if output is not None:
                        os.close(output)
                    os.close(drain)

    def test_termination_signals_with_stdout_pressure(self):
        for number in (signal.SIGINT, signal.SIGTERM):
            with self.subTest(signal=number):
                drain, output = os.pipe()
                try:
                    with MCPProcess(stdout_fd=output) as client:
                        client.wait_for_log("server_started")
                        client.send(request(1, "initialize", {
                            "protocolVersion": "2025-11-25", "capabilities": {},
                            "clientInfo": {"name": "signal-pressure", "version": "1"},
                        }))
                        # Drain only the initialization response, then deliberately keep stdout full.
                        response = bytearray()
                        deadline = time.monotonic() + DEADLINE
                        while not response.endswith(b"\n"):
                            ready, _, _ = select.select([drain], [], [], max(0, deadline - time.monotonic()))
                            self.assertTrue(ready, "Initialization did not complete before pressure")
                            chunk = os.read(drain, 4096)
                            self.assertTrue(chunk, "Stdout closed during initialization")
                            response.extend(chunk)
                            self.assertLess(len(response), 65536)
                        self.assertIn("result", json.loads(response))
                        client.send({"jsonrpc": "2.0", "method": "notifications/initialized"})
                        filled = self.fill_pipe(output)
                        os.close(output)
                        output = None
                        client.send(tool_request(2))
                        client.wait_for_log("tool_completed")
                        client.process.send_signal(number)
                        status = client.process.wait(timeout=DEADLINE)
                        # Retiring an active transport write may report a transport failure.
                        self.assertIn(status, (0, 1), "Signal shutdown must not abort or hit the process deadline")
                        client.wait_for_exit(expected=status)
                        events = {json.loads(line)["event"] for line in client.stderr.splitlines()}
                        self.assertIn("server_stopped" if status == 0 else "transport_failed", events)
                    captured = bytearray()
                    while chunk := os.read(drain, 4096):
                        captured.extend(chunk)
                    self.assertEqual(captured, b"x" * filled, "Stdout must remain full throughout shutdown")
                finally:
                    if output is not None:
                        os.close(output)
                    os.close(drain)

    def test_stderr_json_is_separate_and_omits_literal_inputs(self):
        with MCPProcess() as client:
            client.initialize()
            self.assertIn("result", client.call("cidr_inspect", {"kind": "address", "value": "192.0.2.123"}))
            client.call("unknown\n192.0.2.123", {})
            client.eof()
            self.assertNotIn(b"192.0.2.123", client.stderr)
            self.assertNotIn(b"unknown", client.stderr)
            records = [json.loads(line) for line in client.stderr.splitlines()]
            self.assertTrue(records)
            for record in records:
                self.assertTrue({"level", "component", "event"} <= set(record))
                if record["event"] != "logs_dropped":
                    self.assertIn("timestamp", record)

    def test_stderr_pressure_does_not_block_protocol(self):
        drain, output = os.pipe()
        try:
            os.set_blocking(output, False)
            filled = 0
            # CHANGE: Establish actual EAGAIN before launch; a fixed call count cannot prove pipe pressure.
            for chunk in (b"x" * 512, b"x"):
                while True:
                    try:
                        filled += os.write(output, chunk)
                    except BlockingIOError:
                        break
                    self.assertLess(filled, 4 * 1024 * 1024, "Pressure fixture exceeded its bounded capacity")
            self.assertGreater(filled, 0)
            with self.assertRaises(BlockingIOError):
                os.write(output, b"x")
            with MCPProcess(read_stderr=False, stderr_fd=output) as client:
                os.close(output)
                output = None
                client.initialize()
                for _ in range(8):
                    self.assertIn("result", client.call("cidr_inspect", {"kind": "address", "value": "::1"}))
                client.eof()
            captured = bytearray()
            while chunk := os.read(drain, 4096):
                captured.extend(chunk)
            self.assertEqual(captured, b"x" * filled, "The full pipe must remain undrained throughout execution")
            print(f"stderr pressure: observed EAGAIN with {filled} bytes before server launch", flush=True)
        finally:
            if output is not None:
                os.close(output)
            os.close(drain)

    def test_stdout_backpressure_has_a_bounded_failure(self):
        process = subprocess.Popen([str(BINARY), "--stdio"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=0)
        try:
            initialization = request(1, "initialize", {"protocolVersion": "2025-11-25", "capabilities": {}, "clientInfo": {"name": "blocked-reader", "version": "1"}})
            frames = [initialization, {"jsonrpc": "2.0", "method": "notifications/initialized"}]
            frames.extend(request(i, "tools/list") for i in range(10, 30))
            process.stdin.write(b"".join(encoded(frame) for frame in frames))
            # CHANGE: Deliberately do not drain stdout; communicate() here would invalidate the backpressure test.
            self.assertNotEqual(process.wait(timeout=DEADLINE), 0)
        finally:
            if process.poll() is None:
                process.kill()
            process.communicate(timeout=DEADLINE)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", type=Path, default=BINARY)
    options, remaining = parser.parse_known_args()
    BINARY = options.binary.resolve()
    if not BINARY.is_file():
        parser.error(f"Executable does not exist: {BINARY}")
    unittest.main(argv=[sys.argv[0], *remaining])
