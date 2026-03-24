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

## Docker Compose startup order

The **bot** uses `depends_on: lavalink` (start order only, not `service_healthy`). We **do not** ship a Lavalink `HEALTHCHECK` in this file: Coolify and some image variants lack `curl`/`wget`, and the YouTube plugin JAR download on first boot can exceed typical `start_period` windows—those cases were marking Lavalink **unhealthy** and blocking the bot from starting. Wavelink reconnects until the node is up. You can add a non-blocking health probe in Coolify if your image supports it.

## Coolify: environment overrides the repo

Coolify often sets Lavalink options in the UI (**Environment Variables** on the Lavalink service), not only from `docker-compose.yaml` in git. If logs still say:

`Downloading ... youtube-plugin-1.18.2.jar` → **FileNotFoundException**

then the server is still pinned to a **non-existent** JAR (1.18.2 is not published on `maven.lavalink.dev`). In Coolify, set:

`LAVALINK_PLUGINS_0_DEPENDENCY` = `dev.lavalink.youtube:youtube-plugin:1.18.0`

(or another version listed in `https://maven.lavalink.dev/releases/dev/lavalink/youtube/youtube-plugin/maven-metadata.xml`), save, and **redeploy** Lavalink. Until Lavalink boots cleanly, Wavelink will show `Connect call failed` or `name not known` for `lavalink:2333` because nothing is listening.

## Operational check

After deploy, Lavalink logs should show a successful plugin load and no `FileNotFoundException` on plugin JAR URLs. The bot logs should show the Wavelink node ready event.

## Bot container: Discord TLS / gateway errors

If bot logs show `ClientConnectorSSLError` or `SSL: TLSV1_UNRECOGNIZED_NAME` to `gateway-*.discord.gg:443`:

1. **Redeploy** after pulling the updated `Dockerfile` (explicit `ca-certificates`, `SSL_CERT_FILE`, etc.).
2. On the Coolify host, ensure nothing is **MITM / SSL-bumping** Discord (transparent proxies break SNI).
3. Do **not** point the bot at an `https_proxy` that intercepts Discord unless you trust its CA **inside** the image.
4. If errors persist only on this server, try from the host: `openssl s_client -connect gateway.discord.gg:443 -servername gateway.discord.gg -brief` — the handshake must succeed with a valid Discord cert chain.

Flaky gateway TLS often causes **voice join timeouts** afterward (`ChannelTimeoutException`): fix TLS/network first, then retest `-play`.

## Bot joins voice but you hear no audio

On Linux (including Docker), **discord.py needs a system Opus library** to encode audio. The bot image installs **`libopus0`** for this. If you built the image without it or use a custom base image, reinstall or add `libopus0`; otherwise the bot can **connect** to the voice channel with **silent playback**.

Rebuild/redeploy the bot after Dockerfile changes so the layer is applied.

Confirm inside the running bot container:

```bash
ls -l /usr/lib/*-linux-gnu/libopus.so.0
```

If that file is missing, Coolify is **not using** the repo `Dockerfile` build (wrong deploy type / stale cache). Force **rebuild without cache** or fix the build context.

