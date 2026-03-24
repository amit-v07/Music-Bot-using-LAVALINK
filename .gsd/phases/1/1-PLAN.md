---
phase: 1
plan: 1
wave: 1
must_haves:
  truths:
    - "Bot reconnects to Lavalink automatically if the node drops"
    - "All commands have try/except and send user-facing error messages, not crash silently"
    - "Bot disconnects from voice cleanly after 60s of empty queue"
    - "on_track_end does not leave a dead player in voice channel"
  artifacts:
    - path: "bot.py"
      provides: "on_wavelink_node_ready, on_track_end, on_wavelink_inactive_player handlers"
    - path: "utils/logger.py"
      provides: "Structured error logging for all failures"
  key_links:
    - from: "wavelink.Pool"
      to: "bot.py"
      via: "on_wavelink_node_ready reconnect"
---

# Plan 1.1: Resilience — Node Reconnect & Inactive Player Handling

## Objective
The bot must survive Lavalink restarts and idle periods without manual intervention. Currently there is no reconnect logic and `on_track_end` sends an AI response but never awaits it (unreliable). This plan fixes both.

## Context
- `bot.py` — all wavelink setup and event listeners
- `utils/logger.py` — error logging
- `.gsd/ARCHITECTURE.md`

## Tasks

<task type="auto">
  <name>Add Lavalink auto-reconnect</name>
  <files>bot.py</files>
  <action>
    In `LavalinkBot.setup_hook`, after the `wavelink.Pool.connect` call, store the node list on `self` so it can be reused. Add a new event handler `on_wavelink_node_closed` that:
    1. Logs a warning.
    2. Waits 5 seconds with `await asyncio.sleep(5)`.
    3. Calls `await wavelink.Pool.connect(nodes=self._nodes, client=self)` to reconnect.
    4. Wraps the entire reconnect in a try/except — log error if reconnect fails, retry once more after 15s.
    Do NOT raise exceptions from event handlers, they must always be silent except for logging.
  </action>
  <verify>Select-String -Path "bot.py" -Pattern "on_wavelink_node_closed"</verify>
  <done>bot.py contains on_wavelink_node_closed with reconnect logic and asyncio.sleep(5)</done>
</task>

<task type="auto">
  <name>Fix on_track_end and add on_wavelink_inactive_player</name>
  <files>bot.py</files>
  <action>
    Fix `on_track_end`: the `ai_brain.get_response("queue_end", {})` call result is never used — remove it (it just wastes an API call and adds latency). The 60s disconnect logic is fine but wrap it in try/except.
    
    Add a NEW event handler `on_wavelink_inactive_player`:
    ```python
    @bot.listen('on_wavelink_inactive_player')
    async def on_inactive_player(payload: wavelink.InactivePlayerEventPayload):
        vc = payload.player
        if vc and vc.connected:
            await ui_manager.cleanup_all_messages(vc.guild.id)
            await vc.disconnect()
    ```
    This uses Wavelink's native inactivity timeout. Set `inactive_timeout=60` on the Player when connecting in the `play` command: `await ctx.author.voice.channel.connect(cls=wavelink.Player, inactive_timeout=60)`.
  </action>
  <verify>Select-String -Path "bot.py" -Pattern "on_wavelink_inactive_player|inactive_timeout"</verify>
  <done>bot.py has on_wavelink_inactive_player handler and inactive_timeout=60 set during connect</done>
</task>

## Success Criteria
- [ ] on_wavelink_node_closed handler exists with reconnect logic
- [ ] on_wavelink_inactive_player handler exists
- [ ] inactive_timeout=60 passed on Player connect
- [ ] on_track_end no longer makes an unawaited AI call
