import sys
from pathlib import Path

# Add project root to sys.path so modules can be imported directly
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
from src.data_loader import load_data, validate_dataset, STATE_TO_ABBREV, MONTH_ORDER
from src.metrics import (
    compute_kpis,
    get_monthly_summary,
    get_monthly_by_sex,
    get_state_summary,
    get_sex_summary,
    get_state_month_matrix
)
from src.charts import (
    plot_monthly_trend,
    plot_monthly_by_sex_trend,
    plot_sex_comparison,
    plot_state_ranking,
    plot_choropleth_map,
    plot_state_month_heatmap,
    plot_top_bottom_comparison
)

def test_data_loading_and_audit():
    df = load_data()
    assert len(df) == 1224, f"Expected 1224 rows, got {len(df)}"
    assert df["Births"].sum() == 3604640, f"Expected 3604640 births, got {df['Births'].sum()}"
    assert df["State of Residence"].nunique() == 51
    assert df["Month"].nunique() == 12
    assert set(df["Sex of Infant"].unique()) == {"Female", "Male"}
    assert df["State Abbreviation"].isnull().sum() == 0, "Missing state abbreviation mapping"
    assert len(set(STATE_TO_ABBREV.values())) == 51, "Duplicate state abbreviations"

def test_kpis_baseline():
    df = load_data()
    kpis = compute_kpis(df)
    assert kpis["total_births"] == 3604640
    assert kpis["geo_count"] == 51
    assert abs(kpis["avg_monthly_births"] - 300386.67) < 1.0
    assert kpis["top_geo_name"] == "California"
    assert kpis["top_geo_births"] == 393111
    assert kpis["top_month_name"] == "July"
    assert kpis["top_month_births"] == 321538
    assert not kpis["is_empty"]

def test_kpis_filtered_female():
    df = load_data()
    df_female = df[df["Sex of Infant"] == "Female"]
    kpis = compute_kpis(df_female)
    assert kpis["total_births"] == 1762840
    assert kpis["geo_count"] == 51
    assert kpis["top_geo_name"] == "California"

def test_kpis_empty_state():
    df = load_data()
    df_empty = df[df["State of Residence"] == "NonExistentState"]
    kpis = compute_kpis(df_empty)
    assert kpis["total_births"] == 0
    assert kpis["geo_count"] == 0
    assert kpis["is_empty"] is True

def test_all_charts_generation():
    df = load_data()
    m_sum = get_monthly_summary(df)
    m_sex = get_monthly_by_sex(df)
    s_sum = get_state_summary(df)
    sx_sum = get_sex_summary(df)
    mat = get_state_month_matrix(df)

    # Verify figures are created with traces and data
    f1 = plot_monthly_trend(m_sum)
    assert len(f1.data) == 1
    
    f2 = plot_monthly_by_sex_trend(m_sex)
    assert len(f2.data) == 2

    f3 = plot_sex_comparison(sx_sum)
    assert len(f3.data) == 1

    f4 = plot_state_ranking(s_sum, max_states=10)
    assert len(f4.data) == 1

    f5 = plot_choropleth_map(s_sum)
    assert len(f5.data) == 1

    f6 = plot_state_month_heatmap(mat)
    assert len(f6.data) == 1

    f7 = plot_top_bottom_comparison(s_sum, n=5)
    assert len(f7.data) == 1

if __name__ == "__main__":
    test_data_loading_and_audit()
    test_kpis_baseline()
    test_kpis_filtered_female()
    test_kpis_empty_state()
    test_all_charts_generation()
    print("ALL 5 TEST SUITES PASSED PERFECTLY!")
