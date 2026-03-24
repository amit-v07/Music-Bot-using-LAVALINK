# Deploy: Lavalink + bot (Docker / Coolify)

## Configuration authority (do not drift)

| Runtime | Canonical Lavalink config | Parity requirement |
|--------|---------------------------|--------------------|
| **Docker Compose / Coolify** (this repo) | Environment variables on the **`lavalink`** service (`LAVALINK_PLUGINS_*`, `LAVALINK_SERVER_*`, `SERVER_PORT`, `_JAVA_OPTIONS`, …) | **`application.yml` must declare the same `youtube-plugin` version and Maven repository** as `docker-compose.yaml` so file-based runs and docs match production. |

If you change the YouTube plugin version, update **both** `docker-compose.yaml` (`LAVALINK_PLUGINS_0_DEPENDENCY`) and `application.yml` (`lavalink.plugins[].dependency`). Confirm the JAR exists under `https://maven.lavalink.dev/releases/dev/lavalink/youtube/youtube-plugin/` (see `maven-metadata.xml` for published versions).

## Bot → Lavalink

- **`LAVALINK_HOST`**: use the Compose **service name** (`lavalink`) when the bot container is on the **same** Compose network as Lavalink (typical Coolify single-stack deploy).
- **`LAVALINK_PORT`**: `2333` unless you change `SERVER_PORT` / `server.port`.
- **`LAVALINK_PASSWORD`**: must match Lavalink’s server password (`LAVALINK_SERVER_PASSWORD` in Compose / `lavalink.server.password` in YAML).

## Secrets

- Keep **Discord token**, **Google API keys**, and production Lavalink passwords in **Coolify secrets** or an untracked `.env`, not in git.
- Use `.env.example` as a template only.

## Docker Compose healthcheck

The `lavalink` service uses `GET /version` (unauthenticated in Lavalink v4) for `HEALTHCHECK`. The **bot** waits for `service_healthy` before starting, so first boot can take up to ~2 minutes while the YouTube plugin JAR downloads. The official **Ubuntu** Lavalink image includes `curl`; **Alpine/distroless** variants may need a different `healthcheck` command.

## Coolify: environment overrides the repo

Coolify often sets Lavalink options in the UI (**Environment Variables** on the Lavalink service), not only from `docker-compose.yaml` in git. If logs still say:

`Downloading ... youtube-plugin-1.18.2.jar` → **FileNotFoundException**

then the server is still pinned to a **non-existent** JAR (1.18.2 is not published on `maven.lavalink.dev`). In Coolify, set:

`LAVALINK_PLUGINS_0_DEPENDENCY` = `dev.lavalink.youtube:youtube-plugin:1.18.0`

(or another version listed in `https://maven.lavalink.dev/releases/dev/lavalink/youtube/youtube-plugin/maven-metadata.xml`), save, and **redeploy** Lavalink. Until Lavalink boots cleanly, Wavelink will show `Connect call failed` or `name not known` for `lavalink:2333` because nothing is listening.

## Operational check

After deploy, Lavalink logs should show a successful plugin load and no `FileNotFoundException` on plugin JAR URLs. The bot logs should show the Wavelink node ready event.
