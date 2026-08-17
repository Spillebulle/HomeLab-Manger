# Nginx Proxy Manager

Where a published service's route comes from. Configure it on the Services page,
under Integrations.

## Settings

| Key | What it is |
|---|---|
| `base_url` | Address of the Nginx Proxy Manager admin interface, for example `http://npm.lan:81`. |
| `email` | Administrator sign-in address. |
| `password` | Administrator password. Stored encrypted, and blank on a later edit means keep the existing one. |
| `le_email` | Address Let's Encrypt registers certificates against. |

Test connection signs in and reports whether the credentials work.

## What the app does with it

Creating a service creates a proxy host for `subdomain.domain` pointing at the
forward address and port you gave, then requests a Let's Encrypt certificate and
attaches it. The host is deliberately created without the certificate first, so
a failed issuance still leaves a working HTTP route rather than nothing.
Certificate issuance is retried three times, 25 seconds apart, to ride out DNS
propagation.

Editing a service pushes the forward target and the seven per-service switches
back to the host: WebSockets, block exploits, cache assets, force SSL, HTTP/2,
HSTS and HSTS subdomains. The SSL switches are only sent once a certificate is
attached, because the host rejects them before that.

Renaming a service rewrites the host's domain list in place, keeping any extra
domains the host serves, and issues a fresh certificate, because a Let's Encrypt
certificate cannot be renamed.

## Importing what is already there

The Services page lists proxy hosts that exist in Nginx Proxy Manager but are
not managed here, with an Import button. Import opens the normal dialog
prefilled from the host, so you can correct the forward target before it is
adopted. Import adopts the host in place: it is not recreated, its custom
configuration is left alone, and its DNS record is assumed to exist already, so
deleting the service later will not remove a record the app did not create.

A host imported without a certificate finishes at the certificate step, and
Retry issues one.

## What it will not do

- It will not change a host's domain list except during a rename.
- It will not delete a certificate it did not create, because a wildcard
  certificate may be shared with hosts it knows nothing about.
- There is no support for a DNS challenge. Issuance is HTTP-01, so the domain
  must resolve to your public address with ports 80 and 443 reaching Nginx Proxy
  Manager.

Both the modern certificate API, from version 2.12, and the older one are
handled, so the version you run should not matter.
