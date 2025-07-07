from openai import OpenAI
from dotenv import load_dotenv
import os
import re
from typing import Optional, Tuple

load_dotenv()

token = os.environ["GITHUB_TOKEN"]
endpoint = "https://models.github.ai/inference"
model = "openai/gpt-4.1"

client = OpenAI(
    base_url=endpoint,
    api_key=token,
)

def extract_content_from_tags(text: str, tag: str) -> Optional[str]:
    """Extract content between XML-like tags"""
    pattern = f"<{tag}>(.*?)</{tag}>"
    match = re.search(pattern, text, re.DOTALL)
    return match.group(1).strip() if match else None

def clean_code_block(code: str) -> str:
    """Remove markdown code fences and clean up code"""
    # Remove markdown fences
    code = re.sub(r'^```(?:python)?\s*\n?', '', code, flags=re.MULTILINE)
    code = re.sub(r'\n?```\s*$', '', code, flags=re.MULTILINE)
    
    # Remove extra whitespace but preserve indentation
    lines = code.split('\n')
    # Remove empty lines at start and end
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    
    return '\n'.join(lines)


_XML_TAG_CLOSURE_INSTRUCTION = (
    "IMPORTANT XML TAG USAGE: You MUST ensure all XML-style tags in your response "
    "(e.g., `<tag_name>...</tag_name>`) are correctly and explicitly closed. "
    "For example, always write `<manim_code>\\n[CODE]\\n</manim_code>`, "
    "NOT `<manim_code>\\n[CODE]\\n` or `<manim_code>\\n[CODE]\\n<explanation>...`. "
    "Unclosed tags will cause parsing failure and render your output unusable. "
    "The content within the tags is primary; the tags are for structuring."
)

PROMPT_ENHANCEMENT_SYSTEM = f"""You are a Manim visualization expert. Your task is to enhance user prompts for creating educational mathematical and scientific animations.

You should:
1. Add mathematical context and educational value
2. Suggest appropriate Manim objects and animations
3. Specify visual elements like colors, positioning, and timing
4. Include relevant mathematical concepts and formulas
5. Ensure the animation tells a clear story

Format your response as:
<enhanced_prompt>
[Your enhanced prompt here]
</enhanced_prompt>

<suggestions>
[Brief bullet points of key visual elements to include]
</suggestions>

{_XML_TAG_CLOSURE_INSTRUCTION}

"""

MANIM_CODE_GENERATION_SYSTEM = f"""You are an expert Manim developer. Generate clean, working Python code for Manim animations.

CRITICAL REQUIREMENTS:
1. Always use the class name "GeneratedScene" that inherits from Scene
2. Implement the construct() method
3. Use proper Manim imports (from manim import *)
4. Follow Manim best practices for animations
5. Include comments explaining key steps
6. Use appropriate wait() calls between animations
7. Ensure all objects are properly positioned and styled

Common Manim objects to use:
- Text, MathTex, Tex for text and formulas
- Circle, Square, Rectangle, Line for shapes
- NumberPlane, Axes for coordinate systems
- VGroup for grouping objects
- Transform, FadeIn, FadeOut, Create, Write for animations

Format your response EXACTLY as:
<manim_code>
[Your complete Python code here]
</manim_code>

<explanation>
[Brief explanation of what the animation does]
</explanation>

{_XML_TAG_CLOSURE_INSTRUCTION}

"""

ERROR_FIXING_SYSTEM = f"""You are a Manim debugging expert. Fix Python Manim code based on error messages.

CRITICAL REQUIREMENTS:
1. Keep the class name as "GeneratedScene"
2. Analyze the error carefully and fix the root cause
3. Ensure all imports are correct
4. Fix syntax errors, missing methods, or incorrect Manim usage
5. Maintain the original animation intent while fixing bugs
6. Use proper Manim syntax and methods

Common fixes:
- Import missing modules
- Fix method names and parameters
- Correct object positioning and scaling
- Fix animation timing and sequencing
- Resolve attribute errors

Format your response EXACTLY as:
<fixed_code>
[Your corrected Python code here]
</fixed_code>

<fix_explanation>
[Brief explanation of what was fixed]
</fix_explanation>

{_XML_TAG_CLOSURE_INSTRUCTION}

"""

def enhance_prompt_and_generate_code(prompt: str) -> Tuple[str, str]:
    """
    Enhance the user prompt and generate Manim code.
    Returns: (manim_code, explanation)
    """
    try:
        # Step 1: Enhance the prompt
        enhanced_resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": PROMPT_ENHANCEMENT_SYSTEM},
                {"role": "user", "content": f"Enhance this prompt for creating an educational animation: {prompt}"}
            ],
            max_tokens=800,
            temperature=0.7,
        )
        
        enhanced_content = enhanced_resp.choices[0].message.content or ""
        enhanced_prompt = extract_content_from_tags(enhanced_content, "enhanced_prompt")
        
        if not enhanced_prompt:
            enhanced_prompt = prompt  # Fallback to original
        
        print(f"Enhanced prompt: {enhanced_prompt}")
        
        # Step 2: Generate Manim code from enhanced prompt
        code_resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": MANIM_CODE_GENERATION_SYSTEM},
                {"role": "user", "content": f"Create a Manim animation for: {enhanced_prompt}"}
            ],
            temperature=0.3,  # Lower temperature for more consistent code
        )
        
        code_content = code_resp.choices[0].message.content or ""
        manim_code = extract_content_from_tags(code_content, "manim_code")
        explanation = extract_content_from_tags(code_content, "explanation") or "Animation generated"
        
        if not manim_code:
            # Fallback: try to extract code from the entire response
            manim_code = clean_code_block(code_content)
        else:
            manim_code = clean_code_block(manim_code)
        
        # Ensure the code has proper structure
        if "class GeneratedScene" not in manim_code:
            manim_code = add_scene_wrapper(manim_code)
        
        return manim_code, explanation
        
    except Exception as e:
        print(f"Error in prompt enhancement/code generation: {e}")
        # Return a basic fallback
        fallback_code = generate_fallback_code(prompt)
        return fallback_code, "Fallback animation due to generation error"

def fix_manim_code_with_error(raw_code: str, error_message: str, attempt_number: int = 1) -> Tuple[str, str]:
    """
    Fix Manim code based on error message.
    Returns: (fixed_code, fix_explanation)
    """
    try:
        # Create a comprehensive error context
        error_context = f"""
ATTEMPT NUMBER: {attempt_number}

CURRENT CODE:
```python
{raw_code}
```

ERROR MESSAGE:
```
{error_message}
```

Please analyze the error and provide a complete fixed version of the code.
"""
        
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": ERROR_FIXING_SYSTEM},
                {"role": "user", "content": error_context}
            ],
            max_tokens=2000,
            temperature=0.1,  # Very low temperature for consistent fixes
        )
        
        fix_content = resp.choices[0].message.content or ""
        fixed_code = extract_content_from_tags(fix_content, "fixed_code")
        fix_explanation = extract_content_from_tags(fix_content, "fix_explanation") or "Code fixed"
        
        if not fixed_code:
            # Fallback: try to clean the entire response
            fixed_code = clean_code_block(fix_content)
        else:
            fixed_code = clean_code_block(fixed_code)
        
        # Ensure the fixed code has proper structure
        if "class GeneratedScene" not in fixed_code:
            fixed_code = add_scene_wrapper(fixed_code)
        
        return fixed_code, fix_explanation
        
    except Exception as e:
        print(f"Error in code fixing: {e}")
        # Return the original code with a basic fix attempt
        return raw_code, f"Unable to fix error: {str(e)}"

def add_scene_wrapper(code_content: str) -> str:
    """Add proper Scene class wrapper if missing"""
    wrapper = f"""from manim import *

class GeneratedScene(Scene):
    def construct(self):
{chr(10).join('        ' + line for line in code_content.split(chr(10)) if line.strip())}
"""
    return wrapper

def generate_fallback_code(prompt: str) -> str:
    """Generate a basic fallback animation if all else fails"""
    return f"""from manim import *

class GeneratedScene(Scene):
    def construct(self):
        # Fallback animation for: {prompt}
        title = Text("{prompt[:30]}...", font_size=48)
        self.play(Write(title))
        self.wait(2)
        
        subtitle = Text("Animation generated successfully!", font_size=24)
        subtitle.next_to(title, DOWN, buff=1)
        self.play(FadeIn(subtitle))
        self.wait(2)
"""

def extract_scene_name_from_code(code: str) -> str:
    """Extract the scene class name from Manim code"""
    # Look for class definition
    class_pattern = r'class\s+(\w+)\s*\([^)]*Scene[^)]*\)'
    match = re.search(class_pattern, code)
    return match.group(1) if match else "GeneratedScene"

# Additional utility function for validation
def validate_manim_code(code: str) -> Tuple[bool, str]:
    """Basic validation of Manim code structure"""
    issues = []
    
    if "from manim import" not in code and "import manim" not in code:
        issues.append("Missing Manim imports")
    
    if "class" not in code:
        issues.append("Missing Scene class definition")
    
    if "def construct(self)" not in code:
        issues.append("Missing construct method")
    
    if "self.play" not in code and "self.add" not in code:
        issues.append("No animations or objects added to scene")
    
    is_valid = len(issues) == 0
    return is_valid, "; ".join(issues) if issues else "Code structure looks good"