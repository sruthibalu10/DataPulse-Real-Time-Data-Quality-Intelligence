import io
import base64
import pandas as pd
from typing import Dict, List, Optional, Tuple, Union

def detect_file_type(filename: str) -> str:
    """
    Detect the type of file based on its extension.
    
    Args:
        filename: Name of the file
        
    Returns:
        String indicating the file type ('csv', 'excel', or 'unknown')
    """
    filename_lower = filename.lower()
    if filename_lower.endswith('.csv'):
        return 'csv'
    elif any(filename_lower.endswith(ext) for ext in ['.xls', '.xlsx', '.xlsm']):
        return 'excel'
    else:
        return 'unknown'

def read_file_content(content_string: str, file_type: str) -> pd.DataFrame:
    """
    Read the content of a file into a pandas DataFrame.
    
    Args:
        content_string: Base64 encoded content of the file
        file_type: Type of the file ('csv' or 'excel')
        
    Returns:
        pandas DataFrame containing the file contents
    
    Raises:
        ValueError: If the file type is unsupported
    """
    decoded = base64.b64decode(content_string)
    
    if file_type == 'csv':
        # Try different encodings and delimiters
        try:
            return pd.read_csv(io.StringIO(decoded.decode('utf-8')))
        except UnicodeDecodeError:
            try:
                return pd.read_csv(io.StringIO(decoded.decode('latin-1')))
            except Exception as e:
                raise ValueError(f"Failed to decode CSV with UTF-8 and Latin-1 encodings: {e}")
    elif file_type == 'excel':
        try:
            return pd.read_excel(io.BytesIO(decoded))
        except Exception as e:
            raise ValueError(f"Failed to read Excel file: {e}")
    else:
        raise ValueError(f"Unsupported file type: {file_type}")

def read_excel_sheets(content_string: str) -> Dict[str, pd.DataFrame]:
    """
    Read all sheets from an Excel file.
    
    Args:
        content_string: Base64 encoded content of the Excel file
        
    Returns:
        Dictionary mapping sheet names to pandas DataFrames
    """
    decoded = base64.b64decode(content_string)
    xl = pd.ExcelFile(io.BytesIO(decoded))
    
    sheets = {}
    for sheet_name in xl.sheet_names:
        sheets[sheet_name] = pd.read_excel(xl, sheet_name=sheet_name)
    
    return sheets

def extract_headers(df: pd.DataFrame) -> List[str]:
    """
    Extract headers (column names) from a DataFrame.
    
    Args:
        df: pandas DataFrame
        
    Returns:
        List of column names
    """
    return list(df.columns)

def compare_headers(headers_list: List[List[str]], labels: List[str]) -> pd.DataFrame:
    """
    Compare multiple sets of headers.
    
    Args:
        headers_list: List of lists, where each inner list contains headers
        labels: Labels for each set of headers
        
    Returns:
        DataFrame containing the comparison result
    """
    all_unique_headers = sorted(set().union(*headers_list))
    
    comparison_data = []
    for header in all_unique_headers:
        row = {'Header': header}
        for i, headers in enumerate(headers_list):
            row[labels[i]] = 'Present' if header in headers else 'Missing'
        comparison_data.append(row)
    
    return pd.DataFrame(comparison_data)

def extract_metadata(df: pd.DataFrame, filename: str) -> Dict:
    """
    Extract metadata from a DataFrame.
    
    Args:
        df: pandas DataFrame
        filename: Name of the file
        
    Returns:
        Dictionary containing metadata
    """
    return {
        'filename': filename,
        'rows': len(df),
        'columns': len(df.columns),
        'column_names': list(df.columns),
        'dtypes': {col: str(df[col].dtype) for col in df.columns},
        'missing_values': df.isna().sum().to_dict(),
        'duplicate_rows': df.duplicated().sum()
    }

def validate_template_file(sheets: Dict[str, pd.DataFrame]) -> Tuple[bool, str]:
    """
    Validate the structure of a template file.
    
    Args:
        sheets: Dictionary mapping sheet names to DataFrames
        
    Returns:
        Tuple of (is_valid, message)
    """
    # Check for required sheets
    required_sheets = ['Target header']
    missing_sheets = [sheet for sheet in required_sheets if sheet not in sheets]
    
    if missing_sheets:
        return False, f"Template is missing required sheets: {', '.join(missing_sheets)}"
    
    # Check if Target header sheet has content
    if sheets['Target header'].empty:
        return False, "Target header sheet is empty"
    
    return True, "Template file is valid"

def create_header_mapping(source_headers: List[str], target_headers: List[str], 
                         mapping_sheet: Optional[pd.DataFrame] = None) -> Dict[str, str]:
    """
    Create a mapping from source headers to target headers.
    
    Args:
        source_headers: List of source headers
        target_headers: List of target headers
        mapping_sheet: Optional DataFrame containing mapping information
        
    Returns:
        Dictionary mapping source headers to target headers
    """
    mapping = {}
    
    # First, map identical headers
    for source in source_headers:
        if source in target_headers:
            mapping[source] = source
    
    # Then, use the mapping sheet if provided
    if mapping_sheet is not None and not mapping_sheet.empty:
        # Assuming the mapping sheet has columns for source and target headers
        for _, row in mapping_sheet.iterrows():
            if 'source' in row and 'target' in row:
                mapping[row['source']] = row['target']
    
    return mapping