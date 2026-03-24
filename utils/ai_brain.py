"""
AI Brain Module for Music Bot
Uses Google GenAI SDK (new unified SDK) for dynamic, funny Hinglish responses.
"""
from google import genai
from google.genai import types
from config import config
from utils.logger import logger

class AIBrain:
    """Handles AI text generation for the bot"""
    
    def __init__(self):
        self.enabled = False
        self.client = None
        
        if config.google_api_key:
            try:
                # Initialize the new GenAI client
                self.client = genai.Client(api_key=config.google_api_key)
                
                # Test with available models (2.5-flash is current stable model)
                self.model_name = 'gemini-2.5-flash'
                
                self.enabled = True
                logger.info(f"🧠 AI Brain initialized successfully ({self.model_name})")
            except Exception as e:
                logger.error("ai_init_failed", e)
                logger.warning("🧠 AI Brain disabled: Failed to initialize GenAI client")
        else:
            logger.warning("🧠 AI Brain disabled: No Google API Key found")

    async def get_response(self, action: str, context: dict = None) -> str:
        """
        Generate a response based on an action and context.
        
        Args:
            action: The event triggering the response (e.g., 'skip', 'play', 'error')
            context: Dictionary containing relevant data (e.g., song title, user name)
        """
        if not self.enabled or not self.client:
            return self._get_fallback_response(action)

        import asyncio

        try:
            prompt = self._build_prompt(action, context or {})
            
            # Use the new SDK's generate_content method, but with a timeout
            # to prevent tenacity from hanging for 60+ seconds on 429 retries
            response = await asyncio.wait_for(
                self.client.aio.models.generate_content(
                    model=self.model_name,
                    contents=prompt
                ),
                timeout=4.0
            )
            
            return response.text.strip()
            
        except asyncio.TimeoutError:
            logger.warning(f"🧠 AI Generation Timeout (4s) for '{action}'. Using fallback.")
            return self._get_fallback_response(action)
        except Exception as e:
            error_msg = str(e)
            
            # Check if this is the known google-genai aiohttp AttributeError hiding a 429 error
            is_quota_exceeded = "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg
            is_sdk_bug = False
            
            if not is_quota_exceeded and isinstance(e, AttributeError) and "ClientConnectorDNSError" in error_msg:
                is_sdk_bug = True
                if hasattr(e, "__context__") and e.__context__:
                    context_msg = str(e.__context__)
                    if "429" in context_msg or "RESOURCE_EXHAUSTED" in context_msg:
                        is_quota_exceeded = True

            if is_quota_exceeded:
                logger.warning(f"🧠 AI Quota Exceeded (Free Tier Limit). Using fallback for '{action}'.")
            elif is_sdk_bug:
                logger.warning(f"🧠 AI GenAI SDK connection error for '{action}'. Using fallback.")
            else:
                logger.error(f"ai_generation_failed ({action})", e)
            
            return self._get_fallback_response(action)

    def _build_prompt(self, action: str, context: dict) -> str:
        """Constructs the prompt for the AI"""
        
        song = context.get('song', 'music')
        user = context.get('user', 'yaar')
        count = context.get('count', 0)
        
        # Base persona instruction
        system_instruction = (
            "You are a funny, high-energy Discord Music Bot for a group of Indian friends. "
            "You speak in 'Hinglish' (Hindi + English mix). "
            "You love Bollywood references, slang (like 'yaar', 'bhai', 'mast', 'bakwaas'), and being slightly dramatic. "
            "Keep your response SHORT (max 1-2 sentences). No hashtags. Use emojis sparingly."
        )

        # Scenario specific instructions
        scenarios = {
            'play': f"User '{user}' just added the song '{song}'. Hype it up!",
            'skip': f"User '{user}' skipped the song '{song}'. Make a funny comment about their bad taste or impatience.",
            'stop': "User stopped the music. Say goodbye dramatically.",
            'queue_end': "The queue ended. Suggest they add more songs or mention you're finding more.",
            'error': "An error occurred. Apologize in a funny way (blame the internet or wifi).",
            'autoplay_start': f"Autoplay is starting. You picked '{song}' and {count} total songs automatically. Brag about your excellent taste.",
            'join': "You just joined the voice channel. Greet everyone loudly.",
            'leave': "You are leaving. Say bye nicely.",
            'pause': f"User '{user}' paused the music. Say something about taking a short break.",
            'resume': f"User '{user}' resumed the music. Say something about getting the party back on!",
            'loop_song': f"User '{user}' looped the current song '{song}'. Make a joke about listening to the same thing forever.",
            'loop_queue': "User looped the entire queue. Call it an endless party!",
            'loop_off': "User turned off the loop. Say moving on to new vibes.",
            'shuffle': "User shuffled the queue. Comment on mixing things up.",
            'remove': f"User removed a song. Say something funny about kicking it out.",
            'move': "User moved a song's position in the queue. Make a joke about VIP treatment.",
            'clear': "User cleared the entire queue. Act shocked or make a joke about the party dying.",
            'jump': "User jumped to a specific song in the queue. Make a joke about time travel or skipping the boring stuff.",
            'volume': f"User changed the volume. Comment on either making it deafeningly loud or too quiet.",
            'queue': "User asked to view the queue. Taunt them if it's too long or too short."
        }

        specific_instruction = scenarios.get(action, f"Event: {action}. Context: {context}")
        
        return f"{system_instruction}\n\nScenario: {specific_instruction}\n\nYour response:"

    def _get_fallback_response(self, action: str) -> str:
        """Fallback static responses if AI fails"""
        fallbacks = {
            'play': "Bajate raho! 🎵",
            'skip': "Chalo next! ⏭️",
            'stop': "Music band. Shanti. 🤫",
            'error': "Arre yaar, kuch gadbad ho gayi. ❌",
            'join': "Hello ji! Main aa gayi! 👋",
            'leave': "Chalti hoon, dua mein yaad rakhna. 👋",
            'queue_end': "Queue khatam? Tension mat lo, main aur gaane dhoondh rahi hoon! 🔎",
            'autoplay_start': "Lo ji! Mast gaane ready kar diye! 🔥",
            'pause': "Thoda saans le lo bhai! Paused. ⏸️",
            'resume': "Chalo wapas shuru karte hain! ▶️",
            'loop_song': "Bas yehi sunna hai ab! Loop ON. 🔂",
            'loop_queue': "Poori raat yehi queue chalegi. Loop All ON. 🔁",
            'loop_off': "Chalo bhot ho gaya loop! Loop OFF. ➡️",
            'shuffle': "Dhoom machale! Queue ghuma di. 🔀",
            'remove': "Hata diya kachra gaana! 🗑️",
            'move': "Shift kar diya! VIP entry. 🚚",
            'clear': "Poora saaf kar diya queue. Jhaadoo lag gaya! 🧹",
            'jump': "Seedha udhar gaya! 🚀",
            'volume': "Set kar diya volume tere aukaat hisaab se. 🔊",
            'queue': "Lo dekh lo queue apna. 🎵"
        }
        return fallbacks.get(action, "Oye hoye! 🎵")

# Global instance
ai_brain = AIBrain()
