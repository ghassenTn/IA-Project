# Visualization utilities for Road Accident Analysis
"""
Functions for generating charts and visualizations for the dashboard.
"""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Optional


def create_temporal_chart(
    df: pd.DataFrame,
    time_column: str,
    title: str,
    x_label: str = None
) -> go.Figure:
    """
    Create a bar chart showing accident counts over time.
    
    Args:
        df: DataFrame with accident data
        time_column: Column name for time grouping (e.g., 'hour', 'day_of_week')
        title: Chart title
        x_label: Optional x-axis label
        
    Returns:
        Plotly figure object
    """
    counts = df[time_column].value_counts().sort_index()
    fig = px.bar(
        x=counts.index,
        y=counts.values,
        title=title,
        labels={'x': x_label or time_column, 'y': 'Number of Accidents'}
    )
    return fig


def create_categorical_chart(
    df: pd.DataFrame,
    column: str,
    title: str,
    labels_map: Optional[dict] = None
) -> go.Figure:
    """
    Create a bar chart for categorical variable distribution.
    
    Args:
        df: DataFrame with accident data
        column: Column name for the categorical variable
        title: Chart title
        labels_map: Optional mapping from codes to labels
        
    Returns:
        Plotly figure object
    """
    counts = df[column].value_counts().sort_index()
    
    if labels_map:
        x_labels = [labels_map.get(idx, str(idx)) for idx in counts.index]
    else:
        x_labels = counts.index
    
    fig = px.bar(
        x=x_labels,
        y=counts.values,
        title=title,
        labels={'x': column, 'y': 'Number of Accidents'}
    )
    return fig


def create_pie_chart(
    df: pd.DataFrame,
    column: str,
    title: str,
    labels_map: Optional[dict] = None
) -> go.Figure:
    """
    Create a pie chart for categorical variable distribution.
    
    Args:
        df: DataFrame with accident data
        column: Column name for the categorical variable
        title: Chart title
        labels_map: Optional mapping from codes to labels
        
    Returns:
        Plotly figure object
    """
    counts = df[column].value_counts()
    
    if labels_map:
        names = [labels_map.get(idx, str(idx)) for idx in counts.index]
    else:
        names = [str(idx) for idx in counts.index]
    
    fig = px.pie(
        values=counts.values,
        names=names,
        title=title
    )
    return fig

def create_accident_map(
    df: pd.DataFrame,
    lat_col: str = 'lat',
    lon_col: str = 'long',
    map_type: str = 'heatmap',
    zoom: int = 4,
    radius: int = 15,
    opacity: float = 0.6
) -> go.Figure:
    """
    Create a map visualization of accidents.

    Args:
        df: DataFrame containing accident data
        lat_col: Name of latitude column
        lon_col: Name of longitude column
        map_type: Type of map ('heatmap' or 'scatter')
        zoom: Initial zoom level
        radius: Radius for heatmap (default 15)
        opacity: Opacity for heatmap (default 0.6)

    Returns:
        Plotly figure object
    """
    # Ensure coordinates are numeric
    df_map = df.copy()
    if lat_col not in df_map.columns or lon_col not in df_map.columns:
        fig = go.Figure()
        fig.update_layout(
            title=f"Missing coordinates columns: {lat_col}, {lon_col}",
            xaxis={"visible": False},
            yaxis={"visible": False}
        )
        return fig

    df_map[lat_col] = pd.to_numeric(df_map[lat_col], errors='coerce')
    df_map[lon_col] = pd.to_numeric(df_map[lon_col], errors='coerce')
    df_map = df_map.dropna(subset=[lat_col, lon_col])

    if df_map.empty:
        # Return empty figure with message
        fig = go.Figure()
        fig.update_layout(
            title="No valid location data available for selected filters",
            xaxis={"visible": False},
            yaxis={"visible": False}
        )
        return fig

    # Center roughly on France
    center_lat = 46.603354
    center_lon = 1.888334

    if map_type == 'heatmap':
        fig = px.density_mapbox(
            df_map,
            lat=lat_col,
            lon=lon_col,
            radius=radius,
            opacity=opacity,
            center=dict(lat=center_lat, lon=center_lon),
            zoom=zoom,
            mapbox_style="open-street-map",
            title="Accident Density Heatmap"
        )
    else:
        # Scatter map
        # Determine color column if available
        color_col = None
        if "max_severity" in df_map.columns:
            color_col = "max_severity"
        elif "col" in df_map.columns:
            color_col = "col"

        fig = px.scatter_mapbox(
            df_map,
            lat=lat_col,
            lon=lon_col,
            color=color_col,
            hover_data=[lat_col, lon_col],
            zoom=zoom,
            center=dict(lat=center_lat, lon=center_lon),
            mapbox_style="open-street-map",
            title="Accident Locations"
        )

    fig.update_layout(margin={"r":0,"t":40,"l":0,"b":0})
    return fig
