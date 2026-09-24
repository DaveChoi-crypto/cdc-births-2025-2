# CDC 2025 Provisional Natality Explorer

An interactive business analytics dashboard built with **Streamlit**, **Pandas**, and **Plotly** to explore provisional 2025 United States natality records from the CDC National Center for Health Statistics (NCHS).

---

## 🎯 Target Audience & Purpose

This project is designed as an educational application for **undergraduate business analytics students**. It demonstrates:
- How to structure clean, maintainable modular Python analytics code (`src/` architecture).
- The fundamental difference between **counts** (raw volume) and **rates** (population-adjusted metrics).
- How to conduct automated data quality audits during ETL loading.
- Ethical visualization design: avoiding deceptively truncated axes, using accessible palettes, and maintaining chronological ordering.

---

## 📁 Project Structure

```text
CDC 2025-2/
│
├── data/
│   └── Provisional_Natality_2025_CDC.xlsx     # Original CDC Excel dataset (strictly read-only)
│
├── src/
│   ├── __init__.py                             # Package initialization marker
│   ├── data_loader.py                          # Caching (@st.cache_data), audit validation, postal mapping
│   ├── metrics.py                              # KPI aggregations and summary math functions
│   └── charts.py                               # Reusable Plotly chart builders with consistent styling
│
├── app.py                                      # Main Streamlit dashboard application
├── requirements.txt                            # Explicit package dependencies
└── README.md                                   # Student guide and documentation
```

---

## 🚀 Running the Dashboard

### 1. Requirements
Ensure you have Python 3.10+ installed with the following packages:
```bash
pip install -r requirements.txt
```

### 2. Launching Locally
From the project root folder (`CDC 2025-2`), run:
```bash
streamlit run app.py
```
Streamlit will launch a local web server (usually at `http://localhost:8501`).

---

## 📋 Data Dictionary

| Variable Name | Storage Type | Description |
| :--- | :--- | :--- |
| `State of Residence` | Text (`str`) | US State or District of Columbia where the mother resides (51 geographies). |
| `Month` | Categorical | Calendar month of the birth event (January to December). |
| `Month Code` | Integer (`int64`) | Sequential calendar month number (1 = January, 12 = December). |
| `Year Code` | Integer (`int64`) | Calendar reporting year (2025). |
| `Sex of Infant` | Text (`str`) | Biological sex assigned at birth (`Female`, `Male`). |
| `Births` | Integer (`int64`) | Discrete count of registered live births in that stratum. |

---

## 🔍 Data-Quality Audit Baseline
The application automatically validates the following benchmarks on startup:
- **1,224 Observations:** Exactly $51 \text{ geographies} \times 12 \text{ months} \times 2 \text{ infant-sex categories}$.
- **3,604,640 Total Births:** Exactly matches the certified CDC provisional sum.
- **Zero Missing Values:** 100% complete data matrix.
- **Zero Duplicate Rows:** Pure Cartesian product.

---

## 💡 Key Business Analytics Concepts for Students

1. **Counts vs. Rates:**
   - The data reported here are **birth counts**, not fertility rates or crude birth rates.
   - For example, California recorded 393,111 births while Wyoming recorded 5,825. This volume difference is primarily a function of population scale (~39M vs. ~580K residents). Calculating birth rates requires an external population denominator.
2. **Provisional Data Status:**
   - Provisional vital statistics are subject to ongoing registry updates, reporting lags, and post-audits.
3. **Visualization Integrity:**
   - Bar and trend charts must feature zero-anchored baselines (`range=[0, max * 1.15]`) to prevent artificial exaggeration of small relative fluctuations.
