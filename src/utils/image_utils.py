"""
Image processing utilities for SmartDoc Dolphin system.
"""

import copy
import cv2
import numpy as np
from PIL import Image
from typing import Tuple, Any, Optional, List
from dataclasses import dataclass


@dataclass
class ImageDimensions:
    """Class to store image dimensions"""
    original_w: int
    original_h: int
    padded_w: int
    padded_h: int


def prepare_image(image: Image.Image) -> Tuple[np.ndarray, ImageDimensions]:
    """
    Prepare image for processing by padding to square format.
    
    Args:
        image: PIL Image to prepare
        
    Returns:
        Tuple of (padded_image_array, image_dimensions)
    """
    # Convert PIL to numpy array
    img_array = np.array(image)
    if len(img_array.shape) == 3 and img_array.shape[2] == 3:
        img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
    
    # Get original dimensions
    orig_h, orig_w = img_array.shape[:2]
    
    # Calculate target size (square with max dimension)
    target_size = max(orig_h, orig_w)
    
    # Calculate padding
    pad_h = (target_size - orig_h) // 2
    pad_w = (target_size - orig_w) // 2
    
    # Create padded image
    if len(img_array.shape) == 3:
        padded = np.full((target_size, target_size, 3), 255, dtype=img_array.dtype)
        padded[pad_h:pad_h + orig_h, pad_w:pad_w + orig_w] = img_array
    else:
        padded = np.full((target_size, target_size), 255, dtype=img_array.dtype)
        padded[pad_h:pad_h + orig_h, pad_w:pad_w + orig_w] = img_array
    
    dims = ImageDimensions(
        original_w=orig_w,
        original_h=orig_h,
        padded_w=target_size,
        padded_h=target_size
    )
    
    return padded, dims


def process_coordinates(
    coords: List[float],
    padded_image: np.ndarray,
    dims: ImageDimensions,
    previous_box: Optional[List[float]] = None
) -> Tuple[int, int, int, int, int, int, int, int, List[float]]:
    """
    Process and adjust coordinates from normalized to absolute.
    
    Args:
        coords: Normalized coordinates [x1, y1, x2, y2]
        padded_image: Padded image array
        dims: Image dimensions object
        previous_box: Previous box coordinates for overlap adjustment
        
    Returns:
        Tuple of (x1, y1, x2, y2, orig_x1, orig_y1, orig_x2, orig_y2, new_previous_box)
    """
    try:
        # Convert normalized coordinates to absolute coordinates in padded image
        x1 = int(coords[0] * dims.padded_w)
        y1 = int(coords[1] * dims.padded_h)
        x2 = int(coords[2] * dims.padded_w)
        y2 = int(coords[3] * dims.padded_h)
        
        # Ensure coordinates are within bounds
        x1 = max(0, min(x1, dims.padded_w - 1))
        y1 = max(0, min(y1, dims.padded_h - 1))
        x2 = max(x1 + 1, min(x2, dims.padded_w))
        y2 = max(y1 + 1, min(y2, dims.padded_h))
        
        # Map to original image coordinates
        orig_x1, orig_y1, orig_x2, orig_y2 = map_to_original_coordinates(x1, y1, x2, y2, dims)
        
        return x1, y1, x2, y2, orig_x1, orig_y1, orig_x2, orig_y2, coords
        
    except Exception as e:
        print(f"Error processing coordinates: {str(e)}")
        # Return safe default coordinates
        return 0, 0, 100, 100, 0, 0, 100, 100, coords


def map_to_original_coordinates(x1: int, y1: int, x2: int, y2: int, dims: ImageDimensions) -> Tuple[int, int, int, int]:
    """
    Map coordinates from padded image back to original image.
    
    Args:
        x1, y1, x2, y2: Coordinates in padded image
        dims: Image dimensions object
        
    Returns:
        Tuple of (x1, y1, x2, y2) coordinates in original image
    """
    try:
        # Calculate padding offsets
        pad_h = (dims.padded_h - dims.original_h) // 2
        pad_w = (dims.padded_w - dims.original_w) // 2
        
        # Map back to original coordinates
        orig_x1 = max(0, x1 - pad_w)
        orig_y1 = max(0, y1 - pad_h)
        orig_x2 = min(dims.original_w, x2 - pad_w)
        orig_y2 = min(dims.original_h, y2 - pad_h)
        
        # Ensure valid box dimensions
        if orig_x2 <= orig_x1:
            orig_x2 = min(orig_x1 + 1, dims.original_w)
        if orig_y2 <= orig_y1:
            orig_y2 = min(orig_y1 + 1, dims.original_h)
            
        return int(orig_x1), int(orig_y1), int(orig_x2), int(orig_y2)
        
    except Exception as e:
        print(f"Error mapping coordinates: {str(e)}")
        return 0, 0, min(100, dims.original_w), min(100, dims.original_h)


def check_coord_valid(x1: float, y1: float, x2: float, y2: float, 
                     image_size: Optional[Tuple[int, int]] = None, 
                     abs_coord: bool = True) -> Tuple[bool, Optional[str]]:
    """
    Check if coordinates are valid.
    
    Args:
        x1, y1, x2, y2: Coordinates to check
        image_size: Optional image size (width, height)
        abs_coord: Whether coordinates are absolute or normalized
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if x2 <= x1 or y2 <= y1:
        return False, f"Invalid box dimensions: [{x1}, {y1}, {x2}, {y2}]"
    
    if x1 < 0 or y1 < 0:
        return False, f"Negative coordinates: [{x1}, {y1}, {x2}, {y2}]"
    
    if not abs_coord:
        if x2 > 1 or y2 > 1:
            return False, f"Normalized coordinates out of range: [{x1}, {y1}, {x2}, {y2}]"
    elif image_size is not None:
        if x2 > image_size[0] or y2 > image_size[1]:
            return False, f"Coordinates out of image bounds: [{x1}, {y1}, {x2}, {y2}]"
    
    return True, None


def adjust_box_edges(image: np.ndarray, boxes: List[List[float]], 
                    max_pixels: int = 15, threshold: float = 0.2) -> List[List[float]]:
    """
    Adjust box edges to better align with content boundaries.
    
    Args:
        image: Image array
        boxes: List of bounding boxes [[x1, y1, x2, y2]]
        max_pixels: Maximum pixels to adjust
        threshold: Threshold for edge detection
        
    Returns:
        List of adjusted bounding boxes
    """
    if isinstance(image, str):
        image = cv2.imread(image)
    
    img_h, img_w = image.shape[:2]
    new_boxes = []
    
    for box in boxes:
        best_box = copy.deepcopy(box)
        current_box = copy.deepcopy(box)
        
        # Ensure box is within image bounds
        current_box[0] = max(0, min(current_box[0], img_w - 1))
        current_box[1] = max(0, min(current_box[1], img_h - 1))
        current_box[2] = max(current_box[0] + 1, min(current_box[2], img_w))
        current_box[3] = max(current_box[1] + 1, min(current_box[3], img_h))
        
        def check_edge(img: np.ndarray, box: List[float], edge_idx: int, is_vertical: bool) -> float:
            """Calculate edge score for box adjustment."""
            edge = int(box[edge_idx])
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            
            if is_vertical:
                line = binary[int(box[1]):int(box[3]) + 1, edge]
            else:
                line = binary[edge, int(box[0]):int(box[2]) + 1]
            
            if len(line) <= 1:
                return 1.0
            
            transitions = np.abs(np.diff(line.astype(float)))
            return np.sum(transitions) / len(transitions) if len(transitions) > 0 else 1.0
        
        # Edges to adjust: (index, direction, is_vertical)
        edges = [(0, -1, True), (2, 1, True), (1, -1, False), (3, 1, False)]
        
        for edge_idx, direction, is_vertical in edges:
            best_score = check_edge(image, current_box, edge_idx, is_vertical)
            
            if best_score <= threshold:
                continue
            
            for step in range(max_pixels):
                test_box = copy.deepcopy(current_box)
                test_box[edge_idx] += direction
                
                # Keep within bounds
                if edge_idx in [0, 2]:  # x coordinates
                    test_box[edge_idx] = max(0, min(test_box[edge_idx], img_w - 1))
                else:  # y coordinates
                    test_box[edge_idx] = max(0, min(test_box[edge_idx], img_h - 1))
                
                # Ensure valid box
                if edge_idx == 0 and test_box[0] >= test_box[2]:
                    break
                if edge_idx == 1 and test_box[1] >= test_box[3]:
                    break
                if edge_idx == 2 and test_box[2] <= test_box[0]:
                    break
                if edge_idx == 3 and test_box[3] <= test_box[1]:
                    break
                
                score = check_edge(image, test_box, edge_idx, is_vertical)
                
                if score < best_score:
                    best_score = score
                    best_box = copy.deepcopy(test_box)
                    current_box = copy.deepcopy(test_box)
                
                if score <= threshold:
                    break
        
        new_boxes.append(best_box)
    
    return new_boxes


def resize_image_with_aspect_ratio(image: Image.Image, target_size: Tuple[int, int]) -> Image.Image:
    """
    Resize image while maintaining aspect ratio.
    
    Args:
        image: PIL Image to resize
        target_size: Target size (width, height)
        
    Returns:
        Resized PIL Image
    """
    target_w, target_h = target_size
    orig_w, orig_h = image.size
    
    # Calculate scale to fit within target size
    scale = min(target_w / orig_w, target_h / orig_h)
    
    # Calculate new size
    new_w = int(orig_w * scale)
    new_h = int(orig_h * scale)
    
    # Resize image
    resized = image.resize((new_w, new_h), Image.Resampling.LANCZOS)
    
    # Create target size image with white background
    result = Image.new('RGB', target_size, color='white')
    
    # Center the resized image
    paste_x = (target_w - new_w) // 2
    paste_y = (target_h - new_h) // 2
    result.paste(resized, (paste_x, paste_y))
    
    return result


def enhance_image_for_ocr(image: Image.Image) -> Image.Image:
    """
    Enhance image quality for better OCR results.
    
    Args:
        image: PIL Image to enhance
        
    Returns:
        Enhanced PIL Image
    """
    # Convert to OpenCV format
    cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    
    # Apply denoising
    denoised = cv2.fastNlMeansDenoisingColored(cv_image, None, 10, 10, 7, 21)
    
    # Enhance contrast using CLAHE
    lab = cv2.cvtColor(denoised, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l = clahe.apply(l)
    enhanced = cv2.merge([l, a, b])
    enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
    
    # Convert back to PIL
    return Image.fromarray(cv2.cvtColor(enhanced, cv2.COLOR_BGR2RGB))


def crop_margin(image: Image.Image, margin_ratio: float = 0.02) -> Image.Image:
    """
    Crop margins from image to remove potential scanning artifacts.
    
    Args:
        image: PIL Image to crop
        margin_ratio: Ratio of margin to crop from each side
        
    Returns:
        Cropped PIL Image
    """
    width, height = image.size
    
    # Calculate crop margins
    margin_w = int(width * margin_ratio)
    margin_h = int(height * margin_ratio)
    
    # Crop the image
    left = margin_w
    top = margin_h
    right = width - margin_w
    bottom = height - margin_h
    
    return image.crop((left, top, right, bottom)) 