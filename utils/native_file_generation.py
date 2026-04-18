"""
Native Python file generation utility.
Bypasses Claude's artifact system using Python's io module.
"""

import io


def generate_native_file(content: str, filename: str, format: str):
    """
    Generate a file using Python's native io module.
    
    Args:
        content: The text content to write to the file
        filename: Base filename (without extension)
        format: File format - 'py', 'md', or 'js'
    
    Returns:
        tuple: (file_bytes, mime_type, final_filename)
    
    Raises:
        ValueError: If format is not supported
    """
    
    # Format-specific MIME types and extensions
    format_map = {
        'py': {
            'mime': 'text/x-python',
            'ext': '.py'
        },
        'md': {
            'mime': 'text/markdown',
            'ext': '.md'
        },
        'js': {
            'mime': 'application/javascript',
            'ext': '.js'
        }
    }
    
    # Validate format
    if format not in format_map:
        raise ValueError(
            f"Unsupported format: {format}. "
            f"Supported formats: {', '.join(format_map.keys())}"
        )
    
    # Get format config
    config = format_map[format]
    
    # Generate final filename
    final_filename = f"{filename}{config['ext']}"
    
    # Create in-memory binary buffer
    buffer = io.BytesIO()
    
    # Write content as UTF-8 bytes
    buffer.write(content.encode('utf-8'))
    
    # Get the bytes
    buffer.seek(0)
    file_bytes = buffer.read()
    
    # Clean up
    buffer.close()
    
    return (file_bytes, config['mime'], final_filename)
