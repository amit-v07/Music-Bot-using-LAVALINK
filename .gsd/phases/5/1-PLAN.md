---
phase: 5
plan: 1
wave: 1
must_haves:
  truths:
    - "Bot DMs the owner if the Lavalink node disconnects"
    - "Bot includes a -status command showing versions of Bot, Lavalink, and Plugins"
    - "All versions in docker-compose.yaml are pinned (4.0.8, youtube-plugin 1.18.0 per maven.lavalink.dev)"
  artifacts:
    - path: "bot.py"
      provides: "Event handler and status command"
---

# Plan 5.1: Maintenance & Future-Proofing

## Objective
Ensure the user is notified if anything breaks and provides a way to verify the stack versioning.

## Tasks
1. **[TASK] Version Pinning Audit:** Verify `docker-compose.yaml` and `requirements.txt` are pinned.
2. **[TASK] Admin Alert System:** 
   - Add `OWNER_ID` to `.env`.
   - Implement `on_wavelink_node_closed` alert.
3. **[TASK] Status Command:**
   - Implement `-status` command.
   - Show Lavalink version, Node ID, and Bot version.
