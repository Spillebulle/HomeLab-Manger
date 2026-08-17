# Portainer

Optional, and read-only. It fills in forward targets when publishing a service
and shows each service's container state. Configure it under Integrations.

## Settings

| Key | What it is |
|---|---|
| `base_url` | Address of the Portainer interface, for example `https://portainer.lan:9443`. |
| `api_key` | A Portainer API key. Stored encrypted, and blank on a later edit means keep the existing one. |
| `endpoint_id` | Optional. Restricts the app to one environment. Left empty, every environment is listed. |
| `docker_host_ip` | Optional. The address to suggest for containers on a locally socketed environment. Defaults to the host in `base_url`. |

## What it is used for

**Filling in a forward target.** The add, edit and import dialogs offer a
container dropdown. Picking a container fills in the address and the first
published port. Containers are listed across every environment, and the address
suggested is that environment's own host, taken from the environment's URL, so a
three-host setup suggests the right machine rather than always the same one.

**Showing state.** A service can be linked to a container, and the service list
then carries a chip coloured by the container's live state, linking through to
it in Portainer. The link is stored by container name rather than by id, so
recreating the container does not break it.

**Matching on import.** Importing a proxy host from Nginx Proxy Manager matches
it to a container automatically, by published port on the host address, then by
the container's network address, then by name.

An environment that is offline is skipped with a warning rather than failing the
whole listing.

## What it will not do

Nothing is ever written to Portainer. The app does not start, stop, recreate or
reconfigure containers, and the integration can be removed at any time without
affecting a published service beyond losing the state chip.
