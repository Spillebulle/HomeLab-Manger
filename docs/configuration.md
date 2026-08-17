# Configuration

Every environment variable the app reads, what it defaults to, and when you
would change it. There is no configuration file: the app is configured by
environment variables and by the settings you enter in the interface.

## Environment variables

| Variable | Default | What it does |
|---|---|---|
| `DB_PATH` | `/data/homelab.db` | Path to the SQLite database. The directory also holds the generated session secret, the credential key and the cached OUI registry. |
| `PORT` | `8080` | Port uvicorn listens on inside the container. Read by the container start command, not by the Python code, so it only applies to the image. |
| `ADMIN_USERNAME` | `admin` | Username created on first start. |
| `ADMIN_PASSWORD` | `changeme` | Password created on first start. |
| `SESSION_SECRET` | generated | Key that signs the `homelab_session` cookie. |
| `CREDENTIAL_KEY` | generated | Fernet key that encrypts stored device credentials at rest. |
| `POLL_INTERVAL` | `60` | Seconds between background polls, for devices with no per-device interval set. |
| `METRICS_RETENTION_DAYS` | `30` | Days of time-series history kept for the graphs. `0` keeps everything. |

### When to change each one

**`DB_PATH`** needs setting when you run from source rather than from the
image, because `/data` does not exist on a development machine. In the
container, leave it alone and mount a volume at `/data` instead.

**`PORT`** matters when the host cannot publish 8080. Set it and publish the
matching port, for example `-e PORT=9000 -p 9000:9000`. `EXPOSE 8080` in the
`Dockerfile` is documentation and does not override this.

**`ADMIN_USERNAME` and `ADMIN_PASSWORD`** are read only while the `auth_users`
table is empty, which in practice means the very first start. Setting them on a
later restart does nothing. Leaving `ADMIN_PASSWORD` unset creates the account
with the password `changeme` and logs a warning. To reset a forgotten password,
stop the app, delete the row (`DELETE FROM auth_users;` against the SQLite
file), set `ADMIN_PASSWORD` and start again.

**`SESSION_SECRET`** is worth setting explicitly for anything long-lived. If it
is unset, a random secret is generated on first start and written to
`.session_secret` beside the database, so sessions survive a restart as long as
that file does. Lose the file and everybody is signed out.

**`CREDENTIAL_KEY`** works the same way, with a generated key at
`.credential_key` beside the database. Changing or losing it makes every stored
device credential undecryptable: the app stays up, logs an error per device and
returns an empty credential set, and you have to re-enter each device's
credentials by hand. There is no key-rotation path, so set it once, from a
secret store, or leave the generated file alone.

**`POLL_INTERVAL`** is the fallback cadence. Each device can override it in the
add or edit dialog, which is the better place to slow a device down. The
per-device value is clamped to a 5 second minimum. Raise the global default if
you have many devices and the log fills with poll warnings.

**`METRICS_RETENTION_DAYS`** trades disk for history. Samples are written once
per poll for every numeric reading a device reports, so a 5 second UPS interval
over 30 days is a lot more rows than a 60 second one.

## What is configured in the interface, not here

| Setting | Where |
|---|---|
| Device hostname, credentials, adapter, poll interval | Add or edit a device |
| API keys | Account area, the `</>` icon |
| Discord webhook and which events notify | Notifications tab on a device |
| UPS shutdown plan: targets, order, thresholds, delays | Shutdown tab on a UPS |
| Nginx Proxy Manager, Namecheap, Portainer and monitoring credentials | Integrations on the Services and Monitoring pages |
| Dark, light or follow the system | The theme control, stored in the browser rather than on the server. See [`ui-conventions.md`](ui-conventions.md). |

Integration credentials are encrypted with the same key as device credentials.

## Container storage

The `/data` volume holds four things that must survive a restart.

| File | Loss means |
|---|---|
| `homelab.db` | Everything: devices, history, services, monitors, the admin account. |
| `.session_secret` | Everybody is signed out on the next start. |
| `.credential_key` | Stored device credentials can no longer be decrypted. |
| `oui.csv` | Nothing lasting. The MAC vendor registry is refetched from IEEE, and a bundled copy is used until it arrives. |

## USB passthrough for a UPS

The `usbups` adapter reads the UPS through its `/dev/hidrawN` node, and that
node changes when the UPS re-enumerates. Bind the whole of `/dev` read-only and
run the container privileged:

```bash
docker run --privileged -v /dev:/dev:ro ...
```

Binding only `/dev/bus/usb`, or mapping a single `--device`, snapshots the node
list at container start and the UPS disappears the first time it re-enumerates.
Network-only installations do not need either flag. If a UPS is not found,
`GET /api/devices/{id}/usb-diagnostics` reports which device nodes the
container can actually see.

## Themes

Themes are files, not settings. The library is a directory beside the database:

| Path | What it is |
|---|---|
| `<DB_PATH dir>/themes/` | One `.umbertheme` file per theme you have imported or made. Ordinary files; copy them out or hand them to somebody. |

Nothing shipped lives there. Graphite and Paper are compiled into the app and are
read-only, so an update can never replace something you edited. Deleting the
directory loses your themes and nothing else; the app falls back to Graphite.

The format is shared with the other apps built to the same design principles, so
a theme moves between them unchanged. `docs/ui-conventions.md` covers what the
interface is made of.
