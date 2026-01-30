"""
Geographic Analysis Page - Department-based Analysis

Displays accidents by department (bar chart) and top 10 departments with most accidents.
Requirements: 3.5, 3.6
"""
import streamlit as st
import pandas as pd
import plotly.express as px
from utils.visualizations import create_accident_map
from utils.data_loader import (
    load_cleaned_data, 
    get_data_status_message, 
    apply_filters,
    get_department_name,
    get_department_display_name,
    DEPARTMENT_NAMES
)

# Label mappings
COLLISION_TYPE_LABELS = {
    1: "Two vehicles - frontal",
    2: "Two vehicles - rear",
    3: "Two vehicles - side",
    4: "Three+ vehicles - chain",
    5: "Three+ vehicles - multiple",
    6: "Other collision",
    7: "No collision"
}

LOCATION_LABELS = {
    1: "Urban",
    2: "Rural"
}

st.set_page_config(
    page_title="Geographic Analysis - Road Accident Analysis",
    page_icon="🗺️",
    layout="wide"
)

st.title("Geographic Analysis")
st.markdown("*Analyze accident distribution by department*")

# Check data availability
error_message = get_data_status_message()
if error_message:
    st.error(error_message)
    st.stop()

# Load data
try:
    df = load_cleaned_data()
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()


def create_filter_sidebar(df: pd.DataFrame) -> dict:
    """Create sidebar filters."""
    st.sidebar.header("🔍 Filters")
    filters = {}
    
    if "year" in df.columns:
        years = sorted(df["year"].dropna().unique())
        filters["year"] = st.sidebar.multiselect(
            "Year", options=years, default=[],
            help="Select years to filter (leave empty for all)"
        )
    
    if "dep" in df.columns:
        departments = sorted(df["dep"].dropna().unique())
        # Create mapping from display name to code
        dept_options = {
            get_department_display_name(dep): dep 
            for dep in departments
        }
        # Sort by display name
        sorted_display_names = sorted(dept_options.keys())
        selected_display_names = st.sidebar.multiselect(
            "Department", options=sorted_display_names, default=[],
            help="Select departments to filter (leave empty for all)"
        )
        # Convert selected display names back to codes
        filters["department"] = [dept_options[name] for name in selected_display_names]
    
    if "col" in df.columns:
        collision_types = sorted(df["col"].dropna().unique())
        collision_options = {
            ct: COLLISION_TYPE_LABELS.get(ct, f"Type {ct}") 
            for ct in collision_types
        }
        selected_labels = st.sidebar.multiselect(
            "Collision Type",
            options=list(collision_options.values()),
            default=[],
            help="Select collision types to filter (leave empty for all)"
        )
        label_to_code = {v: k for k, v in collision_options.items()}
        filters["collision_type"] = [label_to_code[label] for label in selected_labels]
    
    return filters


# Create filters and apply
filters = create_filter_sidebar(df)
filtered_df = apply_filters(df, filters)

# Show filter status
if any(len(v) > 0 for v in filters.values() if isinstance(v, list)):
    st.sidebar.success(f"Showing {len(filtered_df):,} of {len(df):,} records")

# Top 10 Departments
st.header("🏆 Top 10 Departments with Most Accidents")

if "dep" in filtered_df.columns:
    dept_counts = filtered_df.groupby("dep").size().reset_index(name="count")
    top_10 = dept_counts.nlargest(10, "count")
    
    # Add department names
    top_10["dept_name"] = top_10["dep"].apply(get_department_name)
    top_10["dept_display"] = top_10["dep"].apply(get_department_display_name)
    
    fig_top10 = px.bar(
        top_10,
        x="dept_name",
        y="count",
        title="Top 10 Departments by Number of Accidents",
        color="count",
        color_continuous_scale="Reds",
        text="count",
        custom_data=["dep", "dept_display"]
    )
    fig_top10.update_layout(
        xaxis_title="Department",
        yaxis_title="Number of Accidents",
        showlegend=False
    )
    fig_top10.update_traces(
        texttemplate='%{text:,}',
        textposition='outside',
        hovertemplate="<b>%{customdata[1]}</b><br>Accidents: %{y:,}<extra></extra>"
    )
    st.plotly_chart(fig_top10, use_container_width=True)
    
    # Display as table
    st.subheader("📋 Top 10 Departments Table")
    top_10_display = top_10.copy()
    top_10_display = top_10_display[["dep", "dept_name", "count"]].copy()
    top_10_display.columns = ["Code", "Department", "Accidents"]
    top_10_display["Rank"] = range(1, 11)
    top_10_display = top_10_display[["Rank", "Department", "Code", "Accidents"]]
    st.dataframe(top_10_display, hide_index=True, use_container_width=True)
else:
    st.warning("Department column not available in the dataset.")

st.divider()

# All Departments Distribution
st.header("📊 Accidents by Department (All)")

if "dep" in filtered_df.columns:
    dept_counts = filtered_df.groupby("dep").size().reset_index(name="count")
    dept_counts = dept_counts.sort_values("count", ascending=False)
    
    # Add department names
    dept_counts["dept_name"] = dept_counts["dep"].apply(get_department_name)
    dept_counts["dept_display"] = dept_counts["dep"].apply(get_department_display_name)
    
    fig_all_depts = px.bar(
        dept_counts,
        x="dept_name",
        y="count",
        title="Number of Accidents by Department",
        color="count",
        color_continuous_scale="Blues",
        custom_data=["dep", "dept_display"]
    )
    fig_all_depts.update_layout(
        xaxis_title="Department",
        yaxis_title="Number of Accidents",
        showlegend=False,
        xaxis={'categoryorder': 'total descending'}
    )
    fig_all_depts.update_traces(
        hovertemplate="<b>%{customdata[1]}</b><br>Accidents: %{y:,}<extra></extra>"
    )
    st.plotly_chart(fig_all_depts, use_container_width=True)

st.divider()

# Urban vs Rural Analysis
st.header("🏙️ Urban vs Rural Distribution")

col1, col2 = st.columns(2)

with col1:
    if "agg" in filtered_df.columns:
        location_counts = filtered_df.groupby("agg").size().reset_index(name="count")
        location_counts["location_type"] = location_counts["agg"].map(LOCATION_LABELS)
        
        fig_location = px.pie(
            location_counts,
            values="count",
            names="location_type",
            title="Urban vs Rural Accidents",
            color_discrete_sequence=px.colors.qualitative.Set2
        )
        fig_location.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_location, use_container_width=True)
    else:
        st.warning("Location type (agg) column not available.")

with col2:
    if "agg" in filtered_df.columns:
        location_counts = filtered_df.groupby("agg").size().reset_index(name="count")
        location_counts["location_type"] = location_counts["agg"].map(LOCATION_LABELS)
        
        fig_location_bar = px.bar(
            location_counts,
            x="location_type",
            y="count",
            title="Accidents by Location Type",
            color="location_type",
            color_discrete_sequence=px.colors.qualitative.Set2,
            text="count"
        )
        fig_location_bar.update_layout(
            xaxis_title="Location Type",
            yaxis_title="Number of Accidents",
            showlegend=False
        )
        fig_location_bar.update_traces(
            texttemplate='%{text:,}',
            textposition='outside'
        )
        st.plotly_chart(fig_location_bar, use_container_width=True)

st.divider()

# Interactive Map
st.header("🗺️ Interactive Accident Map")

if "lat" in filtered_df.columns and "long" in filtered_df.columns:
    # Controls
    col_map1, col_map2 = st.columns([1, 3])

    with col_map1:
        map_type = st.radio(
            "Map Style",
            options=["Heatmap", "Scatter"],
            help="Choose between density heatmap or individual points"
        )

        # Heatmap controls
        heatmap_radius = 15
        heatmap_opacity = 0.6

        if map_type == "Heatmap":
            heatmap_radius = st.slider(
                "Heatmap Radius",
                min_value=5,
                max_value=50,
                value=15,
                help="Adjust the smoothing radius of the heatmap"
            )
            heatmap_opacity = st.slider(
                "Opacity",
                min_value=0.1,
                max_value=1.0,
                value=0.6,
                step=0.1,
                help="Adjust the opacity of the heatmap layer"
            )

        # Limit points for performance if too many
        max_points = 5000
        if len(filtered_df) > max_points:
            st.info(f"Showing first {max_points:,} points for performance")
            map_df = filtered_df.head(max_points)
        else:
            map_df = filtered_df

    with col_map2:
        with st.spinner(f"Generating {map_type} map..."):
            fig_map = create_accident_map(
                map_df,
                lat_col="lat",
                lon_col="long",
                map_type=map_type.lower(),
                radius=heatmap_radius,
                opacity=heatmap_opacity
            )
            st.plotly_chart(fig_map, use_container_width=True)
else:
    st.warning("Latitude/Longitude data not available for mapping.")

st.divider()

# Department Statistics Summary
st.header("📈 Department Statistics")

if "dep" in filtered_df.columns:
    dept_counts = filtered_df.groupby("dep").size()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Total Departments",
            value=f"{len(dept_counts):,}"
        )
    
    with col2:
        st.metric(
            label="Avg Accidents/Dept",
            value=f"{dept_counts.mean():,.0f}"
        )
    
    with col3:
        max_dept_code = dept_counts.idxmax()
        max_dept_name = get_department_name(max_dept_code)
        st.metric(
            label="Max Accidents",
            value=f"{dept_counts.max():,}",
            delta=f"{max_dept_name}"
        )
    
    with col4:
        min_dept_code = dept_counts.idxmin()
        min_dept_name = get_department_name(min_dept_code)
        st.metric(
            label="Min Accidents",
            value=f"{dept_counts.min():,}",
            delta=f"{min_dept_name}"
        )

st.divider()

# Severity by Department (Top 10)
st.header("⚠️ Severity Analysis by Top Departments")

if "dep" in filtered_df.columns and "num_killed" in filtered_df.columns:
    dept_severity = filtered_df.groupby("dep").agg({
        "num_killed": "sum",
        "num_hospitalized": "sum" if "num_hospitalized" in filtered_df.columns else lambda x: 0,
        "num_light_injury": "sum" if "num_light_injury" in filtered_df.columns else lambda x: 0
    }).reset_index()
    
    dept_severity["total_casualties"] = (
        dept_severity["num_killed"] + 
        dept_severity.get("num_hospitalized", 0) + 
        dept_severity.get("num_light_injury", 0)
    )
    
    top_10_severity = dept_severity.nlargest(10, "total_casualties")
    
    # Add department names
    top_10_severity["dept_name"] = top_10_severity["dep"].apply(get_department_name)
    top_10_severity["dept_display"] = top_10_severity["dep"].apply(get_department_display_name)
    
    fig_severity = px.bar(
        top_10_severity,
        x="dept_name",
        y=["num_killed", "num_hospitalized", "num_light_injury"],
        title="Casualties by Department (Top 10)",
        barmode="stack",
        labels={"value": "Count", "variable": "Severity"},
        color_discrete_map={
            "num_killed": "#d62728",
            "num_hospitalized": "#ff7f0e",
            "num_light_injury": "#2ca02c"
        },
        custom_data=["dep", "dept_display"]
    )
    fig_severity.update_layout(
        xaxis_title="Department",
        yaxis_title="Number of Casualties",
        legend_title="Severity"
    )
    # Update legend labels
    fig_severity.for_each_trace(lambda t: t.update(
        name={"num_killed": "Fatalities", "num_hospitalized": "Hospitalized", "num_light_injury": "Light Injuries"}.get(t.name, t.name)
    ))
    st.plotly_chart(fig_severity, use_container_width=True)
else:
    st.info("Severity data not available for department analysis.")
