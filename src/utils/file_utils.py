"""
File processing utilities for SmartDoc Dolphin system.
"""

import hashlib
import os
import mimetypes
from pathlib import Path
from typing import Optional, Tuple

from PIL import Image
import aiofiles

from ..core.config import settings


def calculate_file_hash(file_path: str, algorithm: str = "sha256") -> str:
    """
    Calculate hash of a file.
    
    Args:
        file_path: Path to the file
        algorithm: Hash algorithm to use
        
    Returns:
        Hexadecimal hash string
    """
    hash_func = hashlib.new(algorithm)
    
    with open(file_path, "rb") as f:
        # Read file in chunks to handle large files
        for chunk in iter(lambda: f.read(4096), b""):
            hash_func.update(chunk)
    
    return hash_func.hexdigest()


async def calculate_file_hash_async(file_path: str, algorithm: str = "sha256") -> str:
    """
    Asynchronously calculate hash of a file.
    
    Args:
        file_path: Path to the file
        algorithm: Hash algorithm to use
        
    Returns:
        Hexadecimal hash string
    """
    hash_func = hashlib.new(algorithm)
    
    async with aiofiles.open(file_path, "rb") as f:
        # Read file in chunks to handle large files
        while chunk := await f.read(4096):
            hash_func.update(chunk)
    
    return hash_func.hexdigest()


def validate_file_format(file_path: str, allowed_formats: Optional[list] = None) -> Tuple[bool, str]:
    """
    Validate if file format is allowed.
    
    Args:
        file_path: Path to the file
        allowed_formats: List of allowed file formats
        
    Returns:
        Tuple of (is_valid, file_format)
    """
    if allowed_formats is None:
        allowed_formats = settings.allowed_image_formats
    
    # Get file extension
    file_ext = Path(file_path).suffix.lower().lstrip('.')
    
    # Check if extension is in allowed formats
    if file_ext in [fmt.lower() for fmt in allowed_formats]:
        return True, file_ext
    
    # Try to detect format using MIME type
    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type:
        if mime_type.startswith('image/'):
            format_from_mime = mime_type.split('/')[-1]
            if format_from_mime in [fmt.lower() for fmt in allowed_formats]:
                return True, format_from_mime
    
    return False, file_ext


def validate_image_file(file_path: str) -> Tuple[bool, str, Optional[Tuple[int, int]]]:
    """
    Validate image file and get dimensions.
    
    Args:
        file_path: Path to the image file
        
    Returns:
        Tuple of (is_valid, error_message, dimensions)
    """
    try:
        # Check file exists
        if not os.path.exists(file_path):
            return False, "File does not exist", None
        
        # Check file size
        file_size = os.path.getsize(file_path)
        if file_size > settings.max_image_size:
            return False, f"File size ({file_size} bytes) exceeds maximum allowed size", None
        
        # Validate file format
        is_valid_format, file_format = validate_file_format(file_path)
        if not is_valid_format:
            return False, f"Unsupported file format: {file_format}", None
        
        # Try to open and validate image
        with Image.open(file_path) as img:
            dimensions = img.size
            
            # Check if image has valid dimensions
            if dimensions[0] <= 0 or dimensions[1] <= 0:
                return False, "Invalid image dimensions", None
            
            # Check image mode
            if img.mode not in ['RGB', 'RGBA', 'L', 'P']:
                return False, f"Unsupported image mode: {img.mode}", None
        
        return True, "", dimensions
        
    except Exception as e:
        return False, f"Error validating image: {str(e)}", None 