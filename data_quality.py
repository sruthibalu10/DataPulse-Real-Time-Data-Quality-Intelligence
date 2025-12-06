import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Union, Any
import re
from datetime import datetime

def standardize_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardize all missing value representations to NaN.
    
    Args:
        df: Input DataFrame
        
    Returns:
        DataFrame with standardized missing values
    """
    df_copy = df.copy()
    
    # Common missing value representations
    missing_values = ['None', 'NA', 'N/A', 'na', 'n/a', 'null', 'NULL', 'nan', 'NaN', '']
    
    # Replace with NaN
    return df_copy.replace(missing_values, np.nan)

def get_column_statistics(df: pd.DataFrame, column: str) -> Dict[str, Any]:
    """
    Get basic statistics for a column.
    
    Args:
        df: Input DataFrame
        column: Column name
        
    Returns:
        Dictionary with column statistics
    """
    col_data = df[column]
    
    # Basic stats
    stats = {
        'count': len(col_data),
        'missing': col_data.isna().sum(),
        'missing_percent': (col_data.isna().sum() / len(col_data) * 100).round(2),
        'unique': col_data.nunique(),
        'unique_percent': (col_data.nunique() / len(col_data) * 100).round(2),
    }
    
    # Type-specific stats
    if pd.api.types.is_numeric_dtype(col_data):
        # Numeric column
        numeric_data = pd.to_numeric(col_data, errors='coerce')
        stats.update({
            'min': numeric_data.min(),
            'max': numeric_data.max(),
            'mean': numeric_data.mean(),
            'median': numeric_data.median(),
            'std': numeric_data.std(),
            'zeros': (numeric_data == 0).sum(),
            'zeros_percent': ((numeric_data == 0).sum() / len(numeric_data) * 100).round(2),
            'negative': (numeric_data < 0).sum(),
            'negative_percent': ((numeric_data < 0).sum() / len(numeric_data) * 100).round(2)
        })
    elif pd.api.types.is_datetime64_dtype(col_data):
        # Datetime column
        valid_dates = col_data.dropna()
        if not valid_dates.empty:
            stats.update({
                'min_date': valid_dates.min(),
                'max_date': valid_dates.max(),
                'date_range_days': (valid_dates.max() - valid_dates.min()).days
            })
    else:
        # String/object column
        valid_strings = col_data.dropna().astype(str)
        if not valid_strings.empty:
            stats.update({
                'min_length': valid_strings.str.len().min(),
                'max_length': valid_strings.str.len().max(),
                'avg_length': valid_strings.str.len().mean(),
                'empty_strings': (valid_strings == '').sum(),
                'empty_strings_percent': ((valid_strings == '').sum() / len(valid_strings) * 100).round(2)
            })
    
    return stats

def identify_date_columns(df: pd.DataFrame, threshold: float = 0.8) -> List[str]:
    """
    Identify columns that likely contain dates.
    
    Args:
        df: Input DataFrame
        threshold: Minimum percentage of values that should be convertible to dates
        
    Returns:
        List of column names that likely contain dates
    """
    date_columns = []
    
    for column in df.columns:
        # Skip columns that are already datetime
        if pd.api.types.is_datetime64_dtype(df[column]):
            date_columns.append(column)
            continue
            
        # Skip numeric columns
        if pd.api.types.is_numeric_dtype(df[column]):
            continue
            
        # Try to convert to datetime
        datetime_conversion = pd.to_datetime(df[column], errors='coerce')
        conversion_success = datetime_conversion.notna().mean()
        
        if conversion_success >= threshold:
            date_columns.append(column)
    
    return date_columns

def identify_numeric_columns(df: pd.DataFrame, threshold: float = 0.8) -> List[str]:
    """
    Identify columns that likely contain numeric values.
    
    Args:
        df: Input DataFrame
        threshold: Minimum percentage of values that should be convertible to numbers
        
    Returns:
        List of column names that likely contain numeric values
    """
    numeric_columns = []
    
    for column in df.columns:
        # Skip columns that are already numeric
        if pd.api.types.is_numeric_dtype(df[column]):
            numeric_columns.append(column)
            continue
            
        # Try to convert to numeric
        numeric_conversion = pd.to_numeric(df[column], errors='coerce')
        conversion_success = numeric_conversion.notna().mean()
        
        if conversion_success >= threshold:
            numeric_columns.append(column)
    
    return numeric_columns

def fix_numeric_values(value: Any) -> Any:
    """
    Fix common issues with numeric values.
    
    Args:
        value: Value to fix
        
    Returns:
        Fixed value
    """
    if pd.isna(value):
        return value
        
    # Convert to string
    str_value = str(value)
    
    # Handle empty strings
    if str_value.strip() == '':
        return np.nan
        
    # Replace comma with decimal point, but handle special cases
    # Case 1: Numbers like "1,000.00" (keep the thousand separator)
    if ',' in str_value and '.' in str_value:
        # Check if the comma is a thousand separator
        if str_value.find(',') < str_value.find('.'):
            str_value = str_value.replace(',', '')
    # Case 2: Numbers like "1,2" (convert comma to decimal point)
    elif ',' in str_value and not '.' in str_value:
        str_value = str_value.replace(',', '.')
        
    # Handle double periods (e.g., "1..2")
    str_value = str_value.replace('..', '.')
    
    # Handle special values
    if str_value.lower() in ['inf', '+inf', 'infinity']:
        return float('inf')
    elif str_value.lower() in ['-inf', '-infinity']:
        return float('-inf')
        
    # Handle values with leading symbols
    if str_value.startswith('>') or str_value.startswith('<'):
        # For things like "<0.3", return NaN
        return np.nan
        
    # Try to convert to float
    try:
        return float(str_value)
    except ValueError:
        return value

def fix_date_values(value: Any) -> Any:
    """
    Fix common issues with date values.
    
    Args:
        value: Value to fix
        
    Returns:
        Fixed value (datetime or original value if can't convert)
    """
    if pd.isna(value):
        return value
        
    # Convert to string
    str_value = str(value)
    
    # Handle empty strings
    if str_value.strip() == '':
        return np.nan
        
    # Try common date formats
    for date_format in [
        '%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y/%m/%d',
        '%Y-%m-%d %H:%M:%S', '%m/%d/%Y %H:%M:%S', '%d/%m/%Y %H:%M:%S',
        '%d-%b-%Y', '%d-%B-%Y', '%b-%d-%Y', '%B-%d-%Y'
    ]:
        try:
            return datetime.strptime(str_value, date_format)
        except ValueError:
            pass
    
    # If none of the common formats work, try pandas' flexible parser
    try:
        return pd.to_datetime(value)
    except:
        return value

def analyze_column_consistency(df: pd.DataFrame, column: str) -> Dict[str, Any]:
    """
    Analyze the consistency of values in a column.
    
    Args:
        df: Input DataFrame
        column: Column name
        
    Returns:
        Dictionary with consistency analysis results
    """
    col_data = df[column].dropna()
    
    if col_data.empty:
        return {'consistent': True, 'issues': []}
        
    # Case consistency for string columns
    if pd.api.types.is_object_dtype(col_data) or pd.api.types.is_string_dtype(col_data):
        # Check for case variations
        case_variations = {}
        for value in col_data.unique():
            if not isinstance(value, str):
                continue
                
            lower_val = value.lower()
            if lower_val in case_variations:
                case_variations[lower_val].append(value)
            else:
                case_variations[lower_val] = [value]
        
        # Find case inconsistencies
        case_issues = {k: v for k, v in case_variations.items() if len(v) > 1}
        
        if case_issues:
            return {
                'consistent': False,
                'issue_type': 'case_variation',
                'issues': case_issues
            }
    
    # Length consistency for string columns
    if pd.api.types.is_object_dtype(col_data) or pd.api.types.is_string_dtype(col_data):
        # Convert to string and get lengths
        str_lengths = col_data.astype(str).str.len()
        unique_lengths = str_lengths.unique()
        
        if len(unique_lengths) > 1:
            # Check if there's a dominant length
            length_counts = str_lengths.value_counts()
            dominant_length = length_counts.idxmax()
            dominant_percent = (length_counts[dominant_length] / len(str_lengths) * 100).round(2)
            
            if dominant_percent < 90:  # If less than 90% consistency
                return {
                    'consistent': False,
                    'issue_type': 'length_variation',
                    'dominant_length': int(dominant_length),
                    'dominant_percent': dominant_percent,
                    'unique_lengths': unique_lengths.tolist()
                }
    
    # Format consistency for numeric columns
    if pd.api.types.is_numeric_dtype(col_data):
        # Check for decimal precision consistency
        if col_data.dtype == float:
            decimal_places = {}
            
            for value in col_data:
                # Skip non-finite values
                if not np.isfinite(value):
                    continue
                    
                # Get string representation and count decimal places
                str_val = str(value)
                if '.' in str_val:
                    decimal_count = len(str_val.split('.')[1])
                else:
                    decimal_count = 0
                    
                if decimal_count in decimal_places:
                    decimal_places[decimal_count] += 1
                else:
                    decimal_places[decimal_count] = 1
            
            # Check if there's inconsistency in decimal places
            if len(decimal_places) > 1:
                total_values = sum(decimal_places.values())
                decimal_percents = {k: round(v / total_values * 100, 2) for k, v in decimal_places.items()}
                dominant_decimals = max(decimal_places.items(), key=lambda x: x[1])[0]
                dominant_percent = decimal_percents[dominant_decimals]
                
                if dominant_percent < 90:  # If less than 90% consistency
                    return {
                        'consistent': False,
                        'issue_type': 'decimal_variation',
                        'dominant_decimals': dominant_decimals,
                        'dominant_percent': dominant_percent,
                        'decimal_distribution': decimal_percents
                    }
    
    # Date format consistency
    if column in identify_date_columns(df[[column]]):
        # Try to convert to datetime
        date_conversion = pd.to_datetime(col_data, errors='coerce')
        conversion_success = date_conversion.notna().mean() * 100
        
        if conversion_success < 100 and conversion_success > 0:
            # Some but not all values could be converted to dates
            return {
                'consistent': False,
                'issue_type': 'date_format_variation',
                'conversion_success': conversion_success,
                'examples_failed': col_data[date_conversion.isna()].head(5).tolist()
            }
    
    # No consistency issues found
    return {'consistent': True}

def find_potential_typos(df: pd.DataFrame, column: str, similarity_threshold: float = 0.8) -> Dict[str, Any]:
    """
    Find potential typos in a string column.
    
    Args:
        df: Input DataFrame
        column: Column name
        similarity_threshold: Threshold for considering strings similar (0-1)
        
    Returns:
        Dictionary with potential typo findings
    """
    from difflib import SequenceMatcher
    
    col_data = df[column].dropna()
    
    if col_data.empty or not (pd.api.types.is_object_dtype(col_data) or pd.api.types.is_string_dtype(col_data)):
        return {'potential_typos': []}
    
    # Get value counts
    value_counts = col_data.value_counts()
    
    # Skip if too many unique values (performance optimization)
    if len(value_counts) > 100:
        return {'potential_typos': []}
    
    # Find similar strings
    similar_pairs = []
    unique_values = list(value_counts.index)
    
    for i in range(len(unique_values)):
        for j in range(i+1, len(unique_values)):
            str1 = str(unique_values[i])
            str2 = str(unique_values[j])
            
            # Skip very short strings
            if len(str1) < 3 or len(str2) < 3:
                continue
                
            # Calculate similarity
            similarity = SequenceMatcher(None, str1, str2).ratio()
            
            if similarity >= similarity_threshold:
                similar_pairs.append({
                    'value1': str1,
                    'value2': str2,
                    'count1': int(value_counts[unique_values[i]]),
                    'count2': int(value_counts[unique_values[j]]),
                    'similarity': similarity
                })
    
    return {'potential_typos': similar_pairs}

def detect_data_quality_issues(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Comprehensive data quality check across all columns.
    
    Args:
        df: Input DataFrame
        
    Returns:
        Dictionary with data quality issues
    """
    # Standardize missing values
    df_standardized = standardize_missing_values(df)
    
    # Initialize results
    quality_issues = {
        'missing_values': {},
        'data_type_issues': {},
        'consistency_issues': {},
        'potential_typos': {},
        'outliers': {},
        'summary': {
            'total_issues': 0,
            'columns_with_issues': 0,
            'critical_issues': 0
        }
    }
    
    # Check each column
    for column in df_standardized.columns:
        column_issues = []
        
        # 1. Check missing values
        missing_count = df_standardized[column].isna().sum()
        missing_percent = (missing_count / len(df_standardized) * 100).round(2)
        
        if missing_percent > 0:
            quality_issues['missing_values'][column] = {
                'count': int(missing_count),
                'percent': float(missing_percent)
            }
            
            if missing_percent > 20:
                column_issues.append(f"High missing values: {missing_percent}%")
        
        # 2. Check data type issues
        current_type = str(df_standardized[column].dtype)
        
        # Check if column could be date but isn't
        if column in identify_date_columns(df_standardized[[column]]) and not pd.api.types.is_datetime64_dtype(df_standardized[column]):
            quality_issues['data_type_issues'][column] = {
                'current_type': current_type,
                'suggested_type': 'datetime',
                'issue': 'Column contains date-like values but is not datetime type'
            }
            column_issues.append("Date format issues")
        
        # Check if column could be numeric but isn't
        elif column in identify_numeric_columns(df_standardized[[column]]) and not pd.api.types.is_numeric_dtype(df_standardized[column]):
            quality_issues['data_type_issues'][column] = {
                'current_type': current_type,
                'suggested_type': 'numeric',
                'issue': 'Column contains numeric-like values but is not numeric type'
            }
            column_issues.append("Numeric format issues")
        
        # 3. Check consistency issues
        consistency_result = analyze_column_consistency(df_standardized, column)
        if not consistency_result['consistent']:
            quality_issues['consistency_issues'][column] = consistency_result
            column_issues.append(f"Consistency issues: {consistency_result['issue_type']}")
        
        # 4. Check for potential typos in string columns
        if pd.api.types.is_object_dtype(df_standardized[column]) or pd.api.types.is_string_dtype(df_standardized[column]):
            typos_result = find_potential_typos(df_standardized, column)
            if typos_result['potential_typos']:
                quality_issues['potential_typos'][column] = typos_result
                column_issues.append(f"Potential typos: {len(typos_result['potential_typos'])} cases")
        
        # 5. Check for outliers in numeric columns
        if pd.api.types.is_numeric_dtype(df_standardized[column]):
            from scipy import stats
            
            # Convert to numeric and drop NaN
            numeric_data = pd.to_numeric(df_standardized[column], errors='coerce').dropna()
            
            if len(numeric_data) > 10:  # Only check if enough data points
                # Z-score method
                z_scores = stats.zscore(numeric_data, nan_policy='omit')
                outliers = abs(z_scores) > 3
                outlier_count = outliers.sum()
                outlier_percent = (outlier_count / len(numeric_data) * 100).round(2)
                
                if outlier_count > 0:
                    quality_issues['outliers'][column] = {
                        'count': int(outlier_count),
                        'percent': float(outlier_percent),
                        'method': 'zscore'
                    }
                    
                    if outlier_percent > 5:
                        column_issues.append(f"High outliers: {outlier_percent}%")
        
        # Update summary if issues found
        if column_issues:
            quality_issues['summary']['columns_with_issues'] += 1
            quality_issues['summary']['total_issues'] += len(column_issues)
            
            # Check for critical issues
            if any("High missing values" in issue for issue in column_issues) or \
               any("Consistency issues" in issue for issue in column_issues):
                quality_issues['summary']['critical_issues'] += 1
    
    return quality_issues

def suggest_data_cleaning_steps(quality_issues: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Suggest data cleaning steps based on detected quality issues.
    
    Args:
        quality_issues: Dictionary with quality issues from detect_data_quality_issues()
        
    Returns:
        List of suggested cleaning steps with priority
    """
    suggestions = []
    
    # 1. Suggestions for missing values
    for column, info in quality_issues['missing_values'].items():
        if info['percent'] > 50:
            suggestions.append({
                'priority': 'high',
                'type': 'missing_values',
                'column': column,
                'suggestion': f"Consider dropping column '{column}' due to excessive missing values ({info['percent']}%)",
                'action': 'drop_column'
            })
        elif info['percent'] > 20:
            suggestions.append({
                'priority': 'medium',
                'type': 'missing_values',
                'column': column,
                'suggestion': f"Handle missing values in '{column}' ({info['percent']}%)",
                'action': 'handle_missing'
            })
        else:
            suggestions.append({
                'priority': 'low',
                'type': 'missing_values',
                'column': column,
                'suggestion': f"Transform missing values in '{column}' to NaN",
                'action': 'standardize_missing'
            })
    
    # 2. Suggestions for data type issues
    for column, info in quality_issues['data_type_issues'].items():
        suggestions.append({
            'priority': 'high',
            'type': 'data_type',
            'column': column,
            'suggestion': f"Convert '{column}' from {info['current_type']} to {info['suggested_type']}",
            'action': 'convert_type'
        })
    
    # 3. Suggestions for consistency issues
    for column, info in quality_issues['consistency_issues'].items():
        if info['issue_type'] == 'case_variation':
            suggestions.append({
                'priority': 'medium',
                'type': 'consistency',
                'column': column,
                'suggestion': f"Standardize case in '{column}'",
                'action': 'standardize_case'
            })
        elif info['issue_type'] == 'decimal_variation':
            suggestions.append({
                'priority': 'medium',
                'type': 'consistency',
                'column': column,
                'suggestion': f"Standardize decimal places in '{column}' to {info.get('dominant_decimals', 2)}",
                'action': 'standardize_decimals'
            })
        else:
            suggestions.append({
                'priority': 'medium',
                'type': 'consistency',
                'column': column,
                'suggestion': f"Check consistency issues in '{column}'",
                'action': 'check_consistency'
            })
    
    # 4. Suggestions for potential typos
    for column, info in quality_issues['potential_typos'].items():
        if len(info['potential_typos']) > 0:
            suggestions.append({
                'priority': 'medium',
                'type': 'typos',
                'column': column,
                'suggestion': f"Review potential typos in '{column}' ({len(info['potential_typos'])} similar pairs)",
                'action': 'review_typos'
            })
    
    # 5. Suggestions for outliers
    for column, info in quality_issues['outliers'].items():
        if info['percent'] > 10:
            suggestions.append({
                'priority': 'medium',
                'type': 'outliers',
                'column': column,
                'suggestion': f"Handle outliers in '{column}' ({info['count']} outliers, {info['percent']}%)",
                'action': 'handle_outliers'
            })
        elif info['percent'] > 0:
            suggestions.append({
                'priority': 'low',
                'type': 'outliers',
                'column': column,
                'suggestion': f"Review outliers in '{column}' ({info['count']} outliers, {info['percent']}%)",
                'action': 'review_outliers'
            })
    
    # Sort suggestions by priority
    priority_order = {'high': 0, 'medium': 1, 'low': 2}
    suggestions.sort(key=lambda x: priority_order.get(x['priority'], 3))
    
    return suggestions