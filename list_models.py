from config import get_gemini_client

client = get_gemini_client()

for m in client.models.list():
    print(m.name)