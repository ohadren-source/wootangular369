"""
core/file_utils.py
File handling utilities for Sol's file generation.

Filename safety validation, extension handling, etc.
"""

import os
import logging

logger = logging.getLogger(__name__)

# Windows reserved filenames (case-insensitive)
WINDOWS_RESERVED = {
    'CON', 'PRN', 'AUX', 'NUL',
    'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
    'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
}

FORMAT_TO_EXTENSION = {
    'py': '.py',
    'js': '.js',
    'ts': '.ts',
    'tsx': '.tsx',
    'jsx': '.jsx',
    'json': '.json',
    'yaml': '.yaml',
    'yml': '.yml',
    'md': '.md',
    'html': '.html',
    'css': '.css',
    'sql': '.sql',
    'xml': '.xml',
    'txt': '.txt',
    'csv': '.csv',
    'sh': '.sh',
    'bash': '.bash',
    'go': '.go',
    'rust': '.rs',
    'java': '.java',
    'cpp': '.cpp',
    'c': '.c',
    'h': '.h',
    'rb': '.rb',
    'php': '.php',
}

FORMAT_TO_MIMETYPE = {
    'py': 'text/x-python',
    'js': 'text/javascript',
    'ts': 'text/typescript',
    'tsx': 'text/typescript',
    'jsx': 'text/jsx',
    'json': 'application/json',
    'yaml': 'text/yaml',
    'yml': 'text/yaml',
    'md': 'text/markdown',
    'html': 'text/html',
    'css': 'text/css',
    'sql': 'text/sql',
    'xml': 'application/xml',
    'txt': 'text/plain',
    'csv': 'text/csv',
    'sh': 'text/x-shellscript',
    'bash': 'text/x-bash',
    'go': 'text/x-go',
    'rust': 'text/x-rust',
    'java': 'text/x-java',
    'cpp': 'text/x-c++src',
    'c': 'text/x-csrc',
    'h': 'text/x-chdr',
    'rb': 'text/x-ruby',
    'php': 'text/x-php',
}


def is_safe_filename(filename: str) -> bool:
    r"""
    Check if filename is safe without altering it.

    Rejects:
    - Empty strings
    - Path traversal (.. / \)
    - Null bytes
    - Control characters
    - Windows reserved names

    Returns True if safe, False if rejected.
    """
    if not filename or not filename.strip():
        return False

    # Reject path traversal
    if '..' in filename or '/' in filename or '\\' in filename:
        return False

    # Reject null bytes
    if '\x00' in filename:
        return False

    # Reject control characters
    if any(ord(c) < 32 for c in filename):
        return False

    # Reject Windows reserved names (base filename without extension)
    base = filename.split('.')[0].upper()
    if base in WINDOWS_RESERVED:
        return False

    return True


def ensure_extension(filename: str, format: str) -> str:
    """
    Ensure filename has correct extension based on format.

    Does NOT alter the filename — only appends extension if missing.

    Args:
        filename: User-specified filename (e.g., "systemdown" or "systemdown.py")
        format: Format hint ("py", "md", "json", etc.)

    Returns:
        Filename with correct extension (e.g., "systemdown.py")
    """
    ext = FORMAT_TO_EXTENSION.get(format.lower(), f'.{format}')

    # If filename already has the correct extension, return as-is
    if filename.endswith(ext):
        return filename

    # If filename has a different extension, replace it
    if '.' in filename:
        base = '.'.join(filename.split('.')[:-1])
        return base + ext

    # No extension, append it
    return filename + ext


def get_mime_type(format: str) -> str:
    """Get MIME type for a format."""
    return FORMAT_TO_MIMETYPE.get(format.lower(), 'text/plain')


def validate_and_prepare_filename(filename: str, format: str) -> tuple[bool, str, str]:
    """
    Validate and prepare filename for storage.

    Args:
        filename: User-specified filename
        format: Format hint ("py", "md", etc.)

    Returns:
        (is_valid, prepared_filename, error_message)
    """
    if not is_safe_filename(filename):
        return False, "", f"Unsafe filename: {filename}"

    prepared = ensure_extension(filename, format)
    mime_type = get_mime_type(format)

    return True, prepared, ""
