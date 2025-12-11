import json
import os

from dotenv import load_dotenv
from livekit import agents, rtc
from livekit.agents import AgentServer, AgentSession, Agent, room_io, inference
from livekit.plugins import (
    openai,
    noise_cancellation, silero,
)
from livekit.api import LiveKitAPI
from livekit.protocol.room import ListParticipantsRequest

SETTINGS_DIR = "user_json"

load_dotenv()

agent_name = {
    "blake" : "a167e0f3-df7e-4d52-a9c3-f949145efdab",
    "daniela" : "5c5ad5e7-1020-476b-8b91-fdcbe9cc313c",
    "jaqueline" : "9626c31c-bec5-4cca-baa8-f8ba9e84c8bc",
    "robyn" : "f31cc6a7-c1e8-4764-980c-60a361443dd1"
}
agent_language = {
    "en" : "English",
    "fr" : "French",
    "es" : "Spanish",
    "de" : "Deutch",
    "uk" : "Ukrainian"
}
class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions="You are a helpful voice AI assistant.")





server = AgentServer()


@server.rtc_session()
async def my_agent(ctx: agents.JobContext):

    await ctx.connect()
    await ctx.wait_for_participant()

    room = ctx.room
    async with LiveKitAPI() as lkapi:
        all_participants = await lkapi.room.list_participants(ListParticipantsRequest(room=room.name))
        print(all_participants)
    current_user = [p for p in all_participants.participants if not p.permission.agent][0]
    print(current_user.name)
    json_path = os.path.join(SETTINGS_DIR, f"{current_user.name}.json")

    try:
        with open(json_path, "r", encoding="utf-8") as file:
            user_data = json.load(file)
            print(user_data)
    except FileNotFoundError:
        user_data = 1
    session = AgentSession(
        stt="assemblyai/universal-streaming:en",
        llm="openai/gpt-4.1-mini",
        tts=inference.TTS(
            model="cartesia/sonic-3",
            voice = agent_name[user_data["settings"].get("voice")],
            language = user_data["settings"].get("language"),
            extra_kwargs={
                "speed": 1.5,
                "volume": 1.2,
                "emotion": "excited"
            }
        ),
        vad=silero.VAD.load(),
    )

    await session.start(
        room=ctx.room,
        agent=Assistant(),
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=lambda
                    params: noise_cancellation.BVCTelephony() if params.participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP else noise_cancellation.BVC(),
            ),
        ),
    )
    print("Agent session started. Waiting for participant and voice output...")
    await session.generate_reply(
        instructions=f"Greet the user and offer your assistance. Users name is {user_data['settings'].get('name')}."
                     f" Speak in {user_data['settings'].get('personality')} manor with them. Speak {agent_language[user_data['settings'].get('language')]}."
    )
    print("said")


if __name__ == "__main__":
    agents.cli.run_app(server)
