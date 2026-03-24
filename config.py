import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    discord_token = os.getenv("DISCORD_TOKEN")
    google_api_key = os.getenv("GOOGLE_API_KEY")
    error_log_file = "bot_errors.log"

    lavalink_password = os.getenv("LAVALINK_PASSWORD", "hope_lost")
    lavalink_host = os.getenv("LAVALINK_HOST", "lavalink")
    lavalink_port = int(os.getenv("LAVALINK_PORT", "2333"))
    owner_id = os.getenv("OWNER_ID")

    # discord.py voice-channel join timeout (default in library is often 30s)
    voice_connect_timeout = int(os.getenv("VOICE_CONNECT_TIMEOUT", "60"))

    # Lavalink restarts — see bot.on_wavelink_node_closed; align with DEPLOY.md / wavelink upgrades
    lavalink_reconnect_max_attempts = 8
    lavalink_reconnect_base_delay_s = 4.0
    lavalink_reconnect_max_delay_s = 45.0

    # Keep in sync with docker-compose.yaml image tag and youtube-plugin pin
    pinned_lavalink_version = "4.0.8"
    pinned_youtube_plugin = "1.18.0"


config = Config()
