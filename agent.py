from dotenv import load_dotenv
from livekit import agents, rtc
from livekit.agents import AgentServer, AgentSession, Agent, room_io, inference
from livekit.plugins import (
    openai,
    noise_cancellation, silero,
)

load_dotenv()


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions="You are a helpful voice AI assistant.")


server = AgentServer()


@server.rtc_session()
async def my_agent(ctx: agents.JobContext):
    session = AgentSession(
        stt="assemblyai/universal-streaming:en",
        llm="openai/gpt-4.1-mini",
        tts=inference.TTS(
            model="cartesia/sonic-3",
            voice="5c5ad5e7-1020-476b-8b91-fdcbe9cc313c",
            language="en",
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
        instructions="Greet the user and offer your assistance. You should start by speaking in English."
    )
    print("said")

if __name__ == "__main__":
    agents.cli.run_app(server)
