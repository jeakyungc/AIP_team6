import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO
import os
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()
api_key = os.environ.get("GEMINI_API_KEY")

def load_prompter():
    print("Loading Promptist model...")
    prompter_model = AutoModelForCausalLM.from_pretrained("microsoft/Promptist")
    tokenizer = AutoTokenizer.from_pretrained("gpt2")
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "left"
    print("Model loaded successfully!")
    return prompter_model, tokenizer

def generate_optimized_prompt(plain_text, prompter_model, prompter_tokenizer):
    input_ids = prompter_tokenizer(plain_text.strip()+" Rephrase:", return_tensors="pt").input_ids
    eos_id = prompter_tokenizer.eos_token_id
    outputs = prompter_model.generate(
        input_ids, 
        do_sample=False, 
        max_new_tokens=75, 
        num_beams=8, 
        num_return_sequences=8, 
        eos_token_id=eos_id, 
        pad_token_id=eos_id, 
        length_penalty=-1.0
    )
    output_texts = prompter_tokenizer.batch_decode(outputs, skip_special_tokens=True)
    res = output_texts[0].replace(plain_text+" Rephrase:", "").strip()
    return res

def generate_image_with_gemini(prompt, client):
    try:
        print("Generating image with Gemini...")
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp-image-generation",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=["TEXT", "IMAGE"]
            )
        )
        
        # Handle both text and image parts
        image_saved = False
        for part in response.candidates[0].content.parts:
            if getattr(part, "text", None):
                print("📝 Gemini response:", part.text)
            elif getattr(part, "inline_data", None):
                image_data = part.inline_data.data
                image = Image.open(BytesIO(image_data))
                
                # Create unique filename with timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"generated_image_{timestamp}.png"
                image.save(filename)
                print(f"🖼️ Image saved as: {filename}")
                image_saved = True
        
        if not image_saved:
            print("⚠️ No image was generated in the response")
            
    except Exception as e:
        print(f"❌ Error generating image: {e}")

def main():
    # Check if API key is available
    if not api_key:
        print("❌ Error: GEMINI_API_KEY not found in environment variables.")
        print("Please set your Gemini API key in a .env file or environment variable.")
        return
    
    # Initialize Gemini client
    try:
        client = genai.Client(api_key=api_key)
        print("✅ Gemini client initialized successfully!")
    except Exception as e:
        print(f"❌ Error initializing Gemini client: {e}")
        return
    
    # Load the Promptist model
    try:
        prompter_model, prompter_tokenizer = load_prompter()
    except Exception as e:
        print(f"❌ Error loading Promptist model: {e}")
        return
    
    print("\n" + "="*80)
    print("Welcome to the Promptist + Gemini Image Generator!")
    print("Enter simple prompts → Get optimized prompts → Generate AI images")
    print("Type 'quit' or 'exit' to stop.")
    print("="*80 + "\n")
    
    # Example prompts to show users
    examples = [
        "A rabbit is wearing a space suit",
        "Several railroad tracks with one train passing by", 
        "The roof is wet from the rain",
        "Cats dancing in a space club",
        "A futuristic city at sunset",
        "A magical forest with glowing trees"
    ]
    
    print("Example prompts you can try:")
    for i, example in enumerate(examples, 1):
        print(f"{i}. {example}")
    print()
    
    while True:
        try:
            # Get user input
            user_input = input("Enter your prompt (or 'quit' to exit): ").strip()
            
            # Check if user wants to quit
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
            
            # Skip empty inputs
            if not user_input:
                print("Please enter a prompt.\n")
                continue
            
            print("\n🔄 Processing your prompt...")
            
            # Generate optimized prompt
            try:
                optimized_prompt = generate_optimized_prompt(user_input, prompter_model, prompter_tokenizer)
                
                # Display results
                print("\n" + "-"*80)
                print(f"📝 Original prompt: {user_input}")
                print(f"✨ Optimized prompt: {optimized_prompt}")
                print("-"*80)
                
                # Generate image with optimized prompt
                generate_image_with_gemini(optimized_prompt, client)
                print("-"*80 + "\n")
                
            except Exception as e:
                print(f"❌ Error during prompt optimization: {e}")
                print("Please try again.\n")
            
        except KeyboardInterrupt:
            print("\n\nExiting...")
            break
        except Exception as e:
            print(f"❌ An unexpected error occurred: {e}")
            print("Please try again.\n")

if __name__ == "__main__":
    main()