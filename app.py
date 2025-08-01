import os
import requests
from flask import Flask, request, jsonify, render_template, session
from flask_session import Session
from werkzeug.security import generate_password_hash, check_password_hash  # Optional unless needed
from datetime import datetime
import uuid

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MODEL = "llama3-70b-8192"

# --- Mood options ---
MOOD_OPTIONS = ["happy", "sad", "stressed", "anxious", "calm", "angry", "excited", "neutral"]

# --- Helper for journal storage ---
def get_journal():
    if "journal" not in session:
        session["journal"] = []
    return session["journal"]

def save_journal(journal):
    session["journal"] = journal

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

# --- Journal API ---

@app.route("/journal", methods=["GET"])
def get_all_journal_entries():
    """
    Get all journal entries, optionally filter by mood or date.
    Query params: mood, date (YYYY-MM-DD)
    """
    journal = get_journal()
    mood = request.args.get("mood")
    date_str = request.args.get("date")
    results = journal
    if mood:
        results = [entry for entry in results if entry.get("mood") == mood]
    if date_str:
        results = [entry for entry in results if entry.get("timestamp", "").startswith(date_str)]
    return jsonify({"entries": results})

@app.route("/journal", methods=["POST"])
def add_journal_entry():
    """
    Add a new journal entry. Expects JSON: title, body, mood
    """
    data = request.json
    title = data.get("title", "").strip()
    body = data.get("body", "").strip()
    mood = data.get("mood", "").strip()
    if not title or not body or mood not in MOOD_OPTIONS:
        return jsonify({"error": "Missing or invalid title, body, or mood."}), 400
    entry = {
        "id": str(uuid.uuid4()),
        "title": title,
        "body": body,
        "mood": mood,
        "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    }
    journal = get_journal()
    journal.append(entry)
    save_journal(journal)
    return jsonify({"entry": entry}), 201

@app.route("/journal/<entry_id>", methods=["GET"])
def get_journal_entry(entry_id):
    """
    Get a single journal entry by ID.
    """
    journal = get_journal()
    for entry in journal:
        if entry["id"] == entry_id:
            return jsonify({"entry": entry})
    return jsonify({"error": "Entry not found."}), 404

@app.route("/journal/<entry_id>", methods=["PUT"])
def update_journal_entry(entry_id):
    """
    Update a journal entry. Expects JSON: title, body, mood
    """
    data = request.json
    title = data.get("title", "").strip()
    body = data.get("body", "").strip()
    mood = data.get("mood", "").strip()
    journal = get_journal()
    for entry in journal:
        if entry["id"] == entry_id:
            if title: entry["title"] = title
            if body: entry["body"] = body
            if mood in MOOD_OPTIONS: entry["mood"] = mood
            save_journal(journal)
            return jsonify({"entry": entry})
    return jsonify({"error": "Entry not found."}), 404

@app.route("/journal/<entry_id>", methods=["DELETE"])
def delete_journal_entry(entry_id):
    """
    Delete a journal entry by ID.
    """
    journal = get_journal()
    journal_new = [entry for entry in journal if entry["id"] != entry_id]
    if len(journal_new) == len(journal):
        return jsonify({"error": "Entry not found."}), 404
    save_journal(journal_new)
    return jsonify({"success": True})

@app.route("/journal/moods", methods=["GET"])
def get_mood_options():
    """
    Get possible mood options.
    """
    return jsonify({"moods": MOOD_OPTIONS})

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080)
