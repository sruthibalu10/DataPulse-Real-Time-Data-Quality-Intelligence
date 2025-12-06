import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Union, Any
import re
from datetime import datetime

def format_column_name(name: str) -> str:
    """
    Format a column name for display or use as an identifier.
    
    Args:
        name: Original column name
        
    Returns:
        Formatted column name
    """
    # Remove special characters
    formatted = re.sub(r'[^\w\s]', '', str(name))
    # Replace spaces with underscores
    formatted = formatted.replace(' ', '_')
    # Ensure it starts with a letter
    if not formatted or not formatted[0].isalpha():
        formatted = 'col_' + formatted
    
    return formatted

def get_column_type(df: pd.DataFrame, column: str) -> str:
    """
    Get the type category of a column for determining appropriate operations.
    
    Args:
        df: Input DataFrame
        column: Column name
        
    Returns:
        Type category ('numeric', 'datetime', 'text', or 'unknown')
    """
    if column not in df.columns:
        return 'unknown'
    
    dtype = df[column].dtype
    
    if pd.api.types.is_numeric_dtype(dtype):
        return 'numeric'
    elif pd.api.types.is_datetime64_dtype(dtype):
        return 'datetime'
    else:
        return 'text'

def safe_convert_numeric(value: Any) -> Optional[float]:
    """
    Safely convert a value to numeric, handling various formats.
    
    Args:
        value: Value to convert
        
    Returns:
        Converted numeric value or None if conversion fails
    """
    if pd.isna(value):
        return None
    
    if isinstance(value, (int, float)):
        return float(value)
    
    try:
        # Handle string representations
        str_value = str(value).strip()
        
        # Handle empty strings
        if not str_value:
            return None
        
        # Handle comma as decimal separator (e.g., "1,23")
        if ',' in str_value and '.' not in str_value:
            str_value = str_value.replace(',', '.')
        
        # Handle thousand separators (e.g., "1,000.00")
        if ',' in str_value and '.' in str_value:
            parts = str_value.split('.')
            if len(parts) == 2 and len(parts[1]) <= 3:
                str_value = str_value.replace(',', '')
        
        # Convert to float
        return float(str_value)
    except (ValueError, TypeError):
        # Try to extract numeric portion if there's a mix of numbers and text
        match = re.search(r'[-+]?[0-9]*\.?[0-9]+', str(value))
        if match:
            try:
                return float(match.group())
            except (ValueError, TypeError):
                return None
        
        return None

def safe_convert_datetime(value: Any) -> Optional[pd.Timestamp]:
    """
    Safely convert a value to datetime, handling various formats.
    
    Args:
        value: Value to convert
        
    Returns:
        Converted datetime value or None if conversion fails
    """
    if pd.isna(value):
        return None
    
    if isinstance(value, pd.Timestamp):
        return value
    
    try:
        return pd.to_datetime(value)
    except:
        # Try common date formats
        date_formats = [
            '%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y/%m/%d',
            '%Y-%m-%d %H:%M:%S', '%m/%d/%Y %H:%M:%S', '%d/%m/%Y %H:%M:%S',
            '%d-%b-%Y', '%d-%B-%Y', '%b-%d-%Y', '%B-%d-%Y'
        ]
        
        for fmt in date_formats:
            try:
                return pd.to_datetime(value, format=fmt)
            except:
                continue
        
        return None

def standardize_text(value: Any, operation: str = 'clean') -> str:
    """
    Standardize text values based on specified operation.
    
    Args:
        value: Value to standardize
        operation: Standardization operation
            - 'clean': Basic cleaning (trim whitespace, normalize spaces)
            - 'lower': Convert to lowercase
            - 'upper': Convert to uppercase
            - 'capitalize': Capitalize first letter
        
    Returns:
        Standardized text value
    """
    if pd.isna(value):
        return ''
    
    # Convert to string
    text = str(value)
    
    # Perform basic cleaning
    text = text.strip()
    text = re.sub(r'\s+', ' ', text)  # Normalize spaces
    
    # Apply specified operation
    if operation == 'lower':
        return text.lower()
    elif operation == 'upper':
        return text.upper()
    elif operation == 'capitalize':
        return text.capitalize()
    else:
        return text

def extract_pattern(text: str, pattern: str) -> Optional[str]:
    """
    Extract text matching a regex pattern.
    
    Args:
        text: Text to process
        pattern: Regular expression pattern
        
    Returns:
        Extracted text or None if no match
    """
    if pd.isna(text):
        return None
    
    try:
        match = re.search(pattern, str(text))
        return match.group(0) if match else None
    except:
        return None

def replace_pattern(text: str, pattern: str, replacement: str, use_regex: bool = False) -> str:
    """
    Replace occurrences of a pattern in text.
    
    Args:
        text: Text to process
        pattern: Text or pattern to find
        replacement: Replacement text
        use_regex: Whether to interpret pattern as regex
        
    Returns:
        Text with replacements applied
    """
    if pd.isna(text):
        return ''
    
    try:
        if use_regex:
            return re.sub(pattern, replacement, str(text))
        else:
            return str(text).replace(pattern, replacement)
    except:
        return str(text)

def create_value_mapping_dict(df: pd.DataFrame, source_column: str, 
                             mapping_rules: List[Dict[str, Any]]) -> Dict[Any, Any]:
    """
    Create a mapping dictionary from mapping rules.
    
    Args:
        df: Input DataFrame
        source_column: Source column name
        mapping_rules: List of mapping rules
        
    Returns:
        Dictionary mapping source values to target values
    """
    mapping_dict = {}
    
    for rule in mapping_rules:
        from_value = rule.get('from_value')
        to_value = rule.get('to_value')
        
        if from_value is not None and to_value is not None:
            mapping_dict[from_value] = to_value
    
    return mapping_dict

def apply_filter_condition(df: pd.DataFrame, condition: Dict[str, Any]) -> pd.DataFrame:
    """
    Apply a single filter condition to a DataFrame.
    
    Args:
        df: Input DataFrame
        condition: Filter condition
        
    Returns:
        Filtered DataFrame
    """
    column = condition.get('column')
    operator = condition.get('operator')
    value = condition.get('value')
    
    if not column or not operator or (value is None and operator not in ['is_null', 'is_not_null']):
        return df
    
    if column not in df.columns:
        return df
    
    # Apply the filter based on the operator
    if operator == 'eq':
        return df[df[column] == value]
    
    elif operator == 'neq':
        return df[df[column] != value]
    
    elif operator == 'gt':
        return df[df[column] > value]
    
    elif operator == 'gte':
        return df[df[column] >= value]
    
    elif operator == 'lt':
        return df[df[column] < value]
    
    elif operator == 'lte':
        return df[df[column] <= value]
    
    elif operator == 'contains':
        return df[df[column].astype(str).str.contains(str(value), na=False)]
    
    elif operator == 'not_contains':
        return df[~df[column].astype(str).str.contains(str(value), na=False)]
    
    elif operator == 'starts_with':
        return df[df[column].astype(str).str.startswith(str(value), na=False)]
    
    elif operator == 'ends_with':
        return df[df[column].astype(str).str.endswith(str(value), na=False)]
    
    elif operator == 'is_null':
        return df[df[column].isna()]
    
    elif operator == 'is_not_null':
        return df[df[column].notna()]
    
    elif operator == 'in_list':
        # Handle list of values
        if isinstance(value, str):
            value_list = [v.strip() for v in value.split(',')]
        else:
            value_list = [value]
        return df[df[column].isin(value_list)]
    
    elif operator == 'not_in_list':
        # Handle list of values
        if isinstance(value, str):
            value_list = [v.strip() for v in value.split(',')]
        else:
            value_list = [value]
        return df[~df[column].isin(value_list)]
    
    return df