import dash
from dash import dcc, html, dash_table, callback
from dash import ctx, ALL
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import io
import base64
import json
import numpy as np
import datetime
from dash import ALL, MATCH
from dash.exceptions import PreventUpdate
import time
import warnings
import os
import dash_uploader as du
from dash.dependencies import Output
from dash import no_update
from dash.exceptions import PreventUpdate


warnings.filterwarnings("ignore", category=UserWarning, module="dash_bootstrap_components._table")

# Import functionality from existing modules
from file_upload import (
    create_upload_module,
    parse_contents,
)

from data_quality import (
    standardize_missing_values,
    identify_date_columns,
    identify_numeric_columns,
    fix_numeric_values,
    fix_date_values,
    detect_data_quality_issues,
    suggest_data_cleaning_steps
)

from data_compilation import (
    create_compilation_module,
    add_compilation_module_to_app
)

from cleaning_interface import add_interactive_cleaning_module_to_app

from data_visualization import add_visualization_module_to_app

from export import add_export_module_to_app

# Initialize the Dash app with Bootstrap styling and suppress callback exceptions
app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css"
    ],
    suppress_callback_exceptions=True
)
app.title = "Data Cleaning Dashboard"
du.configure_upload(app, "/tmp/uploads")
# Add all module callbacks to the app
add_interactive_cleaning_module_to_app(app)
add_visualization_module_to_app(app)
add_export_module_to_app(app)
add_compilation_module_to_app(app)

# Custom stylesheet for improved colors and spacing
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            :root {
                --primary-color: #4361ee;
                --secondary-color: #3f37c9;
                --success-color: #4cc9f0;
                --light-color: #f8f9fa;
                --dark-color: #212529;
                --accent-color: #f72585;
                --warning-color: #ff9e00;
                --danger-color: #d90429;
                --light-bg: #f5f7fb;
            }

            body {
                background-color: var(--light-bg);
                color: var(--dark-color);
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            }

            .app-header {
                background: linear-gradient(90deg, var(--primary-color), var(--secondary-color));
                color: white;
                padding: 1.5rem;
                border-radius: 0.5rem;
                margin-bottom: 2rem;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }

            .app-header h1 {
                font-weight: 700;
                margin-bottom: 0.5rem;
            }

            .app-header p {
                font-weight: 300;
                margin-bottom: 0;
                opacity: 0.9;
            }

            .dashboard-card {
                border-radius: 0.5rem;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
                margin-bottom: 1.5rem;
                transition: all 0.3s ease;
                border: none;
            }

            .dashboard-card:hover {
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
            }

            .dashboard-card .card-header {
                background-color: white;
                border-bottom: 1px solid #eaeaea;
                border-top-left-radius: 0.5rem;
                border-top-right-radius: 0.5rem;
                padding: 1rem 1.25rem;
            }

            .dashboard-card .card-header h4 {
                margin-bottom: 0;
                color: var(--primary-color);
                font-weight: 600;
            }

            .dashboard-card .card-body {
                padding: 1.5rem;
            }

            .nav-tabs .nav-link {
                color: var(--primary-color);
                border: none;
                border-bottom: 2px solid transparent;
                padding: 0.75rem 1rem;
            }

            .nav-tabs .nav-link.active {
                color: var(--secondary-color);
                background: none;
                border-bottom: 2px solid var(--secondary-color);
                font-weight: 600;
            }

            .btn-primary {
                background-color: var(--primary-color);
                border-color: var(--primary-color);
            }

            .btn-secondary {
                background-color: var(--secondary-color);
                border-color: var(--secondary-color);
            }

            .file-upload {
                border: 2px dashed #ddd;
                border-radius: 0.5rem;
                background-color: #fafafa;
                padding: 2rem;
                text-align: center;
                transition: all 0.3s ease;
            }

            .file-upload:hover {
                border-color: var(--primary-color);
                background-color: #f5f7ff;
            }

            .navigation-bar {
                background-color: white;
                border-radius: 0.5rem;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
                padding: 0.75rem;
                margin-bottom: 1.5rem;
            }

            .app-footer {
                text-align: center;
                padding: 1.5rem 0;
                margin-top: 2rem;
                color: #6c757d;
                font-size: 0.9rem;
                border-top: 1px solid #eaeaea;
            }
                        /* Button hover states */
            .btn {
                transition: all 0.3s ease;
            }

            .btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
            }

            /* Toast notifications */
            .toast-container {
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 1050;
            }

            .toast {
                min-width: 250px;
                background-color: white;
                border-radius: 4px;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
                overflow: hidden;
                margin-bottom: 10px;
                animation: slideIn 0.3s ease-out;
            }

            @keyframes slideIn {
                from {
                    transform: translateX(100%);
                    opacity: 0;
                }
                to {
                    transform: translateX(0);
                    opacity: 1;
                }
            }

            .toast-header {
                display: flex;
                align-items: center;
                padding: 0.5rem 0.75rem;
                background-color: rgba(0, 0, 0, 0.03);
                border-bottom: 1px solid rgba(0, 0, 0, 0.05);
            }

            .toast-body {
                padding: 0.75rem;
            }

            .toast-success .toast-header {
                background-color: var(--success-color);
                color: white;
            }

            .toast-error .toast-header {
                background-color: var(--danger-color);
                color: white;
            }

            .toast-warning .toast-header {
                background-color: var(--warning-color);
                color: white;
            }

            .toast-info .toast-header {
                background-color: var(--primary-color);
                color: white;
            }

            /* Loading overlay */
            .loading-overlay {
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background-color: rgba(255, 255, 255, 0.7);
                display: flex;
                justify-content: center;
                align-items: center;
                z-index: 1000;
                border-radius: 0.5rem;
            }
                        .sidebar {
                position: fixed;
                top: 0;
                bottom: 0;
                left: 0;
                width: 250px;
                padding: 2rem 1rem;
                background-color: white;
                box-shadow: 2px 0 5px rgba(0, 0, 0, 0.05);
                z-index: 100;
                overflow-y: auto;
            }

            .sidebar-header {
                padding-bottom: 1rem;
                margin-bottom: 1rem;
                border-bottom: 1px solid #eaeaea;
            }

            .sidebar-nav {
                padding-left: 0;
                list-style: none;
            }

            .sidebar-nav-item {
                margin-bottom: 0.25rem;
            }

            .sidebar-nav-link {
                display: flex;
                align-items: center;
                padding: 0.75rem 1rem;
                color: var(--dark-color);
                text-decoration: none;
                border-radius: 0.25rem;
                transition: all 0.2s ease;
            }

            .sidebar-nav-link:hover {
                background-color: var(--light-bg);
                color: var(--primary-color);
            }

            .sidebar-nav-link.active {
                background-color: var(--primary-color);
                color: white;
            }

            .sidebar-nav-link i {
                margin-right: 0.75rem;
                width: 20px;
                text-align: center;
            }

            .sidebar-nav-text {
                font-weight: 500;
            }

            .content-wrapper {
                margin-left: 250px;
                padding: 2rem;
                min-height: 100vh;
            }

            .workflow-progress {
                margin: 2rem 0;
            }

            .progress-step {
                position: relative;
                display: flex;
                flex-direction: column;
                align-items: center;
                flex: 1;
            }

            .progress-step:not(:last-child):after {
                content: '';
                position: absolute;
                top: 25px;
                right: -50%;
                width: 100%;
                height: 2px;
                background-color: #e9ecef;
                z-index: 0;
            }

            .progress-step.completed:not(:last-child):after {
                background-color: var(--success-color);
            }

            .progress-step-number {
                display: flex;
                align-items: center;
                justify-content: center;
                width: 50px;
                height: 50px;
                border-radius: 50%;
                background-color: white;
                border: 2px solid #e9ecef;
                color: #6c757d;
                font-weight: 600;
                margin-bottom: 0.5rem;
                z-index: 1;
            }

            .progress-step.active .progress-step-number {
                border-color: var(--primary-color);
                color: var(--primary-color);
            }

            .progress-step.completed .progress-step-number {
                background-color: var(--success-color);
                border-color: var(--success-color);
                color: white;
            }

            .progress-step-text {
                color: #6c757d;
                font-weight: 500;
            }

            .progress-step.active .progress-step-text {
                color: var(--primary-color);
                font-weight: 600;
            }

            .progress-step.completed .progress-step-text {
                color: var(--success-color);
            }

            .breadcrumbs {
                display: flex;
                flex-wrap: wrap;
                padding: 0;
                margin-bottom: 1rem;
                list-style: none;
            }

            .breadcrumb-item {
                display: flex;
                align-items: center;
            }

            .breadcrumb-item + .breadcrumb-item {
                padding-left: 0.5rem;
            }

            .breadcrumb-item + .breadcrumb-item::before {
                display: inline-block;
                padding-right: 0.5rem;
                color: #6c757d;
                content: "/";
            }

            .breadcrumb-item.active {
                color: var(--primary-color);
                font-weight: 500;
            }
        </style>
        {%scripts%}
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# Replace the header with a more modern version
header = html.Div([
    html.H1("Data Cleaning Dashboard", className="display-4"),
    html.P("Interactive tool for cleaning and preparing scientific data", className="lead"),
    html.P("Upload files, identify data quality issues, clean and transform your data, and export the results."),
    html.Div([
        html.Div([
            html.Span("Version 1.0", className="badge bg-light text-dark"),
            html.Span(" | ", className="mx-2"),
            html.Span("Updated May 2025", className="badge bg-light text-dark")
        ], className="mt-2")
    ])
], className="app-header")

# Create a navigation bar with all navigation buttons
# This ensures they exist at app startup regardless of the active tab
# Update the navigation bar
navigation_bar = html.Div([
    dbc.Row([
        dbc.Col([
            dbc.ButtonGroup([
                dbc.Button([html.I(className="fas fa-file-upload me-2"), "Upload"],
                           id="go-to-upload-btn", color="primary", outline=True, className="me-1"),
                dbc.Button([html.I(className="fas fa-object-group me-2"), "Compilation"],
                           id="go-to-compilation-btn", color="primary", outline=True, className="me-1"),
                dbc.Button([html.I(className="fas fa-check-circle me-2"), "Quality Analysis"],
                           id="go-to-quality-btn", color="primary", outline=True, className="me-1"),
                dbc.Button([html.I(className="fas fa-broom me-2"), "Cleaning"],
                           id="go-to-cleaning-btn", color="primary", outline=True, className="me-1"),
                dbc.Button([html.I(className="fas fa-chart-bar me-2"), "Visualization"],
                           id="go-to-visualization-btn", color="primary", outline=True, className="me-1"),
                dbc.Button([html.I(className="fas fa-download me-2"), "Export"],
                           id="go-to-export-btn", color="primary", outline=True)
            ])
        ], width=12)
    ])
], id="navigation-bar", className="navigation-bar")


# Create the sidebar component
def create_sidebar(active_tab):
    """
    Create a sidebar navigation component with active state based on current tab.
    """
    nav_items = [
        {"id": "tab-upload", "icon": "fas fa-file-upload", "text": "File Upload"},
        {"id": "tab-compilation", "icon": "fas fa-object-group", "text": "Data Compilation"},
        {"id": "tab-quality", "icon": "fas fa-check-circle", "text": "Quality Analysis"},
        {"id": "tab-cleaning", "icon": "fas fa-broom", "text": "Interactive Cleaning"},
        {"id": "tab-visualization", "icon": "fas fa-chart-bar", "text": "Visualization"},
        {"id": "tab-export", "icon": "fas fa-download", "text": "Export"}
    ]

    sidebar_nav = []
    for item in nav_items:
        is_active = item["id"] == active_tab
        sidebar_nav.append(
            html.Li(
                dbc.Button(
                    [
                        html.I(className=item["icon"]),
                        html.Span(item["text"], className="sidebar-nav-text")
                    ],
                    id=f"go-to-{item['id'].replace('tab-', '')}-btn",
                    color="primary" if is_active else "light",
                    className=f"sidebar-nav-link {'active' if is_active else ''}",
                    style={"width": "100%", "textAlign": "left"}
                ),
                className="sidebar-nav-item"
            )
        )

    return html.Div([
        html.Div([
            html.H4("Data Cleaning", className="mb-0"),
            html.P("Dashboard", className="text-muted small mb-0")
        ], className="sidebar-header"),

        html.Ul(sidebar_nav, className="sidebar-nav"),

        html.Hr(),

        html.Div([
            html.P("Progress", className="text-muted mb-2"),
            dbc.Progress(
                value=calculate_progress(active_tab),
                color="success",
                striped=True,
                className="mb-3"
            ),
            html.P(f"Step {get_step_number(active_tab)} of 6", className="text-center small mb-0")
        ], className="mt-4")
    ], className="sidebar")


def calculate_progress(active_tab):
    """Calculate progress percentage based on active tab."""
    step_mapping = {
        "tab-upload": 1,
        "tab-compilation": 2,
        "tab-quality": 3,
        "tab-cleaning": 4,
        "tab-visualization": 5,
        "tab-export": 6
    }
    current_step = step_mapping.get(active_tab, 1)
    return (current_step / 6) * 100


def get_step_number(active_tab):
    """Get current step number based on active tab."""
    step_mapping = {
        "tab-upload": 1,
        "tab-compilation": 2,
        "tab-quality": 3,
        "tab-cleaning": 4,
        "tab-visualization": 5,
        "tab-export": 6
    }
    return step_mapping.get(active_tab, 1)


def create_workflow_progress(active_tab):
    """
    Create a workflow progress indicator component.
    """
    steps = [
        {"id": "tab-upload", "text": "Upload"},
        {"id": "tab-compilation", "text": "Compile"},
        {"id": "tab-quality", "text": "Analyze"},
        {"id": "tab-cleaning", "text": "Clean"},
        {"id": "tab-visualization", "text": "Visualize"},
        {"id": "tab-export", "text": "Export"}
    ]

    step_mapping = {step["id"]: idx for idx, step in enumerate(steps)}
    current_step_idx = step_mapping.get(active_tab, 0)

    progress_steps = []
    for idx, step in enumerate(steps):
        status = ""
        if idx < current_step_idx:
            status = "completed"
        elif idx == current_step_idx:
            status = "active"

        progress_steps.append(
            dbc.Col(
                html.Div([
                    html.Div(
                        html.I(className="fas fa-check" if status == "completed" else "")
                        if status == "completed" else idx + 1,
                        className="progress-step-number"
                    ),
                    html.Div(step["text"], className="progress-step-text")
                ], className=f"progress-step {status}"),
            )
        )

    return dbc.Row(progress_steps, className="workflow-progress")


def create_breadcrumbs(active_tab):
    """
    Create breadcrumbs based on active tab.
    """
    breadcrumb_mapping = {
        "tab-upload": [{"text": "Home", "href": "/"}, {"text": "File Upload", "active": True}],
        "tab-compilation": [{"text": "Home", "href": "/"}, {"text": "File Upload", "href": "#"},
                            {"text": "Data Compilation", "active": True}],
        "tab-quality": [{"text": "Home", "href": "/"}, {"text": "File Upload", "href": "#"},
                        {"text": "Data Compilation", "href": "#"}, {"text": "Quality Analysis", "active": True}],
        "tab-cleaning": [{"text": "Home", "href": "/"}, {"text": "File Upload", "href": "#"},
                         {"text": "Quality Analysis", "href": "#"}, {"text": "Interactive Cleaning", "active": True}],
        "tab-visualization": [{"text": "Home", "href": "/"}, {"text": "File Upload", "href": "#"},
                              {"text": "Interactive Cleaning", "href": "#"}, {"text": "Visualization", "active": True}],
        "tab-export": [{"text": "Home", "href": "/"}, {"text": "File Upload", "href": "#"},
                       {"text": "Visualization", "href": "#"}, {"text": "Export", "active": True}]
    }

    breadcrumbs = breadcrumb_mapping.get(active_tab,
                                         [{"text": "Home", "href": "/"}, {"text": "File Upload", "active": True}])

    items = []
    for crumb in breadcrumbs:
        if crumb.get("active", False):
            items.append(html.Li(crumb["text"], className="breadcrumb-item active"))
        else:
            items.append(html.Li(
                html.A(crumb["text"], href=crumb["href"]),
                className="breadcrumb-item"
            ))

    return html.Nav(
        html.Ol(items, className="breadcrumbs"),
        aria_label="breadcrumb"
    )


def create_quality_analysis_module():
    """
    Creates the layout for the data quality analysis module.
    """
    return dbc.Card([
        dbc.CardHeader(html.H4("Data Quality Analysis", className="card-title")),
        dbc.CardBody([
            html.P("Analyze the quality of your data and identify issues."),

            # Quality analysis options
            dbc.Row([
                dbc.Col([
                    html.H5("Quality Analysis Options"),
                    dbc.Checklist(
                        id="quality-analysis-options",
                        options=[
                            {"label": "Check for missing values", "value": "missing_values"},
                            {"label": "Detect inconsistent data formats", "value": "format_issues"},
                            {"label": "Check for outliers", "value": "outliers"},
                            {"label": "Identify potential duplicates", "value": "duplicates"}
                        ],
                        value=["missing_values", "format_issues", "outliers", "duplicates"],
                        inline=False
                    )
                ], width=12)
            ]),

            # Analysis action
            dbc.Row([
                dbc.Col([
                    dbc.Button("Analyze Data Quality", id="analyze-data-btn", color="primary", className="mt-3"),
                    html.Div(id="quality-analysis-results", className="mt-3")
                ], width=12)
            ])
        ])
    ], className="mb-4")


def create_interactive_cleaning_module():
    """
    Creates the layout for the interactive data cleaning module.
    """
    return dbc.Card([
        dbc.CardHeader(html.H4("Interactive Data Cleaning", className="card-title")),
        dbc.CardBody([
            html.P("Clean and transform your data interactively."),

            # Tabs for different cleaning operations
            dbc.Tabs([
                dbc.Tab([
                    html.Div([
                        html.H5("Missing Values", className="mt-3"),
                        html.P("Handle missing values in your dataset."),

                        # Column selection
                        html.Div([
                            html.Label("Select columns:"),
                            dcc.Dropdown(id="missing-values-columns", multi=True)
                        ], className="mb-3"),

                        # Handling options
                        html.Div([
                            html.Label("Handling method:"),
                            dbc.RadioItems(
                                id="missing-values-method",
                                options=[
                                    {"label": "Drop rows", "value": "drop"},
                                    {"label": "Replace with mean", "value": "mean"},
                                    {"label": "Replace with median", "value": "median"},
                                    {"label": "Replace with zero", "value": "zero"}
                                ],
                                value="drop"
                            )
                        ], className="mb-3"),

                        # Custom value input (conditional)
                        html.Div(id="missing-values-custom-input"),

                        # Apply button
                        dbc.Button("Apply", id="apply-missing-values-btn", color="primary", className="mt-2")
                    ])
                ], label="Missing Values", tab_id="tab-missing"),

                dbc.Tab([
                    html.Div([
                        html.H5("Data Format Correction", className="mt-3"),
                        html.P("Correct inconsistent data formats."),

                        # Date columns
                        html.Div([
                            html.Label("Date columns:"),
                            dcc.Dropdown(id="date-format-columns", multi=True)
                        ], className="mb-3"),

                        # Numeric columns
                        html.Div([
                            html.Label("Numeric columns:"),
                            dcc.Dropdown(id="numeric-format-columns", multi=True)
                        ], className="mb-3"),

                        # Apply button
                        dbc.Button("Apply Format Corrections", id="apply-format-corrections-btn",
                                   color="primary", className="mt-2")
                    ])
                ], label="Format Correction", tab_id="tab-format"),

                dbc.Tab([
                    html.Div([
                        html.H5("Outlier Handling", className="mt-3"),
                        html.P("Identify and handle outliers in numeric columns."),

                        # Column selection
                        html.Div([
                            html.Label("Select columns:"),
                            dcc.Dropdown(id="outlier-columns", multi=True)
                        ], className="mb-3"),

                        # Method selection
                        html.Div([
                            html.Label("Detection method:"),
                            dbc.RadioItems(
                                id="outlier-method",
                                options=[
                                    {"label": "Z-score (> 3 std dev)", "value": "zscore"},
                                    {"label": "IQR (1.5x interquartile range)", "value": "iqr"}
                                ],
                                value="zscore"
                            )
                        ], className="mb-3"),

                        # Handling options
                        html.Div([
                            html.Label("Handling method:"),
                            dbc.RadioItems(
                                id="outlier-handling",
                                options=[
                                    {"label": "Remove outliers", "value": "remove"},
                                    {"label": "Cap outliers (winsorize)", "value": "cap"},
                                    {"label": "Replace with mean", "value": "mean"},
                                    {"label": "Replace with median", "value": "median"}
                                ],
                                value="cap"
                            )
                        ], className="mb-3"),

                        # Apply button
                        dbc.Button("Apply Outlier Handling", id="apply-outlier-handling-btn",
                                   color="primary", className="mt-2")
                    ])
                ], label="Outliers", tab_id="tab-outliers"),

                dbc.Tab([
                    html.Div([
                        html.H5("Duplicate Handling", className="mt-3"),
                        html.P("Identify and remove duplicate records."),

                        # Column selection for duplicate checking
                        html.Div([
                            html.Label("Check duplicates based on these columns:"),
                            dcc.Dropdown(id="duplicate-columns", multi=True)
                        ], className="mb-3"),

                        # Apply button
                        dbc.Button("Remove Duplicates", id="remove-duplicates-btn",
                                   color="primary", className="mt-2")
                    ])
                ], label="Duplicates", tab_id="tab-duplicates"),

                dbc.Tab([
                    html.Div([
                        html.H5("Value Rounding", className="mt-3"),
                        html.P("Round numeric values to a specified number of decimal places."),

                        # Column selection
                        html.Div([
                            html.Label("Select columns:"),
                            dcc.Dropdown(id="rounding-columns", multi=True)
                        ], className="mb-3"),

                        # Decimal places
                        html.Div([
                            html.Label("Decimal places:"),
                            dcc.Slider(
                                id="decimal-places",
                                min=0,
                                max=6,
                                step=1,
                                value=2,
                                marks={i: str(i) for i in range(7)}
                            )
                        ], className="mb-3"),

                        # Apply button
                        dbc.Button("Apply Rounding", id="apply-rounding-btn",
                                   color="primary", className="mt-2")
                    ])
                ], label="Rounding", tab_id="tab-rounding")
            ], id="cleaning-tabs", active_tab="tab-missing"),

            # Results display
            html.Div(id="cleaning-results", className="mt-4")
        ])
    ], className="mb-4")


def create_visualization_module():
    """
    Creates the layout for the data visualization module.
    """
    return dbc.Card([
        dbc.CardHeader(html.H4("Data Visualization", className="card-title")),
        dbc.CardBody([
            html.P("Visualize your data to gain insights."),

            # Plot configuration
            dbc.Row([
                dbc.Col([
                    html.H5("Plot Configuration"),

                    # Plot type
                    html.Div([
                        html.Label("Plot type:"),
                        dbc.RadioItems(
                            id="plot-type",
                            options=[
                                {"label": "Scatter Plot", "value": "scatter"},
                                {"label": "Line Plot", "value": "line"},
                                {"label": "Bar Chart", "value": "bar"},
                                {"label": "Box Plot", "value": "box"},
                                {"label": "Histogram", "value": "histogram"}
                            ],
                            value="scatter",
                            inline=True
                        )
                    ], className="mb-3"),

                    # Axes selection
                    html.Div([
                        html.Label("X-axis:"),
                        dcc.Dropdown(id="x-axis-column")
                    ], className="mb-3"),

                    html.Div([
                        html.Label("Y-axis:"),
                        dcc.Dropdown(id="y-axis-column")
                    ], className="mb-3"),

                    # Color by
                    html.Div([
                        html.Label("Color by (optional):"),
                        dcc.Dropdown(id="color-column", options=[{"label": "None", "value": "none"}])
                    ], className="mb-3"),

                    # Plot options
                    html.Div([
                        dbc.Checklist(
                            id="plot-options",
                            options=[
                                {"label": "Show mean line", "value": "mean_line"},
                                {"label": "Show ±3 std dev lines", "value": "std_lines"}
                            ],
                            value=[]
                        )
                    ], className="mb-3"),

                    # Create plot button
                    dbc.Button("Create Plot", id="create-plot-btn", color="primary", className="mt-2")
                ], width=4),

                # Plot display
                dbc.Col([
                    html.Div(id="plot-output")
                ], width=8)
            ])
        ])
    ], className="mb-4")


def create_export_module():
    """
    Creates the layout for the data export module.
    """
    return dbc.Card([
        dbc.CardHeader(html.H4("Data Export", className="card-title")),
        dbc.CardBody([
            html.P("Export your cleaned data."),

            # Export options
            dbc.Row([
                dbc.Col([
                    html.H5("Export Options"),

                    # Format selection
                    html.Div([
                        html.Label("Export format:"),
                        dbc.RadioItems(
                            id="export-format",
                            options=[
                                {"label": "Excel (.xlsx)", "value": "xlsx"},
                                {"label": "CSV (.csv)", "value": "csv"}
                            ],
                            value="xlsx"
                        )
                    ], className="mb-3"),

                    # Include metadata - use FormGroup instead of direct Checkbox with label
                    html.Div([
                        dbc.FormGroup([
                            dbc.Checkbox(id="include-metadata", checked=True),
                            dbc.Label("Include metadata", html_for="include-metadata", className="ml-2")
                        ], check=True)
                    ], className="mb-3"),

                    # Export button
                    dbc.Button("Export Data", id="export-data-btn", color="primary"),

                    # Download component
                    dcc.Download(id="download-cleaned-data")
                ], width=6),

                # Preview
                dbc.Col([
                    html.H5("Data Preview"),
                    html.Div(id="export-preview")
                ], width=6)
            ])
        ])
    ], className="mb-4")


# Toast notification component
def create_toast(id, header, body, icon, color="info"):
    """
    Create a toast notification component.

    Args:
        id: Component ID
        header: Toast header text
        body: Toast body text
        icon: FontAwesome icon class
        color: Toast color (info, success, warning, error)

    Returns:
        Toast component
    """
    return html.Div(
        [
            html.Div(
                [
                    html.I(className=f"{icon} me-2"),
                    html.Strong(header, className="me-auto"),
                    html.Button(
                        html.Span("×", aria_hidden="true"),
                        type="button",
                        className="btn-close",
                        id={"type": "close-toast", "index": id},
                    ),
                ],
                className="toast-header",
            ),
            html.Div(body, className="toast-body"),
        ],
        id=id,
        className=f"toast toast-{color}",
        role="alert",
        aria_live="assertive",
        aria_atomic="true",
    )


# Toast container component
toast_container = html.Div(
    id="toast-container",
    className="toast-container",
    children=[],
)
# Define helper functions first
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

# Define the function to create the upload module with support for multiple file uploads
def create_upload_module():
    """
    Creates the layout for the file upload and processing module with support for multiple files.
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
                                                chunk_size=10,  # in MB
                                                max_files=5,  # Allow up to 5 files
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
                                            html.P(
                                                "Upload a file containing the target headers and mapping information."),
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


# Update the main app layout
# Add toast container to the app layout
app.layout = html.Div([
    dcc.Location(id="url", refresh=False),
    dcc.Store(id='stored-data'),
    dcc.Store(id='stored-template'),
    dcc.Store(id='stored-compiled-data'),
    dcc.Store(id='stored-cleaned-data'),
    dcc.Store(id='stored-edited-data'),
    dcc.Store(id='dashboard-metadata'),
    dcc.Store(id="toast-trigger", data={"show": False, "id": None}),

    # Toast container for notifications
    toast_container,

    # Sidebar will be added dynamically with callback
    html.Div(id="sidebar-container"),

    # Content wrapper
    html.Div([
        # Header and breadcrumbs will be added dynamically with callback
        html.Div(id="header-container"),

        # Progress indicator
        html.Div(id="progress-container"),

        # Main content - Tabs
        dbc.Tabs([
            dbc.Tab([
                # Directly include the upload module in the initial layout
                create_upload_module()
            ], label="File Upload", tab_id="tab-upload"),

            dbc.Tab([
                # Pre-load the compilation module
                create_compilation_module()
            ], label="Data Compilation", tab_id="tab-compilation"),

            dbc.Tab([
                # Pre-load the quality module
                create_quality_analysis_module()
            ], label="Data Quality Analysis", tab_id="tab-quality"),

            dbc.Tab([
                # Pre-load the cleaning module
                create_interactive_cleaning_module()
            ], label="Interactive Cleaning", tab_id="tab-cleaning"),

            dbc.Tab([
                # Pre-load the visualization module
                create_visualization_module()
            ], label="Visualization", tab_id="tab-visualization"),

            dbc.Tab([
                # Pre-load the export module
                create_export_module()
            ], label="Export", tab_id="tab-export")
        ], id="main-tabs", active_tab="tab-upload"),

        # Footer
        html.Div([
            html.Hr(),
            html.Div([
                html.P("Data Cleaning Dashboard - Version 1.0"),
                html.P([
                    "Built with ",
                    html.A("Dash", href="https://dash.plotly.com/", target="_blank"),
                    " and ",
                    html.A("Bootstrap", href="https://getbootstrap.com/", target="_blank")
                ], className="small")
            ])
        ], className="app-footer")
    ], className="content-wrapper")
])


# Add loading overlay to card components
def add_loading_overlay(component_id):
    """
    Add a loading overlay to a component.
    """
    return html.Div(
        [
            dbc.Spinner(
                color="primary",
                size="lg",
            ),
            html.Div("Loading...", className="mt-2"),
        ],
        id=f"loading-{component_id}",
        className="loading-overlay d-none",
    )


# Updated callback for file uploads to properly handle multiple files
@du.callback(
    output=[
        Output('upload-data-output', 'children'),
        Output('stored-data', 'data'),
        Output('file-info-output', 'children')
    ],
    id='upload-data'
)
def handle_upload(status):
    """
    Handle uploaded files using dash-uploader's UploadStatus object.

    Args:
        status: UploadStatus object containing information about uploaded files

    Returns:
        Tuple of (upload output children, stored data, file info)
    """
    if not status.uploaded_files:
        return [], None, []

    all_dfs = []
    all_meta = []
    children = []

    for path in status.uploaded_files:
        # Convert pathlib.Path to string if needed
        path_str = str(path)
        name = os.path.basename(path_str)
        ts = datetime.datetime.fromtimestamp(os.path.getmtime(path_str))
        date_str = ts.strftime('%Y-%m-%d %H:%M:%S')

        # Read into pandas
        ext = name.rsplit('.', 1)[-1].lower()
        try:
            if ext == 'csv':
                df = pd.read_csv(path_str)
            elif ext in ['xlsx', 'xls', 'xlsm']:
                df = pd.read_excel(path_str)
            else:
                children.append(
                    html.Div([
                        html.H5(name),
                        html.P(f"⚠️ Unsupported file format: {ext}", style={'color': 'red'})
                    ])
                )
                continue
        except Exception as e:
            children.append(
                html.Div([
                    html.H5(name),
                    html.P(f"⚠️ Error parsing file: {e}", style={'color': 'red'})
                ])
            )
            continue

        meta = {
            'filename': name,
            'upload_date': date_str,
            'rows': df.shape[0],
            'columns': df.shape[1],
            'column_names': list(df.columns),
            'dtypes': {c: str(d) for c, d in zip(df.columns, df.dtypes)}
        }
        all_dfs.append(df)
        all_meta.append(meta)

        children.append(
            html.Div([
                html.Hr(),
                html.H5(name),
                html.P(f"Uploaded on: {date_str}"),
                html.P(f"Rows: {meta['rows']}, Columns: {meta['columns']}")
            ])
        )

    # Create file summary
    if all_meta:
        summary = [
            dbc.Card([
                dbc.CardHeader(html.H5("File Summary")),
                dbc.CardBody([
                    html.P(f"Number of files: {len(all_meta)}"),
                    html.P(f"Total rows: {sum(m['rows'] for m in all_meta)}"),
                    html.P("Files: " + ", ".join(m['filename'] for m in all_meta))
                ])
            ])
        ]

        # Serialize for dcc.Store
        stored = {
            'dfs': [df.to_json(date_format='iso', orient='split') for df in all_dfs],
            'metadata': all_meta
        }

        return children, stored, summary
    else:
        return children, None, []


@app.callback(
    [Output('upload-template-output', 'children'),
     Output('stored-template', 'data')],
    [Input('upload-template', 'contents')],
    [State('upload-template', 'filename'),
     State('upload-template', 'last_modified')]
)
def update_template_output(contents, filenames, dates):
    """
    Update the output based on uploaded template file(s).
    Handles both single and multiple file uploads.
    """
    if contents is None:
        return html.Div("No template uploaded yet."), None

    # Initialize outputs
    template_outputs = []
    stored_templates = []

    # Handle both single file and multiple files
    if not isinstance(contents, list):
        contents = [contents]
        filenames = [filenames]
        dates = [dates]

    for content, filename, date in zip(contents, filenames, dates):
        # Convert timestamp to readable date
        date_str = datetime.datetime.fromtimestamp(date).strftime('%Y-%m-%d %H:%M:%S')
        df, metadata = parse_contents(content, filename, date_str)

        if isinstance(metadata, str):  # Error message
            template_outputs.append(html.Div([
                html.Hr(),
                html.H5(f"Template: {filename}"),
                html.P(metadata, style={'color': 'red'})
            ]))
            continue

        # Check if the template has the expected structure
        sheets = {}
        if 'xls' in filename.lower():
            try:
                # Read all sheets
                xl = pd.ExcelFile(io.BytesIO(base64.b64decode(content.split(',')[1])))
                for sheet_name in xl.sheet_names:
                    sheets[sheet_name] = pd.read_excel(xl, sheet_name=sheet_name).to_json(date_format='iso',
                                                                                          orient='split')
            except Exception as e:
                template_outputs.append(html.Div([
                    html.Hr(),
                    html.H5(f"Template: {filename}"),
                    html.P(f"Error reading Excel sheets: {str(e)}", style={'color': 'red'})
                ]))
                continue

        template_outputs.append(html.Div([
            html.Hr(),
            html.H5(f"Template: {filename}"),
            html.P(f"Uploaded on: {date_str}"),
            html.P(f"Sheets found: {', '.join(sheets.keys()) if sheets else 'None (CSV file)'}")
        ]))

        stored_templates.append({
            'filename': filename,
            'sheets': sheets,
            'single_df': df.to_json(date_format='iso', orient='split') if df is not None else None
        })

    # For simplicity, we'll use the first valid template as the stored template
    # You might want to modify this logic if you need to handle multiple templates differently
    if stored_templates:
        return html.Div(template_outputs), stored_templates[0]
    else:
        return html.Div(template_outputs), None

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
        buf = io.StringIO(df_json)
        df = pd.read_json(buf, orient='split')
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

    # Add global navigation callbacks
    @app.callback(
        dash.Output("main-tabs", "active_tab"),
        [dash.Input("go-to-upload-btn", "n_clicks"),
         dash.Input("go-to-compilation-btn", "n_clicks"),
         dash.Input("go-to-quality-btn", "n_clicks"),
         dash.Input("go-to-cleaning-btn", "n_clicks"),
         dash.Input("go-to-visualization-btn", "n_clicks"),
         dash.Input("go-to-export-btn", "n_clicks")]
    )
    def navigate_tabs(upload_clicks, compilation_clicks, quality_clicks, cleaning_clicks, viz_clicks, export_clicks):
        """
        Handle navigation between main tabs via buttons.
        """
        ctx = dash.callback_context
        if not ctx.triggered:
            return dash.no_update  # Keep current tab

        button_id = ctx.triggered[0]["prop_id"].split(".")[0]

        if button_id == "go-to-upload-btn":
            return "tab-upload"
        elif button_id == "go-to-compilation-btn":
            return "tab-compilation"
        elif button_id == "go-to-quality-btn":
            return "tab-quality"
        elif button_id == "go-to-cleaning-btn":
            return "tab-cleaning"
        elif button_id == "go-to-visualization-btn":
            return "tab-visualization"
        elif button_id == "go-to-export-btn":
            return "tab-export"

        # Default case
        return dash.no_update

    # Update dashboard metadata callback
    @app.callback(
        Output("dashboard-metadata", "data"),
        [Input("stored-data", "data"),
         Input("stored-compiled-data", "data"),
         Input("stored-cleaned-data", "data"),
         Input("stored-edited-data", "data")]
    )
    def update_dashboard_metadata(stored_data, compiled_data, cleaned_data, edited_data):
        """
        Update dashboard metadata based on current data state.
        """
        metadata = {
            "has_uploaded_data": stored_data is not None,
            "has_compiled_data": compiled_data is not None,
            "has_cleaned_data": cleaned_data is not None,
            "has_edited_data": edited_data is not None,
            "current_stage": "upload"
        }

        # Determine current stage
        if edited_data is not None:
            metadata["current_stage"] = "edited"
            metadata["row_count"] = edited_data.get("rows", 0)
            metadata["column_count"] = len(edited_data.get("columns", []))
        elif cleaned_data is not None:
            metadata["current_stage"] = "cleaned"
            metadata["row_count"] = cleaned_data.get("rows", 0)
            metadata["column_count"] = len(cleaned_data.get("columns", []))
        elif compiled_data is not None:
            metadata["current_stage"] = "compiled"
            metadata["row_count"] = compiled_data.get("rows", 0)
            metadata["column_count"] = len(compiled_data.get("columns", []))
        elif stored_data is not None:
            metadata["current_stage"] = "uploaded"

        return metadata

    def create_header_mapping_interface(stored_data, stored_template):
        """
        Create the interface for mapping headers between files.
        """
        if not stored_data:
            return html.Div("Upload data files to configure header mapping.")

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

        # Create mapping table for each file
        mapping_tables = []

        for i, (headers, filename) in enumerate(zip(all_headers, file_names)):
            # Create target options - either from template or from all unique headers
            target_options = [{'label': header, 'value': header} for header in
                              (template_headers if template_headers else sorted(set().union(*all_headers)))]

            # Create a mapping table
            mapping_table = html.Div([
                html.H6(f"Header Mapping for {filename}"),
                dash_table.DataTable(
                    id={'type': 'mapping-table', 'index': i},
                    columns=[
                        {'name': 'Source Header', 'id': 'source'},
                        {'name': 'Target Header', 'id': 'target', 'presentation': 'dropdown'},
                    ],
                    data=[{'source': header, 'target': header} for header in headers],
                    dropdown={
                        'target': {
                            'options': target_options
                        }
                    },
                    editable=True,
                    style_table={'overflowX': 'auto'},
                    page_size=min(10, len(headers))
                )
            ], className="mb-3")

            mapping_tables.append(mapping_table)

        return html.Div(mapping_tables)

    def compile_dataframes(dfs, target_headers=None, options=None):
        """
        Compile multiple dataframes into one, handling different headers and removing duplicates.

        Args:
            dfs: List of DataFrames to compile
            target_headers: List of target headers to standardize across files
            options: List of compilation options (e.g. 'map_headers', 'remove_duplicates')

        Returns:
            Compiled DataFrame
        """
        if not dfs:
            return pd.DataFrame()

        # Default options
        if options is None:
            options = ['map_headers', 'remove_duplicates']

        compiled_dfs = []

        for df in dfs:
            df_copy = df.copy()

            # Standardize missing values
            df_copy = standardize_missing_values(df_copy)

            # Map headers if option selected and target headers provided
            if 'map_headers' in options and target_headers:
                # Simple mapping for now - rename columns that exist in target headers
                rename_dict = {}
                for col in df_copy.columns:
                    # Check for case-insensitive match
                    matches = [th for th in target_headers if th.lower() == col.lower()]
                    if matches:
                        rename_dict[col] = matches[0]

                if rename_dict:
                    df_copy = df_copy.rename(columns=rename_dict)

                # Only keep columns that exist in target headers
                df_copy = df_copy[[col for col in df_copy.columns if col in target_headers]]

            compiled_dfs.append(df_copy)

        # Concatenate all dataframes
        compiled_df = pd.concat(compiled_dfs, ignore_index=True)

        # Remove duplicates if option selected
        if 'remove_duplicates' in options:
            compiled_df = compiled_df.drop_duplicates()

        return compiled_df

    # Add data quality analysis callback
@app.callback(

    Output("quality-analysis-results", "children"),
    Input("main-tabs", "active_tab"),
    Input("analyze-data-btn", "n_clicks"),
    State("stored-compiled-data", "data"),
     State("quality-analysis-options", "value"),
    prevent_initial_call=True
)
def analyze_data_quality(active_tab, n_clicks, stored_data_fixed, options):
        """
        Analyze data quality based on selected options.
        Enhanced with better error handling and debugging.
        """
        # Only update on button click
        #ctx = dash.callback_context
        #if not ctx.triggered or ctx.triggered[0]["prop_id"].split(".")[0] != "analyze-data-btn":
            #return None

        # Add debugging messages
        #if n_clicks is None or n_clicks == 0:
            #return html.Div("Click the Analyze Data Quality button to start analysis.")
        # 1) Make sure we're on the Quality tab
        if active_tab != "tab-quality":
            raise PreventUpdate

        # 2) Make sure they actually clicked the button
        if not n_clicks or n_clicks < 1:
            raise PreventUpdate

        # Check if we have data to analyze
        if not stored_data_fixed or "data" not in stored_data_fixed:
            #raise PreventUpdate
            # Try falling back to the original uploaded data
            return html.Div("No data available to analyze. Please upload and compile data first.",
                            style={"color": "red"})


        try:
            # Load data with more detailed error handling
            if "data" in stored_data_fixed:
                df = pd.read_json(io.StringIO(stored_data_fixed["data"]), orient='split')
            elif "dfs" in stored_data_fixed and isinstance(stored_data_fixed["dfs"], list) and len(stored_data_fixed["dfs"]) > 0:
                # If stored_data is from "stored-data", we need to select the first dataframe
                df = pd.read_json(io.StringIO(stored_data_fixed["dfs"][0]), orient='split')
            else:
                return html.Div("Data format error: Could not interpret the stored data.",
                                style={"color": "red"})

            # Log data shape for debugging
            data_info = html.Div([
                html.P(f"Data loaded successfully: {df.shape[0]} rows, {df.shape[1]} columns"),
                html.P(f"Columns: {', '.join(df.columns[:10])}{'...' if len(df.columns) > 10 else ''}"),
                html.P(f"Selected analysis options: {', '.join(options) if options else 'None'}")
            ])

            # Run quality analysis with error handling
            try:
                quality_issues = detect_data_quality_issues(df)
                cleaning_suggestions = suggest_data_cleaning_steps(quality_issues)
            except Exception as e:
                return html.Div([
                    data_info,
                    html.P(f"Error during data quality analysis: {str(e)}", style={"color": "red"}),
                    html.Pre(str(df.dtypes))  # Show data types to help debug
                ])

            # Create results output
            results_components = [data_info]

            # Summary
            summary = quality_issues.get('summary', {})
            if summary:
                results_components.append(html.Div([
                    html.H5("Data Quality Summary"),
                    html.P(f"Total issues found: {summary.get('total_issues', 'N/A')}"),
                    html.P(
                        f"Columns with issues: {summary.get('columns_with_issues', 'N/A')} out of {len(df.columns)}"),
                    html.P(f"Critical issues: {summary.get('critical_issues', 'N/A')}")
                ]))

            # Missing values
            if 'missing_values' in options and quality_issues.get('missing_values'):
                missing_data = []
                for col, info in quality_issues['missing_values'].items():
                    missing_data.append({
                        'Column': col,
                        'Missing Count': info.get('count', 'N/A'),
                        'Missing Percent': f"{info.get('percent', 'N/A')}%"
                    })

                if missing_data:
                    results_components.append(html.Div([
                        html.Hr(),
                        html.H5("Missing Values"),
                        dash_table.DataTable(
                            columns=[
                                {'name': 'Column', 'id': 'Column'},
                                {'name': 'Missing Count', 'id': 'Missing Count'},
                                {'name': 'Missing Percent', 'id': 'Missing Percent'}
                            ],
                            data=missing_data,
                            sort_action="native",
                            style_table={'overflowX': 'auto'},
                            style_data_conditional=[
                                {
                                    'if': {'filter_query': '{Missing Percent} contains ">20%"'},
                                    'backgroundColor': '#FFCCCC',
                                    'color': 'black',
                                }
                            ]
                        )
                    ]))

            # Data type issues
            if 'format_issues' in options and quality_issues.get('data_type_issues'):
                type_data = []
                for col, info in quality_issues['data_type_issues'].items():
                    type_data.append({
                        'Column': col,
                        'Current Type': info.get('current_type', 'N/A'),
                        'Suggested Type': info.get('suggested_type', 'N/A'),
                        'Issue': info.get('issue', 'N/A')
                    })

                if type_data:
                    results_components.append(html.Div([
                        html.Hr(),
                        html.H5("Data Format Issues"),
                        dash_table.DataTable(
                            columns=[
                                {'name': 'Column', 'id': 'Column'},
                                {'name': 'Current Type', 'id': 'Current Type'},
                                {'name': 'Suggested Type', 'id': 'Suggested Type'},
                                {'name': 'Issue', 'id': 'Issue'}
                            ],
                            data=type_data,
                            sort_action="native",
                            style_table={'overflowX': 'auto'}
                        )
                    ]))

            # Outliers
            if 'outliers' in options and quality_issues.get('outliers'):
                outlier_data = []
                for col, info in quality_issues['outliers'].items():
                    outlier_data.append({
                        'Column': col,
                        'Outlier Count': info.get('count', 'N/A'),
                        'Outlier Percent': f"{info.get('percent', 'N/A')}%",
                        'Detection Method': info.get('method', 'N/A')
                    })

                if outlier_data:
                    results_components.append(html.Div([
                        html.Hr(),
                        html.H5("Outliers"),
                        dash_table.DataTable(
                            columns=[
                                {'name': 'Column', 'id': 'Column'},
                                {'name': 'Outlier Count', 'id': 'Outlier Count'},
                                {'name': 'Outlier Percent', 'id': 'Outlier Percent'},
                                {'name': 'Detection Method', 'id': 'Detection Method'}
                            ],
                            data=outlier_data,
                            sort_action="native",
                            style_table={'overflowX': 'auto'}
                        )
                    ]))

            # Cleaning suggestions
            if cleaning_suggestions:
                suggestion_data = []
                for suggestion in cleaning_suggestions:
                    suggestion_data.append({
                        'Priority': suggestion.get('priority', 'N/A').capitalize(),
                        'Column': suggestion.get('column', 'N/A'),
                        'Suggestion': suggestion.get('suggestion', 'N/A'),
                        'Action': suggestion.get('action', 'N/A').replace('_', ' ').capitalize()
                    })

                if suggestion_data:
                    results_components.append(html.Div([
                        html.Hr(),
                        html.H5("Suggested Cleaning Steps"),
                        dash_table.DataTable(
                            columns=[
                                {'name': 'Priority', 'id': 'Priority'},
                                {'name': 'Column', 'id': 'Column'},
                                {'name': 'Suggestion', 'id': 'Suggestion'},
                                {'name': 'Action', 'id': 'Action'}
                            ],
                            data=suggestion_data,
                            sort_action="native",
                            style_table={'overflowX': 'auto'},
                            style_data_conditional=[
                                {
                                    'if': {'filter_query': '{Priority} contains "High"'},
                                    'backgroundColor': '#FFCCCC',
                                    'color': 'black',
                                },
                                {
                                    'if': {'filter_query': '{Priority} contains "Medium"'},
                                    'backgroundColor': '#FFFFCC',
                                    'color': 'black',
                                }
                            ]
                        )
                    ]))

            # If no results components were added beyond the data info, add a message
            if len(results_components) <= 1:
                results_components.append(html.Div("No quality issues detected in the data."))

            return html.Div(results_components)

        except Exception as e:
            import traceback
            return html.Div([
                html.P(f"Error analyzing data quality: {str(e)}", style={"color": "red"}),
                html.Pre(traceback.format_exc())
            ])

    # Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
