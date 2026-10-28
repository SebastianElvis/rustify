"""Serve deterministic HTTP responses on the loopback interface."""

import base64
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import threading


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *args):
        pass

    def handle_request(self):
        data = self.rfile.read(int(self.headers.get("Content-Length", "0")))
        request = {"method": self.command, "path": self.path, "headers": list(self.headers.raw_items()), "body_b64": base64.b64encode(data).decode()}
        self.server.requests.append(request)
        status = 200
        headers = {}
        if self.path.startswith(("/redirect/", "/upstream-redirect/")):
            status = int(self.path.split("/")[-1])
            headers["Location"] = "/text" if self.path.startswith("/upstream-redirect/") else "/echo"
            body = b"redirect\n"
        elif self.path.startswith("/status/"):
            status = int(self.path.split("/")[-1])
            body = f"status {status}\n".encode()
        elif self.path == "/text":
            body = b"hello\n"
        elif self.path == "/json":
            body = b'{"hello":"world","n":1}'
            headers["Content-Type"] = "application/json"
        else:
            selected = {name.lower(): self.headers[name] for name in ("Accept", "Content-Type", "X-Test", "User-Agent") if name in self.headers}
            body = json.dumps({"method": self.command, "path": self.path, "headers": selected, "body_b64": request["body_b64"]}, sort_keys=True, separators=(",", ":")).encode()
            headers["Content-Type"] = "application/json"
        self.send_response(status)
        for name, value in headers.items():
            self.send_header(name, value)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    do_GET = handle_request
    do_HEAD = handle_request
    do_POST = handle_request


def start(port=0):
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    server.requests = []
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server
