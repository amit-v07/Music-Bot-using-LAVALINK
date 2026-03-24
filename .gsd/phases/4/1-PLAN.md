---
phase: 4
plan: 1
wave: 1
must_haves:
  truths:
    - "Lavalink runs as a persistent Coolify service with correct application.yml volume"
    - "Bot runs as a separate Coolify service using the built Docker image"
    - "Environment variables (DISCORD_TOKEN, LAVALINK_*, GOOGLE_API_KEY) are set via Coolify UI"
    - "Both services restart automatically on crash or server reboot"
    - "Bot connects to Lavalink using the Coolify internal network hostname"
  artifacts:
    - path: "docker-compose.yml"
      provides: "Coolify-compatible stack definition"
    - path: "application.yml"
      provides: "Lavalink server configuration"
    - path: "Dockerfile"
      provides: "Bot container image"
  key_links:
    - from: "bot service LAVALINK_HOST env var"
      to: "lavalink service hostname"
      via: "Coolify internal network"
---

# Plan 4.1: Coolify Home Server Deployment

## Objective
Deploy the Music Bot stack to a home server running Coolify. Coolify supports Docker Compose deployments from GitHub — we point it at this repo and configure environment variables in its UI. The key challenge is making both services discoverable to each other inside Coolify's Docker network.

## How Coolify Works (Context)
- Coolify connects to your GitHub repo and deploys via Docker Compose
- Each service in docker-compose.yml becomes a Coolify-managed container
- Environment variables are set per-service in the Coolify dashboard (NOT from .env files)
- Services on the same Compose stack can reach each other by service name (e.g. `lavalink`)
- Coolify's `restart: unless-stopped` maps to "restart on crash + server reboot"

## Tasks

<task type="checkpoint:human-verify">
  <name>Deploy via Coolify Dashboard</name>
  <files>docker-compose.yml, application.yml, Dockerfile</files>
  <action>
    Follow these steps in the Coolify dashboard on your home server:

    **Step 1 — Create a new Resource**
    1. Go to your Coolify dashboard → **Projects** → your project
    2. Click **+ New Resource** → **Docker Compose** → **From GitHub**
    3. Select this repository: `amit-v07/Music-Bot-using-LAVALINK`
    4. Branch: `main`
    5. Coolify will detect `docker-compose.yml` automatically

    **Step 2 — Configure Environment Variables**
    After creating the resource, in the **Environment Variables** tab, add these for the `bot` service:
    ```
    DISCORD_TOKEN=<your actual token>
    LAVALINK_HOST=lavalink
    LAVALINK_PASSWORD=hope_lost
    LAVALINK_PORT=2333
    GOOGLE_API_KEY=<your actual key>
    ```
    ⚠️ `LAVALINK_HOST=lavalink` (the Docker service name) — this is already the default in bot.py

    **Step 3 — Deploy**
    Click **Deploy**. Coolify will pull the repo, build the bot image, pull the Lavalink image, and start both containers on the same internal network.

    **Step 4 — Verify**
    - In Coolify, check both `lavalink` and `music_bot` containers show **Running**
    - Check bot logs for: `Bot connected as ... Lavalink Node connected successfully!`
    - Test in Discord: `-play <song name>`
  </action>
  <verify>
    Check Coolify container logs for:
    - lavalink: `Lavalink is ready to accept connections`
    - bot: `Lavalink Node connected successfully!`
  </verify>
  <done>Both containers are Running in Coolify and bot plays music in Discord voice channel</done>
</task>

## Notes
- The `application.yml` volume mount (`./application.yml:/opt/Lavalink/application.yml`) works in Coolify because it mounts from the repo root, which Coolify clones locally
- If Coolify uses a different build path, you may need to set the **Build Context** to `.` in Coolify settings
- If bot can't reach Lavalink on first boot, restart the bot service from Coolify dashboard (Lavalink may have taken longer to start than `depends_on` allows)

## Success Criteria
- [ ] `lavalink` container running in Coolify
- [ ] `music_bot` container running in Coolify
- [ ] Bot logs show successful Lavalink node connection
- [ ] `-play <song>` works in Discord
