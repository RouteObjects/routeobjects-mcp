#!/usr/bin/env python3
"""Test-only byte relay: record selected synthetic negotiation fields, never bodies."""
import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import threading
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binary', type=Path, required=True)
    parser.add_argument('--events', type=Path, required=True)
    args = parser.parse_args()
    args.events.mkdir(parents=True, exist_ok=True, mode=0o700)
    descriptor = os.open(args.events / f'relay-{os.getpid()}.jsonl',
                         os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    lock = threading.Lock()
    requests = {}

    def record(fields):
        with lock:
            value = {'monotonicNs': time.monotonic_ns(), 'relayPID': os.getpid(), **fields}
            data = (json.dumps(value, separators=(',', ':')) + '\n').encode()
            assert len(data) <= 2048
            assert os.write(descriptor, data) == len(data)

    def observe(direction, frame):
        value = json.loads(frame)
        assert isinstance(value, dict), 'This fixture permits only standalone synthetic requests'
        fields = {'direction': direction, 'id': value.get('id')}
        if 'method' in value:
            method = value['method']
            assert method in {'server/discover', 'initialize', 'notifications/initialized', 'tools/list', 'ping'}
            fields['method'] = method
            fields['event'] = 'notification' if 'id' not in value else 'request'
            if 'id' in value:
                with lock:
                    assert len(requests) < 16
                    requests[json.dumps(value['id'])] = method
            if method == 'initialize':
                fields['requestedProtocolVersion'] = value.get('params', {}).get('protocolVersion')
        else:
            with lock:
                method = requests.get(json.dumps(value.get('id')))
            fields.update(event='response', method=method)
            if 'error' in value:
                fields['errorCode'] = value['error'].get('code')
                # CHANGE: Error prose and all argument/result bodies stay out of this negotiation record.
            elif method == 'initialize':
                fields['negotiatedProtocolVersion'] = value.get('result', {}).get('protocolVersion')
            elif method == 'tools/list':
                fields['toolCount'] = len(value.get('result', {}).get('tools', []))
        record(fields)

    def relay(source, destination, direction=None):
        pending = bytearray()
        try:
            while data := os.read(source, 4096):
                if direction:
                    pending.extend(data)
                    while b'\n' in pending:
                        frame, _, pending = pending.partition(b'\n')
                        observe(direction, frame)
                    assert len(pending) <= 65536
                view = memoryview(data)
                while view:
                    view = view[os.write(destination, view):]
            assert not pending, 'Truncated negotiation frame'
        except BrokenPipeError:
            pass
        except Exception as error:
            record({'event': 'relay_failure', 'type': type(error).__name__})
        finally:
            if direction == 'client_to_server':
                child.stdin.close()

    record({'event': 'relay_started'})
    child = subprocess.Popen([str(args.binary.resolve()), '--stdio'], stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=0)
    for number in (signal.SIGTERM, signal.SIGINT):
        signal.signal(number, lambda _number, _frame: child.terminate() if child.poll() is None else None)
    threads = [
        threading.Thread(target=relay, args=(0, child.stdin.fileno(), 'client_to_server'), daemon=True),
        threading.Thread(target=relay, args=(child.stdout.fileno(), 1, 'server_to_client'), daemon=True),
        threading.Thread(target=relay, args=(child.stderr.fileno(), 2), daemon=True),
    ]
    for thread in threads:
        thread.start()
    try:
        status = child.wait(timeout=15)
    except subprocess.TimeoutExpired:
        child.kill()
        status = child.wait(timeout=5)
        record({'event': 'relay_deadline'})
    for thread in threads[1:]:
        thread.join(timeout=1)
    record({'event': 'server_exit', 'status': status})
    # The daemon input pump can still await Inspector EOF; process exit owns its descriptor.
    return status


if __name__ == '__main__':
    sys.exit(main())
