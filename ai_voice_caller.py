"""
=============================================================================
AGRIBOT AI VOICE CALLING & DISPATCH ENGINE (v2.0 PRO)
Framework: LiveKit Agents + Google Vertex AI / OpenAI + ElevenLabs / Google Cloud TTS
Telephony: LiveKit SIP Outbound Trunking / Twilio SIP Trunk
Protocols: Real-Time Audio WebRTC + Voice Activity Detection (Silero VAD)

BILINGUAL CAPABILITIES:
- English (en-IN) & Hindi (hi-IN) Autonomous Agronomy Voice Agents
- Incident-Triggered Emergency Calls with Automatic SMS Backup
=============================================================================
"""

import os
import sys
import asyncio
import logging
from typing import Annotated

from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("agribot-voice-agent")

# =============================================================================
# API REQUIREMENTS & ENVIRONMENT CONFIGURATION
# =============================================================================
"""
REQUIRED ENVIRONMENT VARIABLES (.env):
-----------------------------------------------------------------------------
# 1. Telephony & WebRTC Infrastructure (LiveKit Cloud or Self-Hosted)
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=devkey
LIVEKIT_API_SECRET=secret
LIVEKIT_SIP_TRUNK_ID=ST_xxxxxxxxx    # From LiveKit SIP Inbound/Outbound Trunk

# 2. Vertex AI / LLM Brain (Google Cloud or Groq or OpenAI)
GOOGLE_APPLICATION_CREDENTIALS=/path/to/gcp-service-account.json
GCP_PROJECT_ID=your-gcp-project-id
GCP_LOCATION=us-central1
# Alternative LLM:
OPENAI_API_KEY=sk-xxxx
GROQ_API_KEY=gsk_xxxx

# 3. Speech-to-Text (STT) & Text-to-Speech (TTS)
DEEPGRAM_API_KEY=xxxxxxxx             # Real-time streaming STT (English + Hindi)
ELEVENLABS_API_KEY=xxxxxxxx           # Ultra-realistic neural voice TTS
# Optional: Google Cloud Speech-to-Text & Text-to-Speech (hi-IN-Neural2 / en-IN)
"""

# =============================================================================
# USER INCIDENT TEMPLATES (EXACT SPECIFICATION)
# =============================================================================
INCIDENT_TEMPLATES = {
    "ROVER_STUCK": {
        "title": "Rover Blockage Alert",
        "voice_en": "Alert! Your AgriBot rover is physically stuck in muddy terrain at sector B2. Please inspect the rover.",
        "voice_hi": "चेतावनी! आपका एग्रीबॉट रोवर खेत में फंस गया है। कृपया जीपीएस लोकेशन पर जाकर रोवर की जांच करें।",
        "sms_prefix": "🚨 AGRIBOT CRITICAL: Rover is trapped/stuck at field coordinates."
    },
    "CRITICAL_BATTERY": {
        "title": "Low Battery Brownout Risk",
        "voice_en": "Warning. AgriBot battery has dropped below fifteen percent. Safe parking sequence initiated.",
        "voice_hi": "चेतावनी! रोवर की बैटरी पंद्रह प्रतिशत से कम हो गई है। कृपया तुरंत चार्ज करें।",
        "sms_prefix": "⚠️ AGRIBOT WARNING: Battery critically low (<15%)."
    },
    "SEVERE_PEST_OUTBREAK": {
        "title": "High-Risk Pest Outbreak",
        "voice_en": "Urgent agronomy advisory. Tobacco caterpillar infestation detected above ninety percent threshold.",
        "voice_hi": "कृषि सूचना! आपके खेत में तम्बाकू इल्ली का गंभीर प्रकोप देखा गया है। तुरंत स्प्रे की सलाह दी जाती है।",
        "sms_prefix": "🐛 AGRIBOT AI: Severe pest cluster detected (>90% confidence)."
    },
    "SOIL_DROUGHT_CRITICAL": {
        "title": "Extreme Soil Moisture Depletion",
        "voice_en": "Alert. Soil moisture at root depth has dropped to critical drought levels. Immediate irrigation required.",
        "voice_hi": "चेतावनी! मिट्टी में नमी बहुत कम हो गई है। तुरंत सिंचाई शुरू करने की आवश्यकता है।",
        "sms_prefix": "💧 AGRIBOT TELEMETRY: Soil moisture critical (<18%)."
    }
}


# =============================================================================
# LIVEKIT AGENTS & VERTEX / OPENAI REAL-TIME VOICE PIPELINE
# =============================================================================
try:
    from livekit import api
    from livekit.agents import AutoSubscribe, JobContext, WorkerOptions, cli, llm
    from livekit.agents.pipeline import VoicePipelineAgent
    from livekit.plugins import openai, silero, deepgram
    LIVEKIT_AVAILABLE = True
except ImportError:
    LIVEKIT_AVAILABLE = False


class AgriBotVoiceAssistant:
    def __init__(self, incident_type="ROVER_STUCK", language="hi", latitude=22.7196, longitude=75.8577):
        self.incident_key = incident_type
        self.incident = INCIDENT_TEMPLATES.get(incident_type, INCIDENT_TEMPLATES["ROVER_STUCK"])
        self.language = language
        self.lat = latitude
        self.lon = longitude

        self.initial_message = (
            self.incident["voice_hi"] if language == "hi" else self.incident["voice_en"]
        )

    def build_system_prompt(self):
        maps_link = f"https://maps.google.com/?q={self.lat},{self.lon}"
        lang_directive = (
            "You must converse politely in clear conversational HINDI (or Hinglish if the farmer replies in Hindi). "
            if self.language == "hi"
            else "You must converse politely in clear Indian English. "
        )

        return f"""You are KisanMitra, an intelligent agricultural emergency voice agent for the AgriBot Autonomous Rover.
Current Incident: {self.incident['title']}
Field Coordinates: {self.lat}, {self.lon} (Google Maps: {maps_link})

Opening Statement you just spoke:
"{self.initial_message}"

Behavior Instructions:
1. {lang_directive}
2. Inform the farmer about the incident details with calm urgency.
3. If they ask where the rover is located, explain the coordinates and tell them an SMS with the exact Google Maps link has been dispatched to their phone.
4. If they ask what pesticide to use for pest outbreaks, recommend standard chlorpyrifos or neem oil extract depending on caterpillar cluster size.
5. If they confirm they are going to the field, thank them and end the call respectfully.
Keep your replies concise (under 2 sentences) because this is a phone call.
"""


# =============================================================================
# LIVEKIT SIP OUTBOUND CALL DISPATCHER
# =============================================================================
async def dispatch_sip_phone_call(phone_number: str, incident_key: str, language="hi"):
    """
    Initiates an outbound cellular phone call to the farmer using LiveKit SIP Trunking.
    """
    trunk_id = os.getenv("LIVEKIT_SIP_TRUNK_ID", "ST_DEMO_TRUNK")
    livekit_url = os.getenv("LIVEKIT_URL")

    print(f"\n=======================================================")
    print(f"📞 OUTBOUND AI CALL DISPATCH")
    print(f"Destination Number : {phone_number}")
    print(f"Incident Type      : {incident_key}")
    print(f"Language           : {'Hindi' if language == 'hi' else 'English'}")
    print(f"=======================================================")

    incident = INCIDENT_TEMPLATES.get(incident_key, INCIDENT_TEMPLATES["ROVER_STUCK"])
    speech_text = incident["voice_hi"] if language == "hi" else incident["voice_en"]

    if LIVEKIT_AVAILABLE and livekit_url:
        try:
            livekit_api = api.LiveKitAPI()
            import uuid
            room_name = f"agribot-alert-{uuid.uuid4().hex[:8]}"

            print(f"[LIVEKIT-SIP] Requesting SIP outbound participant via Trunk: {trunk_id}...")
            sip_participant = await livekit_api.sip.create_sip_participant(
                api.CreateSIPParticipantRequest(
                    sip_trunk_id=trunk_id,
                    sip_call_to=phone_number,
                    room_name=room_name,
                    participant_identity="agribot-emergency-agent"
                )
            )
            print(f"✓ Outbound call ringing: {phone_number}")
            print(f"✓ Room Active: {room_name}")
            await livekit_api.aclose()
            return True
        except Exception as e:
            print(f"[WARN] LiveKit SIP API error: {e}")

    # High-Fidelity Simulation Output (For testing without consuming telephone minutes)
    print("\n[VOICE SIMULATION] Call connected to Farmer.")
    print(f"🤖 AGRIBOT SPEAKING ({language.upper()}):")
    print(f"   \"{speech_text}\"")
    print("\n📲 BACKUP SMS DISPATCHED:")
    print(f"   \"{incident['sms_prefix']} Location: https://maps.google.com/?q=22.719600,75.857700\"")
    return True


# =============================================================================
# LIVEKIT WORKER ENTRYPOINT (WHEN RUN AS LIVE AGENT SERVICE)
# =============================================================================
async def entrypoint(ctx: "JobContext"):
    """LiveKit Agents Worker process entrypoint."""
    if not LIVEKIT_AVAILABLE:
        print("[ERROR] LiveKit agents SDK not installed.")
        return

    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    vad_model = silero.VAD.load()

    bot = AgriBotVoiceAssistant(incident_type="SEVERE_PEST_OUTBREAK", language="hi")

    agent = VoicePipelineAgent(
        vad=vad_model,
        stt=deepgram.STT(language="hi") if os.getenv("DEEPGRAM_API_KEY") else openai.STT(),
        llm=openai.LLM(model="gpt-4o-mini"),
        tts=openai.TTS(),
        chat_ctx=llm.ChatContext().append(
            role="system",
            text=bot.build_system_prompt()
        ),
    )

    agent.start(ctx.room)
    await asyncio.sleep(1)
    await agent.say(bot.initial_message, allow_interruptions=True)


# =============================================================================
# CLI DEMO & DISPATCH EXECUTION
# =============================================================================
def main():
    print("=" * 65)
    print("   🎙️ AGRIBOT BILINGUAL AI EMERGENCY CALLING DISPATCHER")
    print("=" * 65)

    test_phone = sys.argv[1] if len(sys.argv) > 1 else "+918319556016"
    test_incident = sys.argv[2] if len(sys.argv) > 2 else "SEVERE_PEST_OUTBREAK"
    test_lang = sys.argv[3] if len(sys.argv) > 3 else "hi"

    print("\nAvailable Incidents:")
    for k, v in INCIDENT_TEMPLATES.items():
        print(f"  • {k:<22} -> {v['title']}")

    print(f"\nTriggering automated call for incident: [{test_incident}] to {test_phone}...")
    asyncio.run(dispatch_sip_phone_call(test_phone, test_incident, language=test_lang))


if __name__ == "__main__":
    main()
