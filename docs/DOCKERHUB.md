![HomeLab Manger](docs/images/banner.png)

One page for **the whole rack**: switches, servers, BMCs and UPSes, each read
over the protocol it already speaks.

SNMP · SSH · Redfish · CIMC XMLAPI · IPMI · USB HID · SQLite · one container,
amd64 and arm64

![The dashboard: a sidebar listing devices grouped into switches and servers, beside a grid of device cards each showing a state dot, the address, the adapter and when it was last seen](docs/images/dashboard.png)

> Built for a trusted network. Device credentials are encrypted at rest, and
> sign-in is throttled against guessing, but the app is single-user, the
> encryption key sits beside the database, and HTTPS is opt-in. Read "What is
> not there yet" below before you put it anywhere public.

## Install

```yaml
# compose.yaml
services:
  homelab-manger:
    image: spillebulle/homelab-manger:0.8.0
    ports:
      - "8080:8080"
    environment:
      ADMIN_PASSWORD: pick-something
    volumes:
      - homelab-data:/data
    restart: unless-stopped

volumes:
  homelab-data:
```

`docker compose up -d`, then open <http://localhost:8080> and sign in as
`admin` with the password you set. `0.8.0` is the current release; `:latest`
also exists and moves with every release, so pin a version if you would rather
choose when to upgrade.

Without compose:

```bash
docker run -d --name homelab-manger \
  -p 8080:8080 -e ADMIN_PASSWORD=pick-something \
  -v homelab-data:/data \
  spillebulle/homelab-manger:0.8.0
```

The same image is published to GitHub Container Registry as
`ghcr.io/spillebulle/homelab-manger`.

**Monitoring a USB-connected UPS needs two extra flags**, `--privileged` and
`-v /dev:/dev:ro`, because the adapter reads the UPS through a `/dev/hidrawN`
node that changes when the UPS re-enumerates. Network-only installations do not
need either.

The `/data` volume holds the database, the session secret and the
credential-encryption key. Keep it across restarts, or sign-ins and stored
device credentials are lost.

## Switches

D-Link DGS-3120, HPE OfficeConnect 1820 and anything generic enough to answer
IF-MIB. Port status, PoE state and per-port power, VLAN membership, and a
Connected tab listing every learned MAC with its port and its vendor from the
IEEE registry.

Writes go over whichever surface the firmware actually supports, which is not
always SNMP: PoE and VLANs on the DGS-3120 are driven over SSH, and the 1820 is
driven through its web interface, because neither exposes them any other way.

| Adapter | Reads | Writes |
|---|---|---|
| `dlink` | SNMP, SSH | SSH |
| `hpe1820` | SNMP | Web interface |
| `snmp` | SNMP | SNMP |

![A switch's Ports tab: a front-panel diagram with a coloured box per port, above a table of VLAN, link, speed, traffic and PoE state for all 48 ports](docs/images/ports-switch.png)

## Servers and BMCs

HP iLO, Dell iDRAC, Huawei iBMC and Cisco UCS C-series. Inventory down to the
DIMM, live sensors and per-PSU wattage, power actions, and a KVM launch that
downloads the console file the firmware itself generates.

Cisco needs the right adapter for its firmware: `cimc` for anything before 3.0,
`cimc_redfish` for 3.0 and later, which reads sensors far faster and adds BIOS
and BMC detail the older interface never exposed.

| Adapter | For |
|---|---|
| `ilo`, `idrac`, `redfish` | Anything speaking Redfish |
| `ibmc` | Huawei iBMC, which rejects basic authentication |
| `cimc` | UCS C-series, CIMC before 3.0 |
| `cimc_redfish` | UCS C-series, CIMC 3.0 and later |

![A server's Hardware tab: the CPUs pane with a card per processor giving model, core count, thread count and clock, beside panes for memory and PCIe, under tabs for storage, network, power, sensors and console](docs/images/server.png)

## UPS and outage orchestration

A USB-connected UPS is read directly over the standard HID power device class,
so most units work without NUT or any per-model configuration. Charge, runtime,
load, watts and input voltage are stored as history and graphed over ranges from
one hour to a custom window.

The Shutdown tab turns that into a plan: pick which machines to bring down, in
what order, at what charge or runtime threshold, and how long to wait between
each. Test plan walks the whole thing and sends the notifications without
powering anything off.

![The UPS Graphs tab: four charts over the last 24 hours, showing load and watts together, battery charge, runtime remaining and input voltage](docs/images/ups-graphs.png)

## Publishing services

One form publishes an internal app at `https://name.your-domain`: the DNS record
in Namecheap, the proxy host in Nginx Proxy Manager and the Let's Encrypt
certificate are provisioned in order, with per-step status and a retry that
picks up where it stopped.

Existing proxy hosts can be imported rather than recreated, renaming a service
re-provisions its record and certificate, and a read-only Portainer connection
fills in forward targets and shows each service's container state.

![The Services page: published services grouped by Docker host, each row showing its address, forward port, container chip and status marks, above a list of proxy hosts not managed here with an Import button each](docs/images/services.png)

## Monitoring, events and notifications

Devices and published services can be registered as monitors in an external
uptime monitor, with their notification channels and status-page membership
managed from the same page. Kuvasz is the implemented provider. Every part of it
reverses: pause a monitor, clear its channels, take it off a page, or delete it
while leaving the remote monitor alone.

Every device also keeps a log of what happened to it: went offline, came back,
went on battery, was shut down by the outage plan. Each device can post those to
a Discord webhook, with separate switches for offline, UPS state and shutdown
actions.

## Interface

Dense and quiet: 12 px type, hairline rules, one accent that only ever means
selected, in hand or primary, and semantic colour reserved for state. Numbers are
monospaced so a column lines up and a reading does not jitter as it changes. A
chart draws a real gap where polling stopped rather than interpolating across it.

Dark, light, or follow the system. A theme is a file: import one, edit the
colours, export it, and hand it to somebody else. The typeface and the icon set
are bundled rather than fetched; Tailwind, Alpine and Chart.js still come from a
CDN, so a machine with no route out gets an unstyled page.

## What is not there yet

| Not there | Detail |
|---|---|
| More than one user | One account, no roles, no registration, no multi-factor, no password-reset flow. Reset means deleting a row and restarting. |
| Protection on a public network | Only sign-in is rate limited. There is no CORS allowlist and HTTPS is opt-in, so put it behind something if it faces the internet. |
| Key rotation | Changing `CREDENTIAL_KEY` makes existing device credentials unreadable and every device has to be re-entered. |
| Uptime Kuma | It has no management API, only a socket protocol, so it is listed and disabled rather than half-working. |
| Serial-over-USB UPSes | Only the HID power device class is read. Megatec and Voltronic units that answer `Q1` over a serial bridge are not supported. |
| Other DNS and proxy providers | Service publishing is Namecheap and Nginx Proxy Manager only, over HTTP-01. There is no DNS challenge. |
| Running with no internet access | Tailwind, Alpine and Chart.js load from a CDN at runtime. The typeface and icons are bundled, but the page is unstyled without a route out. |
| Routers and PDUs | Only through the generic SNMP adapter. There is no vendor adapter for either, and no device can be powered off through a PDU. |

## Configuration

These are the ones worth setting on the first run.

| Variable | Default | What it does |
|---|---|---|
| `ADMIN_PASSWORD` | `changeme` | Password for the account created on first start. Read only while there is no account. |
| `SESSION_SECRET` | generated | Signs the session cookie. Generated beside the database if unset. |
| `CREDENTIAL_KEY` | generated | Encrypts stored device credentials. Generated beside the database if unset. |
| `DB_PATH` | `/data/homelab.db` | Where the database lives. Needs setting when running from source. |
| `PORT` | `8080` | Port the container listens on. Publish the matching host port. |

Every variable, and what is set in the interface rather than the environment,
is in [`docs/configuration.md`](docs/configuration.md).

- The HTTP API, its authentication and every endpoint: [`docs/api.md`](docs/api.md).
- Setting up Nginx Proxy Manager, Namecheap, Portainer and Kuvasz: [`docs/integrations/`](docs/integrations).
- Symptoms, causes and fixes, including the per-vendor ones: [`docs/troubleshooting.md`](docs/troubleshooting.md).

## Source and licence

Source, issues and releases: <https://github.com/Spillebulle/HomeLab-Manger>

GNU General Public License v3.0, in [LICENSE](LICENSE). Archivo is bundled under
the SIL Open Font Licence. Icons are Lucide, under the ISC licence.
