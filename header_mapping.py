import pandas as pd
import numpy as np
import re
from typing import Dict, List, Optional, Tuple, Union
from difflib import SequenceMatcher

def clean_header(header: str) -> str:
    """
    Clean a header string by removing special characters and standardizing format.
    
    Args:
        header: The header string to clean
        
    Returns:
        Cleaned header string
    """
    # Convert to lowercase
    header_lower = header.lower()
    
    # Remove special characters
    header_clean = re.sub(r'[^a-z0-9]', '', header_lower)
    
    return header_clean

def similarity_score(a: str, b: str) -> float:
    """
    Calculate a similarity score between two strings.
    
    Args:
        a: First string
        b: Second string
        
    Returns:
        Similarity score between 0 and 1
    """
    return SequenceMatcher(None, a, b).ratio()

def map_headers_exact(source_headers: List[str], target_headers: List[str]) -> Dict[str, str]:
    """
    Map source headers to target headers using exact matching.
    
    Args:
        source_headers: List of source headers
        target_headers: List of target headers
        
    Returns:
        Dictionary mapping source headers to target headers
    """
    mapping = {}
    
    # Direct match
    for source in source_headers:
        if source in target_headers:
            mapping[source] = source
    
    return mapping

def map_headers_case_insensitive(source_headers: List[str], target_headers: List[str]) -> Dict[str, str]:
    """
    Map source headers to target headers using case-insensitive matching.
    
    Args:
        source_headers: List of source headers
        target_headers: List of target headers
        
    Returns:
        Dictionary mapping source headers to target headers
    """
    mapping = {}
    
    # Create lowercase mapping for target headers
    lower_target = {h.lower(): h for h in target_headers}
    
    for source in source_headers:
        if source.lower() in lower_target:
            mapping[source] = lower_target[source.lower()]
    
    return mapping

def map_headers_fuzzy(source_headers: List[str], target_headers: List[str], threshold: float = 0.8) -> Dict[str, str]:
    """
    Map source headers to target headers using fuzzy matching.
    
    Args:
        source_headers: List of source headers
        target_headers: List of target headers
        threshold: Minimum similarity score (0-1) to consider a match
        
    Returns:
        Dictionary mapping source headers to target headers
    """
    mapping = {}
    
    # Clean target headers for comparison
    clean_targets = {clean_header(h): h for h in target_headers}
    
    for source in source_headers:
        clean_source = clean_header(source)
        
        # Skip empty strings
        if not clean_source:
            continue
        
        # Find best match
        best_match = None
        best_score = 0
        
        for clean_target, original_target in clean_targets.items():
            score = similarity_score(clean_source, clean_target)
            if score > best_score:
                best_score = score
                best_match = original_target
        
        # Apply mapping if score exceeds threshold
        if best_score >= threshold and best_match:
            mapping[source] = best_match
    
    return mapping

def auto_map_headers(source_headers: List[str], target_headers: List[str]) -> Dict[str, str]:
    """
    Automatically map source headers to target headers using multiple methods.
    
    Args:
        source_headers: List of source headers
        target_headers: List of target headers
        
    Returns:
        Dictionary mapping source headers to target headers
    """
    # First try exact matches
    mapping = map_headers_exact(source_headers, target_headers)
    
    # Then try case-insensitive matches for unmapped headers
    unmapped = [h for h in source_headers if h not in mapping]
    case_mapping = map_headers_case_insensitive(unmapped, target_headers)
    mapping.update(case_mapping)
    
    # Finally try fuzzy matching for remaining unmapped headers
    unmapped = [h for h in source_headers if h not in mapping]
    fuzzy_mapping = map_headers_fuzzy(unmapped, target_headers)
    mapping.update(fuzzy_mapping)
    
    return mapping

def parse_mapping_sheet(mapping_df: pd.DataFrame) -> Dict[str, str]:
    """
    Parse a mapping sheet from template file.
    
    Args:
        mapping_df: DataFrame containing mapping information
        
    Returns:
        Dictionary mapping source headers to target headers
    """
    mapping = {}
    
    # Try to identify source and target columns
    columns = list(mapping_df.columns)
    
    # Look for columns that might contain source/target info
    source_col = None
    target_col = None
    
    for col in columns:
        col_lower = col.lower()
        if any(keyword in col_lower for keyword in ['source', 'input', 'from', 'original']):
            source_col = col
        elif any(keyword in col_lower for keyword in ['target', 'output', 'to', 'final']):
            target_col = col
    
    # If we found appropriate columns, build mapping
    if source_col and target_col:
        for _, row in mapping_df.iterrows():
            source = row[source_col]
            target = row[target_col]
            
            # Skip empty values
            if pd.notna(source) and pd.notna(target) and source and target:
                mapping[str(source)] = str(target)
    
    return mapping

def apply_header_mapping(df: pd.DataFrame, header_mapping: Dict[str, str], 
                         drop_unmapped: bool = False) -> pd.DataFrame:
    """
    Apply header mapping to a DataFrame.
    
    Args:
        df: Source DataFrame
        header_mapping: Dictionary mapping source headers to target headers
        drop_unmapped: Whether to drop columns that aren't in the mapping
        
    Returns:
        DataFrame with mapped headers
    """
    # Create a copy to avoid modifying the original
    result_df = df.copy()
    
    # Build rename dictionary (only for columns in the DataFrame)
    rename_dict = {col: header_mapping[col] for col in df.columns if col in header_mapping}
    
    # Rename columns
    if rename_dict:
        result_df = result_df.rename(columns=rename_dict)
    
    # Drop unmapped columns if requested
    if drop_unmapped:
        mapped_cols = [header_mapping.get(col, col) for col in df.columns if col in header_mapping]
        result_df = result_df[mapped_cols]
    
    return result_df

def generate_mapping_report(source_headers: List[str], header_mapping: Dict[str, str]) -> pd.DataFrame:
    """
    Generate a report of header mapping results.
    
    Args:
        source_headers: List of all source headers
        header_mapping: Dictionary mapping source headers to target headers
        
    Returns:
        DataFrame containing mapping report
    """
    report_data = []
    
    for header in source_headers:
        mapped_to = header_mapping.get(header, "Not mapped")
        status = "Mapped" if header in header_mapping else "Skipped"
        
        report_data.append({
            "Source Header": header,
            "Mapped To": mapped_to,
            "Status": status
        })
    
    return pd.DataFrame(report_data)