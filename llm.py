# llm.py

from config import get_gemini_client

client = get_gemini_client()

MODEL = "gemini-flash-lite-latest"


def ask_llm(messages):

    try:
        system_prompt = ""
        contents = []

        for msg in messages:
            role = msg["role"]
            content = msg["content"]

            if role == "system":
                system_prompt += content + "\n\n"
            elif role == "user":
                contents.append({"role": "user", "parts": [{"text": content}]})
            elif role == "assistant":
                contents.append({"role": "model", "parts": [{"text": content}]})

        response = client.models.generate_content(
            model=MODEL,
            contents=contents,
            config={"system_instruction": system_prompt}
        )

        return response.text

    except Exception as e:
        return f"Error : {e}"

from google.genai import types

def ask_llm_with_image(messages, image_bytes, mime_type="image/png"):

    try:
        system_prompt = ""
        contents = []

        for msg in messages:
            role = msg["role"]
            content = msg["content"]

            if role == "system":
                system_prompt += content + "\n\n"
            elif role == "user":
                contents.append({"role": "user", "parts": [{"text": content}]})
            elif role == "assistant":
                contents.append({"role": "model", "parts": [{"text": content}]})

        # Last user message ke saath image bhi attach karo
        image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)

        if contents and contents[-1]["role"] == "user":
            contents[-1]["parts"].append(image_part)

        response = client.models.generate_content(
            model=MODEL,
            contents=contents,
            config={"system_instruction": system_prompt}
        )

        return response.text

    except Exception as e:
        return f"Error : {e}"    