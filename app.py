import os
import requests
from flask import Flask, request, jsonify, render_template, session
from flask_session import Session
from werkzeug.security import generate_password_hash, check_password_hash  # Optional unless needed

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MODEL = "llama3-70b-8192"

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_input = request.json.get("message", "").strip()
    if not user_input:
        return jsonify({"reply": "Please tell me what’s on your mind. I’m here for you 💙"})

    if "chat_history" not in session:
        session["chat_history"] = []

    session["chat_history"].append({"role": "user", "content": user_input})

    full_convo = [
        {
            "role": "system",
            "content": (
                "You are a kind, supportive AI assistant named MindEase. "
                "You help people manage anxiety, stress, and depression. "
                "Always respond with empathy, encouragement, and practical advice. "
                "Avoid giving medical diagnoses or acting like a therapist."
            )
        }
    ] + session["chat_history"]

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": MODEL,
        "messages": full_convo[-10:],  # Keep the last 10 messages for context
        "temperature": 0.8
    }

    try:
        response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=data)
        response.raise_for_status()
        reply = response.json()["choices"][0]["message"]["content"]
        session["chat_history"].append({"role": "assistant", "content": reply})
        return jsonify({"reply": reply})
    except requests.exceptions.RequestException as e:
        print("Groq error:", e)
        return jsonify({"reply": "Sorry, I’m having trouble reaching my brain 🧠 right now. Try again later."})
    except Exception as e:
        print("Unexpected error:", e)
        return jsonify({"reply": "An unexpected error occurred. I’m still here for you."})

@app.route("/reset", methods=["POST"])
def reset():
    session.pop("chat_history", None)
    return jsonify({"reply": "Memory wiped 🧽 — let's start fresh!"})

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080)
