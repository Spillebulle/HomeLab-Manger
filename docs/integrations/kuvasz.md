# Kuvasz

The uptime monitor the Monitoring page pushes devices and published services
into. Configure it under Integrations on that page.

## Settings

| Key | What it is |
|---|---|
| `provider` | `kuvasz`. The monitoring integration is provider-pick, so this chooses which tool the other keys belong to. |
| `base_url` | Address of the Kuvasz instance. |
| `api_key` | A Kuvasz API key. Stored encrypted, and blank on a later edit means keep the existing one. |

Kuvasz version 2 or later is required, because the management API this uses is
the version 2 REST API.

## What a monitor holds

| Field | Default | Notes |
|---|---|---|
| Source | none | A device, a published service, or nothing. Deleting the source leaves the monitor in place with no source rather than deleting it. |
| Target address | suggested | The address Kuvasz checks. |
| Interval | 60 seconds | How often Kuvasz checks. Required by Kuvasz on creation. |
| SSL check | off | Whether Kuvasz also checks the certificate. |
| Notification channels | none | Kuvasz's own channels, chosen from a list read live. |
| Status pages | none | Which of your Kuvasz status pages the monitor appears on. |
| Enabled | on | Turning it off pauses checking without deleting anything. |

A source can carry more than one monitor. The picker dims entries already in use
rather than hiding them.

## Order of operations

Creating a monitor creates it in Kuvasz first, with its notification channels
applied at the same time, so a failure leaves nothing behind here. Status pages
are added afterwards, and if that step fails the monitor is marked with the
error and Save tries again.

Renaming a monitor also re-points every status page it appears on, because a
status page refers to a monitor by its name rather than by an id.

## Reversing it

Everything is reversible from the edit dialog. Clear the notification channels
to stop it notifying. Remove a status page to take it off that page. Turn it off
to pause it. Delete removes it from its status pages and then deletes it in
Kuvasz, and there is a delete that unlinks the row here while leaving the Kuvasz
monitor untouched.

## Uptime Kuma

Not implemented. Uptime Kuma has no management REST API: everything goes over a
socket protocol, and the API keys it issues only unlock a metrics endpoint, so
they cannot create a monitor. It appears in the provider dropdown, disabled, so
the reason it is absent is visible rather than mysterious.
