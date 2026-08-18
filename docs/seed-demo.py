"""Seed a throwaway shots.db with believable demo devices.

Feeds docs/shots.py so the README pictures show real-looking content
rather than an empty install. Section 17.3 asks for real content, and the
field names here match what the adapters actually return.

Run from the repository root: python docs/seed-demo.py
"""
import pathlib as _pl, os as _os, sys as _sys
_root = str(_pl.Path(__file__).resolve().parent.parent)
_os.chdir(_root); _sys.path.insert(0, _root)
import os, json, datetime
os.environ['DB_PATH'] = os.path.join(os.getcwd(), 'shots.db')
os.environ['ADMIN_PASSWORD'] = 'smoketest123'
from backend.database import init_db, SessionLocal
from backend.models import Device, DeviceCache, DeviceMetric, Integration, Service
from backend.timeutil import utcnow
init_db()
db = SessionLocal()
now = utcnow()

def add(name, host, adapter, dtype, cache):
    d = Device(name=name, hostname=host, adapter_type=adapter, device_type=dtype,
               enabled=True, credentials={})
    db.add(d); db.flush()
    for k, v in cache.items():
        db.add(DeviceCache(device_id=d.id, cache_key=k,
                           data=json.dumps(v, default=str), error=None, updated_at=now))
    return d

ports = [{"index": i, "name": f"Port {i}", "alias": "", "operStatus": 1 if i % 3 else 2,
          "adminStatus": 1, "speedMbps": 1000 if i % 3 else None, "combo": i > 44,
          "rxBytes": 8123456789 * i, "txBytes": 4123456789 * i} for i in range(1, 49)]
add("core-sw-01", "10.0.0.2", "dlink", "switch", {
    "status": {"online": True, "sysName": "core-sw-01", "sysDescr": "D-Link DGS-3120-48PC",
               "uptime": "42 days, 3:14", "firmware": "R4.00.B021", "ipOrigin": "manual"},
    "ports": ports,
    "poe": {"ports": [{"key": f"poe-{i}",
                       # A string, like both adapters emit - the frontend
                       # looks PoE up by String(portIndex) and an int here
                       # silently renders every PoE state as absent.
                       "portIndex": str(i), "powerClass": 3 if i % 4 == 0 else None,
                       "detectionStatus": ("fault" if i in (16, 34) else
                                          "delivering" if i % 4 == 0 else "disabled"),
                       "powerWatts": 6.4 if i % 4 == 0 else None, "adminEnabled": True,
                       "maxPowerMilliwatts": 30000} for i in range(1, 49)],
            "totalPowerWatts": 370, "consumptionWatts": 76.8},
    "connected": [{"mac": f"AC:DE:48:{i:02X}:1B:{i*3:02X}", "port": i,
                   "vendor": ["Ubiquiti Inc", "Raspberry Pi Trading", "Intel Corporate", None][i % 4],
                   "ip": f"10.0.0.{20+i}" if i % 5 == 0 else None} for i in range(1, 19)],
})
add("esxi-01", "10.0.0.20", "cimc_redfish", "server", {
    "status": {"online": True, "model": "UCS C220 M4", "serial": "FCH1935V0KZ",
               "power": "on", "health": "OK", "biosVersion": "C220M4.4.1.2c",
               "bmcVersion": "4.1(2g)", "bmcIp": "10.0.0.21"},
    "hardware": {"cpus": [{"model": "Intel Xeon E5-2650 v4", "cores": 12, "threads": 24,
                           "maxSpeedMHz": 2900, "health": "OK"}] * 2,
                 "memory": [{"id": f"DIMM_A{i}", "sizeGB": 32, "speedMHz": 2400,
                             "type": "DDR4", "manufacturer": "Samsung",
                             "serial": f"3A2F{i:04X}", "health": "OK"} for i in range(1, 9)],
                 "pcie": [{"slot": "1", "model": "UCSC-MLOM-C10T-02", "vendor": "Cisco", "class": "Network"}]},
    "storage": {"controllers": [{"name": "Cisco 12G SAS", "model": "UCSC-MRAID12G",
                                 "firmware": "24.12.1-0205", "health": "OK"}],
                "disks": [{"id": str(i), "model": "ST1200MM0088", "capacityGB": 1200,
                           "type": "HDD", "interface": "SAS", "state": "online",
                           "health": "OK", "serial": f"S4D0{i:03d}"} for i in range(1, 7)]},
    "power": {"budget": {"consumedWatts": 214, "capacityWatts": 770},
              "totalWatts": 208,
              "supplies": [{"id": "1", "model": "UCSC-PSU2V2-1400W", "health": "OK",
                            "inputWatts": 112, "lastOutputWatts": 99, "lineVoltage": 230,
                            "firmware": "07.10", "serial": "DTM19340ABC"},
                           {"id": "2", "model": "UCSC-PSU2V2-1400W", "health": "OK",
                            "inputWatts": 108, "lastOutputWatts": 96, "lineVoltage": 230,
                            "firmware": "07.10", "serial": "DTM19340DEF"}]},
    "sensors": {"source": "redfish",
                "temperatures": [{"name": n, "reading": v, "units": "Cel", "health": "OK"}
                                 for n, v in [("PSU1_TEMP", 33.0), ("PSU2_TEMP", 32.0),
                                              ("MB_TEMP_AMBIENT", 24.0), ("CPU1_TEMP", 48.0),
                                              ("CPU2_TEMP", 46.0), ("DIMM_A1_TEMP", 35.0)]],
                "fans": [{"name": f"FAN{i}_TACH", "reading": 8800 + i*40, "units": "RPM",
                          "health": "OK"} for i in range(1, 7)],
                "voltages": [{"name": "P12V", "reading": 12.096, "units": "V", "health": "OK"},
                             {"name": "P5V", "reading": 5.02, "units": "V", "health": "OK"},
                             {"name": "P3V3", "reading": 3.312, "units": "V", "health": "OK"}]},
    "network": {"adapters": [{"name": "MLOM", "model": "UCSC-MLOM-C10T-02", "health": "OK",
                              "interfaces": [{"name": "eth0", "mac": "00:2A:6A:11:22:33",
                                              "linkState": "up", "speedMbps": 10000}]}]},
})
ups = add("apc-rack", "usb", "usbups", "ups", {
    "status": {"online": True, "state": "online", "charge_pct": 100.0,
               "runtime_sec": 2820, "load_pct": 41.0, "watts": 541.2,
               "input_voltage": 232.0, "nominal_voltage": 230.0,
               "flags": {"ac_present": True, "charging": False, "discharging": False}},
    "metrics": {"load_pct": 41.0, "watts": 541.2, "charge_pct": 100.0,
                "runtime_sec": 2820, "input_voltage": 232.0},
})
add("edge-sw-02", "10.0.0.3", "hpe1820", "switch",
    {"status": {"online": False}, "ports": []})

import math, random
random.seed(7)
for h in range(24 * 60 // 5):
    ts = now - datetime.timedelta(minutes=5 * h)
    if 150 < h < 165:      # a real outage: the gap must show as empty space
        continue
    ph = h / 22.0
    for metric, val in [("load_pct", 41 + 9 * math.sin(ph) + random.uniform(-1.5, 1.5)),
                        ("watts", 541 + 118 * math.sin(ph) + random.uniform(-18, 18)),
                        ("charge_pct", 100 if h > 170 or h < 140 else 74 + h % 9),
                        ("runtime_sec", 2820 if h > 170 or h < 140 else 1500 + h),
                        ("input_voltage", 232 + random.uniform(-3, 3))]:
        db.add(DeviceMetric(device_id=ups.id, metric=metric, value=round(val, 2), ts=ts))

# ── Services page ──────────────────────────────────────────────────────────
# The integrations point at docs/demo_stubs.py, which docs/shots.py starts.
# Without them the Services page is two "not configured yet" warnings over an
# empty state, which is not a picture of the app working (§17.3).
from docs.demo_stubs import BASE_URL as _STUB

for name, cfg in [
    ("npm", {"base_url": _STUB, "email": "admin@example.net",
             "password": "demo", "le_email": "admin@example.net"}),
    ("namecheap", {"api_user": "demo", "api_key": "demo", "username": "demo",
                   "client_ip": "203.0.113.10", "domain": "example.net"}),
    ("portainer", {"base_url": _STUB, "api_key": "demo"}),
]:
    db.add(Integration(name=name, config=cfg))

# Two of the stub's five proxy hosts are managed here; the other three are what
# the sync section offers to import.
def svc(name, sub, host, port, hid, container, endpoint):
    db.add(Service(
        name=name, subdomain=sub, domain="example.net",
        forward_scheme="http", forward_host=host, forward_port=port,
        websockets=True, block_exploits=True, caching_enabled=False,
        ssl_forced=True, http2_support=True, hsts_enabled=False,
        hsts_subdomains=False,
        portainer_container=container, portainer_endpoint_id=endpoint,
        npm_proxy_host_id=hid, npm_certificate_id=hid + 20,
        dns_record_type="CNAME", dns_record_target="example.net",
        dns_status="ok", npm_status="ok", cert_status="ok", state="active",
        created_at=now))

svc("Jellyfin",  "jellyfin",  "10.0.0.41", 8096, 11, "jellyfin",  1)
svc("Paperless", "paperless", "10.0.0.42", 8000, 12, "paperless", 2)

db.commit()

print("seeded:", db.query(Device).count(), "devices,", db.query(DeviceMetric).count(), "metric samples")
