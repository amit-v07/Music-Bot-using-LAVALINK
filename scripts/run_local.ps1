param(
  [switch]$NoBuild
)

$ErrorActionPreference = 'Stop'

Write-Host "[local] Starting Lavalink container only..."
if ($NoBuild) {
  docker compose up -d lavalink
} else {
  docker compose up -d --build lavalink
}

Write-Host "[local] Waiting briefly for Lavalink startup..."
Start-Sleep -Seconds 4

Write-Host "[local] Running bot with current Python (activate venv before running this script)."
python bot.py
