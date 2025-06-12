from flask import Flask, request, render_template
from ai.groq_client import get_ai_response
import os

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    ai_reply = ""
    user_prompt = ""
    
    if request.method == "POST":
        user_prompt = request.form.get("prompt", "")
        if user_prompt.strip():
            try:
                ai_reply = get_ai_response(user_prompt)
            except Exception as e:
                ai_reply = f"Something went wrong: {str(e)}"
    
    return render_template("index.html", response=ai_reply, prompt=user_prompt)

if __name__ == "__main__":
    app.run(debug=True)
