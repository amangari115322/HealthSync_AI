import requests
from config import AI_API_KEY, AI_API_URL, AI_MODEL


def is_ai_configured() -> bool:
    return bool(AI_API_KEY and AI_API_URL and AI_MODEL)


def generate_health_insights(patient_data: dict) -> dict:
    """
    Call the configured OpenAI-compatible chat completions API and return:
    {"ok": bool, "content": str, "error": str, "model": str}
    """
    if not is_ai_configured():
        return {
            "ok": False,
            "content": "",
            "error": (
                "AI analysis unavailable. API configuration is missing. "
                "Please set AI_API_KEY, AI_API_URL, and AI_MODEL in your .env file."
            ),
            "model": AI_MODEL or "",
        }

    prompt = f"""
You are a cautious health information assistant, not a medical diagnostician.

Review the following laboratory values as general educational information only.

Patient Record:
- Name: {patient_data.get('full_name', 'Patient')}
- Glucose: {patient_data.get('glucose')}
- Haemoglobin: {patient_data.get('haemoglobin')}
- Cholesterol: {patient_data.get('cholesterol')}

Strict Safety Rules:
- Do NOT claim to diagnose any disease or medical condition.
- Do NOT invent missing test units or assume whether the patient was fasting.
- Use cautious phrasing such as "May warrant review", "Could be associated with", "Requires additional clinical context", and "Discuss with a qualified healthcare professional".
- Keep each section concise, clear, and easy to understand.

Format your response using these exact Markdown headings:
### Observation Summary
### Glucose Observations
### Haemoglobin Observations
### Cholesterol Observations
### Potential Indicators
### Suggested Next Steps
### Medical Disclaimer
"""

    headers = {
        "Authorization": f"Bearer {AI_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": AI_MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You provide cautious, educational health information. "
                    "You never diagnose diseases or invent missing clinical context."
                ),
            },
            {
                "role": "user",
                "content": prompt.strip(),
            },
        ],
        "temperature": 0.3,
    }

    try:
        response = requests.post(
            AI_API_URL,
            headers=headers,
            json=payload,
            timeout=30,
        )

        if response.status_code in (401, 403):
            return {
                "ok": False,
                "content": "",
                "error": "AI authentication failed. Please check your AI_API_KEY configuration.",
                "model": AI_MODEL,
            }

        if response.status_code == 429:
            return {
                "ok": False,
                "content": "",
                "error": "AI service rate limit reached. Please wait a moment and try again.",
                "model": AI_MODEL,
            }

        response.raise_for_status()
        result = response.json()

        remarks = result["choices"][0]["message"]["content"]
        if not remarks or not remarks.strip():
            return {
                "ok": False,
                "content": "",
                "error": "AI service returned an empty response.",
                "model": AI_MODEL,
            }

        return {
            "ok": True,
            "content": remarks.strip(),
            "error": "",
            "model": AI_MODEL,
        }

    except requests.exceptions.Timeout:
        return {
            "ok": False,
            "content": "",
            "error": "AI analysis timed out after 30 seconds. Please try again.",
            "model": AI_MODEL,
        }

    except requests.exceptions.RequestException as exc:
        return {
            "ok": False,
            "content": "",
            "error": f"AI service could not be reached ({type(exc).__name__}). Please check AI_API_URL and network connectivity.",
            "model": AI_MODEL,
        }

    except (KeyError, IndexError, TypeError, ValueError):
        return {
            "ok": False,
            "content": "",
            "error": "AI response format was unexpected and could not be processed.",
            "model": AI_MODEL,
        }


def generate_health_remarks(patient_data: dict) -> str:
    """Backward-compatible wrapper returning remarks text or error message."""
    result = generate_health_insights(patient_data)
    return result["content"] if result["ok"] else result["error"]
