"""
Discord UI components for Music Bot (Lavalink/Wavelink Adaptation)
Interactive views and buttons for music control
"""
import discord
from discord import ui, Embed
from typing import Dict, Optional, Any
import wavelink
import logging

from utils.ai_brain import ai_brain

logger = logging.getLogger('LavalinkUI')

class NowPlayingView(ui.View):
    """Interactive controls for currently playing song"""
    
    def __init__(self, ctx, timeout: float = 600):
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.update_buttons()
    
    def update_buttons(self):
        """Update button states based on current wavelink player state"""
        self.clear_items()
        
        vc: wavelink.Player = self.ctx.voice_client
        if not vc:
            return
            
        # Previous button
        has_history = len(vc.queue.history) > 0
        previous_button = ui.Button(
            label="⏮️ Prev", 
            style=discord.ButtonStyle.secondary, 
            disabled=not has_history
        )
        previous_button.callback = self.prev_song
        self.add_item(previous_button)
        
        # Play/Pause button
        if vc.playing and not vc.paused:
            play_pause_button = ui.Button(
                label="⏸️ Pause", 
                style=discord.ButtonStyle.primary
            )
        else:
            play_pause_button = ui.Button(
                label="▶️ Play", 
                style=discord.ButtonStyle.success
            )
        play_pause_button.callback = self.play_pause
        self.add_item(play_pause_button)
        
        # Next button
        # Enable next if there are tracks in queue or if Autoplay is enabled
        next_enabled = len(vc.queue) > 0 or getattr(vc, 'autoplay', wavelink.AutoPlayMode.disabled) == wavelink.AutoPlayMode.enabled
        skip_button = ui.Button(
            label="⏭️ Next", 
            style=discord.ButtonStyle.secondary, 
            disabled=not next_enabled
        )
        skip_button.callback = self.skip_track
        self.add_item(skip_button)
        
        # Stop button
        stop_button = ui.Button(
            label="⏹️ Stop", 
            style=discord.ButtonStyle.danger
        )
        stop_button.callback = self.stop_track
        self.add_item(stop_button)
        
        # Repeat button
        repeat_enabled = vc.queue.mode == wavelink.QueueMode.loop or vc.queue.mode == wavelink.QueueMode.loop_all
        repeat_button = ui.Button(
            label="🔂 Repeat" if repeat_enabled else "🔁 Repeat",
            style=discord.ButtonStyle.success if repeat_enabled else discord.ButtonStyle.secondary
        )
        repeat_button.callback = self.toggle_repeat
        self.add_item(repeat_button)
        
        # Autoplay button
        autoplay_enabled = getattr(vc, 'autoplay', wavelink.AutoPlayMode.disabled) == wavelink.AutoPlayMode.enabled
        autoplay_button = ui.Button(
            label="🔥 Autoplay" if autoplay_enabled else "💤 Autoplay",
            style=discord.ButtonStyle.success if autoplay_enabled else discord.ButtonStyle.secondary
        )
        autoplay_button.callback = self.toggle_autoplay
        self.add_item(autoplay_button)
    
    async def prev_song(self, interaction: discord.Interaction):
        vc: wavelink.Player = self.ctx.voice_client
        if not vc or not len(vc.queue.history):
            await interaction.response.send_message("❌ Peeche kuch hai hi nahi bhai, kahan jaaun?", ephemeral=True)
            return
            
        await interaction.response.defer(ephemeral=True)
        # Get the previous track and play it
        prev_track = vc.queue.history.get()
        if prev_track:
            # We want to put the current track back to the FRONT of the queue in case they want to go forward again
            if vc.current:
                vc.queue.put_at(0, vc.current)
            await vc.play(prev_track)
            
            reply = await ai_brain.get_response("resume", {"user": interaction.user.display_name})
            await interaction.followup.send(f"⏮️ {reply}", ephemeral=True)
            self.update_buttons()
            try:
                await interaction.edit_original_response(view=self)
            except Exception as e:
                logger.error(f"Error editing response: {e}")
        
    async def play_pause(self, interaction: discord.Interaction):
        vc: wavelink.Player = self.ctx.voice_client
        if not vc:
            await interaction.response.send_message("❌ Main voice channel mein nahi hoon!", ephemeral=True)
            return
            
        await interaction.response.defer(ephemeral=True)
        if vc.playing and not vc.paused:
            await vc.pause(True)
            reply = await ai_brain.get_response("pause", {"user": interaction.user.display_name})
            await interaction.followup.send(f"⏸️ {reply}", ephemeral=True)
        elif vc.paused:
            await vc.pause(False)
            reply = await ai_brain.get_response("resume", {"user": interaction.user.display_name})
            await interaction.followup.send(f"▶️ {reply}", ephemeral=True)
        else:
            await interaction.followup.send("❌ Kuch baj hi nahi raha, kya pause karu?", ephemeral=True)
            return
            
        self.update_buttons()
        await ui_manager.update_now_playing_buttons(self.ctx, self)
    
    async def skip_track(self, interaction: discord.Interaction):
        vc: wavelink.Player = self.ctx.voice_client
        if not vc:
            return await interaction.response.send_message("❌ Aage kuch nahi hai bhai! End of the road.", ephemeral=True)
            
        await interaction.response.defer(ephemeral=True)
        await vc.skip(force=True)
        reply = await ai_brain.get_response("skip", {"user": interaction.user.display_name, "song": "Gaana"})
        await interaction.followup.send(f"⏭️ {reply}", ephemeral=True)
        self.update_buttons()
        # No need to edit_original_response here entirely manually since track end event will re-send UI.
        
    async def stop_track(self, interaction: discord.Interaction):
        vc: wavelink.Player = self.ctx.voice_client
        if vc:
            await interaction.response.defer(ephemeral=True)
            vc.queue.clear()
            await vc.disconnect()
            await ui_manager.cleanup_all_messages(interaction.guild_id)
            reply = await ai_brain.get_response("stop", {"user": interaction.user.display_name})
            await interaction.followup.send(f"⏹️ {reply}", ephemeral=True)
        else:
            await interaction.response.send_message("Kuch chal hi nahi raha hai.", ephemeral=True)
            
    async def toggle_repeat(self, interaction: discord.Interaction):
        vc: wavelink.Player = self.ctx.voice_client
        if not vc: return
        
        await interaction.response.defer(ephemeral=True)
        if vc.queue.mode == wavelink.QueueMode.normal:
            vc.queue.mode = wavelink.QueueMode.loop
            reply = await ai_brain.get_response("loop_song", {"user": interaction.user.display_name})
            await interaction.followup.send(f"🔂 {reply}", ephemeral=True)
        else:
            vc.queue.mode = wavelink.QueueMode.normal
            reply = await ai_brain.get_response("loop_off", {"user": interaction.user.display_name})
            await interaction.followup.send(f"🔁 {reply}", ephemeral=True)
            
        self.update_buttons()
        await ui_manager.update_now_playing_buttons(self.ctx, self)
        
    async def toggle_autoplay(self, interaction: discord.Interaction):
        vc: wavelink.Player = self.ctx.voice_client
        if not vc: return
        
        await interaction.response.defer(ephemeral=True)
        if getattr(vc, 'autoplay', wavelink.AutoPlayMode.disabled) == wavelink.AutoPlayMode.disabled:
            vc.autoplay = wavelink.AutoPlayMode.enabled
            reply = await ai_brain.get_response("autoplay_start", {"user": interaction.user.display_name, "count": len(vc.queue)})
            await interaction.followup.send(f"🔥 {reply}", ephemeral=True)
        else:
            vc.autoplay = wavelink.AutoPlayMode.disabled
            reply = await ai_brain.get_response("loop_off", {"user": interaction.user.display_name})
            await interaction.followup.send(f"💤 {reply}", ephemeral=True)
            
        self.update_buttons()
        await ui_manager.update_now_playing_buttons(self.ctx, self)


class QueueView(ui.View):
    """Paginated queue display with navigation"""
    
    def __init__(self, ctx, timeout: float = 180):
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.per_page = 10
        self.current_page = 0
        self.setup_pagination()
        self.update_buttons()
    
    def get_virtual_queue(self):
        """Constructs a full queue list including history, current song, and upcoming songs."""
        vc: wavelink.Player = self.ctx.voice_client
        if not vc:
            return [], 0
            
        virtual_queue = list(vc.queue.history)
        current_idx = len(virtual_queue)
        
        if vc.current:
            virtual_queue.append(vc.current)
            
        virtual_queue.extend(list(vc.queue))
        return virtual_queue, current_idx

    def setup_pagination(self):
        virtual_queue, _ = self.get_virtual_queue()
        queue_len = len(virtual_queue)
        
        if queue_len == 0:
            self.total_pages = 0
            return
            
        self.total_pages = max(0, (queue_len - 1) // self.per_page)
    
    def update_buttons(self):
        self.clear_items()
        
        prev_button = ui.Button(
            label="⬅️ Prev", 
            style=discord.ButtonStyle.secondary,
            disabled=(self.current_page == 0)
        )
        prev_button.callback = self.prev_page
        self.add_item(prev_button)
        
        next_button = ui.Button(
            label="➡️ Next", 
            style=discord.ButtonStyle.secondary,
            disabled=(self.current_page >= self.total_pages)
        )
        next_button.callback = self.next_page
        self.add_item(next_button)

        # Jump to current song button
        jump_button = ui.Button(
            label="🎵 Current", 
            style=discord.ButtonStyle.primary
        )
        jump_button.callback = self.jump_to_current
        self.add_item(jump_button)
    
    def create_queue_embed(self) -> Embed:
        virtual_queue, current_idx = self.get_virtual_queue()
        
        if not virtual_queue:
            embed = Embed(
                title="🎵 Queue", 
                description="Queue bilkul khaali hai! Kuch add karo na! 🎵",
                color=0x2b2d31
            )
            return embed
        
        start_idx = self.current_page * self.per_page
        end_idx = min(start_idx + self.per_page, len(virtual_queue))
        
        description_lines = []
        
        for i in range(start_idx, end_idx):
            song = virtual_queue[i]
            title = song.title
            if len(title) > 60:
                title = title[:57] + "..."
            
            # Wavelink represents length in milliseconds
            seconds = song.length // 1000
            m, s = divmod(seconds, 60)
            h, m = divmod(m, 60)
            duration = f"{m:02d}:{s:02d}" if h == 0 else f"{h:02d}:{m:02d}:{s:02d}"
            
            prefix = "▶️ " if i == current_idx else ""
            description_lines.append(f"{prefix}**{i + 1}.** [{duration}] {title}")
        
        description = "\n".join(description_lines)
        
        embed = Embed(
            title="🎵 Queue", 
            description=description,
            color=0x2b2d31
        )
        
        if self.total_pages > 0:
            embed.set_footer(
                text=f"Page {self.current_page + 1}/{self.total_pages + 1} • {len(virtual_queue)} songs total"
            )
        else:
            embed.set_footer(text=f"{len(virtual_queue)} songs total")
        
        return embed
    
    async def prev_page(self, interaction: discord.Interaction):
        if self.current_page > 0:
            self.current_page -= 1
            self.update_buttons()
            embed = self.create_queue_embed()
            await interaction.response.edit_message(embed=embed, view=self)
    
    async def next_page(self, interaction: discord.Interaction):
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.update_buttons()
            embed = self.create_queue_embed()
            await interaction.response.edit_message(embed=embed, view=self)

    async def jump_to_current(self, interaction: discord.Interaction):
        virtual_queue, current_idx = self.get_virtual_queue()
        
        if virtual_queue and 0 <= current_idx < len(virtual_queue):
            target_page = current_idx // self.per_page
            if target_page != self.current_page:
                self.current_page = target_page
                self.update_buttons()
                embed = self.create_queue_embed()
                await interaction.response.edit_message(embed=embed, view=self)
            else:
                await interaction.response.send_message("Arre, isi page pe toh ho! 😅", ephemeral=True)
        else:
            await interaction.response.send_message("Koi gaana nahi baj raha abhi.", ephemeral=True)


class UIManager:
    """Manages all UI updates and message handling"""
    
    def __init__(self):
        # Maps guild_id to dict of {'now_playing': msg, 'queue': msg}
        self.ui_messages: Dict[int, Dict[str, discord.Message]] = {}
    
    async def update_now_playing(self, ctx) -> Optional[discord.Message]:
        guild_id = ctx.guild.id
        vc: wavelink.Player = ctx.voice_client
        
        await self._cleanup_message(guild_id, 'now_playing')
        
        if vc and vc.current:
            current_song = vc.current
            embed = Embed(
                title="🎵 Now Playing",
                description=current_song.title,
                color=0x2b2d31
            )
            
            is_autoplay = getattr(vc, 'autoplay', wavelink.AutoPlayMode.disabled) == wavelink.AutoPlayMode.enabled
            ap_status = "ON 🔥" if is_autoplay else "OFF 💤"
            tip_content = f"**Tip:** Non-stop music chahiye? `-ap` type karke Autoplay on karlo! (Abhi: {ap_status})"
            
            if current_song.artwork:
                embed.set_thumbnail(url=current_song.artwork)
            
            seconds = current_song.length // 1000
            m, s = divmod(seconds, 60)
            h, m = divmod(m, 60)
            duration = f"{m:02d}:{s:02d}" if h == 0 else f"{h:02d}:{m:02d}:{s:02d}"
                
            embed.add_field(
                name="Duration", 
                value=duration,
                inline=True
            )
            
            ap_footer_status = "ON" if is_autoplay else "OFF"
            ap_icon = "🔥" if is_autoplay else "💤"
            embed.set_footer(text=f"Autoplay: {ap_footer_status} {ap_icon} • '-ap' use karke non-stop bajao!")
            
            view = NowPlayingView(ctx)
            message = await ctx.send(content=tip_content, embed=embed, view=view)
            
            if guild_id not in self.ui_messages:
                self.ui_messages[guild_id] = {}
            self.ui_messages[guild_id]['now_playing'] = message
            return message
        return None
    
    async def update_queue(self, ctx) -> Optional[discord.Message]:
        guild_id = ctx.guild.id
        vc: wavelink.Player = ctx.voice_client
        
        await self._cleanup_message(guild_id, 'queue')
        
        if vc:
            view = QueueView(ctx)
            embed = view.create_queue_embed()
            message = await ctx.send(embed=embed, view=view)
            
            if guild_id not in self.ui_messages:
                self.ui_messages[guild_id] = {}
            self.ui_messages[guild_id]['queue'] = message
            return message
        return None
    
    async def update_all_ui(self, ctx):
        await self.update_now_playing(ctx)
        await self.update_queue(ctx)
    
    async def update_now_playing_buttons(self, ctx, view: NowPlayingView):
        try:
            guild_id = ctx.guild.id
            if guild_id in self.ui_messages and 'now_playing' in self.ui_messages[guild_id]:
                message = self.ui_messages[guild_id]['now_playing']
                view.update_buttons()
                await message.edit(view=view)
        except Exception as e:
            logger.error(f"update_now_playing_buttons error: {e}")
    
    async def _cleanup_message(self, guild_id: int, message_type: str):
        if guild_id in self.ui_messages and message_type in self.ui_messages[guild_id]:
            try:
                old_message = self.ui_messages[guild_id][message_type]
                await old_message.delete()
            except discord.NotFound:
                pass
            except Exception as e:
                logger.error(f"cleanup_message_{message_type} error: {e}")
            finally:
                self.ui_messages[guild_id].pop(message_type, None)
    
    async def cleanup_all_messages(self, guild_id: int):
        if guild_id in self.ui_messages:
            for message_type in list(self.ui_messages[guild_id].keys()):
                await self._cleanup_message(guild_id, message_type)
            self.ui_messages.pop(guild_id, None)

ui_manager = UIManager()