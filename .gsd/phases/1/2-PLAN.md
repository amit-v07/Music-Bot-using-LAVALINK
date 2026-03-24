---
phase: 1
plan: 2
wave: 2
must_haves:
  truths:
    - "Every command that uses ctx.voice_client correctly checks for None before use"
    - "volume command validates integer input"
    - "play command does not fail silently if Lavalink returns no tracks"
    - "All unhandled exceptions from bot commands are caught at the top level and logged"
  artifacts:
    - path: "bot.py"
      provides: "Comprehensive error handling in all commands"
  key_links:
    - from: "bot.on_command_error"
      to: "bot.py"
      via: "global error handler"
---

# Plan 1.2: Resilience — Global Error Handler & Command Guards

## Objective
Add a `on_command_error` global handler so unexpected errors are always surfaced to the user (not silently dropped). Audit all commands for missing `ctx.voice_client` None checks.

## Context
- `bot.py` — all bot commands
- `utils/logger.py` — logging

## Tasks

<task type="auto">
  <name>Add global on_command_error handler</name>
  <files>bot.py</files>
  <action>
    Add this event listener near the top of command definitions in bot.py:
    ```python
    @bot.event
    async def on_command_error(ctx: commands.Context, error):
        if isinstance(error, commands.CommandNotFound):
            return  # Silently ignore unknown commands
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Bhai, kuch toh argument do! `{error.param.name}` missing hai.")
            return
        if isinstance(error, commands.BadArgument):
            await ctx.send(f"❌ Galat argument diya. Try again properly.")
            return
        # Log and surface unexpected errors
        logger.error(f"Command error in '{ctx.command}': {error}", exc_info=error)
        await ctx.send("❌ Arre yaar, kuch gadbad ho gayi! Server logs mein dekho.")
    ```
    Do NOT suppress this event if it already exists — check first and merge.
  </action>
  <verify>Select-String -Path "bot.py" -Pattern "on_command_error"</verify>
  <done>bot.py contains on_command_error handler covering CommandNotFound, MissingRequiredArgument, BadArgument, and generic fallback</done>
</task>

<task type="auto">
  <name>Audit and fix voice_client None guards in all commands</name>
  <files>bot.py</files>
  <action>
    Review every command that touches `ctx.voice_client`. Ensure that:
    1. `pause` checks `if not ctx.voice_client` FIRST and returns early.
    2. `resume` checks `if not ctx.voice_client` FIRST and returns early.
    3. `volume` casts `vol` to int safely (already typed but add try/except around `set_volume`).
    4. `jump` wraps the loop `del vc.queue[0]` in try/except IndexError — queue can shrink mid-loop.
    
    Pattern for early return:
    ```python
    if not ctx.voice_client:
        return await ctx.send("❌ Pehle music chala toh lein!")
    vc: wavelink.Player = ctx.voice_client
    ```
  </action>
  <verify>Select-String -Path "bot.py" -Pattern "not ctx.voice_client" | Measure-Object -Line</verify>
  <done>All commands have explicit `not ctx.voice_client` guard before accessing vc. jump uses try/except IndexError.</done>
</task>

## Success Criteria
- [ ] on_command_error event handler exists
- [ ] All commands have voice_client None guard
- [ ] jump command IndexError is caught
