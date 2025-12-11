import json
import os

import bcrypt
import psycopg2
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS

from userSettings import userSettings

load_dotenv()

app = Flask(__name__)
CORS(app,
     supports_credentials=True,
     resources={r"/*": {"origins": "*"}})
SETTINGS_DIR = "user_json"
conn = psycopg2.connect("dbname=user_credentials user=postgres host=localhost password=postgres port=5432")


def create_user_json_file(email: str, settings_dict: dict) -> str:
    os.makedirs(SETTINGS_DIR, exist_ok=True)
    file_name = os.path.join(SETTINGS_DIR, f"{email}.json")
    all_data = {"user": {
        "email": email
    },
        "settings": settings_dict}
    with open(file_name, "w", encoding="utf-8") as file:
        json.dump(all_data, file, indent=4)
    print("Saved settings to:", file_name)
    return file_name


@app.route("/login", methods=["POST"])
def login():
    print("Hit the login endpoint")
    data = request.get_json(silent=True) or {}
    print(data)
    email = data["email"]
    received_password = data["password"].encode("utf-8")
    cur = conn.cursor()
    cur.execute("SELECT * FROM user_settings where email = %s", (email,))
    user = cur.fetchone()
    if not user:
        return jsonify({"error": "Invalid email or password"}), 401

    if not bcrypt.checkpw(received_password, bytes(user[3])):
        return jsonify({"error": "Invalid email or password"}), 401
    json_path = os.path.join(SETTINGS_DIR, f"{email}.json")
    try:
        with open(json_path, "r", encoding="utf-8") as file:
            user_data = json.load(file)
            print(user_data)
    except FileNotFoundError:
        return {"user": {"email": email}, "settings": {}}
    cur.close()
    return jsonify(user_data)


@app.route("/register", methods=["POST"])
def register():
    print("Hit the register endpoint")
    cur = conn.cursor()
    data = request.get_json(silent=True) or {}
    print(data)
    email = data["email"]
    username = data["name"]
    password_salt = bcrypt.gensalt()
    password = data["password"].encode("utf-8")
    password_hash = bcrypt.hashpw(password, password_salt)
    cur.execute("Insert into user_settings (email, name, password_hash, password_salt) values (%s, %s, %s,%s)",
                (email, username, password_hash, password_salt))
    conn.commit()
    cur.close()
    print(password_hash)

    return "Successfully registered"


@app.route("/setAgentConfig", methods=["POST"])
def setAgentConfig():
    data = request.get_json(silent=True) or {}
    room_config = data.get("room_config") or {}
    agents = room_config.get("agents") or []


    if agents:
        agent = agents[0]
        user_email = data.get("user_email", "user@email")
        name = agent.get("user_name")
        voice = agent.get("voice","blake")
        personality = agent.get("personality","casual")
        language = agent.get("language", "en")


        cur = conn.cursor()
        cur.execute("SELECT * FROM user_settings where email = %s", (user_email,))
        user = cur.fetchone()
        settings = userSettings(name, voice, personality, language)
        userSettingsJson = settings.__dict__
        print(userSettingsJson)
        filename = create_user_json_file(user_email, userSettingsJson)

        if not user[5]:
            cur.execute("UPDATE user_settings SET user_settings_json_path = %s WHERE email = %s", (filename, user_email,))

    return "Received"


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080, debug=True)
