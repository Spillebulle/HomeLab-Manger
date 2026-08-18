"""Stand-in Nginx Proxy Manager and Portainer, for the screenshot fixture.

The Services page is the one screen that cannot be photographed from the
database alone: the "In NPM - not managed here" section and the Docker chips on
each row are read live from those two tools, and with neither reachable the
page renders an empty state and a pair of "not configured yet" warnings. A
picture of that is a picture of an install nobody has finished, which §17.3 of
the style guide asks us not to ship.

So `docs/shots.py` starts this, and `docs/seed-demo.py` points the npm and
portainer integration rows at it. It answers only the handful of reads the
Services page makes, on one port, because the two APIs do not collide:

    NPM        POST /api/tokens              -> a bearer token
               GET  /api/nginx/proxy-hosts   -> the proxy hosts
    Portainer  GET  /api/endpoints           -> the environments
               GET  /api/endpoints/{id}/docker/containers/json

Nothing here is ever written to, and nothing here runs outside the fixture.
Keep the shapes in step with what services_npm.py and services_portainer.py
read; a field they need and this does not return shows up as an empty column
in the picture rather than as an error.
"""
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = 8212
BASE_URL = f"http://127.0.0.1:{PORT}"

# Two of these (jellyfin, paperless) are also seeded as managed services, so the
# page can match them by proxy-host id; the rest are what the sync section
# offers to import. `nzbget` is deliberately HTTP-only (certificate_id 0) so the
# section shows a host without a certificate too.
_PROXY_HOSTS = [
    {"id": 11, "domain_names": ["jellyfin.example.net"], "forward_scheme": "http",
     "forward_host": "10.0.0.41", "forward_port": 8096, "certificate_id": 31,
     "enabled": True, "allow_websocket_upgrade": True, "block_exploits": True,
     "caching_enabled": False, "ssl_forced": True, "http2_support": True,
     "hsts_enabled": False, "hsts_subdomains": False},
    {"id": 12, "domain_names": ["paperless.example.net"], "forward_scheme": "http",
     "forward_host": "10.0.0.42", "forward_port": 8000, "certificate_id": 32,
     "enabled": True, "allow_websocket_upgrade": True, "block_exploits": True,
     "caching_enabled": False, "ssl_forced": True, "http2_support": True,
     "hsts_enabled": False, "hsts_subdomains": False},
    {"id": 13, "domain_names": ["grafana.example.net"], "forward_scheme": "http",
     "forward_host": "10.0.0.43", "forward_port": 3000, "certificate_id": 33,
     "enabled": True, "allow_websocket_upgrade": True, "block_exploits": True,
     "caching_enabled": False, "ssl_forced": True, "http2_support": True,
     "hsts_enabled": False, "hsts_subdomains": False},
    {"id": 14, "domain_names": ["nzbget.example.net"], "forward_scheme": "http",
     "forward_host": "10.0.0.44", "forward_port": 6789, "certificate_id": 0,
     "enabled": True, "allow_websocket_upgrade": False, "block_exploits": True,
     "caching_enabled": False, "ssl_forced": False, "http2_support": True,
     "hsts_enabled": False, "hsts_subdomains": False},
    {"id": 15, "domain_names": ["vaultwarden.example.net"], "forward_scheme": "http",
     "forward_host": "10.0.0.45", "forward_port": 8080, "certificate_id": 35,
     "enabled": True, "allow_websocket_upgrade": True, "block_exploits": True,
     "caching_enabled": False, "ssl_forced": True, "http2_support": True,
     "hsts_enabled": False, "hsts_subdomains": False},
]

# Two environments, because the real thing usually has more than one and the
# host-IP-per-endpoint logic is worth showing. The agent endpoint's URL is what
# services_portainer.endpoint_host_ip() reads the host IP out of.
_ENDPOINTS = [
    {"Id": 1, "Name": "docker-01", "URL": "unix:///var/run/docker.sock", "Status": 1},
    {"Id": 2, "Name": "docker-02", "URL": "tcp://10.0.0.42:9001", "Status": 1},
]

_CONTAINERS = {
    1: [
        ("jellyfin", "running", 8096), ("grafana", "running", 3000),
        ("nzbget", "running", 6789), ("watchtower", "running", None),
    ],
    2: [
        ("paperless", "running", 8000), ("vaultwarden", "running", 8080),
        ("redis", "running", None), ("watchtower", "exited", None),
    ],
}


def _container(name: str, state: str, port: int | None, host_ip: str) -> dict:
    return {
        "Id": f"{abs(hash(name)) % (16 ** 12):012x}",
        "Names": [f"/{name}"],
        "Image": f"ghcr.io/demo/{name}:latest",
        "State": state,
        "Status": "Up 6 days" if state == "running" else "Exited (0) 2 days ago",
        "Ports": ([{"IP": "0.0.0.0", "PrivatePort": port, "PublicPort": port,
                    "Type": "tcp"}] if port else []),
        "NetworkSettings": {"Networks": {"bridge": {"IPAddress": host_ip}}},
    }


class _Handler(BaseHTTPRequestHandler):
    # HTTP/1.1, not the BaseHTTPRequestHandler default of 1.0. On 1.0 the
    # server closes the socket after every response, and httpx - which is an
    # HTTP/1.1 client with a connection pool - intermittently picked a
    # connection the server had just closed and surfaced it as an empty
    # ConnectError, so the Services page rendered "Could not list NPM proxy
    # hosts" in about one run out of two. Every response here sends a
    # Content-Length, which is what 1.1 requires to keep a connection alive.
    protocol_version = "HTTP/1.1"

    def _send(self, payload, status=200):
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if self.path.startswith("/api/tokens"):
            self._send({"token": "demo-token", "expires": "2099-01-01T00:00:00.000Z"})
        else:
            self._send({"error": {"message": "not stubbed"}}, 404)

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path == "/api/nginx/proxy-hosts":
            self._send(_PROXY_HOSTS)
        elif path == "/api/nginx/certificates":
            self._send([{"id": h["certificate_id"], "provider": "letsencrypt",
                         "nice_name": h["domain_names"][0],
                         "domain_names": h["domain_names"]}
                        for h in _PROXY_HOSTS if h["certificate_id"]])
        elif path == "/api/endpoints":
            self._send(_ENDPOINTS)
        elif path.startswith("/api/endpoints/") and path.endswith("/docker/containers/json"):
            try:
                eid = int(path.split("/")[3])
            except (IndexError, ValueError):
                self._send([], 404); return
            host = "10.0.0.41" if eid == 1 else "10.0.0.42"
            self._send([_container(n, s, p, host) for n, s, p in _CONTAINERS.get(eid, [])])
        else:
            self._send({"error": {"message": "not stubbed"}}, 404)

    def log_message(self, *args):        # the fixture's log is noisy enough
        pass


def serve(port: int = PORT) -> ThreadingHTTPServer:
    """Start the stub on a daemon thread and return the server.

    Threading, not the plain HTTPServer: the Services page fans out to the
    proxy-host list and to every Portainer environment at once, and a
    single-threaded server leaves the rest of them queued behind the first
    until the client's connect timeout fires.
    """
    srv = ThreadingHTTPServer(("127.0.0.1", port), _Handler)
    srv.daemon_threads = True
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


if __name__ == "__main__":
    serve()
    print(f"demo stubs on {BASE_URL} - ctrl-c to stop")
    threading.Event().wait()
