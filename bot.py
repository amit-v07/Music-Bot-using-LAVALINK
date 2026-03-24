import asyncio
import discord
from discord.ext import commands
import wavelink

import logging
from config import config
from utils.ai_brain import ai_brain
from ui.views import TrackEventUIContext, ui_manager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('LavalinkBot')

TOKEN = config.discord_token
LAVALINK_PASSWORD = config.lavalink_password
LAVALINK_HOST = config.lavalink_host
LAVALINK_PORT = config.lavalink_port
OWNER_ID = config.owner_id

class LavalinkBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.voice_states = True # Explicitly ensure voice states are tracked
        intents.guilds = True       # Explicitly ensure guilds are tracked
        
        super().__init__(
            command_prefix='-', 
            intents=intents,
            help_command=commands.DefaultHelpCommand()
        )

    async def setup_hook(self):
        logger.info("Setting up Wavelink Node...")
        self._nodes = [wavelink.Node(
            uri=f"http://{config.lavalink_host}:{config.lavalink_port}",
            password=config.lavalink_password,
        )]
        
        # Connect to Lavalink Server
        await wavelink.Pool.connect(nodes=self._nodes, client=self, cache_capacity=100)

    async def on_ready(self):
        logger.info(f"Bot connected as {self.user} (ID: {self.user.id})")

    async def on_wavelink_node_ready(self, payload: wavelink.NodeReadyEventPayload):
        logger.info(f"Lavalink Node connected successfully! Node ID: {payload.node.identifier}")

    async def on_wavelink_node_closed(self, payload):
        """Supplement Wavelink's own websocket retries for long Lavalink cold starts (Docker/Coolify)."""
        logger.warning(f"Lavalink Node disconnected: {payload.node.identifier}. Attempting reconnect...")
        for attempt in range(1, config.lavalink_reconnect_max_attempts + 1):
            delay = min(
                config.lavalink_reconnect_base_delay_s * (2 ** (attempt - 1)),
                config.lavalink_reconnect_max_delay_s,
            )
            await asyncio.sleep(delay)
            try:
                await wavelink.Pool.connect(nodes=self._nodes, client=self, cache_capacity=100)
                logger.info(f"Lavalink reconnected on attempt {attempt}.")
                
                if OWNER_ID:
                    try:
                        owner = await self.fetch_user(int(OWNER_ID))
                        await owner.send(f"✅ **Lavalink Reconnected** (Attempt {attempt})")
                    except Exception: pass
                return
            except Exception as e:
                logger.error(f"Lavalink reconnect attempt {attempt} failed: {e}")
                if attempt == config.lavalink_reconnect_max_attempts and OWNER_ID:
                    try:
                        owner = await self.fetch_user(int(OWNER_ID))
                        await owner.send(
                            f"⚠️ **Lavalink Critical Failure**: Could not reconnect after "
                            f"{config.lavalink_reconnect_max_attempts} attempts."
                        )
                    except Exception: pass
        logger.error("All Lavalink reconnect attempts failed. Manual restart may be needed.")

bot = LavalinkBot()

# --- Global Error Handler ---

@bot.event
async def on_command_error(ctx: commands.Context, error):
    if isinstance(error, commands.CommandNotFound):
        return
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ Bhai, kuch toh argument do! `{error.param.name}` missing hai.")
        return
    if isinstance(error, commands.BadArgument):
        await ctx.send("❌ Galat argument diya yaar. Sahi se type karo!")
        return
    logger.error(f"Command error in '{ctx.command}': {error}", exc_info=error)
    await ctx.send("❌ Arre yaar, kuch gadbad ho gayi! Thodi der mein phir try karo.")

# --- Music Commands ---

@bot.command(aliases=['p'])
async def play(ctx: commands.Context, *, search: str):
    """Play a song from YouTube, Spotify, or Soundcloud via Lavalink."""
    if not ctx.author.voice:
        await ctx.send("❌ Arre bhai, pehle voice channel toh join karo!")
        return
    
    if not ctx.voice_client:
        vc: wavelink.Player = await ctx.author.voice.channel.connect(cls=wavelink.Player)
        vc.inactive_timeout = 60
    else:
        vc: wavelink.Player = ctx.voice_client

    tracks: wavelink.Search = await wavelink.Playable.search(search)
    
    if not tracks:
        await ctx.send(f"❌ Kuch nahi mila yaar `{search}` ke liye. Spelling check karo!")
        return
        
    if isinstance(tracks, wavelink.Playlist):
        track = tracks[0]
        await vc.queue.put_wait(tracks)
        
        reply = await ai_brain.get_response("play", {"user": ctx.author.display_name, "song": tracks.name})
        await ctx.send(f"🎵 {reply} (Added playlist **{tracks.name}** with {len(tracks)} tracks)")
    else:
        track = tracks[0]
        vc.queue.put(track)
        
        reply = await ai_brain.get_response("play", {"user": ctx.author.display_name, "song": track.title})
        await ctx.send(f"🎵 {reply}")
        
    if not vc.playing:
        await vc.play(vc.queue.get())
    
    await ui_manager.update_all_ui(ctx)

@bot.command(aliases=["s", "next"])
async def skip(ctx: commands.Context):
    """Skip the current song."""
    if not ctx.voice_client:
        return await ctx.send("❌ Bhai main voice channel mein nahi hoon, kis chiz ko skip karu?")
        
    vc: wavelink.Player = ctx.voice_client
    
    current_track = vc.current
    title = current_track.title if current_track else "song"
    
    await vc.skip(force=True)
    
    reply = await ai_brain.get_response("skip", {"user": ctx.author.display_name, "song": title})
    await ctx.send(f"⏭️ **Skip kar diya!** {reply}")

@bot.command()
async def pause(ctx: commands.Context):
    """Pause the current song."""
    if not ctx.voice_client:
        return await ctx.send("❌ Kuch baj hi nahi raha bhai!")
    vc: wavelink.Player = ctx.voice_client
    if not vc.paused:
        await vc.pause(True)
        reply = await ai_brain.get_response("pause", {"user": ctx.author.display_name})
        await ctx.send(f"⏸️ {reply}")
        await ui_manager.update_all_ui(ctx)

@bot.command(aliases=['start'])
async def resume(ctx: commands.Context):
    """Resume the current song."""
    if not ctx.voice_client:
        return await ctx.send("❌ Kuch baj hi nahi raha bhai!")
    vc: wavelink.Player = ctx.voice_client
    if vc.paused:
        await vc.pause(False)
        reply = await ai_brain.get_response("resume", {"user": ctx.author.display_name})
        await ctx.send(f"▶️ {reply}")
        await ui_manager.update_all_ui(ctx)

@bot.command()
async def stop(ctx: commands.Context):
    """Stop the music and leave voice."""
    if not ctx.voice_client:
        return await ctx.send("❌ Arre, main toh kisi voice channel mein hi nahi hoon! Kise roku?")
        
    vc: wavelink.Player = ctx.voice_client
    vc.queue.clear()
    await vc.disconnect()
    await ui_manager.cleanup_all_messages(ctx.guild.id)
    
    reply = await ai_brain.get_response("stop", {"user": ctx.author.display_name})
    await ctx.send(f"⏹️ **Bas, khatam!** {reply}\nQueue aur music sab clear.")

@bot.command(aliases=['bye', 'exit', 'quit', 'dc', 'disconnect', 'out'])
async def leave(ctx: commands.Context):
    """Leave the voice channel"""
    if not ctx.voice_client:
        return await ctx.send("❌ Main pehle se hi bahar hoon bhai!")
        
    vc: wavelink.Player = ctx.voice_client
    vc.queue.clear()
    await vc.disconnect()
    await ui_manager.cleanup_all_messages(ctx.guild.id)
    
    reply = await ai_brain.get_response("leave", {"user": ctx.author.display_name})
    await ctx.send(f"👋 **Chalo, main chalti hoon!** {reply}")

@bot.command(aliases=['ap', 'auto'])
async def autoplay(ctx: commands.Context, toggle: str = None):
    """Toggle AutoPlay / YouTube Recommendations mode"""
    if not ctx.voice_client:
        return await ctx.send("❌ Voice channel mein aao pehle!")
        
    vc: wavelink.Player = ctx.voice_client
    
    if getattr(vc, 'autoplay', wavelink.AutoPlayMode.disabled) == wavelink.AutoPlayMode.enabled:
        vc.autoplay = wavelink.AutoPlayMode.disabled
        reply = await ai_brain.get_response("loop_off", {"user": ctx.author.display_name})
        await ctx.send(f"⏸️ {reply}")
    else:
        vc.autoplay = wavelink.AutoPlayMode.enabled
        reply = await ai_brain.get_response("autoplay_start", {"user": ctx.author.display_name, "count": len(vc.queue)})
        await ctx.send(f"🎵 {reply}")
        
    await ui_manager.update_all_ui(ctx)

# --- Legacy Parity Commands ---

@bot.command(aliases=['q'])
async def queue(ctx: commands.Context):
    """View the current queue."""
    if not ctx.voice_client:
        return await ctx.send("❌ Kuch baj hi nahi raha hai, kya queue dekhoge?")
    
    reply = await ai_brain.get_response("queue", {"user": ctx.author.display_name})
    await ctx.send(f"🎵 {reply}")
    await ui_manager.update_all_ui(ctx)

@bot.command(aliases=['repeat'])
async def loop(ctx: commands.Context):
    """Toggle looping the current song or entire queue."""
    if not ctx.voice_client:
        return await ctx.send("❌ Kisko loop karoon? Kuch nai baj raha.")
        
    vc: wavelink.Player = ctx.voice_client
    
    if vc.queue.mode == wavelink.QueueMode.normal:
        vc.queue.mode = wavelink.QueueMode.loop
        reply = await ai_brain.get_response("loop_song", {"user": ctx.author.display_name, "song": vc.current.title if vc.current else "Gaana"})
        await ctx.send(f"🔂 {reply}")
    elif vc.queue.mode == wavelink.QueueMode.loop:
        vc.queue.mode = wavelink.QueueMode.loop_all
        reply = await ai_brain.get_response("loop_queue", {"user": ctx.author.display_name})
        await ctx.send(f"🔁 {reply}")
    else:
        vc.queue.mode = wavelink.QueueMode.normal
        reply = await ai_brain.get_response("loop_off", {"user": ctx.author.display_name})
        await ctx.send(f"➡️ {reply}")
        
    await ui_manager.update_all_ui(ctx)

@bot.command()
async def shuffle(ctx: commands.Context):
    """Shuffle the current queue."""
    if not ctx.voice_client or not ctx.voice_client.queue:
        return await ctx.send("❌ Shuffle karne ke liye gaane honey chahiye na?")
        
    vc: wavelink.Player = ctx.voice_client
    vc.queue.shuffle()
    reply = await ai_brain.get_response("shuffle", {"user": ctx.author.display_name})
    await ctx.send(f"🔀 {reply}")
    await ui_manager.update_all_ui(ctx)

@bot.command(aliases=['rm', 'delete'])
async def remove(ctx: commands.Context, index: int):
    """Remove a song from the queue by position."""
    if not ctx.voice_client or not ctx.voice_client.queue:
        return await ctx.send("❌ Queue khaali hai bhai!")
        
    vc: wavelink.Player = ctx.voice_client
    if 1 <= index <= len(vc.queue):
        track = vc.queue[index - 1]
        del vc.queue[index - 1]
        reply = await ai_brain.get_response("remove", {"user": ctx.author.display_name, "song": track.title})
        await ctx.send(f"🗑️ {reply}")
        await ui_manager.update_all_ui(ctx)
    else:
        await ctx.send(f"❌ Invalid index! 1 se {len(vc.queue)} ke beech enter karo.")

@bot.command()
async def move(ctx: commands.Context, old_index: int, new_index: int):
    """Move a song from one position to another in the queue."""
    if not ctx.voice_client or not ctx.voice_client.queue:
        return await ctx.send("❌ Queue toh ghanta hai, kya move karu?")
        
    vc: wavelink.Player = ctx.voice_client
    queue_len = len(vc.queue)
    
    if 1 <= old_index <= queue_len and 1 <= new_index <= queue_len:
        track = vc.queue[old_index - 1]
        del vc.queue[old_index - 1]
        vc.queue.put_at(new_index - 1, track)
        reply = await ai_brain.get_response("move", {"user": ctx.author.display_name, "song": track.title})
        await ctx.send(f"🚚 {reply}")
        await ui_manager.update_all_ui(ctx)
    else:
        await ctx.send(f"❌ Invalid index bhai! Check the queue first.")

@bot.command(aliases=['cleanqueue', 'clearqueue', 'clear'])
async def clean(ctx: commands.Context):
    """Clear all songs from the queue."""
    if not ctx.voice_client or not ctx.voice_client.queue:
        return await ctx.send("❌ Queue already saaf hai!")
        
    vc: wavelink.Player = ctx.voice_client
    vc.queue.clear()
    reply = await ai_brain.get_response("clear", {"user": ctx.author.display_name})
    await ctx.send(f"🧹 {reply}")
    await ui_manager.update_all_ui(ctx)

@bot.command(aliases=['skipto'])
async def jump(ctx: commands.Context, index: int):
    """Jump ahead directly to a specific song in the queue."""
    if not ctx.voice_client or not ctx.voice_client.queue:
        return await ctx.send("❌ Queue khaali hai bhai!")
        
    vc: wavelink.Player = ctx.voice_client
    
    if 1 <= index <= len(vc.queue):
        # We need to drop all songs before the target index
        try:
            for _ in range(index - 1):
                del vc.queue[0]
        except IndexError:
            pass  # Queue may have shrunk mid-loop, proceed with skip
            
        await vc.skip(force=True)
        reply = await ai_brain.get_response("jump", {"user": ctx.author.display_name})
        await ctx.send(f"🚀 {reply}")
    else:
        await ctx.send(f"❌ Invalid index! 1 se {len(vc.queue)} ke beech enter karo.")

@bot.command(aliases=['v', 'vol'])
async def volume(ctx: commands.Context, vol: int = None):
    """Change or check the player volume."""
    if not ctx.voice_client:
        return await ctx.send("❌ Pehle music chala toh lein!")
        
    vc: wavelink.Player = ctx.voice_client
    if vol is None:
        return await ctx.send(f"🔊 Abhi ki volume hai: **{vc.volume}%**")
        
    if 0 <= vol <= 1000:
        await vc.set_volume(vol)
        reply = await ai_brain.get_response("volume", {"user": ctx.author.display_name})
        await ctx.send(f"🔊 {reply}")
    else:
        await ctx.send("❌ Volume 0 se 1000 ke beech mein hona chahiye aukaat ke hisaab se.")

# --- Event Listeners for Player ---
@bot.listen('on_wavelink_inactive_player')
async def on_inactive_player(payload):
    """Fires when the player has been inactive (no tracks) for inactive_timeout seconds."""
    vc: wavelink.Player = payload.player
    if vc and vc.connected:
        try:
            await ui_manager.cleanup_all_messages(vc.guild.id)
            await vc.disconnect()
            logger.info(f"Disconnected inactive player from guild {vc.guild.id}")
        except Exception as e:
            logger.error(f"Error disconnecting inactive player: {e}")

@bot.listen('on_wavelink_track_end')
async def on_track_end(payload: wavelink.TrackEndEventPayload):
    vc: wavelink.Player = payload.player
    
    if not vc or not vc.connected:
        return
    
    # Inactive player cleanup is now handled by on_wavelink_inactive_player via inactive_timeout
    # No manual disconnect needed here

@bot.listen('on_wavelink_track_start')
async def on_track_start(payload: wavelink.TrackStartEventPayload):
    vc: wavelink.Player = payload.player
    
    if not vc or not vc.guild or not vc.current:
        return
        
    try:
        # Check if we have an active UI
        if vc.guild.id in ui_manager.ui_messages:
            msg = ui_manager.ui_messages[vc.guild.id].get('now_playing') or ui_manager.ui_messages[vc.guild.id].get('queue')
            if msg:
                await ui_manager.update_all_ui(TrackEventUIContext(vc, msg))
    except Exception as e:
        logger.error(f"Error handling track start UI update: {e}")

@bot.command()
async def status(ctx):
    """Check the health and versions of the music stack."""
    embed = discord.Embed(title="🎵 Music Stack Status", color=discord.Color.blue())
    
    # Bot / Wavelink Info
    embed.add_field(name="Bot Status", value="✅ Online", inline=True)
    embed.add_field(name="Wavelink Version", value=wavelink.__version__, inline=True)
    
    # Node Info
    nodes = wavelink.Pool.nodes
    if not nodes:
        embed.add_field(name="Lavalink Node", value="❌ No Nodes in Pool", inline=False)
    else:
        # Get the first node
        node = list(nodes.values())[0] if isinstance(nodes, dict) else nodes[0]
        status_text = "✅ Connected" if node.status == wavelink.NodeStatus.CONNECTED else "❌ Disconnected"
        embed.add_field(name="Lavalink Node", value=status_text, inline=True)
        embed.add_field(name="Players", value=str(len(node.players)), inline=True)
        
    # Version Pinning info (Static from our config)
    embed.add_field(name="Pinned Lavalink", value=config.pinned_lavalink_version, inline=True)
    embed.add_field(name="Pinned YT Plugin", value=config.pinned_youtube_plugin, inline=True)
    
    embed.set_footer(text=f"Admin Alerts: {'Enabled' if OWNER_ID else 'Disabled'}")
    await ctx.send(embed=embed)

if __name__ == "__main__":
    if not TOKEN:
        logger.error("Please add your Discord Token to the .env file.")
    else:
        bot.run(TOKEN)
