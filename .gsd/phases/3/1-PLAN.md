---
phase: 3
plan: 1
wave: 1
must_haves:
  truths:
    - "NowPlayingView buttons correctly reflect paused vs playing state after each interaction"
    - "UI panel is cleaned up from Discord after bot disconnects from voice"
    - "on_track_start correctly refreshes all UI even during autoplay"
    - "NowPlayingView.stop button cleans up UI messages after disconnect"
    - "QueueView shows accurate count including history + current + upcoming"
  artifacts:
    - path: "ui/views.py"
      provides: "Correct NowPlayingView, QueueView, UIManager"
  key_links:
    - from: "on_wavelink_track_start"
      to: "ui_manager.update_all_ui"
      via: "FakeCtx pattern in bot.py"
---

# Plan 3.1: UI & Player Correctness

## Objective
The UI panel must always reflect live player state. Currently `stop_track` in views.py does NOT call `cleanup_all_messages`, so old embeds linger. The `FakeCtx` used in `on_track_start` is fragile. This plan fixes both.

## Context
- `ui/views.py` — NowPlayingView, QueueView, UIManager
- `bot.py` — on_track_start, on_track_end event handlers

## Tasks

<task type="auto">
  <name>Fix stop_track to clean up UI messages</name>
  <files>ui/views.py</files>
  <action>
    In `NowPlayingView.stop_track`, after `await vc.disconnect()`, add:
    ```python
    await ui_manager.cleanup_all_messages(interaction.guild_id)
    ```
    Currently this is missing, leaving a dead Now Playing embed in chat after stopping.
    
    Also fix `toggle_repeat` — it calls `update_now_playing_buttons` but the view is the same instance, so it should call `self.update_buttons()` THEN `await ui_manager.update_now_playing_buttons(self.ctx, self)`. Verify this flow is correct (it currently is, no change needed if already correct).
  </action>
  <verify>Select-String -Path "ui/views.py" -Pattern "cleanup_all_messages" | Measure-Object -Line</verify>
  <done>cleanup_all_messages is called in stop_track after disconnect. At least 2 occurrences total in views.py.</done>
</task>

<task type="auto">
  <name>Harden FakeCtx in on_track_start and add guild_id to stop</name>
  <files>bot.py</files>
  <action>
    The `FakeCtx` class defined inside `on_track_start` uses `msg.author` as the author, but `msg.author` is the bot itself (since bot sent the message). The author field is not actually used in `update_all_ui`, so this is harmless, but we should clean it up:
    
    1. Remove the `author` field from FakeCtx — it's unused.
    2. Wrap the entire `on_track_start` try block with a check: `if not vc.current: return` at the top.
    3. In `on_track_end`, remove the `reply = await ai_brain.get_response("queue_end", {})` line entirely (the result is never used, it burns API quota silently). Keep the disconnect logic.
    4. In the `cleanup_all_messages` call inside `on_track_end`, use `vc.guild.id` not `ctx.guild.id` since there is no ctx.
    
    Verify `on_track_end` correctly calls `ui_manager.cleanup_all_messages(vc.guild.id)`.
  </action>
  <verify>Select-String -Path "bot.py" -Pattern "vc.guild.id" | Measure-Object -Line</verify>
  <done>on_track_start FakeCtx has no author, on_track_end has no unused AI call, both use vc.guild.id</done>
</task>

## Success Criteria
- [ ] stop_track calls cleanup_all_messages after disconnect
- [ ] on_track_start FakeCtx is cleaned up
- [ ] on_track_end no longer makes unused AI API call
- [ ] All guild_id refs use vc.guild.id in event handlers
