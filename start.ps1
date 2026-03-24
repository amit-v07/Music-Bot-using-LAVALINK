# start.ps1 — Windows startup script for Music Bot
# Starts Lavalink via Docker, then launches the bot locally

# Start Lavalink via Docker Compose
Write-Host "Starting Lavalink via Docker..." -ForegroundColor Cyan
docker compose up lavalink -d

# Wait for Lavalink to warm up
Write-Host "Waiting 8 seconds for Lavalink to warm up..." -ForegroundColor Yellow
Start-Sleep -Seconds 8

# Start bot in a new PowerShell window
Write-Host "Starting Discord Bot..." -ForegroundColor Cyan
if (Test-Path ".venv") {
    Start-Process pwsh -ArgumentList "-NoExit", "-Command", "& { .\.venv\Scripts\Activate.ps1; python bot.py }"
} else {
    Start-Process pwsh -ArgumentList "-NoExit", "-Command", "& { python bot.py }"
}

Write-Host ""
Write-Host "✅ Lavalink running in Docker. Bot starting in a new window." -ForegroundColor Green
Write-Host ""
Write-Host "Useful commands:" -ForegroundColor White
Write-Host "  Stop Lavalink  : docker compose down" -ForegroundColor Gray
Write-Host "  View logs      : docker compose logs -f lavalink" -ForegroundColor Gray
Write-Host "  Full stack up  : docker compose up -d  (runs both Lavalink + Bot in Docker)" -ForegroundColor Gray
