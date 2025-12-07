import json
import os

from dotenv import load_dotenv
from flask import Flask, request
from flask_cors import CORS

from userSettings import userSettings

load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
SETTINGS_DIR = "user_json"


def create_user_json_file(username: str, settings_dict: dict):
    os.makedirs(SETTINGS_DIR, exist_ok=True)
    file_name = os.path.join(SETTINGS_DIR, f"{username}.json")
    with open(file_name, "w", encoding="utf-8") as file:
        json.dump(settings_dict, file, indent=4)
    print("Saved settings to:", file_name)


@app.route("/setAgentConfig", methods=["POST"])
def setAgentConfig():
    data = request.get_json(silent=True) or {}
    print("raw json:", data)
    room_config = data.get("room_config") or {}
    print(room_config)
    agents = room_config.get("agents") or []

    agent = agents[0] if agents else {}

    name = agent.get("user_name", "my name")
    print(name)
    voice = agent.get("voice", "my voice")
    print(voice)
    personality = agent.get("personality", "my personality")
    print(personality)
    language = agent.get("language", "my language")
    print(language)
    settings = userSettings(name, voice, personality, language)
    userSettingsJson = settings.__dict__
    print(userSettingsJson)
    create_user_json_file(name, userSettingsJson)
    return "Received"


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080, debug=True)
