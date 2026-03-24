#!/bin/bash

# Define paths and names
VIRTUAL_ENV=".venv"
BOT_SCRIPT="bot.py"
LAVALINK_JAR="Lavalink.jar"
BOT_SCREEN="discordbot"
LAVA_SCREEN="lavalink"

echo "Starting Music Bot services..."

# 1. Start Lavalink in a screen session
if ! screen -list | grep -q "$LAVA_SCREEN"; then
    echo "Starting Lavalink ($LAVA_SCREEN)..."
    screen -dmS $LAVA_SCREEN java -jar $LAVALINK_JAR
else
    echo "Lavalink is already running in screen: $LAVA_SCREEN"
fi

# 2. Wait a few seconds for Lavalink to initialize before starting the bot
echo "Waiting 5 seconds for Lavalink to warm up..."
sleep 5

# 3. Start Python Bot in a screen session
if ! screen -list | grep -q "$BOT_SCREEN"; then
    echo "Starting Discord Bot ($BOT_SCREEN)..."
    # Ensure virtual environment exists
    if [ -d "$VIRTUAL_ENV" ]; then
        screen -dmS $BOT_SCREEN bash -c "source $VIRTUAL_ENV/bin/activate && python3 $BOT_SCRIPT"
    else
        echo "WARNING: Virtual environment '$VIRTUAL_ENV' not found! Trying system python..."
        screen -dmS $BOT_SCREEN python3 $BOT_SCRIPT
    fi
else
    echo "Discord Bot is already running in screen: $BOT_SCREEN"
fi

echo ""
echo "✅ Everything is started!"
echo ""
echo "Helpful Commands:"
echo "-----------------"
echo "View Bot Logs      : screen -r $BOT_SCREEN"
echo "View Lavalink Logs : screen -r $LAVA_SCREEN"
echo "Exit Logs          : Press Ctrl+A, then D"
echo "Kill all screens   : killall screen"
