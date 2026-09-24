"""Data loader and validation module for the CDC 2025 Provisional Natality dataset.

This module handles:
1. File path resolution that works across local machines and cloud platforms.
2. In-memory caching via Streamlit's @st.cache_data decorator.
3. Automated data-quality checks to ensure analytical integrity before user interaction.
4. Standardization of calendar month ordering and US postal code mapping.
"""

from pathlib import Path
from typing import Dict, List, Tuple
import pandas as pd
import streamlit as st

# Ordered list of calendar months to enforce chronological sorting rather than alphabetical
MONTH_ORDER: List[str] = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]

# Standard US 2-letter postal code mapping for all 50 states + District of Columbia
STATE_TO_ABBREV: Dict[str, str] = {
    "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR", "California": "CA",
    "Colorado": "CO", "Connecticut": "CT", "Delaware": "DE", "District of Columbia": "DC",
    "Florida": "FL", "Georgia": "GA", "Hawaii": "HI", "Idaho": "ID", "Illinois": "IL",
    "Indiana": "IN", "Iowa": "IA", "Kansas": "KS", "Kentucky": "KY", "Louisiana": "LA",
    "Maine": "ME", "Maryland": "MD", "Massachusetts": "MA", "Michigan": "MI", "Minnesota": "MN",
    "Mississippi": "MS", "Missouri": "MO", "Montana": "MT", "Nebraska": "NE", "Nevada": "NV",
    "New Hampshire": "NH", "New Jersey": "NJ", "New Mexico": "NM", "New York": "NY",
    "North Carolina": "NC", "North Dakota": "ND", "Ohio": "OH", "Oklahoma": "OK", "Oregon": "OR",
    "Pennsylvania": "PA", "Rhode Island": "RI", "South Carolina": "SC", "South Dakota": "SD",
    "Tennessee": "TN", "Texas": "TX", "Utah": "UT", "Vermont": "VT", "Virginia": "VA",
    "Washington": "WA", "West Virginia": "WV", "Wisconsin": "WI", "Wyoming": "WY"
}


def get_default_data_path() -> Path:
    """Resolve the path to the Excel workbook across local and cloud environments."""
    this_file = Path(__file__).resolve()
    # Check potential candidate root folders
    candidate_dirs = [
        this_file.parent,
        this_file.parents[1] if len(this_file.parents) > 1 else this_file.parent,
        Path.cwd()
    ]
    for c_dir in candidate_dirs:
        p_sub = c_dir / "data" / "Provisional_Natality_2025_CDC.xlsx"
        if p_sub.exists():
            return p_sub
        p_root = c_dir / "Provisional_Natality_2025_CDC.xlsx"
        if p_root.exists():
            return p_root
            
    # Default fallback
    return (this_file.parents[1] if len(this_file.parents) > 1 else this_file.parent) / "data" / "Provisional_Natality_2025_CDC.xlsx"


def validate_dataset(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """Perform automated data quality checks against expected baseline values.
    
    For Business Analytics students:
    Automated data audits are essential in real-world pipelines to catch data corruption,
    partial ingestion, or schema drift before numbers are displayed to executives.
    """
    issues = []
    
    if len(df) != 1224:
        issues.append(f"Row count mismatch: expected 1,224 observations, found {len(df):,}.")
    
    if df["State of Residence"].nunique() != 51:
        issues.append(f"Geography count mismatch: expected 51 geographies, found {df['State of Residence'].nunique()}.")
        
    if df["Month"].nunique() != 12:
        issues.append(f"Month count mismatch: expected 12 months, found {df['Month'].nunique()}.")
        
    if set(df["Sex of Infant"].unique()) != {"Female", "Male"}:
        issues.append(f"Sex category mismatch: expected {{'Female', 'Male'}}, found {set(df['Sex of Infant'].unique())}.")
        
    missing_count = df.isnull().sum().sum()
    if missing_count > 0:
        issues.append(f"Found {missing_count} missing values across columns.")
        
    duplicate_count = df.duplicated().sum()
    if duplicate_count > 0:
        issues.append(f"Found {duplicate_count} duplicate rows.")
        
    total_births = df["Births"].sum()
    if total_births != 3604640:
        issues.append(f"Total births mismatch: expected 3,604,640, found {total_births:,}.")
        
    is_valid = len(issues) == 0
    return is_valid, issues


@st.cache_data(show_spinner="Loading and validating CDC provisional natality data...")
def load_data(file_path: Path = None) -> pd.DataFrame:
    """Load, validate, and preprocess the CDC Provisional Natality Excel workbook.
    
    The @st.cache_data decorator ensures the workbook is read and parsed only once,
    avoiding costly re-reads on every filter interaction.
    """
    if file_path is None:
        file_path = get_default_data_path()
        
    if not file_path.exists():
        raise FileNotFoundError(
            f"The dataset file could not be found at {file_path}. "
            "Please ensure the Excel file is present in the data/ directory."
        )
        
    # Read the first worksheet (openpyxl engine)
    df = pd.read_excel(file_path, sheet_name=0)
    
    # Strip any potential accidental whitespace in text columns
    text_cols = ["State of Residence", "Month", "Sex of Infant"]
    for col in text_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
            
    # Perform audit checks
    is_valid, issues = validate_dataset(df)
    if not is_valid:
        error_msg = "Data validation failed:\n" + "\n".join(f"- {issue}" for issue in issues)
        raise ValueError(error_msg)
        
    # Enrich with postal abbreviation for map visualizations
    df["State Abbreviation"] = df["State of Residence"].map(STATE_TO_ABBREV)
    
    # Order Month as a categorical column with explicit chronological calendar ordering
    df["Month"] = pd.Categorical(df["Month"], categories=MONTH_ORDER, ordered=True)
    
    return df
