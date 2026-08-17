# Changelog

What changed in each release, newest first. Every version listed here has a
matching `vX.Y.Z` tag and a published container image.

## 0.8.0

2026-08-17

- The whole interface has been redesigned to one visual language: a shared
  palette of cool greys with a single accent, a bundled typeface, a stroke icon
  set, and a denser layout. Selection is a neutral fill with a small accent
  mark, so the accent now only ever means selected, in hand, or primary.
- Dark, light, or follow the system, remembered between visits. The light theme
  is complete on every screen, not just the dashboard.
- Themes are files. Import one, edit its colours, export it, and hand it to
  somebody else. The `.umbertheme` format is shared with the other apps built to
  the same design principles, so a theme moves between them unchanged. Graphite
  and Paper ship built in and are read-only; your own live beside the database.
- Charts redrawn to the same rules: a hairline grid, the single series in the
  accent, and a real gap where polling stopped rather than a line drawn across
  it.
- Switch front panels show each port as a neutral tile with a state dot instead
  of a full colour fill per port, so a glance reads link state without decoding
  a wall of colour.
- Font Awesome is gone. Icons and the typeface are now bundled rather than
  fetched, though Tailwind, Alpine and Chart.js still load from a CDN.
- The README, the docs and every screenshot have been rebuilt. Screenshots are
  now generated from the running app, so they cannot quietly go stale.

## 0.7.0

2026-06-27

- New Monitoring page. Register a device or a published service as a monitor in
  an external uptime monitor and see its live up or down state.
- Manage a monitor without leaving the page, and reverse any of it: assign or
  clear notification channels, add or remove it from status pages, pause it,
  delete it, or unlink it and leave the remote monitor alone.
- Monitoring is a provider-pick integration with its own dropdown. Kuvasz is
  implemented. Uptime Kuma is listed and disabled, because it has no management
  API to drive.
- A source can carry more than one monitor. The Services container picker and
  the monitor source picker dim entries already in use rather than hiding them.

## 0.6.3

2026-06-20

- Outage safety. A shutdown rule now claims its once-per-outage guard before it
  fires, so a database hiccup during an outage cannot power off the same machine
  again and again.
- Live updates are steadier. The connection no longer reconnects in a loop after
  sign-out, one stuck browser tab no longer stalls updates for everybody, rapid
  device switching cannot show the previous device's data, and UPS charts are
  cleaned up when you navigate away.
- DNS safety. The app refuses to rewrite a zone containing record types it
  cannot reproduce faithfully, such as SRV or CAA, rather than risk losing them.
- Lighter polling. Server and BMC adapters reuse one connection per cycle, and
  the device list is read in a single query.
- Hardening across sign-in, credential-key creation, connection tests, servers
  with special characters in the password, and request validation.

## 0.6.2

2026-06-20

- Filtered out spurious single-poll spikes and dips in USB UPS readings, such as
  a voltage of 8932 or a charge dropping from 100 to 80 for one poll. Some UPS
  stacks return torn or mismatched data under load.
- Outage detection deliberately stays unfiltered, so a real power cut still
  triggers the shutdown plan immediately.

## 0.6.1

2026-06-12

- The Namecheap domain field accepts a comma-separated list. A service picks its
  domain when created, and changing it re-provisions the record and certificate.
- Per-service DNS control. Choose CNAME or A and a custom target for one service
  instead of the global default. Changing it replaces the record in place.
- A DNS manager on the Services page. View every record for a domain, add
  standalone A and CNAME records, and delete with an exact-match check. Records
  owned by a service are flagged and protected.

## 0.6.0

2026-06-12

- New Services page. One form publishes an internal app at
  `https://name.your-domain`: the Namecheap record, the Nginx Proxy Manager host
  and the Let's Encrypt certificate are provisioned in order, with per-step
  status and retry.
- Import existing proxy hosts through a prefilled dialog, edit a service's
  forward target and settings, rename it with automatic DNS and certificate
  re-provisioning, or unlink it without deleting anything remote.
- Read-only Portainer integration. The container dropdown fills in the forward
  address and port across several Docker hosts, services show live container
  state, and imports match containers automatically.
- Every Nginx Proxy Manager setting per service: WebSockets, block exploits,
  cache assets, force SSL, HTTP/2, HSTS and HSTS subdomains.
- The service list is compact and grouped by Docker host, with filtering.
- Integration credentials are stored encrypted and can be tested live.

## 0.5.9

2026-06-03

- UPS graphs use a real time axis, so a gap in polling shows as a gap, and gained
  a custom from and to range picker alongside the presets.
- Much quieter logs. Third-party request logging was dropping the full URL of
  every request, which put the Discord webhook address in the log in plain text.
- New `/healthz` endpoint and a container health check, so orchestration can
  restart a wedged container by itself.
- Sign-in locks out after repeated failures from the same address.
- The shutdown plan gained device ordering, a per-device delay, a dry-run Test
  plan that previews and notifies without powering anything off, and an event
  when the rules re-arm as power returns.
- Switch port actions are validated against command injection.
- Polls in flight are cancelled cleanly when the app stops.

## 0.5.8

2026-06-01

- New `GET /api/devices/{id}/graph` endpoint in a flat shape that charting tools
  read directly, for Grafana, Metabase and the like.
- Every timestamp the API returns is now UTC with a `Z` suffix, which fixes
  time-shifted graphs in outside tools and wrong times in the interface.
- Device action endpoints return real status codes, 400 for an unsupported
  action and 502 for a device failure, instead of always returning 200.
- New full HTTP API reference covering authentication, API keys, every endpoint,
  device actions and credential keys.

## 0.5.7

2026-06-01

- The D-Link DGS-3120 overview shows switch temperature.
- The shutdown plan only offers devices that can actually power off. Switches are
  excluded and unsupported actions are refused instead of failing silently.
- Better USB UPS recovery and diagnostics: a clearer message when the UPS is on
  the bus but cannot be opened, a diagnostics endpoint reporting which device
  nodes the container can see, and the USB reset now logs which device it reset.

## 0.5.6

2026-06-01

- API keys. Generate one in the interface and authenticate with a bearer token
  or an `X-API-Key` header.
- UPS outage orchestration. Pick the devices to protect and shut them down
  gracefully, or power them off, at a charge or runtime threshold. Each rule
  fires once per outage and re-arms when mains returns.
- An event log and Discord notifications per device, covering device offline, UPS
  state change and shutdown actions.
- A wedged USB UPS is reset at most once every 5 minutes, so it can recover
  instead of re-enumerating endlessly.

## 0.5.5

2026-06-01

- USB autosuspend is disabled, which was the main cause of a USB UPS dropping
  offline after sitting idle.
- A wedged USB UPS is recovered with a bus reset instead of staying offline until
  the container restarts.
- Per-device poll interval, default 60 seconds, minimum 5. A slow device no
  longer holds up a fast one.
- The add-device dialog explains the container and USB passthrough a device needs.

## 0.5.4

2026-05-31

- An offline UPS shows its last known reading under an offline banner instead of
  going blank.
- A failed poll keeps the last good reading for every device type. Last seen now
  means the last successful contact, so an offline device no longer reads as
  updated just now.

## 0.5.2

2026-05-31

- Fixed UPS watts, which read about 7 W instead of about 850 W. They are derived
  from load and the rated power you enter, and a UPS that reports real power is
  still preferred.
- Fixed the UPS intermittently reporting no device found when a poll overlapped a
  manual refresh or a diagnostics call.

## 0.5.1

2026-05-31

- Fixed USB UPS decoding. The test unit flags its live readings in a way the
  parser was skipping, so only 6 of 45 fields decoded. All readings now populate.
- Ignored the firmware's nonsensical scaling, which turned 230 V into 2.3 billion.
- Relabelled the nominal mains voltage, which was wrongly shown as battery.

## 0.5.0

2026-05-31

- USB-connected UPS support. A new adapter reads any standard HID power device
  UPS over USB, with no NUT required: load, watts, battery charge and runtime.
- A new UPS view with live state, online, on battery or low battery, and cards
  for charge, runtime, load and power draw.
- A Graphs tab charting load, watts, charge, runtime and input voltage over 1
  hour, 6 hours, 24 hours or 7 days.
- Time-series storage with configurable retention and a history endpoint.
- A USB diagnostics endpoint to confirm whether a UPS model is covered.

## 0.4.5

2026-05-29

- Fixed a memory leak that grew container memory into gigabytes and pinned a CPU
  core at 100 % over time on installations with a Huawei iBMC.

## 0.4.4

2026-05-14

- Device credentials are encrypted at rest. Existing plain rows are migrated on
  the first start.
- Editing a device pre-fills its credentials. Secrets stay unchanged unless you
  type over them.
- A Test connection button and a service-requirements tooltip in the add and edit
  dialog, probing each service the adapter needs and reporting what answered.
- Saving a device runs the same test and reports anything unreachable at once.
- Fixed the adapter dropdown showing the wrong selection when editing a device.
- Tidier device cards: noisy descriptors trimmed, manufacturer and model shown
  for servers, serial dropped.

## 0.4.3

2026-05-13

- Fixed the database locking cascade introduced in 0.4.2. The database is now
  opened in a mode where writers do not block readers, and the poller commits
  after each reading instead of holding a write open for a whole poll cycle.

## 0.4.2

2026-05-13

- An empty SNMP community now falls back to the conventional default instead of
  silently timing out and showing the device as failed with no error.
- SNMP failures are logged with the host and the community, plus a summary when
  every probe fails, so a wrong community can be told from an unreachable device.
- Fixed duplicate cache rows, which are cleaned up automatically on first start.

## 0.4.1

2026-05-13

- The container's listen port can be overridden with `PORT`, for hosts that
  cannot publish 8080.

## 0.4.0

2026-05-13

- New HPE OfficeConnect 1820 adapter. SNMP for status, ports, PoE, VLANs and the
  MAC table, and the switch's web interface for writes.
- The adapter dropdown filters by device type, and snaps to a valid choice when
  the device type changes.
- PoE state is cleaner. Idle ports no longer show as searching, so the front
  panel highlights the ports actually drawing power.
- PoE ports sort numerically rather than alphabetically.

## 0.3.1

2026-05-10

- Pinned the SSH library so connections to legacy switches and servers keep
  negotiating. A newer release dropped the algorithms the DGS-3120 needs.
- SSH negotiation is logged before each handshake, and SSH errors now appear in
  the app's own log.

## 0.3.0

2026-05-10

- New adapter for Cisco UCS C-series running CIMC 3.0 and later, using Redfish
  for status, CPU, power and sensors, and the older interface for the inventory
  Redfish does not expose on that firmware.
- Fields the older adapter could not reach: BIOS version, BMC firmware and
  address, PSU firmware, part number and line voltage, and a voltage panel.
  Sensors no longer need IPMI over LAN.
- KVM works on CIMC 3.0 and later, around a firmware fault that broke Java Web
  Start.
- Switch and router cards match the styling of server cards.

## 0.2.1

2026-05-08

- Fixed the D-Link DHCP state, which always read as disabled because the switch
  reports it wrongly over SNMP.
- The switch overview shows address, subnet mask, gateway, DHCP state, MAC,
  firmware and serial, and uptime lost its fractional seconds.
- The server overview shows the BMC address and firmware, and the real hardware
  model on Huawei rather than the marketing name.
- The hardware tab lists PCIe cards on Huawei, and the storage controller shows
  its real model instead of the word Storage.
- The power tab shows PSU model, manufacturer, type, firmware and line voltage.
- Fixed Cisco disks showing no model, serial or size.

## 0.2.0

2026-05-08

- A Connected tab on switches, listing MAC, port, vendor and address for every
  learned device.
- Address, subnet mask, gateway, DHCP state, MAC, firmware and serial on the
  switch overview.
- A version widget with links to the repository and Docker Hub.
- The full IEEE registry, about 40 000 entries, replaced the small built-in
  vendor table, and refreshes itself.
- Renamed from HomeLab Manager to HomeLab Manger.
- Fixed the VLAN dialog opening by itself when switching between tabs.

## 0.1.0

2026-05-08

- First release. A single process serving the interface and the JSON API, backed
  by SQLite, with a background poller and adapters for generic SNMP, D-Link
  switches, Cisco CIMC and Redfish servers, behind a single-user sign-in.
