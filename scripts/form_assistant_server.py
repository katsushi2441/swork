#!/usr/bin/env python3
import json
import subprocess
import sys
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "fill_contact_form.py"


class Handler(BaseHTTPRequestHandler):
    def send_json(self, status, data):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        qs = urllib.parse.parse_qs(parsed.query)
        if parsed.path == "/health":
            self.send_json(200, {"ok": True, "service": "SWork Form Assistant"})
            return
        if parsed.path != "/fill":
            self.send_json(404, {"ok": False, "error": "not found"})
            return
        lead_id = (qs.get("lead_id") or [""])[0].strip()
        if not lead_id:
            self.send_json(400, {"ok": False, "error": "lead_id required"})
            return
        cmd = [sys.executable, str(SCRIPT), "--lead-id", lead_id]
        subprocess.Popen(cmd, cwd=str(ROOT))
        self.send_json(200, {"ok": True, "lead_id": lead_id, "message": "browser launched"})

    def log_message(self, fmt, *args):
        print(self.address_string(), "-", fmt % args)


def main():
    server = ThreadingHTTPServer(("127.0.0.1", 8765), Handler)
    print("SWork Form Assistant: http://127.0.0.1:8765/health")
    server.serve_forever()


if __name__ == "__main__":
    main()
