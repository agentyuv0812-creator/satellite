"""
Operational Intelligence Dashboard Web & API Server - Multi-Facility Support
Serves static web files and provides REST endpoints for telemetry data & updates.
Run: python3 server.py [port]
"""

import os
import sys
import json
import mimetypes
import subprocess
from urllib.parse import parse_qs, urlparse
from http.server import BaseHTTPRequestHandler, HTTPServer

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8085
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
WEB_DIR = os.path.join(BASE_DIR, "web")


class IntelligenceDashboardHandler(BaseHTTPRequestHandler):
    def send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def send_file(self, filepath):
        if not os.path.exists(filepath):
            self.send_error(404, "File Not Found")
            return
        
        mime_type, _ = mimetypes.guess_type(filepath)
        if not mime_type:
            mime_type = "text/plain"
        
        self.send_response(200)
        self.send_header("Content-Type", mime_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        with open(filepath, "rb") as f:
            self.wfile.write(f.read())

    def do_GET(self):
        parsed_url = urlparse(self.path)
        clean_path = parsed_url.path
        query_params = parse_qs(parsed_url.query)

        # API Telemetry Endpoint (Supports ?facility=aerostar or ?facility=methode)
        if clean_path == "/api/data":
            facility = query_params.get("facility", ["methode"])[0].lower()
            if facility == "aerostar":
                target_data = os.path.join(DATA_DIR, "pipeline_data_aerostar.json")
            else:
                target_data = os.path.join(DATA_DIR, "pipeline_data.json")

            if os.path.exists(target_data):
                with open(target_data, "r") as f:
                    self.send_json(json.load(f))
            else:
                self.send_json({"error": f"Data file for {facility} not found"}, status=404)
            return

        # Serve static web files
        if clean_path in ["/", "/index.html"]:
            self.send_file(os.path.join(WEB_DIR, "index.html"))
            return

        web_target = os.path.join(WEB_DIR, clean_path.lstrip("/"))
        if os.path.exists(web_target) and os.path.isfile(web_target):
            self.send_file(web_target)
            return

        data_target = os.path.join(BASE_DIR, clean_path.lstrip("/"))
        if os.path.exists(data_target) and os.path.isfile(data_target):
            self.send_file(data_target)
            return

        self.send_error(404, "File Not Found")

    def do_POST(self):
        parsed_url = urlparse(self.path)
        if parsed_url.path == "/api/trigger-update":
            try:
                scheduler_script = os.path.join(BASE_DIR, "src", "scheduler.py")
                subprocess.run([sys.executable, scheduler_script], check=True)
                self.send_json({"status": "success", "message": "Multi-facility pipeline updated successfully"})
            except Exception as e:
                self.send_json({"status": "error", "message": str(e)}, status=500)
            return

        self.send_error(404, "Not Found")


def run_server(port=PORT):
    server_address = ("0.0.0.0", port)
    httpd = HTTPServer(server_address, IntelligenceDashboardHandler)
    print(f"=================================================================")
    print(f" Multi-Facility Operational Intelligence Server (Apodaca & Romulus)")
    print(f" Dashboard running at: http://localhost:{port}/")
    print(f" Methode API Endpoint:  http://localhost:{port}/api/data?facility=methode")
    print(f" Aerostar API Endpoint: http://localhost:{port}/api/data?facility=aerostar")
    print(f"=================================================================")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server.")
        httpd.server_close()


if __name__ == "__main__":
    run_server()
