import os
import requests

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

def get_ai_response(prompt):
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY is not set in environment variables.")

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "llama3-8b-8192",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7
    }

    try:
        res = requests.post(url, json=data, headers=headers, timeout=10)
        res.raise_for_status()
        json_data = res.json()

        return json_data["choices"][0]["message"]["content"]
    
    except requests.exceptions.RequestException as e:
        return f"API request failed: {str(e)}"
    
    except (KeyError, IndexError) as e:
        return "Unexpected response format from Groq API."

    except Exception as e:
        return f"An unexpected error occurred: {str(e)}"
