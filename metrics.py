"""Metrics calculation and aggregation module for CDC 2025 Natality data.

This module encapsulates all mathematical summaries and aggregations:
- KPI calculations for top-level cards
- Monthly and geographic aggregations
- Infant-sex breakdowns
- Empty-state protection

For Business Analytics students:
Separating business logic (aggregations, sums, averages) from UI presentation ensures
that metrics are unit-testable and consistent across different views of the application.
"""

from typing import Any, Dict, List, Optional
import pandas as pd


def compute_kpis(df: pd.DataFrame) -> Dict[str, Any]:
    """Calculate the five core KPI metrics for the active filter selection.
    
    Returns a dictionary with formatted and raw values. If df is empty, returns
    sensible default fallback values to avoid application crashes.
    """
    if df.empty:
        return {
            "total_births": 0,
            "geo_count": 0,
            "avg_monthly_births": 0.0,
            "top_geo_name": "None",
            "top_geo_births": 0,
            "top_month_name": "None",
            "top_month_births": 0,
            "is_empty": True
        }
        
    total_births = int(df["Births"].sum())
    geo_count = int(df["State of Residence"].nunique())
    month_count = int(df["Month"].nunique())
    
    # Average births per selected month
    avg_monthly_births = (total_births / month_count) if month_count > 0 else 0.0
    
    # Geography with highest selected birth count
    geo_totals = df.groupby("State of Residence")["Births"].sum()
    if not geo_totals.empty:
        top_geo_name = str(geo_totals.idxmax())
        top_geo_births = int(geo_totals.max())
    else:
        top_geo_name = "N/A"
        top_geo_births = 0
        
    # Month with highest selected birth count
    month_totals = df.groupby("Month", observed=False)["Births"].sum()
    # Filter out months with 0 births if they were unselected
    active_months = month_totals[month_totals > 0]
    if not active_months.empty:
        top_month_name = str(active_months.idxmax())
        top_month_births = int(active_months.max())
    else:
        top_month_name = "N/A"
        top_month_births = 0
        
    return {
        "total_births": total_births,
        "geo_count": geo_count,
        "avg_monthly_births": avg_monthly_births,
        "top_geo_name": top_geo_name,
        "top_geo_births": top_geo_births,
        "top_month_name": top_month_name,
        "top_month_births": top_month_births,
        "is_empty": False
    }


def get_monthly_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate total births by calendar month, preserving chronological order."""
    if df.empty:
        return pd.DataFrame(columns=["Month", "Month Code", "Births"])
        
    summary = (
        df.groupby(["Month", "Month Code"], observed=False)["Births"]
        .sum()
        .reset_index()
    )
    # Filter to only months that have records in the current selection
    summary = summary[summary["Births"] > 0].sort_values("Month Code")
    return summary


def get_monthly_by_sex(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate monthly births split by infant sex."""
    if df.empty:
        return pd.DataFrame(columns=["Month", "Month Code", "Sex of Infant", "Births"])
        
    summary = (
        df.groupby(["Month", "Month Code", "Sex of Infant"], observed=False)["Births"]
        .sum()
        .reset_index()
    )
    summary = summary[summary["Births"] > 0].sort_values("Month Code")
    return summary


def get_state_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate total births by state, sorted from highest to lowest."""
    if df.empty:
        return pd.DataFrame(columns=["State of Residence", "State Abbreviation", "Births", "Share"])
        
    summary = (
        df.groupby(["State of Residence", "State Abbreviation"])["Births"]
        .sum()
        .reset_index()
    )
    total = summary["Births"].sum()
    summary["Share"] = (summary["Births"] / total * 100) if total > 0 else 0.0
    summary = summary.sort_values("Births", ascending=False).reset_index(drop=True)
    summary["Rank"] = range(1, len(summary) + 1)
    return summary


def get_sex_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate births by biological infant sex with percentage shares."""
    if df.empty:
        return pd.DataFrame(columns=["Sex of Infant", "Births", "Share"])
        
    summary = df.groupby("Sex of Infant")["Births"].sum().reset_index()
    total = summary["Births"].sum()
    summary["Share"] = (summary["Births"] / total * 100) if total > 0 else 0.0
    return summary


def get_state_month_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """Create a pivot table of State (rows) by Month (columns) for heatmap analysis."""
    if df.empty:
        return pd.DataFrame()
        
    pivot = df.pivot_table(
        index="State of Residence",
        columns="Month",
        values="Births",
        aggfunc="sum",
        observed=False
    ).fillna(0)
    
    # Sort states by total births descending for better visual coherence in heatmaps
    row_totals = pivot.sum(axis=1)
    pivot = pivot.loc[row_totals.sort_values(ascending=False).index]
    
    # Filter out columns (months) with 0 across all states
    active_cols = [col for col in pivot.columns if pivot[col].sum() > 0]
    return pivot[active_cols]
