import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Union, Any
import dash
from dash import dcc, html, dash_table
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import io
import base64
import json
from datetime import datetime
from flask import send_file

def add_export_module_to_app(app):
    """
    Add export module callbacks to the app.
    """

    # Display preview of data to be exported
    @app.callback(
        Output("export-preview", "children"),
        [Input("stored-cleaned-data", "data"),
         Input("stored-compiled-data", "data"),
         Input("main-tabs", "active_tab")]
    )
    def update_export_preview(cleaned_data, compiled_data, active_tab):
        """
        Update the preview of data to be exported.
        """
        # Only update when on the export tab
        if active_tab != "tab-export":
            raise dash.exceptions.PreventUpdate

        # Use cleaned data if available, otherwise use compiled data
        data = cleaned_data if cleaned_data else compiled_data

        if not data:
            return html.Div("No data available for export.")

        # Load the data
        df = pd.read_json(io.StringIO(data["data"]), orient="split")

        # Create preview table
        preview_table = dash_table.DataTable(
            columns=[{'name': col, 'id': col} for col in df.columns],
            data=df.head(5).to_dict('records'),
            style_table={'overflowX': 'auto'},
            page_size=5
        )

        return html.Div([
            html.P(f"Data has {len(df)} rows and {len(df.columns)} columns."),
            preview_table
        ])

    # Handle download of cleaned data
    @app.callback(
        Output("download-cleaned-data", "data"),
        [Input("export-data-btn", "n_clicks")],
        [State("export-format", "value"),
         State("include-metadata", "checked"),  # Changed from "value" to "checked"
         State("stored-cleaned-data", "data"),
         State("stored-compiled-data", "data"),
         State("dashboard-metadata", "data")]
    )
    def download_cleaned_data(n_clicks, export_format, include_metadata, cleaned_data, compiled_data,
                              dashboard_metadata):
        """
        Prepare cleaned data for download.
        """
        # Only trigger on button click
        ctx = dash.callback_context
        if not ctx.triggered or ctx.triggered[0]["prop_id"].split(".")[0] != "export-data-btn":
            return None

        # Use cleaned data if available, otherwise use compiled data
        data = cleaned_data if cleaned_data else compiled_data

        if not data:
            return None

        # Load the data
        df = pd.read_json(io.StringIO(data["data"]), orient="split")

        # Generate timestamp for filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"cleaned_data_{timestamp}"

        if export_format == "csv":
            # Export as CSV
            content = df.to_csv(index=False)

            if include_metadata:
                # Build comprehensive metadata rows list, matching the Excel format
                metadata_rows = [
                    ["Export Date", datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
                    ["Rows", len(df)],
                    ["Columns", len(df.columns)],
                    ["Column Names", ", ".join(df.columns.tolist())]
                ]

                if dashboard_metadata and "current_stage" in dashboard_metadata:
                    metadata_rows.append(["Processing Stage", dashboard_metadata.get("current_stage", "unknown")])

                # Add cleaning history with enhanced details
                if cleaned_data and "cleaning_history" in cleaned_data:
                    metadata_rows.extend([
                        ["", ""],
                        ["Cleaning History", ""]
                    ])

                    for i, op in enumerate(cleaned_data["cleaning_history"], 1):
                        operation_type = op['operation'].replace('_', ' ').title()
                        metadata_rows.extend([
                            [f'Operation {i}', operation_type],
                            ['Time', op['timestamp']]
                        ])

                        # Add detailed information based on operation type
                        if 'columns' in op:
                            metadata_rows.append(['Affected Columns', ', '.join(op['columns'])])

                        if operation_type == "Missing Values":
                            metadata_rows.append(['Method', op.get('method', 'Unknown')])
                            if 'custom_value' in op and op['custom_value']:
                                metadata_rows.append(['Custom Replacement Value', op['custom_value']])

                        elif operation_type == "Format Correction":
                            if 'date_columns' in op and op['date_columns']:
                                metadata_rows.append(['Date Columns', ', '.join(op['date_columns'])])
                            if 'numeric_columns' in op and op['numeric_columns']:
                                metadata_rows.append(['Numeric Columns', ', '.join(op['numeric_columns'])])

                        elif operation_type == "Outlier Handling":
                            metadata_rows.append(['Detection Method', op.get('method', 'Unknown')])
                            metadata_rows.append(['Handling Method', op.get('handling', 'Unknown')])

                        elif operation_type == "Rounding":
                            metadata_rows.append(['Decimal Places', op.get('decimal_places', 'Unknown')])

                        # Add statistics about changes if available
                        if 'stats' in op:
                            stats = op['stats']
                            if 'values_changed' in stats:
                                metadata_rows.append(['Values Changed', stats['values_changed']])
                            if 'rows_affected' in stats:
                                metadata_rows.append(['Rows Affected', stats['rows_affected']])

                            # Add sample changes
                            if 'before_after_samples' in stats and stats['before_after_samples']:
                                metadata_rows.append(['Sample Changes (Before → After)', ''])
                                for sample in stats['before_after_samples'][:5]:  # Limit to 5 samples
                                    if 'column' in sample:
                                        metadata_rows.append([
                                            f"  {sample['column']}",
                                            f"{sample['before']} → {sample['after']}"
                                        ])
                                    else:
                                        metadata_rows.append([
                                            f"  Row {sample.get('row_index', 'Unknown')}",
                                            f"{sample['before']} → {sample['after']}"
                                        ])

                        metadata_rows.append(['Details', op['result_message']])
                        metadata_rows.append(['', ''])  # Empty row for spacing

                # Add column statistics if available
                if cleaned_data and "column_stats" in cleaned_data:
                    metadata_rows.extend([
                        ["", ""],
                        ["Column Statistics", ""]
                    ])

                    # Add header row for the stats section
                    metadata_rows.append([
                        'Column', 'Data Type', 'Non-Null Count', 'Missing Count', 'Missing %',
                        'Unique Values', 'Min', 'Max', 'Mean', 'Median', 'Std Dev'
                    ])

                    # Add stats for each column
                    for col, stats in cleaned_data["column_stats"].items():
                        metadata_rows.append([
                            col,
                            stats.get('data_type', 'Unknown'),
                            stats.get('non_null_count', ''),
                            stats.get('missing_count', ''),
                            stats.get('missing_percent', ''),
                            stats.get('unique_count', ''),
                            stats.get('min', ''),
                            stats.get('max', ''),
                            stats.get('mean', ''),
                            stats.get('median', ''),
                            stats.get('std_dev', '')
                        ])

                # Create a ZIP with two CSVs
                import zipfile
                buf = io.BytesIO()
                with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
                    # Add cleaned data CSV
                    zf.writestr("cleaned_data.csv", df.to_csv(index=False))

                    # Add metadata CSV - make sure to handle the varying row lengths
                    metadata_df = pd.DataFrame(metadata_rows)
                    zf.writestr("metadata.csv", metadata_df.to_csv(index=False, header=False))

                    # Add a README file to explain the contents
                    readme_text = """# Data Cleaning Dashboard Export

        This archive contains the following files:
        - cleaned_data.csv: The cleaned dataset
        - metadata.csv: Comprehensive metadata about the cleaning process

        The metadata.csv file contains information about the data cleaning operations performed,
        including details on each operation, statistics, and before/after samples of changes made.
        """
                    zf.writestr("README.txt", readme_text)

                buf.seek(0)
                return dcc.send_bytes(
                    buf.getvalue(),
                    filename=f"cleaned_data_{timestamp}.zip"
                )
            else:
                # No metadata: simple CSV
                return dcc.send_bytes(
                    content.encode('utf-8'),
                    filename=f"{filename}.csv"
                )




        elif export_format == "xlsx":
            # Create Excel writer
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                # Write main data
                df.to_excel(writer, sheet_name='Cleaned Data', index=False)

                # Write metadata sheet if requested
                if include_metadata:
                    dashboard_metadata = dashboard_metadata or {}
                    metadata_rows = [
                        ['Export Date', datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
                        ['Rows', len(df)],
                        ['Columns', len(df.columns)],
                        ['Column Names', ', '.join(df.columns.tolist())],
                        ['Processing Stage', dashboard_metadata.get('current_stage', 'unknown')]
                    ]

                    # Add cleaning history if available with enhanced details
                    if cleaned_data and "cleaning_history" in cleaned_data:
                        metadata_rows.extend([
                            ['', ''],
                            ['Cleaning History', '']
                        ])

                        for i, op in enumerate(cleaned_data["cleaning_history"], 1):
                            operation_type = op['operation'].replace('_', ' ').title()
                            metadata_rows.extend([
                                [f'Operation {i}', operation_type],
                                ['Time', op['timestamp']]
                            ])

                            # Add detailed information based on operation type
                            if 'columns' in op:
                                metadata_rows.append(['Affected Columns', ', '.join(op['columns'])])

                            if operation_type == "Missing Values":
                                metadata_rows.append(['Method', op.get('method', 'Unknown')])
                                if 'custom_value' in op and op['custom_value']:
                                    metadata_rows.append(['Custom Replacement Value', op['custom_value']])

                            elif operation_type == "Format Correction":
                                if 'date_columns' in op and op['date_columns']:
                                    metadata_rows.append(['Date Columns', ', '.join(op['date_columns'])])
                                if 'numeric_columns' in op and op['numeric_columns']:
                                    metadata_rows.append(['Numeric Columns', ', '.join(op['numeric_columns'])])

                            elif operation_type == "Outlier Handling":
                                metadata_rows.append(['Detection Method', op.get('method', 'Unknown')])
                                metadata_rows.append(['Handling Method', op.get('handling', 'Unknown')])

                            elif operation_type == "Rounding":
                                metadata_rows.append(['Decimal Places', op.get('decimal_places', 'Unknown')])

                            # Add statistics about changes if available
                            if 'stats' in op:
                                stats = op['stats']
                                if 'values_changed' in stats:
                                    metadata_rows.append(['Values Changed', stats['values_changed']])
                                if 'rows_affected' in stats:
                                    metadata_rows.append(['Rows Affected', stats['rows_affected']])

                                # Add sample changes
                                if 'before_after_samples' in stats and stats['before_after_samples']:
                                    metadata_rows.append(['Sample Changes (Before → After)', ''])
                                    for sample in stats['before_after_samples'][:5]:  # Limit to 5 samples
                                        metadata_rows.append([
                                            f"  {sample['column']}",
                                            f"{sample['before']} → {sample['after']}"
                                        ])

                            metadata_rows.append(['Details', op['result_message']])
                            metadata_rows.append(['', ''])  # Empty row for spacing

                    # Create metadata DataFrame and write to Excel
                    metadata_df = pd.DataFrame(metadata_rows)
                    metadata_df.to_excel(writer, sheet_name='Metadata', index=False, header=False)

                    # If detailed column stats are available, add a column stats sheet
                    if cleaned_data and "column_stats" in cleaned_data:
                        col_stats = cleaned_data["column_stats"]
                        col_stats_rows = []

                        # Header row
                        col_stats_rows.append(['Column', 'Data Type', 'Non-Null Count', 'Missing Count', 'Missing %',
                                               'Unique Values', 'Min', 'Max', 'Mean', 'Median', 'Std Dev'])

                        # Add stats for each column
                        for col, stats in col_stats.items():
                            col_stats_rows.append([
                                col,
                                stats.get('data_type', 'Unknown'),
                                stats.get('non_null_count', ''),
                                stats.get('missing_count', ''),
                                stats.get('missing_percent', ''),
                                stats.get('unique_count', ''),
                                stats.get('min', ''),
                                stats.get('max', ''),
                                stats.get('mean', ''),
                                stats.get('median', ''),
                                stats.get('std_dev', '')
                            ])

                        # Create column stats DataFrame and write to Excel
                        col_stats_df = pd.DataFrame(col_stats_rows)
                        col_stats_df.to_excel(writer, sheet_name='Column Statistics', index=False, header=False)

            # Get the Excel file content
            output.seek(0)
            return dcc.send_bytes(output.getvalue(), f"{filename}.xlsx")
        else:
            return {}