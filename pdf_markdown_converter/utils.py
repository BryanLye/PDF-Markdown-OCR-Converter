"""
Utility functions for PDF to Markdown conversion
"""

from pathlib import Path


def sanitize_filename(filename):
    """
    Create a safe directory name from filename.
    
    Args:
        filename: Original filename (str or Path object)
        
    Returns:
        str: Sanitized filename safe for all operating systems
    """
    name = Path(filename).stem
    safe_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_. "
    sanitized = ''.join(c if c in safe_chars else '_' for c in name)
    return sanitized[:50].strip()