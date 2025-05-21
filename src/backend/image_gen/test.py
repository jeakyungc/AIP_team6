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
    "Create me an ER diagram"
    " Artist(artist id, artist name, bio) Play(artist id, song id) Song(song id, song title, duration, genre) Album(album id, album name, release date) Contain(album id, song id) (Constraint 1) Multiple artists can play the same song for their own albums (Constriaint 2) The Contain relationship between Album and Song is many-to-many. That is, an album can contain multiple songs, and a song can belong to multiple albums. (Constriaint 3) Every song must be part of at least one album, i.e., total participation."
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
