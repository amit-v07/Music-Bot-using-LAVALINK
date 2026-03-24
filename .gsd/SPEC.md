# Music Bot — Project Spec

> status: FINALIZED

## Goal

A production-grade Discord Music Bot that runs continuously without interruptions, streaming music in voice channels via Lavalink. The bot must be stable, self-healing, and easy to operate.

## Core Requirements

### Functional
- Play music from YouTube, SoundCloud, Spotify links/searches
- Queue management: add, remove, move, jump, shuffle, clear
- Playback controls: play, pause, resume, skip, stop, volume, loop, autoplay
- Interactive UI: Discord buttons for controls (now playing panel)
- AI personality: Hinglish Gemini-powered responses with fallbacks

### Non-Functional
- **Reliability**: Bot must not silently die — reconnect to Lavalink after disconnects
- **Stability**: Wavelink player must not freeze or hang
- **Resilience**: Graceful error handling in all commands, no unhandled exceptions
- **Longevity**: Bot stays in voice channel as long as music plays or queue is active
- **Correctness**: UI panels update properly on every track change
- **Deployment**: Both Lavalink (Docker) and bot.py can be started reliably

## Out of Scope
- Web dashboard
- Music downloading
- Premium tiers
- Database (SQLite is fine for history)

## Stack
- Python 3.x, discord.py 2.x, wavelink 3.x
- Lavalink 4 via Docker (youtube-plugin 1.17.0)
- Google Gemini API (gemini-2.5-flash)
- docker-compose for Lavalink, plain Python process for bot
