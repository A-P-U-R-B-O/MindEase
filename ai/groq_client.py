import os
import requests

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = "llama3-70b-8192"

def get_ai_response(user_prompt, chat_history=None):
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY is not set in environment variables.")

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    # Build full message list with system prompt and optional history
    messages = [{"role": "system", "content": "You are an AI Mental Wellness Coach who helps people suffering from anxiety, stress, and depression. Be gentle, supportive, and calming."}]
    
    if chat_history:
        messages.extend(chat_history)

    messages.append({"role": "user", "content": user_prompt})

    data = {
        "model": GROQ_MODEL,
        "messages": messages[-10:],  # Keep it light for faster response
        "temperature": 0.8
    }

    try:
        res = requests.post(url, headers=headers, json=data, timeout=10)
        res.raise_for_status()
        return res.json()["choices"][0]["message"]["content"]

    except requests.exceptions.RequestException as e:
        return f"API request failed: {str(e)}"

    except (KeyError, IndexError) as e:
        return "Unexpected response format from Groq API."

    except Exception as e:
        return f"An unexpected error occurred: {str(e)}"
