# Roadmap

## Milestone 1: Stable Production Bot

### Phase 1: Resilience & Error Handling
Harden the bot against disconnects, crashed players, and unhandled exceptions so it can run for days without manual intervention.

### Phase 2: Lavalink & Deployment Polish
Ensure the Lavalink Docker setup, bot startup, and environment config are correct, reproducible, and easy to manage with a single command.

### Phase 3: UI & Player Correctness
Ensure the interactive now-playing panel and queue view always reflect live state correctly across edge cases (track end, autoplay, skip, disconnect).

### Phase 4: Coolify Home Server Deployment
**Status**: ✅ Complete

### Phase 5: Maintenance & Future-Proofing
**Status**: 🏗️ In Progress
Pin specific, tested versions across the entire stack (Python, Wavelink, Lavalink, Plugins) to prevent "surprise" breaking updates. Implement a simple "Admin Notification" system if the Node disconnects or errors.
