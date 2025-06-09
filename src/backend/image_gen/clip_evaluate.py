import os
import torch
import clip
from PIL import Image
from torchvision.transforms import Compose, Resize, CenterCrop, ToTensor, Normalize

# Load CLIP model
device = "cuda" if torch.cuda.is_available() else "cpu"
model, preprocess = clip.load("ViT-B/32", device=device)


image_dir = "./images"  
prompt = "A futuristic car in a cyberpunk city at night"

relevance_prompt = "futuristic car"

def get_image_features(image_path):
    image = preprocess(Image.open(image_path).convert("RGB")).unsqueeze(0).to(device)
    with torch.no_grad():
        return model.encode_image(image)

def get_text_features(text):
    with torch.no_grad():
        return model.encode_text(clip.tokenize([text]).to(device))

def cosine_sim(a, b):
    return torch.nn.functional.cosine_similarity(a, b).item()

# Compute text features
context_feat = get_text_features(prompt)
relevance_feat = get_text_features(relevance_prompt)

results = []

print("Evaluating images...")

for filename in os.listdir(image_dir):
    if filename.lower().endswith(".png"):
        img_path = os.path.join(image_dir, filename)
        img_feat = get_image_features(img_path)

        # Normalize
        img_feat /= img_feat.norm(dim=-1, keepdim=True)
        context_feat /= context_feat.norm(dim=-1, keepdim=True)
        relevance_feat /= relevance_feat.norm(dim=-1, keepdim=True)

        context_score = cosine_sim(img_feat, context_feat)
        relevance_score = cosine_sim(img_feat, relevance_feat)

        # Interpretability: High similarity to common text = easier to interpret
        interpret_score = cosine_sim(
            img_feat, get_text_features("A clear, realistic image with identifiable objects")
        )

        results.append({
            "image": filename,
            "context_fidelity": round(context_score, 3),
            "relevance": round(relevance_score, 3),
            "interpretability": round(interpret_score, 3)
        })

# Sort by fidelity
results.sort(key=lambda x: x["context_fidelity"], reverse=True)

print("\n=== Evaluation Results ===")
for res in results:
    print(f"{res['image']}\n"
          f"  Context Fidelity: {res['context_fidelity']}\n"
          f"  Relevance:        {res['relevance']}\n"
          f"  Interpretability: {res['interpretability']}\n")