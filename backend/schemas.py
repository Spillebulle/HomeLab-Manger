from typing import Any, Optional
from pydantic import BaseModel, Field


class DeviceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    hostname: str = Field(min_length=1, max_length=255)
    device_type: str = Field(min_length=1)
    adapter_type: str = Field(min_length=1)
    credentials: dict[str, Any] = {}
    enabled: bool = True
    notes: Optional[str] = None
    # Seconds between polls; None ⇒ poller default. Clamped to a minimum by the
    # poller. Empty form values arrive as None.
    poll_interval: Optional[int] = Field(default=None, ge=1)


class DeviceUpdate(BaseModel):
    # Optional + min_length: None (field omitted) passes, but an empty string is
    # rejected so a PUT can't blank out a required field.
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    hostname: Optional[str] = Field(default=None, min_length=1, max_length=255)
    device_type: Optional[str] = Field(default=None, min_length=1)
    adapter_type: Optional[str] = Field(default=None, min_length=1)
    credentials: Optional[dict[str, Any]] = None
    enabled: Optional[bool] = None
    notes: Optional[str] = None
    poll_interval: Optional[int] = Field(default=None, ge=1)


class ApiKeyCreate(BaseModel):
    name: Optional[str] = None


class ShutdownRuleCreate(BaseModel):
    target_device_id: int
    action: str = "graceful_shutdown"
    # charge is a percentage; runtime/priority/delay are non-negative. Bounding
    # here turns a silent never-fires/always-fires misconfig into a 422.
    trigger_charge_pct: Optional[int] = Field(default=None, ge=0, le=100)
    trigger_runtime_sec: Optional[int] = Field(default=None, ge=0)
    enabled: bool = True
    priority: int = Field(default=100, ge=0)     # lower fires first during an outage
    delay_after_sec: int = Field(default=0, ge=0)  # wait after this rule before the next


class ShutdownRuleUpdate(BaseModel):
    action: Optional[str] = None
    trigger_charge_pct: Optional[int] = Field(default=None, ge=0, le=100)
    trigger_runtime_sec: Optional[int] = Field(default=None, ge=0)
    enabled: Optional[bool] = None
    priority: Optional[int] = Field(default=None, ge=0)
    delay_after_sec: Optional[int] = Field(default=None, ge=0)


class NotificationConfigUpdate(BaseModel):
    webhook_url: Optional[str] = None
    enabled: Optional[bool] = None
    notify_offline: Optional[bool] = None
    notify_ups_state: Optional[bool] = None
    notify_action: Optional[bool] = None


class ServiceCreate(BaseModel):
    """A published web service. `domain` picks one of the configured
    Namecheap domains (default: the first); `dns_record_type`/`_target`
    optionally override the integration's default record plan (CNAME to the
    domain root) for this service. The toggle block maps 1:1 to NPM
    proxy-host settings."""
    name: str = Field(min_length=1, max_length=255)
    subdomain: str = Field(min_length=1, max_length=255)
    domain: Optional[str] = None
    dns_record_type: Optional[str] = None    # CNAME | A | None (= default)
    dns_record_target: Optional[str] = None  # None = default (domain root / config)
    forward_scheme: str = "http"
    forward_host: str = Field(min_length=1)
    forward_port: int = Field(ge=1, le=65535)
    websockets: bool = True
    block_exploits: bool = True
    caching_enabled: bool = False
    ssl_forced: bool = True
    http2_support: bool = True
    hsts_enabled: bool = False
    hsts_subdomains: bool = False
    portainer_container: Optional[str] = None
    portainer_endpoint_id: Optional[int] = None


class ServiceUpdate(BaseModel):
    """Partial edit. A subdomain or domain change triggers DNS + certificate
    re-provisioning in the PUT handler, and a DNS type/target change replaces
    the record; everything else is synced to NPM by the pipeline's
    settings-sync step."""
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    subdomain: Optional[str] = Field(default=None, min_length=1, max_length=255)
    domain: Optional[str] = None
    dns_record_type: Optional[str] = None
    dns_record_target: Optional[str] = None
    forward_scheme: Optional[str] = None
    forward_host: Optional[str] = Field(default=None, min_length=1)
    forward_port: Optional[int] = Field(default=None, ge=1, le=65535)
    websockets: Optional[bool] = None
    block_exploits: Optional[bool] = None
    caching_enabled: Optional[bool] = None
    ssl_forced: Optional[bool] = None
    http2_support: Optional[bool] = None
    hsts_enabled: Optional[bool] = None
    hsts_subdomains: Optional[bool] = None
    portainer_container: Optional[str] = None
    portainer_endpoint_id: Optional[int] = None


class LoginRequest(BaseModel):
    username: str
    password: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class PreflightRequest(BaseModel):
    """Active connectivity test for a *prospective* device. The add-device
    modal POSTs this so the user can validate creds before saving.

    When the modal is in *edit* mode the secret credential fields come back
    blanked from /api/devices/{id}/credentials (so the browser never holds
    the real passwords), and the user can save without re-typing them
    because the PUT handler merges blanks with stored values. The preflight
    endpoint applies the same merge when `device_id` is supplied - without
    that, clicking "Test connection" on an unmodified edit form sends empty
    passwords and probes fail with "no credentials configured" even though
    the saved device has perfectly good creds in the DB."""
    hostname: str
    adapter_type: str
    credentials: dict[str, Any] = {}
    device_id: Optional[int] = None
