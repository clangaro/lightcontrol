#!/usr/bin/env python3
"""
Light Monitoring Dashboard
---------------------------
Streamlit web application for visualizing light sensor transition data.
Loads transition CSV files from a specified directory, filters events
by sensor, event type, and date, and displays them in an interactive
table and scatter plot.

Author: [Your Name]
Date: 2025-10-29
"""

import os
from typing import List

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

# ---------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------

DATA_DIR: str = r"C:\Users\krieg\Desktop\UCB Age Light Records"


# ---------------------------------------------------------------------
# DATA LOADING
# ---------------------------------------------------------------------
def load_transitions(data_dir: str = DATA_DIR) -> pd.DataFrame:
    """
    Load and combine all light transition CSV files from a directory.

    Args:
        data_dir: Directory containing light transition CSV files.

    Returns:
        A pandas DataFrame containing all transitions, with parsed timestamps.
    """
    # Identify all transition files in the target directory
    files: List[str] = [
        f for f in os.listdir(data_dir) if "light_transitions" in f and f.endswith(".csv")
    ]

    # Combine all CSV files into one DataFrame
    transitions = pd.concat(
        (pd.read_csv(os.path.join(data_dir, f)) for f in files),
        ignore_index=True
    )

    # Parse timestamps into datetime objects
    transitions["timestamp"] = pd.to_datetime(transitions["timestamp"], errors="coerce")

    return transitions


# ---------------------------------------------------------------------
# STREAMLIT DASHBOARD
# ---------------------------------------------------------------------
def main() -> None:
    """Run the Streamlit light monitoring dashboard."""
    st.title("🧠 Light Monitoring Dashboard")

    # Load and cache transition data
    @st.cache_data
    def _cached_load() -> pd.DataFrame:
        return load_transitions()

    transitions = _cached_load()

    # Sidebar filters
    sensor_options = sorted(transitions["sensor"].unique())
    selected_sensors = st.multiselect(
        "Select sensors", sensor_options, default=sensor_options
    )

    selected_events = st.multiselect(
        "Select events", ["ON", "OFF"], default=["ON", "OFF"]
    )

    date_filter = st.date_input("Filter by date(s)", [])

    # Apply filters to dataset
    filtered = transitions[
        (transitions["sensor"].isin(selected_sensors))
        & (transitions["event"].isin(selected_events))
    ]

    if date_filter:
        filtered = filtered[filtered["timestamp"].dt.date.isin(date_filter)]

    # Display filtered data table
    st.write("### Detected Transitions", filtered)

    # -----------------------------------------------------------------
    # PLOT TRANSITIONS
    # -----------------------------------------------------------------
    st.write("### Visualization: Light ON/OFF Transitions Over Time")

    fig, ax = plt.subplots(figsize=(10, 5))

    for sensor in selected_sensors:
        sensor_data = filtered[filtered["sensor"] == sensor]
        ax.scatter(
            sensor_data["timestamp"],
            [sensor] * len(sensor_data),
            label=sensor,
            alpha=0.7,
        )

    ax.set_title("Light ON/OFF Transitions Over Time")
    ax.set_xlabel("Timestamp")
    ax.set_ylabel("Sensor")
    ax.legend(title="Sensor", bbox_to_anchor=(1.05, 1), loc="upper left")
    plt.xticks(rotation=45)
    plt.tight_layout()

    st.pyplot(fig)


# ---------------------------------------------------------------------
# ENTRY POINT
# ---------------------------------------------------------------------
if __name__ == "__main__":
    main()
