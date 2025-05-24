from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO
import os
from dotenv import load_dotenv

# Load environment variables (e.g., GEMINI_API_KEY)
load_dotenv()
api_key = os.environ.get("GEMINI_API_KEY")

# ✅ 직접 Client에 api_key 전달
client = genai.Client(api_key=api_key)

contents = (
    "a diagram of er model for user management system"
)

# ✅ response_modalities must include both TEXT and IMAGE
response = client.models.generate_content(
    model="gemini-2.0-flash-exp-image-generation",
    contents=contents,
    config=types.GenerateContentConfig(
        response_modalities=["TEXT", "IMAGE"]
    )
)

# ✅ Handle both text and image parts
for part in response.candidates[0].content.parts:
    if getattr(part, "text", None):
        print("📝 Text:", part.text)
    elif getattr(part, "inline_data", None):
        image_data = part.inline_data.data
        image = Image.open(BytesIO(image_data))
        image.save("og_er.png")
