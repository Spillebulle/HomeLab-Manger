# Troubleshooting

Symptoms you are likely to hit, what usually causes them, and what to do. Most
of these are quirks of the hardware rather than of the app, which is why the
answer is often a setting on the device.

Before anything else: the container log names the device and the failing probe
on every poll error, and the Test connection button in the add or edit dialog
probes each service the adapter needs and reports which ones answered.

## Any device

| Symptom | Likely cause | What to do |
|---|---|---|
| Device card is red and no error is obvious | The poll failed. Poll warnings are logged with the host, the OID and the community. | Read the container log. If every probe failed, the device is unreachable, the community is wrong, or an ACL is blocking you. |
| A reading looks a minute out of date | Reads come from the cache, which the background poller fills. The default interval is 60 seconds. | Press Refresh for an immediate poll, or lower the device's poll interval in its edit dialog. |
| The card still shows a reading while the device is plainly down | A failed poll keeps the last good reading and only records the error, so the value does not vanish. | Check the "last seen" time, which only moves on a successful poll. |
| Sign-in returns 429 | Five failed sign-ins from one address inside 5 minutes locks that address out. | Wait for the time in the `Retry-After` header, or restart the app, which clears the counter. |

## Switches

| Symptom | Likely cause | What to do |
|---|---|---|
| D-Link DGS-3120: the PoE tab is empty | This firmware exposes no PoE data over SNMP at all, so the adapter reads it over SSH instead. | Give the device SSH credentials. Without them there is no PoE data to show. |
| D-Link: SSH keeps failing although the password is right | Web access does not imply SSH access on this switch, and the local password database can fall out of step. | On the switch, run `config ssh user <name> authmode password`, confirm the account exists with `show account`, then `config account <name>` to re-set the password. |
| D-Link: the overview always says the address is manual | The firmware reports every address as statically configured over SNMP, whatever it actually is. | Nothing to fix. With SSH credentials the adapter reads the real state from `show ipif` instead. |
| D-Link: a VLAN change is gone after a reboot | A change that is not saved lives only in the running configuration. | Nothing to fix in current versions. Every VLAN action saves the configuration in the same session. |
| D-Link: the switch refuses a VLAN change | The switch enforces its own rules, for instance a port cannot be tagged on a VLAN where it is already untagged. | The switch's own message is shown in the interface. Act on that, not on a retry. |
| HPE OfficeConnect 1820: the device never comes up | SNMP is off by default on this switch. | In the switch's web interface, enable SNMPv1/v2 and add a community, then use it in the device's credentials. |
| HPE 1820: writes start failing, sign-in returns 503 | The switch caps active web sessions at about three and they do not expire quickly. | Close any browser tabs holding the switch's web interface open, and wait a few minutes. |
| Connected devices list has ports and MAC addresses but no IP addresses | A switch only learns an address if that host talked to the switch itself, which is rarely. | Expected. The vendor comes from the IEEE registry and does not need an address. |
| A connected device shows no vendor | Locally administered MAC addresses, such as private Wi-Fi addresses, are not in any registry. | Nothing to fix. |

## Servers and BMCs

| Symptom | Likely cause | What to do |
|---|---|---|
| Cisco CIMC: "Maximum sessions reached" | CIMC allows four sessions in total across the web interface, the API and SSH. | Close the CIMC web interface. The app releases its own session after every poll. |
| CIMC: the Sensors tab is thin and says its source is `xmlapi` | IPMI over LAN is disabled on the BMC, so the app falls back to the small set of readings the XML API exposes. | Enable Admin, Communication Services, IPMI over LAN. Fan speeds and per-DIMM temperatures then appear. |
| CIMC: the KVM viewer reports a 403 on a `.jar` | Firmware 3.0 and later rejects the HEAD request Java Web Start makes against cached files. | Use the `cimc_redfish` adapter for firmware 3.0 and later. It serves the KVM files through the app, which works around the firmware. |
| CIMC: the KVM viewer says the sign-in failed or timed out | The KVM tokens are tied to the session that minted them, and the viewer took too long to present them. | Launch the file promptly after downloading it. |
| A Huawei iBMC is rejected with a session error | iBMC refuses HTTP basic authentication. | Set the adapter type to `ibmc` rather than `redfish`. |
| iBMC: the CPU is called "Central Processor", DIMMs have no type, the model is a marketing name | The Redfish version on this firmware carries none of that. The app reads it from the vendor's SNMP tables instead. | Enable SNMPv3 in the iBMC web interface. The Redfish user works as the SNMP user by default, or set the SNMP credentials on the device. |
| A power action is missing on a server | Not every firmware offers every action. Cisco CIMC before 3.0 has no graceful shutdown, and switches have none at all. | Use the actions the device offers. The shutdown plan only lists devices that can actually power off. |

## UPS

| Symptom | Likely cause | What to do |
|---|---|---|
| "No USB HID Power Device found" although the UPS is plugged in | The container cannot see the UPS's `/dev/hidrawN` node, usually because only `/dev/bus/usb` was mounted or a single device was mapped. | Run the container with `--privileged -v /dev:/dev:ro`. Call `GET /api/devices/{id}/usb-diagnostics` to see which nodes the container has. |
| The UPS works and then goes offline after some idle time | The kernel suspended the UPS's USB interface and the device did not resume. | Nothing to fix in current versions. The adapter disables autosuspend before every read and resets a wedged device at most once every 5 minutes. |
| A single reading on the graph spikes or dips absurdly | Some UPS stacks return torn or wrong-report data under load. | Upgrade to 0.6.2 or later, which rejects those reads. Outage detection deliberately stays unfiltered, so a real power cut still triggers the shutdown plan at once. |
| Watts look far too low or far too high | The UPS reports load as a percentage and no real power, so watts are derived from the rated power you entered. | Set Rated Power on the device to the unit's real rating. |
| The UPS is found but no readings decode | The unit is probably a serial-over-USB model rather than a HID power device. | Check `usb-diagnostics`. If it lists no power device usages, this adapter cannot read it and there is no alternative in the app yet. |
| A machine was shut down more than once during one outage | Should not happen. Each rule fires once per outage and re-arms only when mains returns. | Use Test plan, which walks the plan and notifies without powering anything off. |

## Services and monitoring

| Symptom | Likely cause | What to do |
|---|---|---|
| Namecheap says the API key is invalid or API access is not enabled | The message is misleading. It also appears for the wrong account username and for a source address that is not whitelisted. | Check the username is the account sign-in name, and whitelist the address the app connects from. |
| The app refuses to write DNS records for a domain | The zone holds a record type the app cannot reproduce faithfully, such as SRV or CAA, and every write replaces the whole zone. | Manage that domain by hand, or remove the unsupported records. |
| A service is stuck at "provisioning" | The app restarted while the pipeline was running. | Press Retry. Steps that already succeeded are skipped, and existing proxy hosts and certificates are adopted rather than duplicated. |
| The certificate step fails but the site works over HTTP | The proxy host is created before the certificate on purpose, so a failed issuance still leaves a working route. | Confirm the domain resolves to your public address and that ports 80 and 443 reach Nginx Proxy Manager, then press Retry. |
| Deleting a service returns an error and the service stays | One of the remote objects could not be removed. | The message names what is left. Fix it and delete again, or use the forced delete the dialog offers to remove the row only. |
| Uptime Kuma cannot be selected as a monitoring provider | Uptime Kuma has no management API. Everything is a socket protocol, and its API keys only unlock metrics. | Use Kuvasz, which is the implemented provider. |
