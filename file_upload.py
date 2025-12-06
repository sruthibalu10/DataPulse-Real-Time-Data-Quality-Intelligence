import base64
import datetime
import io
import os
from typing import Dict, List, Optional, Tuple, Union

import dash
from dash import dcc, html, dash_table, callback
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objs as go
import dash_uploader as du

# Initialize the Dash app with Bootstrap styling
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# configure dash-uploader to write chunks to disk immediately
du.configure_upload(app, "/tmp/uploads")  # no leading '+' here :contentReference[oaicite:1]{index=1}

def add_loading_overlay(component_id):
    """
    Add a loading overlay to a component.
    """
    return html.Div(
        [
            dbc.Spinner(color="primary", size="lg"),
            html.Div("Loading...", className="mt-2"),
        ],
        id=f"loading-{component_id}",
        className="loading-overlay d-none",
    )

def create_upload_module():
    """
    Creates the layout for the file upload and processing module.
    """
    return html.Div(
        [
            dbc.Card(
                [
                    dbc.CardHeader(
                        html.H4("File Upload & Processing", className="card-title")
                    ),
                    dbc.CardBody(
                        [
                            # Row with two columns: data upload & template upload
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            html.H5("Upload Data Files"),
                                            html.P("Upload CSV, XLSX, or XLSM files containing your data."),
                                            du.Upload(
                                                id="upload-data",
                                                text="Drag & Drop or Select Files (max 200 MB)",
                                                filetypes=["csv", "xls", "xlsx", "xlsm"],
                                                max_file_size=200,  # in MB
                                                chunk_size=10,      # in MB
                                                max_files=5,        # Allow up to 5 files
                                                default_style={
                                                    "width": "100%",
                                                    "height": "60px",
                                                    "lineHeight": "60px",
                                                    "borderStyle": "dashed",
                                                    "borderWidth": "1px",
                                                    "borderRadius": "5px",
                                                    "textAlign": "center",
                                                    "margin": "10px",
                                                    "color": "#333"
                                                }
                                            ),
                                            html.Div(id="upload-data-output", className="mt-3"),
                                        ],
                                        width=6,
                                    ),
                                    dbc.Col(
                                        [
                                            html.H5("Upload Header Template (Optional)"),
                                            html.P("Upload a file containing the target headers and mapping information."),
                                            dcc.Upload(
                                                id="upload-template",
                                                children=html.Div(
                                                    [
                                                        html.I(className="fas fa-file-excel me-2"),
                                                        "Drag and Drop or ",
                                                        html.A("Select Template"),
                                                    ]
                                                ),
                                                className="file-upload",
                                                multiple=True,
                                            ),
                                            html.Div(id="upload-template-output", className="mt-3"),
                                        ],
                                        width=6,
                                    ),
                                ],
                                className="position-relative",
                            ),
                            # File info
                            dbc.Row(
                                [
                                    dbc.Col(html.Div(id="file-info-output", className="mt-4"), width=12)
                                ]
                            ),
                            # Header comparison
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            html.H5("Header Comparison", className="mt-4"),
                                            html.Div(id="header-comparison-output"),
                                        ],
                                        width=12,
                                    )
                                ]
                            ),
                            # Data preview
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            html.H5("Data Preview", className="mt-4"),
                                            html.Div(id="data-preview-output"),
                                        ],
                                        width=12,
                                    )
                                ]
                            ),
                        ]
                    ),
                ],
                className="dashboard-card mb-4",
            ),
            # loading overlay
            add_loading_overlay("upload-module"),
        ],
        className="position-relative",
    )

# Main app layout
app.layout = dbc.Container([
    html.H1("Data Cleaning Dashboard", className="my-4"),
    html.Hr(),
    create_upload_module(),
    dcc.Store(id='stored-data'),
    dcc.Store(id='stored-template')
], fluid=True)

# Helper function to parse uploaded files
def parse_contents(contents, filename, date):
    """
    Parse the contents of an uploaded file.
    
    Args:
        contents: Content of the uploaded file
        filename: Name of the uploaded file
        date: Date of upload
        
    Returns:
        DataFrame and metadata about the parsed file
    """
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    
    try:
        if 'csv' in filename.lower():
            # Assume that the user uploaded a CSV file
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
        elif 'xls' in filename.lower():
            # Assume that the user uploaded an Excel file
            df = pd.read_excel(io.BytesIO(decoded))
        else:
            return None, f"Unsupported file type: {filename}"
        
        # Extract metadata
        metadata = {
            'filename': filename,
            'upload_date': date,
            'rows': len(df),
            'columns': len(df.columns),
            'column_names': list(df.columns),
            'dtypes': {col: str(df[col].dtype) for col in df.columns}
        }
        
        return df, metadata
    except Exception as e:
        return None, f"Error processing {filename}: {e}"

# Callback for uploading data files
@app.callback(
    [Output('upload-data-output', 'children'),
     Output('stored-data', 'data'),
     Output('file-info-output', 'children')],
    [Input('upload-data', 'contents')],
    [State('upload-data', 'filename'),
     State('upload-data', 'last_modified')]
)
def update_data_output(list_of_contents, list_of_filenames, list_of_dates):
    """
    Update the output based on uploaded data files.
    """
    if list_of_contents is None:
        return html.Div("No files uploaded yet."), None, None
    
    all_dfs = []
    all_metadata = []
    output_children = []
    
    for c, n, d in zip(list_of_contents, list_of_filenames, list_of_dates):
        if c is not None:
            # Convert timestamp to readable date
            date = datetime.datetime.fromtimestamp(d).strftime('%Y-%m-%d %H:%M:%S')
            df, metadata = parse_contents(c, n, date)
            
            if isinstance(metadata, str):  # Error message
                output_children.append(html.Div([
                    html.Hr(),
                    html.H5(f"File: {n}"),
                    html.P(metadata, style={'color': 'red'})
                ]))
            else:
                all_dfs.append(df)
                all_metadata.append(metadata)
                output_children.append(html.Div([
                    html.Hr(),
                    html.H5(f"File: {n}"),
                    html.P(f"Uploaded on: {date}"),
                    html.P(f"Rows: {metadata['rows']}, Columns: {metadata['columns']}")
                ]))
    
    # Store data for later use
    stored_data = {
        'dfs': [df.to_json(date_format='iso', orient='split') for df in all_dfs],
        'metadata': all_metadata
    }
    
    # Create file info summary
    if all_metadata:
        file_info = dbc.Card([
            dbc.CardHeader(html.H5("File Summary")),
            dbc.CardBody([
                html.P(f"Number of files uploaded: {len(all_metadata)}"),
                html.P(f"Total rows across all files: {sum(m['rows'] for m in all_metadata)}"),
                html.P(f"Files: {', '.join(m['filename'] for m in all_metadata)}")
            ])
        ])
    else:
        file_info = None
    
    return output_children, stored_data, file_info

# Callback for the header template upload
@app.callback(
    [Output('upload-template-output', 'children'),
     Output('stored-template', 'data')],
    [Input('upload-template', 'contents')],
    [State('upload-template', 'filename'),
     State('upload-template', 'last_modified')]
)
def update_template_output(contents, filename, date):
    """
    Update the output based on uploaded template file.
    """
    if contents is None:
        return html.Div("No template uploaded yet."), None
    
    # Convert timestamp to readable date
    date_str = datetime.datetime.fromtimestamp(date).strftime('%Y-%m-%d %H:%M:%S')
    df, metadata = parse_contents(contents, filename, date_str)
    
    if isinstance(metadata, str):  # Error message
        template_output = html.Div([
            html.Hr(),
            html.H5(f"Template: {filename}"),
            html.P(metadata, style={'color': 'red'})
        ])
        stored_template = None
    else:
        # Check if the template has the expected structure
        sheets = {}
        if 'xls' in filename.lower():
            # Read all sheets
            xl = pd.ExcelFile(io.BytesIO(base64.b64decode(contents.split(',')[1])))
            for sheet_name in xl.sheet_names:
                sheets[sheet_name] = pd.read_excel(xl, sheet_name=sheet_name).to_json(date_format='iso', orient='split')
        
        template_output = html.Div([
            html.Hr(),
            html.H5(f"Template: {filename}"),
            html.P(f"Uploaded on: {date_str}"),
            html.P(f"Sheets found: {', '.join(sheets.keys()) if sheets else 'None (CSV file)'}")
        ])
        
        stored_template = {
            'filename': filename,
            'sheets': sheets,
            'single_df': df.to_json(date_format='iso', orient='split') if df is not None else None
        }
    
    return template_output, stored_template

# Callback for header comparison
@app.callback(
    Output('header-comparison-output', 'children'),
    [Input('stored-data', 'data'),
     Input('stored-template', 'data')]
)
def update_header_comparison(stored_data, stored_template):
    """
    Compare headers across uploaded files and against the template.
    """
    if not stored_data:
        return html.Div("Upload data files to see header comparison.")
    
    # Extract headers from each file
    all_headers = []
    file_names = []
    
    for i, metadata in enumerate(stored_data['metadata']):
        all_headers.append(metadata['column_names'])
        file_names.append(metadata['filename'])
    
    # Add template headers if available
    template_headers = []
    if stored_template and 'sheets' in stored_template:
        if 'Target header' in stored_template['sheets']:
            template_df = pd.read_json(io.StringIO(stored_template['sheets']['Target header']), orient='split')
            if not template_df.empty:
                template_headers = template_df.iloc[:, 0].tolist()
                all_headers.append(template_headers)
                file_names.append(f"{stored_template['filename']} (Target header)")
    
    # Create a set of all unique headers
    all_unique_headers = sorted(set().union(*all_headers))
    
    # Create a comparison table
    comparison_data = []
    for header in all_unique_headers:
        row = {'Header': header}
        for i, file_headers in enumerate(all_headers):
            row[file_names[i]] = '✓' if header in file_headers else '✗'
        comparison_data.append(row)
    
    # Create the comparison table
    comparison_table = dash_table.DataTable(
        id='header-comparison-table',
        columns=[{'name': 'Header', 'id': 'Header'}] + 
                [{'name': name, 'id': name} for name in file_names],
        data=comparison_data,
        style_table={'overflowX': 'auto'},
        style_data_conditional=[
            {
                'if': {'filter_query': '{{{col}}} contains "✓"'.format(col=col),
                       'column_id': col},
                'backgroundColor': '#CCFFCC',
                'color': 'black',
            } for col in file_names
        ] + [
            {
                'if': {'filter_query': '{{{col}}} contains "✗"'.format(col=col),
                       'column_id': col},
                'backgroundColor': '#FFCCCC',
                'color': 'black',
            } for col in file_names
        ],
        style_header={
            'backgroundColor': 'rgb(230, 230, 230)',
            'fontWeight': 'bold'
        },
        sort_action="native",
        filter_action="native",
    )
    
    return html.Div([
        html.P("This table compares headers across all uploaded files and the template (if provided)."),
        comparison_table
    ])

# Callback for data preview
@app.callback(
    Output('data-preview-output', 'children'),
    [Input('stored-data', 'data')]
)
def update_data_preview(stored_data):
    """
    Display a preview of the data from each uploaded file.
    """
    if not stored_data:
        return html.Div("Upload data files to see data preview.")
    
    preview_children = []
    
    for i, df_json in enumerate(stored_data['dfs']):
        df = pd.read_json(io.StringIO(df_json), orient='split')
        metadata = stored_data['metadata'][i]
        
        # Create tabs for first 10 and last 10 rows
        first_10 = df.head(10)
        last_10 = df.tail(10)
        
        preview_tabs = dbc.Tabs([
            dbc.Tab(dash_table.DataTable(
                id=f'first-10-table-{i}',
                columns=[{'name': col, 'id': col} for col in first_10.columns],
                data=first_10.to_dict('records'),
                style_table={'overflowX': 'auto'},
                page_size=10
            ), label="First 10 Rows"),
            dbc.Tab(dash_table.DataTable(
                id=f'last-10-table-{i}',
                columns=[{'name': col, 'id': col} for col in last_10.columns],
                data=last_10.to_dict('records'),
                style_table={'overflowX': 'auto'},
                page_size=10
            ), label="Last 10 Rows")
        ])
        
        preview_children.append(html.Div([
            html.Hr(),
            html.H5(f"Preview: {metadata['filename']}"),
            preview_tabs
        ], className="mt-3"))
    
    return html.Div(preview_children)

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)