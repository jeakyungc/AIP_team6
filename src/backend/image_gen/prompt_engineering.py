from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO
import os
from dotenv import load_dotenv
import json

load_dotenv()
api_key = os.environ.get("GEMINI_API_KEY")

class ERDiagramGenerator:
    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)
        self.model = "gemini-2.0-flash-exp-image-generation"
    
    def create_detailed_er_prompt(self, description: str) -> str:
        """
        Create a highly detailed prompt for accurate ER diagram generation
        """
        base_prompt = f"""
INSTRUCTION: Create a professional Entity-Relationship (ER) diagram with precise database design notation.

DESCRIPTION: {description}

TECHNICAL REQUIREMENTS:
1. ENTITIES: Draw as rectangles with entity names at the top
2. ATTRIBUTES: List inside entity rectangles, primary keys UNDERLINED
3. RELATIONSHIPS: Diamond shapes connecting entities
4. CARDINALITY: Show 1, M, or N near relationship lines
5. NOTATION: Use crow's foot notation for relationships
6. LAYOUT: Arrange entities to minimize line crossings
7. STYLE: Clean, professional database diagram style
8. LABELS: All relationships must be clearly labeled with verbs

VISUAL SPECIFICATIONS:
- Use black text on white background
- Entity rectangles: filled with light blue (#E6F3FF)
- Relationship diamonds: filled with light yellow (#FFF9C4)
- Primary key attributes: bold and underlined
- Foreign key attributes: italic
- Relationship lines: solid black lines
- Cardinality indicators: bold numbers/letters

CRITICAL: This must be a technically accurate ER diagram following standard database design conventions. Include ALL entities, attributes, and relationships mentioned in the description.

Generate the ER diagram now:
        """
        return base_prompt
    
    def parse_er_requirements(self, description: str) -> dict:
        """
        Parse the description to extract ER diagram components
        """
        # This would ideally use NLP to extract entities, attributes, and relationships
        # For now, we'll create a structured approach
        
        entities = []
        relationships = []
        attributes = {}
        
        # Basic keyword detection (you could enhance this with NLP)
        words = description.lower().split()
        
        # Look for common entity indicators
        entity_indicators = ['entity', 'table', 'object', 'class']
        relationship_indicators = ['relationship', 'relates', 'connected', 'associated']
        
        return {
            'entities': entities,
            'relationships': relationships, 
            'attributes': attributes
        }
    
    def generate_with_validation(self, description: str, max_attempts: int = 3) -> tuple:
        """
        Generate ER diagram with validation and retry logic
        """
        for attempt in range(max_attempts):
            try:
                prompt = self.create_detailed_er_prompt(description)
                
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_modalities=["TEXT", "IMAGE"],
                        generation_config={
                            "temperature": 0.05,  # Very low for consistency
                            "max_output_tokens": 1500,
                            "top_p": 0.8
                        }
                    )
                )
                
                text_response = ""
                image_data = None
                
                for part in response.candidates[0].content.parts:
                    if getattr(part, "text", None):
                        text_response = part.text
                    elif getattr(part, "inline_data", None):
                        image_data = part.inline_data.data
                
                # Basic validation
                if image_data and self.validate_er_diagram(text_response, description):
                    return text_response, image_data
                else:
                    print(f"Attempt {attempt + 1} failed validation, retrying...")
                    
            except Exception as e:
                print(f"Attempt {attempt + 1} failed with error: {e}")
        
        raise Exception("Failed to generate valid ER diagram after maximum attempts")
    
    def validate_er_diagram(self, text_response: str, original_description: str) -> bool:
        """
        Basic validation to check if the generated diagram meets requirements
        """
        # Check if response mentions key ER diagram components
        er_keywords = ['entity', 'relationship', 'attribute', 'primary key', 'foreign key']
        
        text_lower = text_response.lower()
        keyword_count = sum(1 for keyword in er_keywords if keyword in text_lower)
        
        # Simple validation: at least 3 ER keywords should be mentioned
        return keyword_count >= 3
    
    def save_diagram(self, image_data: bytes, filename: str = "er_diagram.png") -> str:
        """
        Save the generated ER diagram
        """
        image = Image.open(BytesIO(image_data))
        image.save(filename)
        return filename
    
    def generate_er_diagram(self, description: str, output_file: str = "er_diagram.png") -> dict:
        """
        Main method to generate ER diagram
        """
        try:
            print("🔄 Generating ER diagram...")
            text_response, image_data = self.generate_with_validation(description)
            
            # Save the image
            saved_file = self.save_diagram(image_data, output_file)
            
            print("✅ ER diagram generated successfully!")
            print(f"📝 Description: {text_response[:200]}...")
            print(f"💾 Saved as: {saved_file}")
            
            return {
                "success": True,
                "description": text_response,
                "file_path": saved_file,
                "image_data": image_data
            }
            
        except Exception as e:
            print(f"❌ Error generating ER diagram: {e}")
            return {
                "success": False,
                "error": str(e)
            }

# Usage example
if __name__ == "__main__":
    load_dotenv()
    api_key = os.environ.get("GEMINI_API_KEY")
    
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment variables")
    
    # Initialize the ER diagram generator
    er_generator = ERDiagramGenerator(api_key)
    
    # Example 1: Simple university system
    university_description = """
    Create an ER diagram for a university course registration system:
    
    ENTITIES:
    - Student: student_id (PK), name, email, major, year, GPA
    - Course: course_id (PK), course_name, credits, department, max_enrollment
    - Professor: professor_id (PK), name, department, office, email
    - Semester: semester_id (PK), season, year, start_date, end_date
    
    RELATIONSHIPS:
    - Student ENROLLS IN Course for Semester (Many-to-Many with attributes: grade, enrollment_date)
    - Professor TEACHES Course in Semester (Many-to-Many)
    - Course OFFERED IN Semester (Many-to-Many)
    
    Include proper cardinality constraints and all attributes.
    """
    
    result = er_generator.generate_er_diagram(
        university_description, 
        "university_er_diagram.png"
    )
    
    if result["success"]:
        print("\n🎉 University ER diagram generated successfully!")
    else:
        print(f"\n❌ Failed to generate diagram: {result['error']}")