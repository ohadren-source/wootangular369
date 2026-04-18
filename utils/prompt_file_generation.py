"""
AI-driven file generation utility.
Uses Claude to generate file content from natural language prompts.
"""

import os
import json
from anthropic import Anthropic
from .native_file_generation import generate_native_file


# Initialize Claude client
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def generate_prompt_file(prompt: str):
    """
    Generate a file from a natural language prompt using Claude.
    
    Args:
        prompt: Natural language description of what file to generate
                Example: "Create a Python script that prints hello world"
    
    Returns:
        tuple: (file_bytes, mime_type, final_filename)
    
    Raises:
        ValueError: If Claude's response is invalid
        Exception: If API call fails
    """
    
    # System prompt for file generation
    system_prompt = """You are a file generation assistant.

When given a prompt, you must:
1. Generate the appropriate file content
2. Determine the correct file format (py, md, or js)
3. Choose a descriptive filename (no extension)

Respond ONLY with valid JSON in this exact format:
{
  "content": "the actual file content here",
  "format": "py|md|js",
  "filename": "descriptive_filename_without_extension"
}

Examples:
- "Create a Python hello world" → format: "py", filename: "hello_world"
- "Write docs for a REST API" → format: "md", filename: "api_documentation"
- "Build a click counter" → format: "js", filename: "click_counter"

Keep content clean, functional, and production-ready.
Use the most appropriate format for the request.
"""
    
    try:
        # Call Claude API
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4096,
            system=system_prompt,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )
        
        # Extract response text
        response_text = response.content[0].text.strip()
        
        # Parse JSON response
        try:
            file_spec = json.loads(response_text)
        except json.JSONDecodeError:
            raise ValueError(f"Claude returned invalid JSON: {response_text}")
        
        # Validate required fields
        required_fields = ['content', 'format', 'filename']
        missing = [f for f in required_fields if f not in file_spec]
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")
        
        # Extract fields
        content = file_spec['content']
        format_type = file_spec['format']
        filename = file_spec['filename']
        
        # Validate format
        if format_type not in ['py', 'md', 'js']:
            raise ValueError(f"Invalid format '{format_type}'. Must be py, md, or js")
        
        # Generate file using native generation
        return generate_native_file(
            content=content,
            filename=filename,
            format=format_type
        )
        
    except Exception as e:
        # Re-raise with context
        raise Exception(f"File generation failed: {str(e)}")
