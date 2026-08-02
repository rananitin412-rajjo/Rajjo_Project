from config import get_gemini_client

client = get_gemini_client()

def ask_gemini(prompt):
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        return response.text

    except Exception as e:
        return f"Gemini Error:\n{e}"