import io

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Union, Any
import dash
from dash import dcc, html, dash_table
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
from datetime import datetime
from scipy import stats


def add_interactive_cleaning_module_to_app(app):
    """
    Add interactive cleaning module callbacks to the app.
    """

    # Populate dropdown options based on available data
    @app.callback(
        [Output("missing-values-columns", "options"),
         Output("missing-values-columns", "value"),
         Output("date-format-columns", "options"),
         Output("date-format-columns", "value"),
         Output("numeric-format-columns", "options"),
         Output("numeric-format-columns", "value"),
         Output("outlier-columns", "options"),
         Output("outlier-columns", "value"),
         Output("duplicate-columns", "options"),
         Output("duplicate-columns", "value"),
         Output("rounding-columns", "options"),
         Output("rounding-columns", "value")],
        [Input("stored-compiled-data", "data"),
         Input("main-tabs", "active_tab")]  # Add tab change as a trigger
    )
    def populate_cleaning_dropdowns(compiled_data, active_tab):
        """
        Populate dropdown options for cleaning operations based on compiled data.
        """
        # Only update when on the cleaning tab
        if active_tab != "tab-cleaning":
            raise dash.exceptions.PreventUpdate

        if not compiled_data:
            empty_options = []
            return [empty_options, [], empty_options, [], empty_options, [],
                    empty_options, [], empty_options, [], empty_options, []]

        try:
            # Load the compiled data
            df = pd.read_json(io.StringIO(compiled_data["data"]), orient="split")

            # Create options for all columns
            all_columns = [{"label": col, "value": col} for col in df.columns]

            # Build a single list of ALL columns
            all_columns = [{"label": col, "value": col} for col in df.columns]
            numeric_cols = [col for col in df.columns
                            if pd.api.types.is_numeric_dtype(df[col])]

            # Use all columns for both date- and numeric-format correction
            date_options = all_columns
            numeric_options = all_columns

            # And set the defaults to *all* columns (so nothing is "missing" by default)
            date_default = []
            numeric_default = []

            # Columns with missing values
            # missing_cols = [col for col in df.columns if df[col].isna().any()]
            # missing_options = [{"label": col, "value": col} for col in missing_cols]
            missing_columns = all_columns
            missing_default = []
            # 7–8: outlier – use numeric columns by default
            outlier_options = numeric_options
            outlier_default = []

            # 9–10: duplicates – show all columns, default to none selected
            duplicate_options = all_columns
            duplicate_default = []

            # 11–12: rounding – numeric columns, default to none selected
            rounding_options = numeric_options
            rounding_default = []

            return [
                all_columns,  # 1: missing-options
                missing_default,  # 2: missing-value
                date_options,  # 3: date-options
                date_default,  # 4: date-value
                numeric_options,  # 5: numeric-options
                numeric_default,  # 6: numeric-value
                outlier_options,  # 7: outlier-options
                outlier_default,  # 8: outlier-value
                duplicate_options,  # 9: duplicate-options
                duplicate_default,  # 10: duplicate-value
                rounding_options,  # 11: rounding-options
                rounding_default  # 12: rounding-value
            ]
        except Exception as e:
            print(f"Error populating dropdowns: {str(e)}")
            empty_options = []
            return [empty_options, [], empty_options, [], empty_options, [],
                    empty_options, [], empty_options, [], empty_options, []]

    # Show custom input for missing values if selected
    # @app.callback(
    #     Output("missing-values-custom-input", "children"),
    #     [Input("missing-values-method", "value")]
    # )
    # def show_custom_missing_input(method):
    #     """
    #     Show custom input field if custom replacement is selected.
    #     """
    #     if method == "custom":
    #         return html.Div([
    #             html.Label("Custom replacement value:"),
    #             dbc.Input(id="custom-missing-value", type="text", placeholder="Enter value")
    #         ], className="mb-3")
    #     return []

    # Handle missing values
    @app.callback(
        [Output("cleaning-results", "children"),
         Output("stored-cleaned-data", "data")],
        [Input("apply-missing-values-btn", "n_clicks"),
         Input("apply-format-corrections-btn", "n_clicks"),
         Input("apply-outlier-handling-btn", "n_clicks"),
         Input("remove-duplicates-btn", "n_clicks"),
         Input("apply-rounding-btn", "n_clicks")],
        [State("missing-values-columns", "value"),
         State("missing-values-method", "value"),
         State("date-format-columns", "value"),
         State("numeric-format-columns", "value"),
         State("outlier-columns", "value"),
         State("outlier-method", "value"),
         State("outlier-handling", "value"),
         State("duplicate-columns", "value"),
         State("rounding-columns", "value"),
         State("decimal-places", "value"),
         State("stored-compiled-data", "data"),
         State("stored-cleaned-data", "data")]
    )
    def process_cleaning_operations(
            missing_clicks, format_clicks, outlier_clicks, duplicate_clicks, rounding_clicks,
            missing_columns, missing_method,
            date_columns, numeric_columns, outlier_columns, outlier_method, outlier_handling,
            duplicate_columns, rounding_columns, decimal_places,
            compiled_data, cleaned_data
    ):
        """
        Apply selected cleaning operations to the data.
        """
        # Determine which button was clicked
        ctx = dash.callback_context
        if not ctx.triggered:
            return None, cleaned_data

        button_id = ctx.triggered[0]["prop_id"].split(".")[0]

        # Get the latest data to work with
        if cleaned_data:
            df = pd.read_json(io.StringIO(cleaned_data["data"]), orient="split")
            cleaning_history = cleaned_data.get("cleaning_history", [])
            column_stats = cleaned_data.get("column_stats", {})
        elif compiled_data:
            df = pd.read_json(io.StringIO(compiled_data["data"]), orient="split")
            cleaning_history = []
            column_stats = {}
        else:
            # Return a user-friendly message instead of an error
            return html.Div("Please upload and compile data first before cleaning."), None

        try:
            # Store the original dataframe for comparison
            df_original = df.copy()
            operation_performed = False

            # Apply the appropriate cleaning operation based on which button was clicked
            if button_id == "apply-missing-values-btn" and missing_columns:
                # Using a custom_value of None for now (you can add this input if needed)
                df, result_msg, operation_stats = handle_missing_values(df, missing_columns, missing_method)

                # Create detailed cleaning history entry
                cleaning_entry = {
                    "operation": "missing_values",
                    "timestamp": datetime.now().isoformat(),
                    "columns": missing_columns,
                    "method": missing_method,
                    "result_message": result_msg,
                    "stats": operation_stats
                }
                cleaning_history.append(cleaning_entry)
                operation_performed = True

            elif button_id == "apply-format-corrections-btn" and (date_columns or numeric_columns):
                df, result_msg, operation_stats = correct_data_formats(df, date_columns, numeric_columns)

                # Create detailed cleaning history entry
                cleaning_entry = {
                    "operation": "format_correction",
                    "timestamp": datetime.now().isoformat(),
                    "date_columns": date_columns,
                    "numeric_columns": numeric_columns,
                    "result_message": result_msg,
                    "stats": operation_stats
                }
                cleaning_history.append(cleaning_entry)
                operation_performed = True

            elif button_id == "apply-outlier-handling-btn" and outlier_columns:
                df, result_msg, operation_stats = handle_outliers(df, outlier_columns, outlier_method, outlier_handling)

                # Create detailed cleaning history entry
                cleaning_entry = {
                    "operation": "outlier_handling",
                    "timestamp": datetime.now().isoformat(),
                    "columns": outlier_columns,
                    "method": outlier_method,
                    "handling": outlier_handling,
                    "result_message": result_msg,
                    "stats": operation_stats
                }
                cleaning_history.append(cleaning_entry)
                operation_performed = True

            elif button_id == "remove-duplicates-btn":
                df, result_msg, operation_stats = remove_duplicates(df, duplicate_columns)

                # Create detailed cleaning history entry
                cleaning_entry = {
                    "operation": "remove_duplicates",
                    "timestamp": datetime.now().isoformat(),
                    "columns": duplicate_columns,
                    "result_message": result_msg,
                    "stats": operation_stats
                }
                cleaning_history.append(cleaning_entry)
                operation_performed = True

            elif button_id == "apply-rounding-btn" and rounding_columns:
                df, result_msg, operation_stats = round_numeric_values(df, rounding_columns, decimal_places)

                # Create detailed cleaning history entry
                cleaning_entry = {
                    "operation": "rounding",
                    "timestamp": datetime.now().isoformat(),
                    "columns": rounding_columns,
                    "decimal_places": decimal_places,
                    "result_message": result_msg,
                    "stats": operation_stats
                }
                cleaning_history.append(cleaning_entry)
                operation_performed = True

            # If no operation was performed, show a friendly message
            if not operation_performed:
                return html.Div("Please select columns for the operation."), cleaned_data

            # Update column statistics
            column_stats = calculate_column_statistics(df)

        except Exception as e:
            # Log the error to console but don't show it in the UI
            print(f"Error during cleaning operation: {str(e)}")

            # Return a user-friendly message
            return html.Div(
                "Operation could not be completed. Please check your selections and try again."), cleaned_data

        # Create result output
        result_output = html.Div([
            html.Hr(),
            html.H5("Cleaning Operation Results"),
            html.P(result_msg),

            # Preview of cleaned data
            html.H6("Preview of Cleaned Data:"),
            dash_table.DataTable(
                columns=[{'name': col, 'id': col} for col in df.columns],
                data=df.head(10).to_dict('records'),
                style_table={'overflowX': 'auto'},
                page_size=10
            ),

            # Display cleaning history
            html.Hr(),
            html.H6("Cleaning History:"),
            html.Div([
                html.Div([
                    html.Strong(f"Operation {i + 1}: {op['operation'].replace('_', ' ').title()}"),
                    html.P(f"Time: {op['timestamp']}"),
                    html.P(f"Details: {op['result_message']}"),
                    # Display affected columns
                    html.P(
                        f"Affected Columns: {', '.join(op.get('columns', op.get('date_columns', []) + op.get('numeric_columns', [])))}") if 'columns' in op or 'date_columns' in op or 'numeric_columns' in op else None,
                    # Display statistics if available
                    html.Div([
                        html.P(f"Values Changed: {op['stats'].get('values_changed', 'Unknown')}"),
                        html.P(f"Rows Affected: {op['stats'].get('rows_affected', 'Unknown')}")
                    ]) if 'stats' in op else None
                ], className="mb-3") for i, op in enumerate(cleaning_history)
            ])
        ])

        # Store cleaned data with enhanced cleaning history and column statistics
        new_cleaned_data = {
            'data': df.to_json(date_format='iso', orient='split'),
            'rows': len(df),
            'columns': list(df.columns),
            'cleaning_history': cleaning_history,
            'column_stats': column_stats
        }

        return result_output, new_cleaned_data


def calculate_column_statistics(df):
    """
    Calculate detailed statistics for each column in the DataFrame.

    Args:
        df: Input DataFrame

    Returns:
        Dictionary with column statistics
    """
    stats = {}

    for col in df.columns:
        col_stats = {
            'data_type': str(df[col].dtype),
            'non_null_count': int(df[col].count()),
            'missing_count': int(df[col].isna().sum()),
            'missing_percent': round(df[col].isna().sum() / len(df) * 100, 2),
            'unique_count': int(df[col].nunique())
        }

        # Add numeric statistics if applicable
        if pd.api.types.is_numeric_dtype(df[col]):
            col_stats.update({
                'min': float(df[col].min()) if not df[col].empty and not pd.isna(df[col].min()) else None,
                'max': float(df[col].max()) if not df[col].empty and not pd.isna(df[col].max()) else None,
                'mean': float(df[col].mean()) if not df[col].empty and not pd.isna(df[col].mean()) else None,
                'median': float(df[col].median()) if not df[col].empty and not pd.isna(df[col].median()) else None,
                'std_dev': float(df[col].std()) if not df[col].empty and not pd.isna(df[col].std()) else None
            })

        # Add datetime statistics if applicable
        elif pd.api.types.is_datetime64_dtype(df[col]):
            non_null = df[col].dropna()
            if not non_null.empty:
                col_stats.update({
                    'min': non_null.min().isoformat(),
                    'max': non_null.max().isoformat(),
                    'range_days': (non_null.max() - non_null.min()).days
                })

        # Add string statistics if applicable
        elif pd.api.types.is_object_dtype(df[col]) or pd.api.types.is_string_dtype(df[col]):
            non_null = df[col].dropna().astype(str)
            if not non_null.empty:
                col_stats.update({
                    'min_length': int(non_null.str.len().min()),
                    'max_length': int(non_null.str.len().max()),
                    'avg_length': float(non_null.str.len().mean())
                })

        stats[col] = col_stats

    return stats


# Helper functions for data cleaning - enhanced to track more detailed information
def handle_missing_values(df, columns, method, custom_value=None):
    """
    Handle missing values in the specified columns.

    Args:
        df: Input DataFrame
        columns: List of columns to process
        method: Method to handle missing values (drop, mean, median, zero, custom)
        custom_value: Custom replacement value if method is 'custom'

    Returns:
        Tuple of (processed DataFrame, result message, operation statistics)
    """
    df_copy = df.copy()
    initial_row_count = len(df_copy)

    # Track changes for detailed metadata
    operation_stats = {
        'values_changed': 0,
        'rows_affected': 0,
        'before_after_samples': []
    }

    if method == "drop":
        # Track rows to be dropped
        rows_to_drop = df_copy[df_copy[columns].isna().any(axis=1)].index
        rows_affected = len(rows_to_drop)

        # Capture sample values before dropping (for metadata)
        if not rows_to_drop.empty:
            for col in columns:
                missing_rows = df_copy[df_copy[col].isna()]
                if not missing_rows.empty:
                    for idx, row in missing_rows.head(3).iterrows():  # Sample up to 3 rows
                        operation_stats['before_after_samples'].append({
                            'column': col,
                            'row_index': int(idx),
                            'before': 'NULL',
                            'after': 'DROPPED'
                        })

        # Drop rows with missing values in the specified columns
        df_copy = df_copy.dropna(subset=columns)
        removed_rows = initial_row_count - len(df_copy)

        # Update operation stats
        operation_stats['values_changed'] = removed_rows
        operation_stats['rows_affected'] = rows_affected

        result_msg = f"Removed {removed_rows} rows with missing values in the selected columns."
    else:
        # Replace missing values - track detailed changes for each column
        total_changes = 0
        affected_rows = set()

        for col in columns:
            # Count missing values before replacement
            missing_mask = df_copy[col].isna()
            missing_count = missing_mask.sum()

            if missing_count > 0:
                # Record the indices of affected rows
                affected_indices = df_copy[missing_mask].index.tolist()
                affected_rows.update(affected_indices)

                # Track sample before values (up to 3)
                sample_indices = affected_indices[:3]

                # Determine replacement value
                if pd.api.types.is_numeric_dtype(df_copy[col]):
                    if method == "mean":
                        fill_value = df_copy[col].mean()
                        df_copy[col] = df_copy[col].fillna(fill_value)
                        value_desc = f"mean ({fill_value:.4f})"
                    elif method == "median":
                        fill_value = df_copy[col].median()
                        df_copy[col] = df_copy[col].fillna(fill_value)
                        value_desc = f"median ({fill_value:.4f})"
                    elif method == "zero":
                        fill_value = 0
                        df_copy[col] = df_copy[col].fillna(fill_value)
                        value_desc = "0"
                    elif method == "custom" and custom_value is not None:
                        try:
                            # Try to convert to numeric if column is numeric
                            fill_value = float(custom_value)
                            df_copy[col] = df_copy[col].fillna(fill_value)
                            value_desc = f"custom value ({fill_value})"
                        except ValueError:
                            # Use the string value if conversion fails
                            fill_value = custom_value
                            df_copy[col] = df_copy[col].fillna(fill_value)
                            value_desc = f"custom value ({fill_value})"
                else:
                    # For non-numeric columns
                    if method == "zero":
                        fill_value = "0"
                        df_copy[col] = df_copy[col].fillna(fill_value)
                        value_desc = '"0"'
                    elif method in ["mean", "median"]:
                        fill_value = "N/A"
                        df_copy[col] = df_copy[col].fillna(fill_value)
                        value_desc = '"N/A"'
                    elif method == "custom" and custom_value is not None:
                        fill_value = custom_value
                        df_copy[col] = df_copy[col].fillna(fill_value)
                        value_desc = f'"{fill_value}"'
                    else:
                        fill_value = "N/A"
                        df_copy[col] = df_copy[col].fillna(fill_value)
                        value_desc = '"N/A"'

                # Record sample replacements for detailed metadata
                for idx in sample_indices:
                    operation_stats['before_after_samples'].append({
                        'column': col,
                        'row_index': int(idx),
                        'before': 'NULL',
                        'after': str(fill_value)
                    })

                # Update counts
                total_changes += missing_count

        # Update operation stats
        operation_stats['values_changed'] = total_changes
        operation_stats['rows_affected'] = len(affected_rows)

        result_msg = f"Replaced {total_changes} missing values in {len(columns)} columns using {method} method."
        if method == "custom":
            result_msg = f"Replaced {total_changes} missing values in {len(columns)} columns with custom value: {custom_value}"

    # Count remaining missing values
    remaining_missing = df_copy[columns].isna().sum().sum()

    if remaining_missing > 0:
        result_msg += f" There are still {remaining_missing} missing values."

    return df_copy, result_msg, operation_stats


def correct_data_formats(df, date_columns, numeric_columns):
    """
    Correct data formats for date and numeric columns.

    Args:
        df: Input DataFrame
        date_columns: List of columns to convert to dates
        numeric_columns: List of columns to convert to numeric

    Returns:
        Tuple of (processed DataFrame, result message, operation statistics)
    """
    df_copy = df.copy()
    corrections_count = 0

    # Track changes for detailed metadata
    operation_stats = {
        'values_changed': 0,
        'rows_affected': 0,
        'date_values_changed': 0,
        'numeric_values_changed': 0,
        'before_after_samples': []
    }

    # Convert date columns
    date_corrections = 0
    date_affected_rows = set()

    for col in date_columns or []:
        if col in df_copy.columns:
            # Track the original values for comparison
            original_values = df_copy[col].copy()

            # Apply date formatting function
            try:
                df_copy[col] = pd.to_datetime(df_copy[col], errors='coerce')

                # Find changed values by comparing with original
                changed_mask = ~df_copy[col].isna() & (
                            (original_values.astype(str) != df_copy[col].astype(str)) | original_values.isna())
                changed_count = changed_mask.sum()

                # Update counts
                date_corrections += changed_count
                date_affected_rows.update(df_copy[changed_mask].index.tolist())

                # Record sample changes for detailed metadata (up to 3)
                sample_indices = df_copy[changed_mask].head(3).index.tolist()
                for idx in sample_indices:
                    before_val = str(original_values.loc[idx]) if not pd.isna(original_values.loc[idx]) else "NULL"
                    after_val = str(df_copy[col].loc[idx]) if not pd.isna(df_copy[col].loc[idx]) else "NULL"

                    operation_stats['before_after_samples'].append({
                        'column': col,
                        'row_index': int(idx),
                        'before': before_val,
                        'after': after_val
                    })

            except Exception as e:
                print(f"Error converting {col} to date: {str(e)}")

    # Convert numeric columns
    numeric_corrections = 0
    numeric_affected_rows = set()

    for col in numeric_columns or []:
        if col in df_copy.columns:
            # Track the original values for comparison
            original_values = df_copy[col].copy()

            # Apply numeric formatting function
            try:
                df_copy[col] = pd.to_numeric(df_copy[col], errors='coerce')

                # Find changed values by comparing with original
                changed_mask = ~df_copy[col].isna() & (
                            (original_values.astype(str) != df_copy[col].astype(str)) | original_values.isna())
                changed_count = changed_mask.sum()

                # Update counts
                numeric_corrections += changed_count
                numeric_affected_rows.update(df_copy[changed_mask].index.tolist())

                # Record sample changes for detailed metadata (up to 3)
                sample_indices = df_copy[changed_mask].head(3).index.tolist()
                for idx in sample_indices:
                    before_val = str(original_values.loc[idx]) if not pd.isna(original_values.loc[idx]) else "NULL"
                    after_val = str(df_copy[col].loc[idx]) if not pd.isna(df_copy[col].loc[idx]) else "NULL"

                    operation_stats['before_after_samples'].append({
                        'column': col,
                        'row_index': int(idx),
                        'before': before_val,
                        'after': after_val
                    })

            except Exception as e:
                print(f"Error converting {col} to numeric: {str(e)}")

    # Update overall stats
    total_corrections = date_corrections + numeric_corrections
    total_affected_rows = len(date_affected_rows.union(numeric_affected_rows))

    operation_stats['values_changed'] = total_corrections
    operation_stats['rows_affected'] = total_affected_rows
    operation_stats['date_values_changed'] = date_corrections
    operation_stats['numeric_values_changed'] = numeric_corrections

    result_msg = f"Applied format corrections to {total_corrections} values across {total_affected_rows} rows."

    if date_columns:
        result_msg += f" Converted {date_corrections} values in {len(date_columns)} date columns."

    if numeric_columns:
        result_msg += f" Converted {numeric_corrections} values in {len(numeric_columns)} numeric columns."

    return df_copy, result_msg, operation_stats


def handle_outliers(df, columns, method="zscore", handling="cap"):
    """
    Identify and handle outliers in numeric columns.

    Args:
        df: Input DataFrame
        columns: List of columns to process
        method: Detection method ('zscore' or 'iqr')
        handling: Handling method ('remove', 'cap', 'mean', 'median')

    Returns:
        Tuple of (processed DataFrame, result message, operation statistics)
    """
    df_copy = df.copy()
    total_outliers = 0
    all_outlier_indices = set()

    # Track changes for detailed metadata
    operation_stats = {
        'values_changed': 0,
        'rows_affected': 0,
        'outliers_per_column': {},
        'before_after_samples': []
    }

    for col in columns:
        if col in df_copy.columns and pd.api.types.is_numeric_dtype(df_copy[col]):
            # Get numeric data without NaNs
            data = df_copy[col].dropna()

            # Skip if not enough data
            if len(data) < 3:
                continue

            # Detect outliers
            if method == "zscore":
                z_scores = np.abs(stats.zscore(data, nan_policy='omit'))
                outliers = z_scores > 3
                outlier_indices = data.index[outliers]

                # Store thresholds for reporting
                mean_val = data.mean()
                std_val = data.std()
                lower_threshold = mean_val - 3 * std_val
                upper_threshold = mean_val + 3 * std_val
                threshold_info = f"mean±3std: [{lower_threshold:.4f}, {upper_threshold:.4f}]"

            else:  # IQR method
                q1 = data.quantile(0.25)
                q3 = data.quantile(0.75)
                iqr = q3 - q1
                lower_bound = q1 - 1.5 * iqr
                upper_bound = q3 + 1.5 * iqr
                outliers = (data < lower_bound) | (data > upper_bound)
                outlier_indices = data.index[outliers]

                # Store thresholds for reporting
                threshold_info = f"IQR bounds: [{lower_bound:.4f}, {upper_bound:.4f}]"

            # Count outliers
            outlier_count = len(outlier_indices)
            total_outliers += outlier_count
            all_outlier_indices.update(outlier_indices)

            # Store per-column outlier count
            operation_stats['outliers_per_column'][col] = {
                'count': outlier_count,
                'percent': round(outlier_count / len(data) * 100, 2),
                'threshold_info': threshold_info
            }

            # Handle outliers
            if outlier_count > 0:
                # Store original values for reporting
                original_values = df_copy.loc[outlier_indices, col].copy()

                if handling == "remove":
                    # For tracking changes before removing rows
                    for idx in outlier_indices[:3]:  # Limit to 3 samples
                        operation_stats['before_after_samples'].append({
                            'column': col,
                            'row_index': int(idx),
                            'before': float(original_values.loc[idx]),
                            'after': 'REMOVED'
                        })

                    df_copy = df_copy.drop(outlier_indices)

                elif handling == "cap":
                    if method == "zscore":
                        # Cap at ±3 standard deviations
                        mean = data.mean()
                        std = data.std()

                        # Process upper outliers
                        upper_mask = df_copy[col] > mean + 3 * std
                        upper_indices = df_copy[upper_mask].index

                        if len(upper_indices) > 0:
                            cap_value = mean + 3 * std

                            # Record sample changes
                            for idx in upper_indices[:3]:
                                if idx in original_values.index:
                                    operation_stats['before_after_samples'].append({
                                        'column': col,
                                        'row_index': int(idx),
                                        'before': float(original_values.loc[idx]),
                                        'after': float(cap_value)
                                    })

                            # Apply capping
                            df_copy.loc[upper_mask, col] = cap_value

                        # Process lower outliers
                        lower_mask = df_copy[col] < mean - 3 * std
                        lower_indices = df_copy[lower_mask].index

                        if len(lower_indices) > 0:
                            cap_value = mean - 3 * std

                            # Record sample changes
                            for idx in lower_indices[:3]:
                                if idx in original_values.index:
                                    operation_stats['before_after_samples'].append({
                                        'column': col,
                                        'row_index': int(idx),
                                        'before': float(original_values.loc[idx]),
                                        'after': float(cap_value)
                                    })

                            # Apply capping
                            df_copy.loc[lower_mask, col] = cap_value

                    else:  # IQR method
                        # Cap at IQR boundaries
                        # Process upper outliers
                        upper_mask = df_copy[col] > upper_bound
                        upper_indices = df_copy[upper_mask].index

                        if len(upper_indices) > 0:
                            # Record sample changes
                            for idx in upper_indices[:3]:
                                if idx in original_values.index:
                                    operation_stats['before_after_samples'].append({
                                        'column': col,
                                        'row_index': int(idx),
                                        'before': float(original_values.loc[idx]),
                                        'after': float(upper_bound)
                                    })

                            # Apply capping
                            df_copy.loc[upper_mask, col] = upper_bound

                        # Process lower outliers
                        lower_mask = df_copy[col] < lower_bound
                        lower_indices = df_copy[lower_mask].index

                        if len(lower_indices) > 0:
                            # Record sample changes
                            for idx in lower_indices[:3]:
                                if idx in original_values.index:
                                    operation_stats['before_after_samples'].append({
                                        'column': col,
                                        'row_index': int(idx),
                                        'before': float(original_values.loc[idx]),
                                        'after': float(lower_bound)
                                    })

                            # Apply capping
                            df_copy.loc[lower_mask, col] = lower_bound

                elif handling == "mean":
                    mean_value = data[~outliers].mean()

                    # Record sample changes
                    for idx in outlier_indices[:3]:
                        if idx in df_copy.index:
                            operation_stats['before_after_samples'].append({
                                'column': col,
                                'row_index': int(idx),
                                'before': float(original_values.loc[idx]),
                                'after': float(mean_value)
                            })

                    # Apply replacement
                    df_copy.loc[outlier_indices, col] = mean_value

                elif handling == "median":
                    median_value = data[~outliers].median()

                    # Record sample changes
                    for idx in outlier_indices[:3]:
                        if idx in df_copy.index:
                            operation_stats['before_after_samples'].append({
                                'column': col,
                                'row_index': int(idx),
                                'before': float(original_values.loc[idx]),
                                'after': float(median_value)
                            })

                    # Apply replacement
                    df_copy.loc[outlier_indices, col] = median_value

    # Update operation stats
    operation_stats['values_changed'] = total_outliers
    operation_stats['rows_affected'] = len(all_outlier_indices)

    # Create result message
    result_msg = f"Found {total_outliers} outliers across {len(columns)} columns using {method} method."

    if total_outliers > 0:
        if handling == "remove":
            rows_removed = len(df) - len(df_copy)
            result_msg += f" Removed {rows_removed} rows with outliers."
        elif handling == "cap":
            result_msg += f" Capped {total_outliers} outliers at threshold values."
        elif handling == "mean":
            result_msg += f" Replaced {total_outliers} outliers with mean values (excluding outliers)."
        elif handling == "median":
            result_msg += f" Replaced {total_outliers} outliers with median values (excluding outliers)."

    return df_copy, result_msg, operation_stats


def remove_duplicates(df, columns=None):
    """
    Remove duplicate rows from the DataFrame.

    Args:
        df: Input DataFrame
        columns: List of columns to consider for duplicates (None = all columns)

    Returns:
        Tuple of (processed DataFrame, result message, operation statistics)
    """
    df_copy = df.copy()
    initial_row_count = len(df_copy)

    # Track changes for detailed metadata
    operation_stats = {
        'values_changed': 0,
        'rows_affected': 0,
        'before_after_samples': []
    }

    # Find duplicate indices before removal
    if columns:
        duplicate_mask = df_copy.duplicated(subset=columns, keep='first')
        duplicate_indices = df_copy[duplicate_mask].index.tolist()
    else:
        duplicate_mask = df_copy.duplicated(keep='first')
        duplicate_indices = df_copy[duplicate_mask].index.tolist()

    # Record sample duplicates before removal
    for idx in duplicate_indices[:3]:  # Limit to 3 samples
        sample_row = df_copy.loc[idx]

        # For duplicates, show which columns match
        matching_cols = []
        if columns:
            for col in columns:
                matching_cols.append(f"{col}: {sample_row[col]}")
        else:
            # Just pick a few columns to show as examples
            for col in df_copy.columns[:3]:
                matching_cols.append(f"{col}: {sample_row[col]}")

        sample_info = ", ".join(matching_cols)

        operation_stats['before_after_samples'].append({
            'row_index': int(idx),
            'before': f"Duplicate row with {sample_info}",
            'after': 'REMOVED'
        })

    # Remove duplicates
    if columns:
        df_copy = df_copy.drop_duplicates(subset=columns)
        removed_rows = initial_row_count - len(df_copy)
        result_msg = f"Removed {removed_rows} duplicate rows based on {len(columns)} selected columns."
    else:
        df_copy = df_copy.drop_duplicates()
        removed_rows = initial_row_count - len(df_copy)
        result_msg = f"Removed {removed_rows} duplicate rows based on all columns."

    # Update operation stats
    operation_stats['values_changed'] = removed_rows
    operation_stats['rows_affected'] = removed_rows

    return df_copy, result_msg, operation_stats


def round_numeric_values(df, columns, decimal_places):
    """
    Round numeric values to specified decimal places.

    Args:
        df: Input DataFrame
        columns: List of columns to round
        decimal_places: Number of decimal places

    Returns:
        Tuple of (processed DataFrame, result message, operation statistics)
    """
    df_copy = df.copy()
    rounded_columns = 0
    total_values_rounded = 0
    affected_rows = set()

    # Track changes for detailed metadata
    operation_stats = {
        'values_changed': 0,
        'rows_affected': 0,
        'columns_rounded': [],
        'before_after_samples': []
    }

    for col in columns:
        if col in df_copy.columns and pd.api.types.is_numeric_dtype(df_copy[col]):
            # Track original values
            original_values = df_copy[col].copy()

            # Apply rounding
            df_copy[col] = df_copy[col].round(decimal_places)

            # Identify changed values
            changed_mask = original_values != df_copy[col]
            changed_count = changed_mask.sum()

            if changed_count > 0:
                rounded_columns += 1
                total_values_rounded += changed_count
                affected_rows.update(df_copy[changed_mask].index.tolist())
                operation_stats['columns_rounded'].append(col)

                # Record sample changes
                sample_indices = df_copy[changed_mask].head(3).index.tolist()
                for idx in sample_indices:
                    operation_stats['before_after_samples'].append({
                        'column': col,
                        'row_index': int(idx),
                        'before': float(original_values.loc[idx]),
                        'after': float(df_copy[col].loc[idx])
                    })

    # Update operation stats
    operation_stats['values_changed'] = total_values_rounded
    operation_stats['rows_affected'] = len(affected_rows)

    result_msg = f"Rounded {total_values_rounded} values in {rounded_columns} columns to {decimal_places} decimal places."
    return df_copy, result_msg, operation_stats