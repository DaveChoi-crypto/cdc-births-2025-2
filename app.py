"""US Provisional Natality Explorer (2025) - Streamlit Dashboard.

Designed for undergraduate business analytics students to explore geographic,
seasonal, and demographic patterns in provisional CDC birth counts.

Author: Development Agent (Pair-programmed with User)
Dataset: CDC Provisional Natality Data (2025)
"""

import os
import sys
from pathlib import Path
from typing import List, Tuple
import pandas as pd
import streamlit as st

# -----------------------------------------------------------------------------
# 1. Page Configuration & Path Setup
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="CDC 2025 Natality Explorer",
    page_icon="👶",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Ensure both project root and src/ directory are in sys.path
ROOT_DIR = Path(__file__).resolve().parent
SRC_DIR = ROOT_DIR / "src"
for path_dir in [ROOT_DIR, SRC_DIR]:
    if str(path_dir) not in sys.path:
        sys.path.insert(0, str(path_dir))

# Modular imports with fallback to handle both package ('src.X') and flat ('X') repository structures
try:
    from src.data_loader import MONTH_ORDER, load_data
    from src.metrics import (
        compute_kpis,
        get_monthly_by_sex,
        get_monthly_summary,
        get_sex_summary,
        get_state_month_matrix,
        get_state_summary,
    )
    from src.charts import (
        plot_choropleth_map,
        plot_monthly_by_sex_trend,
        plot_monthly_trend,
        plot_sex_comparison,
        plot_state_month_heatmap,
        plot_state_ranking,
        plot_top_bottom_comparison,
    )
except ModuleNotFoundError:
    try:
        from data_loader import MONTH_ORDER, load_data
        from metrics import (
            compute_kpis,
            get_monthly_by_sex,
            get_monthly_summary,
            get_sex_summary,
            get_state_month_matrix,
            get_state_summary,
        )
        from charts import (
            plot_choropleth_map,
            plot_monthly_by_sex_trend,
            plot_monthly_trend,
            plot_sex_comparison,
            plot_state_month_heatmap,
            plot_state_ranking,
            plot_top_bottom_comparison,
        )
    except ModuleNotFoundError as err:
        all_files = []
        for root, dirs, files in os.walk("."):
            for f in files:
                all_files.append(os.path.join(root, f))
        file_tree = "\n".join(sorted(all_files)) if all_files else "(no files found)"
        st.error(
            f"### ⚠️ GitHub Repository Structure Error\n\n"
            f"**Error Details:** `{err}`\n\n"
            "Streamlit Cloud cannot locate `data_loader.py`, `metrics.py`, or `charts.py`.\n\n"
            f"**Files currently detected in your GitHub deployment container:**\n"
            f"```text\n{file_tree}\n```\n\n"
            "**How to fix:**\n"
            "Please ensure that the `src/` folder (or the `.py` files inside it) and the `data/` folder "
            "are uploaded to your GitHub repository."
        )
        st.stop()

# Custom minimal CSS to enhance readability, typography, and card presentation
st.markdown(
    """
    <style>
    /* Metric card styling */
    div[data-testid="stMetric"] {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 12px 16px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    div[data-testid="stMetricLabel"] {
        font-size: 0.85rem !important;
        font-weight: 600;
        color: #475569;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.5rem !important;
        font-weight: 700;
        color: #0F172A;
    }
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 8px 16px;
        font-weight: 500;
        border-radius: 6px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# -----------------------------------------------------------------------------
# 2. Data Ingestion & State Initialization
# -----------------------------------------------------------------------------
@st.cache_data
def get_cached_dataset() -> pd.DataFrame:
    """Wrapper to load and cache the dataset with data-validation assertions."""
    return load_data()


try:
    df_raw = get_cached_dataset()
except Exception as e:
    st.error(f"❌ Failed to load dataset: {e}")
    st.stop()

# Master filter candidate lists
ALL_STATES: List[str] = sorted(df_raw["State of Residence"].unique().tolist())
ALL_MONTHS: List[str] = [m for m in MONTH_ORDER if m in df_raw["Month"].values]
ALL_SEX_OPTIONS: List[str] = ["All", "Female", "Male"]

# Initialize session state for filter controls if not yet present
if "filter_states" not in st.session_state:
    st.session_state["filter_states"] = ALL_STATES.copy()
if "filter_months" not in st.session_state:
    st.session_state["filter_months"] = ALL_MONTHS.copy()
if "filter_sex" not in st.session_state:
    st.session_state["filter_sex"] = "All"


def reset_filters():
    """Callback to reset all sidebar filters to default values."""
    st.session_state["filter_states"] = ALL_STATES.copy()
    st.session_state["filter_months"] = ALL_MONTHS.copy()
    st.session_state["filter_sex"] = "All"


def select_all_geos_and_months():
    """Callback to select all states and months."""
    st.session_state["filter_states"] = ALL_STATES.copy()
    st.session_state["filter_months"] = ALL_MONTHS.copy()


# -----------------------------------------------------------------------------
# 3. Sidebar Filtering Controls
# -----------------------------------------------------------------------------
with st.sidebar:
    st.title("🎛️ Dashboard Filters")
    st.caption("Customize your view by geography, month, and infant sex.")

    # Action buttons
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        st.button("Select All", on_click=select_all_geos_and_months, use_container_width=True, help="Select all states and months")
    with col_btn2:
        st.button("Reset Filters", on_click=reset_filters, use_container_width=True, help="Reset all filters to defaults")

    st.markdown("---")

    # 1. State / Geography Multiselect
    selected_states = st.multiselect(
        "State / Geography",
        options=ALL_STATES,
        default=st.session_state["filter_states"],
        key="filter_states",
        help="Filter data to specific US states or the District of Columbia."
    )

    # 2. Calendar Month Multiselect (Preserving chronological order)
    selected_months = st.multiselect(
        "Calendar Month",
        options=ALL_MONTHS,
        default=st.session_state["filter_months"],
        key="filter_months",
        help="Select calendar months. Displayed in chronological order (January to December)."
    )

    # 3. Infant Sex Selector
    selected_sex = st.radio(
        "Infant Biological Sex",
        options=ALL_SEX_OPTIONS,
        index=ALL_SEX_OPTIONS.index(st.session_state["filter_sex"]),
        key="filter_sex",
        horizontal=True,
        help="Filter by infant sex category or view both combined."
    )

    st.markdown("---")

    # Filter summary indicator
    st.subheader("📋 Active Filter Summary")
    st.write(f"• **Geographies:** {len(selected_states)} of {len(ALL_STATES)}")
    st.write(f"• **Months:** {len(selected_months)} of {len(ALL_MONTHS)}")
    st.write(f"• **Infant Sex:** {selected_sex}")

    st.info(
        "💡 **Analytic Tip:**\n\n"
        "Birth statistics are strictly **counts**. Because population denominators are not included, "
        "do not interpret variations as birth rates.",
        icon="ℹ️"
    )


# -----------------------------------------------------------------------------
# 4. Data Filtering Logic
# -----------------------------------------------------------------------------
df_filtered = df_raw[
    (df_raw["State of Residence"].isin(selected_states)) &
    (df_raw["Month"].isin(selected_months))
]

if selected_sex != "All":
    df_filtered = df_filtered[df_filtered["Sex of Infant"] == selected_sex]


# -----------------------------------------------------------------------------
# 5. Header Component & Important Guidance
# -----------------------------------------------------------------------------
st.title("👶 US Provisional Natality Explorer (2025)")
st.markdown(
    "Explore geographic, seasonal, and demographic distributions in provisional United States birth counts. "
    "Designed for business analytics coursework and exploratory data analysis."
)

# Mandatory analytical notice banner
st.warning(
    "**CDC Source & Analytical Notice:** "
    "Data source: **CDC National Center for Health Statistics (NCHS) Provisional Natality System (2025)**. "
    "Figures in this dashboard represent **provisional recorded birth counts**, *not* birth rates or general fertility rates. "
    "Provisional data are subject to ongoing registry updates and reporting delays.",
    icon="⚠️"
)


# -----------------------------------------------------------------------------
# 6. KPI Metric Summary Cards
# -----------------------------------------------------------------------------
kpis = compute_kpis(df_filtered)

kpi_col1, kpi_col2, kpi_col3, kpi_col4, kpi_col5 = st.columns(5)
with kpi_col1:
    st.metric(
        label="Total Selected Births",
        value=f"{kpis['total_births']:,}",
        help="Sum of recorded birth counts across active filters."
    )
with kpi_col2:
    st.metric(
        label="Geographies Included",
        value=f"{kpis['geo_count']} / {len(ALL_STATES)}",
        help="Number of US states and territories included in current selection."
    )
with kpi_col3:
    st.metric(
        label="Monthly Average",
        value=f"{kpis['avg_monthly_births']:,.0f}",
        help="Average births per selected calendar month."
    )
with kpi_col4:
    top_geo_label = f"{kpis['top_geo_name']}" if kpis["top_geo_name"] != "None" else "None"
    st.metric(
        label="Top Geography",
        value=top_geo_label,
        delta=f"{kpis['top_geo_births']:,} births" if kpis["top_geo_births"] > 0 else None,
        delta_color="off",
        help="Geography with highest aggregate births in current selection."
    )
with kpi_col5:
    top_month_label = f"{kpis['top_month_name']}" if kpis["top_month_name"] != "None" else "None"
    st.metric(
        label="Peak Month",
        value=top_month_label,
        delta=f"{kpis['top_month_births']:,} births" if kpis["top_month_births"] > 0 else None,
        delta_color="off",
        help="Month with highest aggregate births in current selection."
    )

st.markdown("---")


# -----------------------------------------------------------------------------
# 7. Empty State Handling
# -----------------------------------------------------------------------------
if df_filtered.empty:
    st.error(
        "⚠️ **No observations match the current filter selection.**\n\n"
        "Please select at least one State/Geography and one Calendar Month in the sidebar to view metrics and charts."
    )
    st.stop()


# -----------------------------------------------------------------------------
# 8. Dashboard Tabs
# -----------------------------------------------------------------------------
tab_overview, tab_geo, tab_monthly_sex, tab_table, tab_about = st.tabs([
    "📈 Overview",
    "🗺️ Geographic Analysis",
    "📅 Monthly & Sex Analysis",
    "📋 Data Table & Download",
    "📖 About the Data",
])

# Pre-compute aggregations needed across tabs
df_monthly = get_monthly_summary(df_filtered)
df_monthly_sex = get_monthly_by_sex(df_filtered)
df_state = get_state_summary(df_filtered)
df_sex = get_sex_summary(df_filtered)
pivot_heatmap = get_state_month_matrix(df_filtered)


# -----------------------------------------------------------------------------
# TAB 1: OVERVIEW
# -----------------------------------------------------------------------------
with tab_overview:
    st.markdown("### Executive Overview")
    st.write(
        "This view provides a macro summary of provisional 2025 US natality patterns, "
        "highlighting overall volume, monthly temporal progression, and demographic distribution."
    )

    col_trend, col_sex = st.columns([3, 2])
    with col_trend:
        fig_trend = plot_monthly_trend(df_monthly)
        st.plotly_chart(fig_trend, use_container_width=True, key="chart_overview_trend")

    with col_sex:
        fig_sex = plot_sex_comparison(df_sex)
        st.plotly_chart(fig_sex, use_container_width=True, key="chart_overview_sex")

    st.markdown("#### Geographic Concentration Preview")
    st.write("A quick comparison between the largest and smallest selected geographies by recorded births:")
    fig_top_bottom = plot_top_bottom_comparison(df_state, n=5)
    st.plotly_chart(fig_top_bottom, use_container_width=True, key="chart_overview_top_bottom")


# -----------------------------------------------------------------------------
# TAB 2: GEOGRAPHIC ANALYSIS
# -----------------------------------------------------------------------------
with tab_geo:
    st.markdown("### Geographic Distribution of Births")
    st.write(
        "Analyze spatial variations across the United States. "
        "Notice how birth volume naturally concentrates in high-population states like California, Texas, and Florida."
    )

    # US Choropleth Map
    fig_map = plot_choropleth_map(df_state)
    st.plotly_chart(fig_map, use_container_width=True, key="chart_geo_map")

    st.markdown("---")

    num_states = len(df_state)
    col_rank, col_slider = st.columns([3, 1])
    with col_slider:
        st.markdown("#### Display Settings")
        if num_states > 5:
            max_rank_items = st.slider(
                "Number of States in Ranking Chart:",
                min_value=5,
                max_value=num_states,
                value=min(25, num_states),
                step=5 if num_states >= 10 else 1,
                help="Adjust how many states are displayed in the ranking chart below."
            )
        else:
            max_rank_items = num_states
            st.caption(f"Showing all {num_states} selected geography(ies).")

        max_possible_compare = num_states // 2
        if max_possible_compare > 1:
            compare_n = st.slider(
                "Top N vs Bottom N Comparison:",
                min_value=1,
                max_value=min(15, max_possible_compare),
                value=min(5, max_possible_compare),
                step=1,
                help="Number of top and bottom states to compare side-by-side."
            )
        else:
            compare_n = 1
            if num_states > 1:
                st.caption("Comparing Top 1 vs Bottom 1 geography.")

    with col_rank:
        fig_ranking = plot_state_ranking(df_state, max_states=max_rank_items)
        st.plotly_chart(fig_ranking, use_container_width=True, key="chart_geo_ranking")

    st.markdown("---")
    st.markdown("#### Top N vs. Bottom N Disparity")
    if num_states >= 2:
        fig_compare = plot_top_bottom_comparison(df_state, n=compare_n)
        st.plotly_chart(fig_compare, use_container_width=True, key="chart_geo_compare")
    else:
        st.info("💡 **Geographic Comparison Note:** Select at least 2 geographies in the sidebar to compare top and bottom performers.", icon="ℹ️")


# -----------------------------------------------------------------------------
# TAB 3: MONTHLY AND SEX ANALYSIS
# -----------------------------------------------------------------------------
with tab_monthly_sex:
    st.markdown("### Monthly Seasonality and Infant Sex Analysis")
    st.write(
        "Explore seasonal dynamics throughout 2025 alongside infant biological sex patterns. "
        "In demographic studies, birth volumes often exhibit summer/early-autumn peaks, while sex ratios remain remarkably stable."
    )

    # Monthly comparison across infant sex
    fig_month_sex = plot_monthly_by_sex_trend(df_monthly_sex)
    st.plotly_chart(fig_month_sex, use_container_width=True, key="chart_monthly_sex_trend")

    st.markdown("---")

    # Heatmap of States by Month
    st.markdown("#### Cross-Tabulated Seasonality: State × Month Matrix")
    st.caption("Visualizing birth volume density across all selected geographies and months.")
    fig_heatmap = plot_state_month_heatmap(pivot_heatmap)
    st.plotly_chart(fig_heatmap, use_container_width=True, key="chart_monthly_heatmap")

    # Sex ratio commentary for students
    if not df_sex.empty and len(df_sex) == 2:
        female_count = df_sex[df_sex["Sex of Infant"] == "Female"]["Births"].values[0]
        male_count = df_sex[df_sex["Sex of Infant"] == "Male"]["Births"].values[0]
        ratio = (male_count / female_count) if female_count > 0 else 0
        st.info(
            f"📊 **Secondary Sex Ratio Insight:** For the active selection, there are **{male_count:,} male births** "
            f"and **{female_count:,} female births**, representing a male-to-female ratio of **{ratio:.3f}** "
            f"(approximately {ratio * 100:.1f} boys per 100 girls). This is consistent with natural demographic baselines (~1.05).",
            icon="👶"
        )


# -----------------------------------------------------------------------------
# TAB 4: DATA TABLE AND DOWNLOAD
# -----------------------------------------------------------------------------
with tab_table:
    st.markdown("### Granular Data Access & Export")
    st.write(
        "Inspect the filtered subset of CDC records or download the data for independent analysis in Excel, R, or Python."
    )

    view_mode = st.radio(
        "Select Data Table View:",
        options=["Granular Records (State × Month × Sex)", "Aggregated State Summary"],
        horizontal=True
    )

    if view_mode.startswith("Granular"):
        display_df = df_filtered.copy()
        display_df["Births"] = display_df["Births"].map("{:,}".format)
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "State of Residence": st.column_config.TextColumn("State / Geography"),
                "Month": st.column_config.TextColumn("Month"),
                "Month Code": st.column_config.NumberColumn("Month Code", format="%d"),
                "Year Code": st.column_config.NumberColumn("Year", format="%d"),
                "Sex of Infant": st.column_config.TextColumn("Infant Sex"),
                "Births": st.column_config.TextColumn("Birth Count"),
                "State Abbreviation": st.column_config.TextColumn("Postal Code"),
            }
        )
        csv_data = df_filtered.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download Filtered Data as CSV",
            data=csv_data,
            file_name="cdc_provisional_natality_2025_filtered.csv",
            mime="text/csv",
            help="Export currently filtered observations to a standard CSV file."
        )
    else:
        display_state_df = df_state.copy()
        display_state_df["Births"] = display_state_df["Births"].map("{:,}".format)
        display_state_df["Share"] = display_state_df["Share"].map("{:.2f}%".format)
        st.dataframe(
            display_state_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Rank": st.column_config.NumberColumn("Rank", format="%d"),
                "State of Residence": st.column_config.TextColumn("State / Geography"),
                "State Abbreviation": st.column_config.TextColumn("Postal Code"),
                "Births": st.column_config.TextColumn("Total Births"),
                "Share": st.column_config.TextColumn("Share of Selection"),
            }
        )
        csv_data = df_state.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download State Summary as CSV",
            data=csv_data,
            file_name="cdc_provisional_natality_2025_state_summary.csv",
            mime="text/csv",
            help="Export state-level totals to a CSV file."
        )


# -----------------------------------------------------------------------------
# TAB 5: ABOUT THE DATA
# -----------------------------------------------------------------------------
with tab_about:
    st.markdown("### About the Dataset & Business Analytics Guide")
    st.markdown(
        """
        This dashboard is built using provisional natality records published by the 
        **Centers for Disease Control and Prevention (CDC) National Center for Health Statistics (NCHS)**.
        
        #### 1. Data Dictionary
        | Variable | Type | Description |
        | :--- | :--- | :--- |
        | **State of Residence** | Text (`object`) | US State or District of Columbia where the mother resides. |
        | **Month** | Categorical | Calendar month of the birth event (January – December). |
        | **Month Code** | Integer (`int64`) | Numeric calendar sequence (1 = Jan, 12 = Dec). |
        | **Year Code** | Integer (`int64`) | Calendar reporting year (2025). |
        | **Sex of Infant** | Text (`object`) | Biological sex of infant recorded at birth (`Female`, `Male`). |
        | **Births** | Integer (`int64`) | Discrete count of registered live births in that stratum. |

        ---

        #### 2. Critical Business Analytics Principles for Students
        
        ##### A. Birth Counts vs. Birth Rates
        - **Counts:** The numbers displayed throughout this dashboard are raw totals of birth occurrences.
        - **Rates:** A *Crude Birth Rate (CBR)* is calculated as:
          $$\\text{CBR} = \\left( \\frac{\\text{Total Live Births in Period}}{\\text{Total Midyear Population}} \\right) \\times 1,000$$
        - **Key Lesson:** California recorded 393,111 births while Wyoming recorded 5,825. This disparity reflects the fact that California has ~39 million residents while Wyoming has ~580,000. **Do not conclude that California mothers have more children per capita than Wyoming mothers based on counts alone.**
        
        ##### B. The Meaning of "Provisional" Data
        - National vital statistics are collected continuously from 57 jurisdictions (50 states, DC, territories).
        - Provisional data are released early to allow timely public health and demographic monitoring. They undergo final auditing and reconciliation before becoming final vital statistics benchmarks.
        
        ##### C. Ethical & Accurate Data Visualization: Avoiding Truncated Axes
        - Notice that all bar charts and trend charts in this application explicitly anchor their zero baselines. Truncating axes can deceptively exaggerate minor percentage differences, misleading business stakeholders.
        
        ---

        #### 3. Automated Data Quality Audit Verification
        Upon application launch, the dataset undergoes automated programmatic verification:
        - ✅ **1,224 Balanced Observations** (51 geographies × 12 months × 2 sexes)
        - ✅ **51 Distinct Geographies** (50 States + DC)
        - ✅ **12 Calendar Months**
        - ✅ **0 Missing Values & 0 Duplicate Rows**
        - ✅ **3,604,640 Total Recorded Live Births**
        """
    )
