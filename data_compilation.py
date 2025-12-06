import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Union, Any
import dash
from dash import dcc, html, dash_table, ALL, MATCH
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import json
import io

from data_quality import standardize_missing_values

def create_header_mapping_dictionary(source_headers: List[str], target_headers: List[str]) -> Dict[str, str]:
    """
    Create a mapping dictionary from source headers to target headers.
    Uses fuzzy matching to suggest the best matches.
    
    Args:
        source_headers: List of source column headers
        target_headers: List of target column headers
        
    Returns:
        Dictionary mapping source headers to target headers
    """
    import difflib
    
    mapping = {}
    
    for source in source_headers:
        # Find closest match in target headers
        matches = difflib.get_close_matches(source, target_headers, n=1)
        
        if matches:
            mapping[source] = matches[0]
        else:
            # If no close match, keep the original header
            mapping[source] = source
    
    return mapping

def map_headers(df: pd.DataFrame, header_mapping: Dict[str, str]) -> pd.DataFrame:
    """
    Rename dataframe columns based on a header mapping.
    
    Args:
        df: Input DataFrame
        header_mapping: Dictionary mapping source headers to target headers
        
    Returns:
        DataFrame with renamed columns
    """
    # Only use mappings for columns that exist in the DataFrame
    valid_mappings = {col: header_mapping[col] for col in df.columns if col in header_mapping}
    
    # Rename columns
    return df.rename(columns=valid_mappings)

def compile_dataframes(dfs: List[pd.DataFrame], 
                      target_headers: Optional[List[str]] = None,
                      header_mappings: Optional[List[Dict[str, str]]] = None,
                      remove_duplicates: bool = True,
                      case_sensitive_categories: bool = False) -> pd.DataFrame:
    """
    Compile multiple dataframes into one, handling different headers and removing duplicates.
    
    Args:
        dfs: List of DataFrames to compile
        target_headers: Optional list of target headers for the final DataFrame
        header_mappings: Optional list of dictionaries mapping source headers to target headers
        remove_duplicates: Whether to remove duplicate rows
        case_sensitive_categories: Whether to preserve case sensitivity in categorical values
        
    Returns:
        Compiled DataFrame
    """
    if not dfs:
        return pd.DataFrame()
    
    # Process each dataframe
    processed_dfs = []
    
    for i, df in enumerate(dfs):
        df_copy = df.copy()
        
        # Standardize missing values
        df_copy = standardize_missing_values(df_copy)
        
        # Apply header mapping if provided
        if header_mappings and i < len(header_mappings):
            df_copy = map_headers(df_copy, header_mappings[i])
        elif target_headers:
            # Auto-generate mapping if not provided but target headers are available
            auto_mapping = create_header_mapping_dictionary(df_copy.columns.tolist(), target_headers)
            df_copy = map_headers(df_copy, auto_mapping)
        
        # Filter columns if target headers are specified
        if target_headers:
            # Keep only columns that exist in target headers
            existing_targets = [col for col in target_headers if col in df_copy.columns]
            if existing_targets:
                df_copy = df_copy[existing_targets]
        
        # Standardize categorical columns (like classification)
        df_copy = standardize_categorical_columns(df_copy, case_sensitive=case_sensitive_categories)
        
        processed_dfs.append(df_copy)
    
    # Concatenate all dataframes
    compiled_df = pd.concat(processed_dfs, ignore_index=True)
    
    # Remove duplicates if specified
    if remove_duplicates:
        compiled_df = compiled_df.drop_duplicates()
    
    return compiled_df



def create_compilation_module():
    """
    Creates the layout for the data compilation module.
    """
    return dbc.Card([
        dbc.CardHeader(html.H4("Data Compilation", className="card-title")),
        dbc.CardBody([
            html.P("Combine data from multiple files into a single dataset."),
            
            # Header mapping options
            dbc.Row([
                dbc.Col([
                    html.H5("Header Mapping"),
                    html.P("Map headers from different files to a standardized format."),
                    html.Div(id="header-mapping-interface"),
                    html.Div(id="mapping-data-store", style={"display": "none"})
                ], width=12)
            ]),
            
            # Compilation options
            dbc.Row([
                dbc.Col([
                    html.H5("Compilation Options", className="mt-3"),
                    dbc.Checklist(
                        id="compilation-options",
                        options=[
                            {"label": "Handle different headers across files", "value": "map_headers"},
                            {"label": "Remove duplicate records", "value": "remove_duplicates"},
                            {"label": "Make categorical values case-insensitive", "value": "case_insensitive"} # New option
                        ],
                        value=["map_headers", "remove_duplicates", "case_insensitive"], # Default to true
                        inline=False
                    )
                ], width=12)
            ]),
            
            # Compilation action
            dbc.Row([
                dbc.Col([
                    dbc.Button("Compile Data", id="compile-data-btn", color="primary", className="mt-3"),
                    html.Div(id="compilation-results", className="mt-3")
                ], width=12)
            ])
        ])
    ], className="mb-4")
    
    
def standardize_categorical_columns(df, categorical_columns=None, case_sensitive=False):
    """
    Standardize categorical columns in a DataFrame, optionally making them case-insensitive.
    
    Args:
        df: Input DataFrame
        categorical_columns: List of column names to treat as categorical
                            If None, will try to detect categorical columns automatically
        case_sensitive: Whether to preserve case sensitivity in categorical values
                       If False, will convert all values to lowercase
    
    Returns:
        DataFrame with standardized categorical columns
    """
    # Make a copy to avoid modifying the input
    result_df = df.copy()
    
    # Auto-detect categorical columns if not provided
    if categorical_columns is None:
        # Detect columns with string values or fewer than 10 unique values
        categorical_columns = []
        for col in result_df.columns:
            col_data = result_df[col]
            if not isinstance(col_data, pd.Series):
                continue
            if pd.api.types.is_object_dtype(col_data) or (
                    pd.api.types.is_numeric_dtype(col_data) and
                    1 < col_data.nunique() < 10
            ):
                categorical_columns.append(col)
    
    # Process each categorical column
    for col in categorical_columns:
        if col in result_df.columns:
            # Skip columns with all numeric values
            if pd.api.types.is_numeric_dtype(result_df[col]) and not result_df[col].astype(str).str.isalpha().any():
                continue
                
            # Convert to string to handle mixed types
            result_df[col] = result_df[col].astype(str)
            
            # Convert to lowercase if not case sensitive
            if not case_sensitive:
                result_df[col] = result_df[col].str.lower()
    
    return result_df
    

def add_compilation_module_to_app(app):
    """
    Add compilation module callbacks to the app.
    """
    # Combined callback for all mappings functionality - a single callback approach solves the duplicate outputs problem
    @app.callback(
        [Output("header-mapping-interface", "children"),
         Output("mapping-data-store", "children"),
         Output("compilation-results", "children"),
         Output("stored-compiled-data", "data")],
        [Input("stored-data", "data"),
         Input("stored-template", "data"),
         Input("main-tabs", "active_tab"),
         Input({"type": "mapping-dropdown", "file": ALL, "header": ALL}, "value"),
         Input({"type": "reset-btn", "file": ALL}, "n_clicks"),
         Input({"type": "identical-btn", "file": ALL}, "n_clicks"),
         Input("compile-data-btn", "n_clicks")],
        [State("mapping-data-store", "children"),
         State("compilation-options", "value")]
    )
    def handle_all_mapping_functionality(
        stored_data, stored_template, active_tab,
        dropdown_values, reset_clicks, identical_clicks, compile_clicks,
        current_mappings_json, options
    ):
        """
        Combined callback for all mapping functionality.
        This unified approach avoids the duplicate outputs problem.
        """
        # Check which input triggered the callback
        ctx = dash.callback_context
        if not ctx.triggered:
            # No triggers, this is the initial call
            return init_mapping_interface(stored_data, stored_template, active_tab)
        
        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
        
        # Handle the main cases
        
        # Case 1: Tab change or data loading (initialize mapping interface)
        if trigger_id in ["stored-data", "stored-template", "main-tabs"]:
            return init_mapping_interface(stored_data, stored_template, active_tab)
            
        # Case 2: Dropdown or button clicks (update mappings)
        elif "mapping-dropdown" in trigger_id or "reset-btn" in trigger_id or "identical-btn" in trigger_id:
            if not stored_data or active_tab != "tab-compilation":
                raise dash.exceptions.PreventUpdate
            
            # Update mappings
            updated_mappings = update_mappings(
                dropdown_values, reset_clicks, identical_clicks,
                current_mappings_json, stored_data, stored_template,
                trigger_id
            )
            
            # Regenerate the interface with the updated mappings
            interface = create_mapping_interface_with_preview(stored_data, stored_template, updated_mappings)
            
            # Return updated values (keeping results and compiled data unchanged)
            return interface, updated_mappings, dash.no_update, dash.no_update
            
        # Case 3: Compile button clicked
        elif trigger_id == "compile-data-btn":
            if not stored_data:
                raise dash.exceptions.PreventUpdate
                
            # Compile data and create results
            results, compiled_data = compile_data(compile_clicks, options, stored_data, current_mappings_json)
            
            # Return all values
            return dash.no_update, current_mappings_json, results, compiled_data
        
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update

    def init_mapping_interface(stored_data, stored_template, active_tab):
        """Initialize the mapping interface and return default values."""
        # Only update when on the compilation tab
        if active_tab != "tab-compilation":
            raise dash.exceptions.PreventUpdate
            
        if not stored_data:
            empty_interface = html.Div("Upload data files to configure header mapping.")
            return empty_interface, "{}", dash.no_update, dash.no_update
            
        # Create the interface and initial mappings
        interface = create_mapping_interface_with_preview(stored_data, stored_template)
        
        # Generate initial mappings
        all_mappings = create_initial_mappings(stored_data, stored_template)
        initial_mappings = {i: mapping for i, mapping in enumerate(all_mappings)}
        mappings_json = json.dumps(initial_mappings)
        
        return interface, mappings_json, dash.no_update, dash.no_update

    def create_mapping_interface_with_preview(stored_data, stored_template, current_mappings_json=None):
        """Create the header mapping interface with live preview."""
        # Extract file names and headers
        file_names = []
        all_headers = []
        
        for metadata in stored_data.get("metadata", []):
            file_names.append(metadata.get("filename", ""))
            all_headers.append(metadata.get("column_names", []))
        
        # Get template headers if available
        template_headers = []
        if stored_template and 'sheets' in stored_template:
            if 'Target header' in stored_template['sheets']:
                template_df = pd.read_json(io.StringIO(stored_template['sheets']['Target header']), orient='split')
                if not template_df.empty:
                    template_headers = template_df.iloc[:, 0].tolist()
        
        # Create all unique headers for dropdown options
        all_unique_headers = set()
        for headers in all_headers:
            all_unique_headers.update(headers)
        
        # Use template headers if available, otherwise use all unique headers
        target_options = template_headers if template_headers else sorted(all_unique_headers)
        
        # Parse current mappings if provided
        current_mappings = {}
        try:
            if current_mappings_json:
                current_mappings = json.loads(current_mappings_json)
        except (json.JSONDecodeError, TypeError):
            pass
        
        # Get mappings for each file
        all_mappings = []
        for i, headers in enumerate(all_headers):
            if str(i) in current_mappings:
                # Use existing mappings from the current_mappings
                file_mapping = current_mappings[str(i)]
            else:
                # Create new mappings
                if template_headers:
                    try:
                        from header_mapping import auto_map_headers
                        file_mapping = auto_map_headers(headers, template_headers)
                    except ImportError:
                        file_mapping = create_header_mapping_dictionary(headers, template_headers)
                else:
                    file_mapping = {header: header for header in headers}
            
            all_mappings.append(file_mapping)
        
        # Create tables for each file with status indicators
        mapping_tables = []
        for i, (filename, headers) in enumerate(zip(file_names, all_headers)):
            file_mapping = all_mappings[i] if i < len(all_mappings) else {h: h for h in headers}
            
            # Create table rows with status indicators
            table_rows = []
            for header in headers:
                # Create dropdown options
                options = [{"label": "Skip this column", "value": ""}]
                options.extend([{"label": target, "value": target} for target in target_options])
                
                # Get current mapping
                current_mapping = file_mapping.get(header, header)
                
                # Create dropdown
                dropdown = dcc.Dropdown(
                    id={
                        'type': 'mapping-dropdown',
                        'file': i,
                        'header': header
                    },
                    options=options,
                    value=current_mapping,
                    clearable=False,
                    style={"width": "100%"}
                )
                
                # Add status indicator
                status = html.Span(
                    "✓ Mapped" if current_mapping else "❌ Skipped",
                    style={
                        "color": "green" if current_mapping else "red",
                        "fontWeight": "bold"
                    }
                )
                
                # Create row
                table_rows.append(
                    html.Tr([
                        html.Td(header),
                        html.Td(dropdown),
                        html.Td(status)
                    ])
                )
            
            # Create buttons
            reset_button = html.Button(
                "Reset to Auto Mappings",
                id={
                    'type': 'reset-btn',
                    'file': i
                },
                className="btn btn-secondary btn-sm mr-2"
            )
            
            identical_button = html.Button(
                "Map All to Same Name",
                id={
                    'type': 'identical-btn',
                    'file': i
                },
                className="btn btn-secondary btn-sm ml-2"
            )
            
            # Create table
            table = html.Div([
                html.H6(f"Header Mapping for {filename}"),
                html.Table([
                    html.Thead([
                        html.Tr([
                            html.Th("Source Header"),
                            html.Th("Target Header"),
                            html.Th("Status")  # Added status column
                        ])
                    ]),
                    html.Tbody(table_rows)
                ], className="table table-striped"),
                html.Div([
                    reset_button,
                    identical_button
                ], className="mt-2 mb-4")
            ])
            
            mapping_tables.append(table)
        
        # Calculate mapping summary
        total_columns = sum(len(headers) for headers in all_headers)
        mapped_columns = sum(sum(1 for v in mapping.values() if v) for mapping in all_mappings)
        skipped_columns = total_columns - mapped_columns
        
        # Add mapping summary
        mapping_summary = html.Div([
            html.Hr(),
            html.H5("Mapping Summary"),
            html.P([
                f"Total columns: {total_columns}",
                html.Br(),
                f"Mapped columns: {mapped_columns}",
                html.Br(),
                f"Skipped columns: {skipped_columns}"
            ]),
            html.P("Click 'Compile Data' to apply these mappings.", className="font-weight-bold")
        ])
        
        # Add instructions
        instructions = html.Div([
            html.Hr(),
            html.H5("Instructions for Header Mapping"),
            html.P("Use the dropdown menus to map each source header to a target header for the compiled dataset."),
            html.Ul([
                html.Li("Select 'Skip this column' to exclude it from the compiled data"),
                html.Li("Use 'Reset to Auto Mappings' to restore the system's suggested mappings"),
                html.Li("Use 'Map All to Same Name' to map each header to itself")
            ]),
            html.P("When you're satisfied with the mappings, click 'Compile Data' to create your dataset.")
        ])
        
        return html.Div(mapping_tables + [mapping_summary, instructions])

    def create_initial_mappings(stored_data, stored_template):
        """Create initial header mappings."""
        # Extract headers
        all_headers = []
        for metadata in stored_data.get("metadata", []):
            all_headers.append(metadata.get("column_names", []))
            
        # Get template headers if available
        template_headers = []
        if stored_template and 'sheets' in stored_template:
            if 'Target header' in stored_template['sheets']:
                template_df = pd.read_json(io.StringIO(stored_template['sheets']['Target header']), orient='split')
                if not template_df.empty:
                    template_headers = template_df.iloc[:, 0].tolist()
        
        # Generate mappings for each file
        all_mappings = []
        for headers in all_headers:
            if template_headers:
                try:
                    # Try to use the header_mapping module
                    from header_mapping import auto_map_headers
                    mapping = auto_map_headers(headers, template_headers)
                except ImportError:
                    # Fallback to our local function
                    mapping = create_header_mapping_dictionary(headers, template_headers)
            else:
                # Default to identity mapping
                mapping = {header: header for header in headers}
            
            all_mappings.append(mapping)
            
        return all_mappings

    def update_mappings(dropdown_values, reset_clicks, identical_clicks, 
                      current_mappings_json, stored_data, stored_template,
                      trigger_id):
        """Update mappings when dropdowns or buttons are used."""
        # Parse current mappings
        try:
            current_mappings = json.loads(current_mappings_json)
        except (json.JSONDecodeError, TypeError):
            current_mappings = {}
            
        # Get file metadata
        file_headers = []
        for metadata in stored_data.get("metadata", []):
            file_headers.append(metadata.get("column_names", []))
            
        # Get template headers if available
        template_headers = []
        if stored_template and 'sheets' in stored_template:
            if 'Target header' in stored_template['sheets']:
                template_df = pd.read_json(io.StringIO(stored_template['sheets']['Target header']), orient='split')
                if not template_df.empty:
                    template_headers = template_df.iloc[:, 0].tolist()
        
        # Handle reset button clicks
        if "reset-btn" in trigger_id:
            # Extract file index from the trigger
            try:
                trigger_dict = json.loads(trigger_id.split(".")[0])
                file_idx = trigger_dict["file"]
                
                # Create auto-mappings for this file
                if file_idx < len(file_headers):
                    headers = file_headers[file_idx]
                    if template_headers:
                        try:
                            from header_mapping import auto_map_headers
                            new_mapping = auto_map_headers(headers, template_headers)
                        except ImportError:
                            new_mapping = create_header_mapping_dictionary(headers, template_headers)
                    else:
                        new_mapping = {header: header for header in headers}
                        
                    # Update mappings for this file
                    current_mappings[str(file_idx)] = new_mapping
            except (json.JSONDecodeError, KeyError, ValueError):
                pass
                
        # Handle identical button clicks
        elif "identical-btn" in trigger_id:
            # Extract file index from the trigger
            try:
                trigger_dict = json.loads(trigger_id.split(".")[0])
                file_idx = trigger_dict["file"]
                
                # Create identity mappings for this file
                if file_idx < len(file_headers):
                    headers = file_headers[file_idx]
                    new_mapping = {header: header for header in headers}
                    
                    # Update mappings for this file
                    current_mappings[str(file_idx)] = new_mapping
            except (json.JSONDecodeError, KeyError, ValueError):
                pass
                
        # Handle dropdown changes - IMPROVED
        elif "mapping-dropdown" in trigger_id:
            # Get context for proper access to inputs and values
            ctx = dash.callback_context
            
            # Extract the specific dropdown that was changed and its value
            try:
                triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]
                trigger_dict = json.loads(triggered_id)
                file_idx = trigger_dict.get("file")
                header = trigger_dict.get("header")
                
                # Get the changed value directly from the trigger
                changed_value = ctx.triggered[0]["value"]
                
                if file_idx is not None and header is not None:
                    # Ensure the file has a mapping dict
                    if str(file_idx) not in current_mappings:
                        # Create default mapping if needed
                        if file_idx < len(file_headers):
                            headers = file_headers[file_idx]
                            current_mappings[str(file_idx)] = {h: h for h in headers}
                    
                    # Update the mapping
                    if str(file_idx) in current_mappings:
                        current_mappings[str(file_idx)][header] = changed_value
                        
            except (json.JSONDecodeError, KeyError, ValueError, TypeError, IndexError):
                pass
        
        # Return updated mappings
        return json.dumps(current_mappings)

    def compile_data(n_clicks, options, stored_data, current_mappings):
        """Compile data using the current mappings."""
        if not stored_data:
            return html.Div("No data to compile. Please upload files first."), None
        
        # Load all dataframes

        all_dfs = [pd.read_json(io.StringIO(df_json), orient='split') for df_json in stored_data['dfs']]
        
        # Parse mapping values
        try:
            mappings_dict = json.loads(current_mappings)
            
            # Convert to list of mappings in correct order
            header_mappings = []
            for i in range(len(all_dfs)):
                if str(i) in mappings_dict:
                    # Filter out empty values (skipped columns)
                    mapping = mappings_dict[str(i)]
                    filtered_mapping = {src: tgt for src, tgt in mapping.items() if tgt}
                    header_mappings.append(filtered_mapping)
                else:
                    # Default mapping if missing
                    headers = stored_data['metadata'][i]['column_names']
                    header_mappings.append({header: header for header in headers})
                    
        except (json.JSONDecodeError, TypeError, KeyError):
            # Fallback to default mappings
            header_mappings = []
            for i in range(len(all_dfs)):
                headers = stored_data['metadata'][i]['column_names']
                header_mappings.append({header: header for header in headers})
        
        # Check if case insensitive option is selected
        case_sensitive = 'case_insensitive' not in options
        
        # Compile data with user mappings
        compiled_df = compile_dataframes(
            all_dfs, 
            header_mappings=header_mappings,
            remove_duplicates='remove_duplicates' in options,
            case_sensitive_categories=case_sensitive
        )
        
        # Create results output
        result_output = html.Div([
            html.Hr(),
            html.H5("Compilation Results"),
            html.P(f"Successfully compiled {len(all_dfs)} files using your custom header mappings."),
            html.P(f"Compiled dataset has {len(compiled_df)} rows and {len(compiled_df.columns)} columns."),
            
            # Preview of compiled data
            html.H6("Preview of Compiled Data:"),
            dash_table.DataTable(
                columns=[{'name': col, 'id': col} for col in compiled_df.columns],
                data=compiled_df.head(10).to_dict('records'),
                style_table={'overflowX': 'auto'},
                page_size=10
            )
        ])
        
        # Store compiled data
        stored_compiled_data = {
            'data': compiled_df.to_json(date_format='iso', orient='split'),
            'rows': len(compiled_df),
            'columns': list(compiled_df.columns)
        }
        
        return result_output, stored_compiled_data