---
phase: 2
plan: 1
wave: 1
must_haves:
  truths:
    - "docker-compose.yml includes the Python bot service so both start together"
    - ".env.example file exists with all required variables documented"
    - "LAVALINK_HOST defaults correctly for Docker networking (lavalink, not 127.0.0.1)"
    - "start.sh is updated or replaced with a Windows-compatible start script"
  artifacts:
    - path: "docker-compose.yml"
      provides: "Full stack startup (Lavalink + Bot)"
    - path: ".env.example"
      provides: "Environment variable documentation"
    - path: "start.ps1"
      provides: "Windows-native startup script replacing start.sh"
  key_links:
    - from: "docker-compose.yml lavalink service"
      to: "bot.py LAVALINK_HOST"
      via: "service name 'lavalink' used as hostname"
---

# Plan 2.1: Deployment — Docker Stack & Startup Scripts

## Objective
Right now, starting the bot requires two separate manual steps (Docker for Lavalink, then Python for the bot). Unify them and ensure the default config works out-of-the-box.

## Context
- `docker-compose.yml`
- `bot.py` — LAVALINK_HOST env var default
- `.env` / `.env.example`

## Tasks

<task type="auto">
  <name>Add bot service to docker-compose.yml</name>
  <files>docker-compose.yml</files>
  <action>
    Add a `bot` service to docker-compose.yml:
    ```yaml
    bot:
      build: .
      container_name: music_bot
      restart: unless-stopped
      env_file:
        - .env
      depends_on:
        - lavalink
      networks:
        - lavalink_network
    ```
    Also add a `Dockerfile` if it doesn't exist:
    ```dockerfile
    FROM python:3.12-slim
    WORKDIR /app
    COPY requirements.txt .
    RUN pip install --no-cache-dir -r requirements.txt
    COPY . .
    CMD ["python", "bot.py"]
    ```
    Update the default `LAVALINK_HOST` in `bot.py` from `"127.0.0.1"` to `"lavalink"` (the Docker service name) so it works out of the box when running with Docker Compose.
  </action>
  <verify>Select-String -Path "docker-compose.yml" -Pattern "music_bot"; Test-Path "Dockerfile"</verify>
  <done>docker-compose.yml has bot service, Dockerfile exists, bot.py LAVALINK_HOST default is "lavalink"</done>
</task>

<task type="auto">
  <name>Create .env.example and start.ps1</name>
  <files>.env.example, start.ps1</files>
  <action>
    Create `.env.example`:
    ```
    DISCORD_TOKEN=your_discord_bot_token_here
    LAVALINK_PASSWORD=hope_lost
    LAVALINK_HOST=lavalink
    LAVALINK_PORT=2333
    GOOGLE_API_KEY=your_google_api_key_here
    ```
    
    Create `start.ps1` for Windows users who don't use Docker for the bot:
    ```powershell
    # Start Lavalink via Docker Compose
    docker compose up lavalink -d
    Start-Sleep -Seconds 8
    
    # Start bot in new PowerShell window
    if (Test-Path ".venv") {
        Start-Process pwsh -ArgumentList "-NoExit", "-Command", ".\.venv\Scripts\Activate.ps1; python bot.py"
    } else {
        Start-Process pwsh -ArgumentList "-NoExit", "-Command", "python bot.py"
    }
    Write-Host "✅ Lavalink started in Docker. Bot starting in new window."
    ```
  </action>
  <verify>Test-Path ".env.example"; Test-Path "start.ps1"</verify>
  <done>.env.example with all 5 vars exists. start.ps1 that starts Lavalink via Docker then bot locally exists.</done>
</task>

## Success Criteria
- [ ] docker-compose.yml has bot service with depends_on lavalink
- [ ] Dockerfile exists
- [ ] LAVALINK_HOST default in bot.py is "lavalink"
- [ ] .env.example documents all required variables
- [ ] start.ps1 for Windows startup exists
