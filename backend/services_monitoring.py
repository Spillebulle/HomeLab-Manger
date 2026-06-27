"""Async clients for external uptime-monitoring tools, behind one factory.

Currently implements **Kuvasz** (kuvasz-uptime.dev) over its REST API v2.

**Uptime Kuma is intentionally NOT implemented yet.** It has no management
REST API at all - everything goes over Socket.IO, and its "API keys" only
unlock the Prometheus `/metrics` HTTP endpoint, they can't add monitors. Wiring
it up means the `uptime-kuma-api` socket.io library + an admin username/password
(not an API key). The factory leaves a clear slot for it so adding it later is
a new class, not a refactor.

Kuvasz specifics (verified against API v2):
- Auth: `X-API-KEY` header (works on every v2; Bearer auth is only >= 2.1.0).
- Monitor create/patch bodies use **kebab-case** keys (`uptime-check-interval`,
  `ssl-check-enabled`, ...).
- Notification channels are referenced by `"<type>:<name>"` ids (e.g.
  `email:my-email`) in a monitor's `integrations` array - set on create and via
  PATCH. The available channels come from `GET /api/v2/integrations`.
- A monitor is referenced on a status page by `"<type>:<name>"` too - for an
  HTTP monitor that's `http:<name>`. Status-page membership is edited by
  GET-modify-PATCH of the page's `monitors` list, preserving the other entries
  (same read-modify-write discipline as the Namecheap setHosts guard).
"""
import logging

import httpx

logger = logging.getLogger(__name__)


class MonitoringError(Exception):
    """Any monitoring-provider API failure, with a human-readable message."""


def _err_detail(resp: httpx.Response) -> str:
    try:
        data = resp.json()
        if isinstance(data, dict):
            return str(data.get("message") or data.get("error")
                       or data.get("detail") or f"HTTP {resp.status_code}")
        if isinstance(data, list) and data:
            return "; ".join(str(d.get("message") or d) if isinstance(d, dict)
                             else str(d) for d in data)
    except Exception:
        pass
    return f"HTTP {resp.status_code}"


class KuvaszClient:
    """REST client for Kuvasz v2. Short-lived `httpx.AsyncClient` per call,
    mirroring NPMClient / PortainerClient - instances live one request."""

    PROVIDER = "kuvasz"

    def __init__(self, base_url: str, api_key: str, timeout: float = 20.0):
        self.base_url = (base_url or "").rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    async def _request(self, method: str, path: str, json_body=None,
                       ok_404: bool = False):
        try:
            async with httpx.AsyncClient(verify=False, timeout=self.timeout) as c:
                r = await c.request(method, f"{self.base_url}/api/v2{path}",
                                    json=json_body,
                                    headers={"X-API-KEY": self.api_key})
        except httpx.HTTPError as exc:
            raise MonitoringError(f"Cannot reach Kuvasz at {self.base_url}: {exc}") from exc
        if r.status_code == 404 and ok_404:
            return None
        if r.status_code in (401, 403):
            raise MonitoringError("Kuvasz rejected the API key (check ADMIN_API_KEY)")
        if r.status_code >= 400:
            raise MonitoringError(f"Kuvasz {method} {path}: {_err_detail(r)}")
        if r.status_code == 204 or not r.content:
            return None
        return r.json()

    # ── probe ───────────────────────────────────────────────────────────────

    async def test(self) -> dict:
        """List monitors - the cheapest call that proves both the API key and
        the base URL are right (GET /health would prove reachability only)."""
        monitors = await self.list_monitors()
        return {"ok": True, "detail": f"Connected - {len(monitors)} monitor(s) configured"}

    # ── monitors ──────────────────────────────────────────────────────────────

    @staticmethod
    def monitor_ref(monitor: dict) -> str:
        """The `"<type>:<name>"` string a status page uses to reference this
        monitor. HTTP monitors are always `http:<name>`."""
        return f"http:{monitor.get('name')}"

    async def list_monitors(self) -> list[dict]:
        return await self._request("GET", "/http-monitors") or []

    async def get_monitor(self, monitor_id) -> dict | None:
        return await self._request("GET", f"/http-monitors/{monitor_id}", ok_404=True)

    async def create_monitor(self, spec: dict) -> dict:
        """`spec` is a normalized dict: {name, url, interval, ssl_check,
        enabled, integrations: [ids]}. Returns the created monitor dict
        (guaranteed to carry `id` + `name`)."""
        body = {
            "name": spec["name"],
            "url": spec["url"],
            "uptimeCheckInterval": int(spec.get("interval") or 60),
            "enabled": bool(spec.get("enabled", True)),
            "sslCheckEnabled": bool(spec.get("ssl_check", False)),
            "integrations": list(spec.get("integrations") or []),
        }
        created = await self._request("POST", "/http-monitors", body)
        # Some Kuvasz builds answer the POST with 201 + empty body; fall back to
        # looking the monitor up by the (unique) name we just created it with.
        if not isinstance(created, dict) or created.get("id") is None:
            created = None
            for m in await self.list_monitors():
                if m.get("name") == spec["name"]:
                    created = m
                    break
            if created is None:
                raise MonitoringError("Monitor created but could not be read back by name")
        created.setdefault("name", spec["name"])
        return created

    # Normalized patch key → Kuvasz JSON body key. The REST API is camelCase
    # (the kebab-case in the docs is the YAML/IaC format only). The PATCH
    # endpoint takes a partial JSON object (ObjectNode), so sending just the
    # changed keys is correct - it merges onto the existing monitor.
    _PATCH_MAP = {
        "name": "name", "url": "url", "interval": "uptimeCheckInterval",
        "ssl_check": "sslCheckEnabled", "enabled": "enabled",
        "integrations": "integrations",
    }

    async def update_monitor(self, monitor_id, normalized: dict) -> dict | None:
        body = {self._PATCH_MAP[k]: v for k, v in normalized.items()
                if k in self._PATCH_MAP}
        if not body:
            return None
        return await self._request("PATCH", f"/http-monitors/{monitor_id}", body)

    async def delete_monitor(self, monitor_id) -> None:
        await self._request("DELETE", f"/http-monitors/{monitor_id}", ok_404=True)

    # ── notification channels (integrations) ───────────────────────────────────

    async def list_integrations(self) -> list[dict]:
        """Configured notification channels, normalized to
        {id, type, name, enabled}. The `id` is what goes in a monitor's
        `integrations` array (`"<type>:<name>"`)."""
        raw = await self._request("GET", "/integrations") or []
        out: list[dict] = []
        for it in raw:
            if isinstance(it, str):
                out.append({"id": it, "type": it.split(":", 1)[0],
                            "name": it.split(":", 1)[-1], "enabled": True})
                continue
            if not isinstance(it, dict):
                continue
            itype = it.get("type") or ""
            iname = it.get("name") or ""
            iid = it.get("id") or (f"{itype}:{iname}".lower() if itype else iname)
            out.append({"id": iid, "type": itype, "name": iname or iid,
                        "enabled": bool(it.get("enabled", True))})
        return out

    # ── status pages ────────────────────────────────────────────────────────

    async def list_status_pages(self) -> list[dict]:
        return await self._request("GET", "/status-pages") or []

    async def get_status_page(self, page_id) -> dict | None:
        return await self._request("GET", f"/status-pages/{page_id}", ok_404=True)

    async def add_monitor_to_page(self, page_id, monitor_ref: str) -> None:
        page = await self.get_status_page(page_id)
        if page is None:
            raise MonitoringError(f"Status page {page_id} not found")
        monitors = list(page.get("monitors") or [])
        if monitor_ref not in monitors:
            monitors.append(monitor_ref)
            await self._request("PATCH", f"/status-pages/{page_id}",
                                {"monitors": monitors})

    async def remove_monitor_from_page(self, page_id, monitor_ref: str) -> None:
        page = await self.get_status_page(page_id)
        if page is None:
            return  # page gone ⇒ nothing to remove from; idempotent
        current = list(page.get("monitors") or [])
        kept = [m for m in current if m != monitor_ref]
        if len(kept) != len(current):
            await self._request("PATCH", f"/status-pages/{page_id}",
                                {"monitors": kept})


def monitoring_client(cfg: dict):
    """Factory: pick the provider client from the integration config. Kuvasz
    today; Uptime Kuma is the planned second provider (see module docstring)."""
    provider = (cfg.get("provider") or "kuvasz").strip().lower()
    if provider == "kuvasz":
        return KuvaszClient(cfg["base_url"], cfg["api_key"])
    if provider == "uptime_kuma":
        raise MonitoringError(
            "Uptime Kuma support is not implemented yet (it needs a Socket.IO "
            "admin session, not an API key)")
    raise MonitoringError(f"Unknown monitoring provider: {provider!r}")
