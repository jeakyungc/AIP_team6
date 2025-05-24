import torch
import os
from diffusers import StableDiffusionPipeline, DPMSolverMultistepScheduler
from PIL import Image, ImageDraw, ImageFont
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
import json

class DreamBoothComparison:
    def __init__(self, base_model_path="runwayml/stable-diffusion-v1-5", 
                 finetuned_model_path="./dreambooth-model"):
        """
        Initialize comparison between base and fine-tuned models
        
        Args:
            base_model_path: Path to base Stable Diffusion model
            finetuned_model_path: Path to your fine-tuned DreamBooth model
        """
        self.base_model_path = base_model_path
        self.finetuned_model_path = finetuned_model_path
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # Load models
        self.base_pipe = None
        self.finetuned_pipe = None
        
        # Results storage
        self.comparison_results = []
        
    def load_base_model(self):
        """Load the original Stable Diffusion model"""
        print("Loading base model...")
        self.base_pipe = StableDiffusionPipeline.from_pretrained(
            self.base_model_path,
            torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
            safety_checker=None,
            requires_safety_checker=False
        )
        self.base_pipe.scheduler = DPMSolverMultistepScheduler.from_config(
            self.base_pipe.scheduler.config
        )
        self.base_pipe = self.base_pipe.to(self.device)
        print("✅ Base model loaded!")
        
    def load_finetuned_model(self):
        """Load your fine-tuned DreamBooth model"""
        print("Loading fine-tuned model...")
        try:
            self.finetuned_pipe = StableDiffusionPipeline.from_pretrained(
                self.finetuned_model_path,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                safety_checker=None,
                requires_safety_checker=False
            )
            self.finetuned_pipe.scheduler = DPMSolverMultistepScheduler.from_config(
                self.finetuned_pipe.scheduler.config
            )
            self.finetuned_pipe = self.finetuned_pipe.to(self.device)
            print("✅ Fine-tuned model loaded!")
        except Exception as e:
            print(f"❌ Error loading fine-tuned model: {e}")
            print("Make sure your model path is correct and training completed successfully")
            
    def generate_comparison_images(self, prompts, seed=42, num_inference_steps=50, 
                                 guidance_scale=7.5, height=512, width=512):
        """
        Generate images from both models for comparison
        
        Args:
            prompts: List of prompts to test
            seed: Random seed for reproducible results
            num_inference_steps: Number of denoising steps
            guidance_scale: How closely to follow the prompt
            height, width: Image dimensions
        """
        
        if self.base_pipe is None:
            self.load_base_model()
        if self.finetuned_pipe is None:
            self.load_finetuned_model()
            
        results = []
        
        for i, prompt in enumerate(prompts):
            print(f"\n🎨 Generating images for prompt {i+1}/{len(prompts)}: '{prompt}'")
            
            # Set seed for reproducibility
            torch.manual_seed(seed + i)
            
            # Generate with base model
            print("  📷 Base model...")
            base_image = self.base_pipe(
                prompt,
                num_inference_steps=num_inference_steps,
                guidance_scale=guidance_scale,
                height=height,
                width=width,
                generator=torch.Generator(device=self.device).manual_seed(seed + i)
            ).images[0]
            
            # Generate with fine-tuned model
            print("  🎯 Fine-tuned model...")
            finetuned_image = self.finetuned_pipe(
                prompt,
                num_inference_steps=num_inference_steps,
                guidance_scale=guidance_scale,
                height=height,
                width=width,
                generator=torch.Generator(device=self.device).manual_seed(seed + i)
            ).images[0]
            
            result = {
                'prompt': prompt,
                'base_image': base_image,
                'finetuned_image': finetuned_image,
                'seed': seed + i
            }
            results.append(result)
            
        self.comparison_results = results
        return results
    
    def create_side_by_side_comparison(self, result, save_path=None):
        """
        Create a side-by-side comparison image
        
        Args:
            result: Single comparison result dict
            save_path: Optional path to save the comparison
        """
        
        base_img = result['base_image']
        finetuned_img = result['finetuned_image']
        prompt = result['prompt']
        
        # Create comparison canvas
        width, height = base_img.size
        comparison_img = Image.new('RGB', (width * 2 + 20, height + 100), 'white')
        
        # Paste images
        comparison_img.paste(base_img, (0, 50))
        comparison_img.paste(finetuned_img, (width + 20, 50))
        
        # Add text labels
        draw = ImageDraw.Draw(comparison_img)
        try:
            font = ImageFont.truetype("arial.ttf", 16)
            title_font = ImageFont.truetype("arial.ttf", 14)
        except:
            font = ImageFont.load_default()
            title_font = ImageFont.load_default()
        
        # Title
        title_text = f"Prompt: {prompt[:60]}..." if len(prompt) > 60 else f"Prompt: {prompt}"
        draw.text((10, 10), title_text, fill='black', font=title_font)
        
        # Labels
        draw.text((width//2 - 50, height + 60), "Base Model", fill='black', font=font)
        draw.text((width + 20 + width//2 - 70, height + 60), "Fine-tuned Model", fill='black', font=font)
        
        if save_path:
            comparison_img.save(save_path)
            
        return comparison_img
    
    def create_comparison_grid(self, save_dir="./comparison_results"):
        """
        Create a grid of all comparisons
        """
        if not self.comparison_results:
            print("❌ No comparison results found. Run generate_comparison_images() first.")
            return
            
        os.makedirs(save_dir, exist_ok=True)
        
        # Create individual comparisons
        comparison_images = []
        for i, result in enumerate(self.comparison_results):
            save_path = os.path.join(save_dir, f"comparison_{i+1}.png")
            comp_img = self.create_side_by_side_comparison(result, save_path)
            comparison_images.append(comp_img)
            print(f"💾 Saved: {save_path}")
        
        # Create master grid
        if len(comparison_images) > 1:
            self.create_master_grid(comparison_images, save_dir)
            
        return comparison_images
    
    def create_master_grid(self, comparison_images, save_dir):
        """Create a master grid showing all comparisons"""
        
        if not comparison_images:
            return
            
        # Calculate grid dimensions
        num_images = len(comparison_images)
        cols = min(2, num_images)
        rows = (num_images + cols - 1) // cols
        
        # Get image dimensions
        img_width, img_height = comparison_images[0].size
        
        # Create master canvas
        master_width = cols * img_width + (cols - 1) * 20
        master_height = rows * img_height + (rows - 1) * 20
        master_img = Image.new('RGB', (master_width, master_height), 'white')
        
        # Paste images
        for i, img in enumerate(comparison_images):
            row = i // cols
            col = i % cols
            x = col * (img_width + 20)
            y = row * (img_height + 20)
            master_img.paste(img, (x, y))
        
        master_path = os.path.join(save_dir, "master_comparison.png")
        master_img.save(master_path)
        print(f"🎨 Master grid saved: {master_path}")
        
    def evaluate_results(self, save_metrics=True):
        """
        Evaluate and compare the results
        This is a placeholder for more sophisticated evaluation
        """
        
        if not self.comparison_results:
            print("❌ No results to evaluate")
            return
            
        evaluation = {
            'timestamp': datetime.now().isoformat(),
            'num_prompts': len(self.comparison_results),
            'base_model': self.base_model_path,
            'finetuned_model': self.finetuned_model_path,
            'prompts_tested': [r['prompt'] for r in self.comparison_results]
        }
        
        # Simple visual inspection metrics
        print("\n📊 EVALUATION RESULTS:")
        print(f"✅ Successfully generated {len(self.comparison_results)} comparison pairs")
        print(f"🎯 Base model: {self.base_model_path}")
        print(f"🎯 Fine-tuned model: {self.finetuned_model_path}")
        
        print("\n🔍 PROMPTS TESTED:")
        for i, result in enumerate(self.comparison_results):
            print(f"  {i+1}. {result['prompt']}")
            
        if save_metrics:
            with open("./comparison_results/evaluation_metrics.json", "w") as f:
                json.dump(evaluation, f, indent=2)
            print("\n💾 Metrics saved to: ./comparison_results/evaluation_metrics.json")
            
        return evaluation

def run_dreambooth_comparison_test():
    """
    Main function to run the complete comparison test
    """
    
    # Initialize comparison
    comparator = DreamBoothComparison(
        base_model_path="runwayml/stable-diffusion-v1-5",
        finetuned_model_path="./dreambooth-model"  # Update this path
    )
    
    # Define test prompts
    # Replace 'sks' with your unique identifier and 'dog' with your subject
    test_prompts = [
        "a photo of sks dog",
        "sks dog sitting in a park",
        "sks dog wearing a red collar",
        "oil painting of sks dog",
        "sks dog running on the beach",
        "portrait of sks dog, professional photography",
        "sks dog in the style of a renaissance painting",
        "sks dog as a superhero, digital art"
    ]
    
    print("🚀 Starting DreamBooth Comparison Test")
    print("="*50)
    
    # Generate comparison images
    print("\n📷 Generating comparison images...")
    results = comparator.generate_comparison_images(
        prompts=test_prompts,
        seed=42,
        num_inference_steps=50,
        guidance_scale=7.5
    )
    
    # Create comparison grids
    print("\n🎨 Creating comparison visualizations...")
    comparison_images = comparator.create_comparison_grid()
    
    # Evaluate results
    print("\n📊 Evaluating results...")
    evaluation = comparator.evaluate_results()
    
    print("\n✅ COMPARISON TEST COMPLETE!")
    print("📁 Check ./comparison_results/ folder for:")
    print("   - Individual comparison images")
    print("   - Master comparison grid")
    print("   - Evaluation metrics")
    
    return results, comparison_images, evaluation

# Alternative: Quick comparison function
def quick_comparison(base_model, finetuned_model, prompt, seed=42):
    """
    Quick single-prompt comparison
    """
    
    print(f"🎯 Quick comparison for: '{prompt}'")
    
    # Load models
    base_pipe = StableDiffusionPipeline.from_pretrained(
        base_model, torch_dtype=torch.float16, safety_checker=None
    ).to("cuda")
    
    finetuned_pipe = StableDiffusionPipeline.from_pretrained(
        finetuned_model, torch_dtype=torch.float16, safety_checker=None
    ).to("cuda")
    
    # Generate images
    torch.manual_seed(seed)
    base_img = base_pipe(prompt, num_inference_steps=50).images[0]
    
    torch.manual_seed(seed)
    finetuned_img = finetuned_pipe(prompt, num_inference_steps=50).images[0]
    
    # Create side-by-side
    width, height = base_img.size
    comparison = Image.new('RGB', (width * 2 + 20, height), 'white')
    comparison.paste(base_img, (0, 0))
    comparison.paste(finetuned_img, (width + 20, 0))
    
    comparison.save("quick_comparison.png")
    print("💾 Saved: quick_comparison.png")
    
    return base_img, finetuned_img, comparison

# Example usage
if __name__ == "__main__":
    # Run full comparison test
    results, images, evaluation = run_dreambooth_comparison_test()
    
    # Or run quick comparison
    # quick_comparison(
    #     "runwayml/stable-diffusion-v1-5",
    #     "./dreambooth-model", 
    #     "a photo of sks dog"
    # )