import io

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Union, Any
import dash
from dash import dcc, html, dash_table
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import plotly.express as px
import plotly.graph_objects as go


def add_visualization_module_to_app(app):
    """
    Add visualization module callbacks to the app.
    """

    # Populate dropdown options based on available data
    @app.callback(
        [Output("x-axis-column", "options"),
         Output("x-axis-column", "value"),
         Output("y-axis-column", "options"),
         Output("y-axis-column", "value"),
         Output("color-column", "options"),
         Output("color-column", "value")],
        [Input("stored-cleaned-data", "data"),
         Input("stored-compiled-data", "data"),
         Input("main-tabs", "active_tab")]
    )
    def populate_visualization_dropdowns(cleaned_data, compiled_data, active_tab):
        """
        Populate dropdown options for visualization based on available data.
        """
        # Only update when on the visualization tab
        if active_tab != "tab-visualization":
            raise dash.exceptions.PreventUpdate

        # Use cleaned data if available, otherwise use compiled data
        data = cleaned_data if cleaned_data else compiled_data

        if not data:
            empty_options = []
            return [empty_options, None, empty_options, None, empty_options, "none"]

        # Load the data
        df = pd.read_json(io.StringIO(data["data"]), orient="split")

        # Create options for all columns
        all_columns = [{"label": col, "value": col} for col in df.columns]

        # Try to find numeric columns for default x and y
        numeric_cols = [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col])]
        default_x = numeric_cols[0] if numeric_cols else df.columns[0]
        default_y = numeric_cols[1] if len(numeric_cols) > 1 else (numeric_cols[0] if numeric_cols else None)

        # Add "None" option for color
        color_options = [{"label": "None", "value": "none"}] + all_columns

        return [all_columns, default_x, all_columns, default_y, color_options, "none"]

    # Create plot based on selected options
    @app.callback(
        Output("plot-output", "children"),
        [Input("create-plot-btn", "n_clicks")],
        [State("plot-type", "value"),
         State("x-axis-column", "value"),
         State("y-axis-column", "value"),
         State("color-column", "value"),
         State("plot-options", "value"),
         State("stored-cleaned-data", "data"),
         State("stored-compiled-data", "data")]
    )
    def create_plot(n_clicks, plot_type, x_column, y_column, color_column, plot_options, cleaned_data, compiled_data):
        """
        Create a plot based on selected options.
        """
        # Only update on button click
        ctx = dash.callback_context
        if not ctx.triggered or ctx.triggered[0]["prop_id"].split(".")[0] != "create-plot-btn":
            return html.Div("Select plot options and click 'Create Plot' to visualize data.")
        
        # Use cleaned data if available, otherwise use compiled data
        data = cleaned_data if cleaned_data else compiled_data
        
        if not data or not x_column:
            return html.Div("No data available for plotting.")
        
        # Load data
        df = pd.read_json(io.StringIO(data["data"]), orient="split")
        
        # Handle histogram (only needs x)
        if plot_type == "histogram":
            fig = create_histogram(df, x_column, color_column, plot_options)
        # Handle box plot (can work with just x or y)
        elif plot_type == "box":
            fig = create_box_plot(df, x_column, y_column, color_column, plot_options)
        # All other plots need both x and y
        elif y_column:
            if plot_type == "scatter":
                fig = create_scatter_plot(df, x_column, y_column, color_column, plot_options)
            elif plot_type == "line":
                fig = create_line_plot(df, x_column, y_column, color_column, plot_options)
            elif plot_type == "bar":
                fig = create_bar_chart(df, x_column, y_column, color_column, plot_options)
            else:
                return html.Div(f"Plot type '{plot_type}' not implemented.")
        else:
            return html.Div("Please select a Y-axis column for this plot type.")
        
        # Create plot display
        plot_display = dcc.Graph(
            id="data-plot",
            figure=fig,
            config={
                "responsive": True,
                "displayModeBar": True,
                "modeBarButtonsToRemove": ["lasso2d", "select2d"]
            },
            style={"height": "600px"}
        )
        
        return plot_display

def create_scatter_plot(df, x_column, y_column, color_column, plot_options):
    """
    Create a scatter plot.
    """
    # Create base plot
    if color_column and color_column != "none":
        fig = px.scatter(df, x=x_column, y=y_column, color=color_column,
                       title=f"{y_column} vs {x_column}",
                       labels={x_column: x_column, y_column: y_column},
                       hover_data=df.columns)
    else:
        fig = px.scatter(df, x=x_column, y=y_column,
                       title=f"{y_column} vs {x_column}",
                       labels={x_column: x_column, y_column: y_column},
                       hover_data=df.columns)
    
    # Add mean line
    if "mean_line" in plot_options:
        mean_y = df[y_column].mean()
        fig.add_hline(y=mean_y, line_dash="dash", line_color="red",
                      annotation_text=f"Mean: {mean_y:.2f}",
                      annotation_position="top right")
    
    # Add standard deviation lines
    if "std_lines" in plot_options:
        mean_y = df[y_column].mean()
        std_y = df[y_column].std()
        
        fig.add_hline(y=mean_y + 3*std_y, line_dash="dot", line_color="orange",
                      annotation_text=f"+3σ: {(mean_y + 3*std_y):.2f}",
                      annotation_position="top right")
        
        fig.add_hline(y=mean_y - 3*std_y, line_dash="dot", line_color="orange",
                      annotation_text=f"-3σ: {(mean_y - 3*std_y):.2f}",
                      annotation_position="bottom right")
    
    # Add trendline
    if "trendline" in plot_options:
        # Only add trendline for numeric x
        if pd.api.types.is_numeric_dtype(df[x_column]):
            fig = px.scatter(df, x=x_column, y=y_column, 
                           color=color_column if color_column != "none" else None,
                           trendline="ols", trendline_color_override="black",
                           title=f"{y_column} vs {x_column}",
                           labels={x_column: x_column, y_column: y_column},
                           hover_data=df.columns)
    
    return fig

def create_line_plot(df, x_column, y_column, color_column, plot_options):
    """
    Create a line plot.
    """
    # Sort by x for line plot
    df_sorted = df.sort_values(by=x_column)
    
    # Create base plot
    if color_column and color_column != "none":
        fig = px.line(df_sorted, x=x_column, y=y_column, color=color_column,
                     title=f"{y_column} vs {x_column}",
                     labels={x_column: x_column, y_column: y_column})
    else:
        fig = px.line(df_sorted, x=x_column, y=y_column,
                     title=f"{y_column} vs {x_column}",
                     labels={x_column: x_column, y_column: y_column})
    
    # Add mean line
    if "mean_line" in plot_options:
        mean_y = df[y_column].mean()
        fig.add_hline(y=mean_y, line_dash="dash", line_color="red",
                      annotation_text=f"Mean: {mean_y:.2f}",
                      annotation_position="top right")
    
    # Add standard deviation lines
    if "std_lines" in plot_options:
        mean_y = df[y_column].mean()
        std_y = df[y_column].std()
        
        fig.add_hline(y=mean_y + 3*std_y, line_dash="dot", line_color="orange",
                      annotation_text=f"+3σ: {(mean_y + 3*std_y):.2f}",
                      annotation_position="top right")
        
        fig.add_hline(y=mean_y - 3*std_y, line_dash="dot", line_color="orange",
                      annotation_text=f"-3σ: {(mean_y - 3*std_y):.2f}",
                      annotation_position="bottom right")
    
    return fig

def create_bar_chart(df, x_column, y_column, color_column, plot_options):
    """
    Create a bar chart.
    """
    # Group by x if necessary (for numeric x)
    if pd.api.types.is_numeric_dtype(df[x_column]) and len(df[x_column].unique()) > 20:
        # Create bins for numeric x with many unique values
        df['binned_x'] = pd.cut(df[x_column], bins=10)
        grouped = df.groupby('binned_x')[y_column].mean().reset_index()
        x_col = 'binned_x'
    else:
        grouped = df
        x_col = x_column
    
    # Create base plot
    if color_column and color_column != "none" and color_column in grouped.columns:
        fig = px.bar(grouped, x=x_col, y=y_column, color=color_column,
                    title=f"{y_column} by {x_column}",
                    labels={x_col: x_column, y_column: y_column})
    else:
        fig = px.bar(grouped, x=x_col, y=y_column,
                    title=f"{y_column} by {x_column}",
                    labels={x_col: x_column, y_column: y_column})
    
    # Add mean line
    if "mean_line" in plot_options:
        mean_y = df[y_column].mean()
        fig.add_hline(y=mean_y, line_dash="dash", line_color="red",
                      annotation_text=f"Mean: {mean_y:.2f}",
                      annotation_position="top right")
    
    return fig

def create_box_plot(df, x_column, y_column, color_column, plot_options):
    """
    Create a box plot.
    """
    # Create base plot
    if y_column:
        if color_column and color_column != "none":
            fig = px.box(df, x=x_column, y=y_column, color=color_column,
                        title=f"Distribution of {y_column} by {x_column}",
                        labels={x_column: x_column, y_column: y_column})
        else:
            fig = px.box(df, x=x_column, y=y_column,
                        title=f"Distribution of {y_column} by {x_column}",
                        labels={x_column: x_column, y_column: y_column})
    else:
        # Box plot of just x
        if color_column and color_column != "none":
            fig = px.box(df, x=x_column, color=color_column,
                        title=f"Distribution of {x_column}",
                        labels={x_column: x_column})
        else:
            fig = px.box(df, x=x_column,
                        title=f"Distribution of {x_column}",
                        labels={x_column: x_column})
    
    return fig

def create_histogram(df, x_column, color_column, plot_options):
    """
    Create a histogram.
    """
    # Create base plot
    if color_column and color_column != "none":
        fig = px.histogram(df, x=x_column, color=color_column,
                          title=f"Distribution of {x_column}",
                          labels={x_column: x_column})
    else:
        fig = px.histogram(df, x=x_column,
                          title=f"Distribution of {x_column}",
                          labels={x_column: x_column})
    
    # Add mean line
    if "mean_line" in plot_options and pd.api.types.is_numeric_dtype(df[x_column]):
        mean_x = df[x_column].mean()
        fig.add_vline(x=mean_x, line_dash="dash", line_color="red",
                      annotation_text=f"Mean: {mean_x:.2f}",
                      annotation_position="top right")
    
    # Add standard deviation lines
    if "std_lines" in plot_options and pd.api.types.is_numeric_dtype(df[x_column]):
        mean_x = df[x_column].mean()
        std_x = df[x_column].std()
        
        fig.add_vline(x=mean_x + 3*std_x, line_dash="dot", line_color="orange",
                      annotation_text=f"+3σ: {(mean_x + 3*std_x):.2f}",
                      annotation_position="top right")
        
        fig.add_vline(x=mean_x - 3*std_x, line_dash="dot", line_color="orange",
                      annotation_text=f"-3σ: {(mean_x - 3*std_x):.2f}",
                      annotation_position="top left")
    
    return fig