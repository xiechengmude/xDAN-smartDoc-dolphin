"""
Parsing utilities for SmartDoc Dolphin system.
"""

import re
import json
from typing import List, Tuple, Dict, Any

from ..core.models import DocumentElement, ElementType


def parse_layout_string(bbox_str: str) -> List[Tuple[List[float], str]]:
    """
    Parse layout string using regular expressions.
    
    Args:
        bbox_str: String containing bounding box and label information
        
    Returns:
        List of tuples containing (coordinates, label)
    """
    # Pattern to match coordinates and labels
    pattern = r"\[(\d*\.?\d+),\s*(\d*\.?\d+),\s*(\d*\.?\d+),\s*(\d*\.?\d+)\]\s*(\w+)"
    matches = re.finditer(pattern, bbox_str)
    
    parsed_results = []
    for match in matches:
        # Extract coordinates and convert to float
        coords = [float(match.group(i)) for i in range(1, 5)]
        label = match.group(5).strip().lower()
        parsed_results.append((coords, label))
    
    return parsed_results


def generate_markdown(elements: List[Dict]) -> str:
    """
    Generate markdown content from document elements.
    
    Args:
        elements: List of document elements
        
    Returns:
        Generated markdown string
    """
    # Sort elements by reading order
    sorted_elements = sorted(elements, key=lambda x: x.get("reading_order", 0))
    
    markdown_parts = []
    
    for element in sorted_elements:
        element_type = element.get("type", "text")
        element_text = element.get("text", "")
        
        if element_type == "text":
            # Add text content directly
            if element_text.strip():
                markdown_parts.append(element_text.strip())
                markdown_parts.append("")  # Add line break
                
        elif element_type == "table":
            # Format table content
            if element_text.strip():
                markdown_parts.append("### Table")
                markdown_parts.append("")
                # If the text is already markdown table format, use it directly
                if "|" in element_text:
                    markdown_parts.append(element_text.strip())
                else:
                    # Convert plain text table to markdown format
                    markdown_parts.append(f"```\n{element_text.strip()}\n```")
                markdown_parts.append("")
                
        elif element_type == "figure":
            # Add figure placeholder
            markdown_parts.append("### Figure")
            markdown_parts.append("")
            markdown_parts.append("*[Figure content]*")
            markdown_parts.append("")
            
        elif element_type == "formula":
            # Add formula content
            if element_text.strip():
                markdown_parts.append("### Formula")
                markdown_parts.append("")
                # Wrap formula in LaTeX math blocks
                formula_text = element_text.strip()
                if not formula_text.startswith("$$"):
                    formula_text = f"$${formula_text}$$"
                markdown_parts.append(formula_text)
                markdown_parts.append("")
    
    return "\n".join(markdown_parts).strip()


def generate_json_output(elements: List[Dict], processing_time: float) -> Dict[str, Any]:
    """
    Generate JSON output from document elements.
    
    Args:
        elements: List of document elements
        processing_time: Time taken to process the document
        
    Returns:
        JSON-serializable dictionary
    """
    return {
        "document_info": {
            "total_elements": len(elements),
            "processing_time": round(processing_time, 2),
            "element_types": {
                "text": len([e for e in elements if e.get("type") == "text"]),
                "table": len([e for e in elements if e.get("type") == "table"]),
                "figure": len([e for e in elements if e.get("type") == "figure"]),
                "formula": len([e for e in elements if e.get("type") == "formula"]),
            }
        },
        "elements": [
            {
                "element_id": element.get("element_id", ""),
                "type": element.get("type", "text"),
                "bbox": element.get("bbox", []),
                "text": element.get("text", ""),
                "confidence": element.get("confidence", 0.0),
                "reading_order": element.get("reading_order", 0),
                "metadata": element.get("metadata", {})
            }
            for element in sorted(elements, key=lambda x: x.get("reading_order", 0))
        ]
    }


def clean_text_content(text: str) -> str:
    """
    Clean and normalize text content.
    
    Args:
        text: Raw text content
        
    Returns:
        Cleaned text content
    """
    if not text:
        return ""
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove leading/trailing whitespace
    text = text.strip()
    
    # Remove special tokens that might be left from model output
    text = re.sub(r'<[^>]+>', '', text)
    
    # Remove extra punctuation
    text = re.sub(r'[^\w\s\.\,\?\!\;\:\-\(\)\[\]\{\}\"\'\/\\]', '', text)
    
    return text


def extract_table_structure(table_text: str) -> Dict[str, Any]:
    """
    Extract table structure from table text.
    
    Args:
        table_text: Raw table text
        
    Returns:
        Dictionary containing table structure information
    """
    if not table_text.strip():
        return {"rows": 0, "columns": 0, "data": []}
    
    lines = [line.strip() for line in table_text.split('\n') if line.strip()]
    
    if not lines:
        return {"rows": 0, "columns": 0, "data": []}
    
    # Try to detect markdown table format
    if "|" in table_text:
        rows = []
        for line in lines:
            if line.startswith("|") and line.endswith("|"):
                # Parse markdown table row
                cells = [cell.strip() for cell in line.split("|")[1:-1]]
                rows.append(cells)
            elif "|" in line:
                # Parse partial markdown table row
                cells = [cell.strip() for cell in line.split("|")]
                rows.append(cells)
        
        if rows:
            max_columns = max(len(row) for row in rows) if rows else 0
            return {
                "rows": len(rows),
                "columns": max_columns,
                "data": rows
            }
    
    # Fall back to simple line-based parsing
    return {
        "rows": len(lines),
        "columns": 1,
        "data": [[line] for line in lines]
    }


def merge_text_blocks(elements: List[DocumentElement], max_distance: float = 50.0) -> List[DocumentElement]:
    """
    Merge nearby text blocks that likely belong to the same paragraph.
    
    Args:
        elements: List of document elements
        max_distance: Maximum distance between elements to consider for merging
        
    Returns:
        List of elements with merged text blocks
    """
    if not elements:
        return elements
    
    # Only merge text elements
    text_elements = [e for e in elements if e.element_type == ElementType.TEXT]
    other_elements = [e for e in elements if e.element_type != ElementType.TEXT]
    
    if len(text_elements) <= 1:
        return elements
    
    # Sort by reading order
    text_elements.sort(key=lambda x: x.reading_order)
    
    merged = []
    current_group = [text_elements[0]]
    
    for i in range(1, len(text_elements)):
        current = text_elements[i]
        previous = current_group[-1]
        
        # Calculate distance between elements
        prev_bottom = previous.bbox[3]
        curr_top = current.bbox[1]
        vertical_distance = abs(curr_top - prev_bottom)
        
        # Check if elements should be merged
        if vertical_distance <= max_distance:
            current_group.append(current)
        else:
            # Merge current group and start new group
            if len(current_group) > 1:
                merged_element = _merge_element_group(current_group)
                merged.append(merged_element)
            else:
                merged.extend(current_group)
            current_group = [current]
    
    # Handle the last group
    if len(current_group) > 1:
        merged_element = _merge_element_group(current_group)
        merged.append(merged_element)
    else:
        merged.extend(current_group)
    
    # Combine with other elements and sort
    all_elements = merged + other_elements
    all_elements.sort(key=lambda x: x.reading_order)
    
    return all_elements


def _merge_element_group(elements: List[DocumentElement]) -> DocumentElement:
    """
    Merge a group of elements into a single element.
    
    Args:
        elements: List of elements to merge
        
    Returns:
        Merged document element
    """
    if not elements:
        raise ValueError("Cannot merge empty element group")
    
    if len(elements) == 1:
        return elements[0]
    
    # Calculate merged bounding box
    min_x = min(e.bbox[0] for e in elements)
    min_y = min(e.bbox[1] for e in elements)
    max_x = max(e.bbox[2] for e in elements)
    max_y = max(e.bbox[3] for e in elements)
    
    # Merge text content
    texts = [e.text for e in elements if e.text.strip()]
    merged_text = " ".join(texts)
    
    # Calculate average confidence
    confidences = [e.confidence for e in elements if e.confidence > 0]
    avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
    
    # Use the reading order of the first element
    reading_order = min(e.reading_order for e in elements)
    
    return DocumentElement(
        element_type=elements[0].element_type,
        bbox=[min_x, min_y, max_x, max_y],
        text=merged_text,
        confidence=avg_confidence,
        reading_order=reading_order
    ) 