# Namecheap

Where a published service's DNS record comes from, and what the DNS manager on
the Services page reads and writes. Configure it under Integrations.

## Settings

| Key | What it is |
|---|---|
| `api_user` | The API user Namecheap issued. |
| `api_key` | The API key. Stored encrypted, and blank on a later edit means keep the existing one. |
| `username` | Your account sign-in name. Often the same as `api_user`, and often the reason a key appears to be rejected when it is not. |
| `client_ip` | The address the app connects from. It must be whitelisted in Namecheap, and Namecheap checks it against the real source address. |
| `domain` | One domain, or several separated by commas. The first is the default offered to a new service. |
| `record_type` | Optional. `CNAME` by default. |
| `record_target` | Optional. The default target for new records. |

API access has to be enabled on the account before any of this works.

## Before you enable it

Namecheap has no call that adds a single record. The only write it offers
replaces the domain's entire record set, so every change here is a read, a
modification and a full rewrite. Three rules follow from that, and they are
enforced:

- Nothing is written unless the preceding read succeeded and the domain is
  actually using Namecheap's own nameservers.
- Nothing is written if the zone contains a record type the app cannot reproduce
  faithfully, which means anything outside A, AAAA, CNAME, ALIAS, NS, TXT, MX,
  URL, URL301 and FRAME. An SRV or CAA record in the zone therefore blocks
  writes to that domain until it is removed, because rewriting it would silently
  drop the fields the app does not carry.
- The domain's email-forwarding mode is read and sent back unchanged, because
  omitting it resets it.

## Per-service records

A service uses the default record type and target unless you override them on
the service itself. The override is also the record of what was actually
written, so deleting a service removes exactly the record it created, even if
the defaults changed since.

Changing the override on an existing service removes the old record and creates
the new one. A change that resolves to the same record is skipped.

## The DNS manager

The Services page has a collapsed DNS section listing every record for a domain.
You can add A and CNAME records and delete them. Other types are shown but not
editable. Deleting requires an exact match on name, type and address, so a typo
cannot remove a different record, and a record owned by a service is flagged and
refused, because the service owns it.

## Error 1011102

Namecheap returns "API Key is invalid or API access has not been enabled" for at
least three different problems: a wrong key, a wrong account username, and a
source address that is not whitelisted. Check all three before assuming the key
is wrong.
