"""Visualization module for the CDC 2025 Provisional Natality dashboard.

Constructs reusable Plotly charts adhering to business analytics standards:
1. No truncated zero-baselines on bar charts.
2. Thousands separators across axes and interactive hover tooltips.
3. Clean, accessible color palettes.
4. Explanatory annotations and titles suitable for undergraduate students.
"""

from typing import Optional
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Professional, accessible palette: Navy, Teal, Coral, Amber, Slate
PALETTE = {
    "primary": "#1E3A8A",      # Deep Navy
    "secondary": "#0D9488",    # Teal
    "accent_female": "#D946EF", # Magenta / Rose
    "accent_male": "#2563EB",   # Royal Blue
    "neutral_dark": "#1E293B",  # Slate 800
    "neutral_light": "#F8FAFC", # Slate 50
    "grid": "#E2E8F0",          # Slate 200
    "top_geo": "#047857",       # Green 700
    "bottom_geo": "#B91C1C",    # Red 700
}

# Standard template settings for all figures
LAYOUT_DEFAULTS = dict(
    font=dict(family="Inter, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif", size=12, color=PALETTE["neutral_dark"]),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=40, r=40, t=60, b=40),
    hoverlabel=dict(bgcolor="white", font_size=12, font_family="Inter, sans-serif"),
)


def plot_monthly_trend(df_monthly: pd.DataFrame) -> go.Figure:
    """Line chart showing the monthly progression of births.
    
    Y-axis starts at zero to ensure students see the proportional variation
    rather than an artificially exaggerated oscillation.
    """
    if df_monthly.empty:
        fig = go.Figure()
        fig.add_annotation(text="No monthly data available for current selection.", showarrow=False)
        return fig

    max_val = df_monthly["Births"].max()

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df_monthly["Month"],
            y=df_monthly["Births"],
            mode="lines+markers",
            line=dict(color=PALETTE["primary"], width=3),
            marker=dict(size=8, color=PALETTE["secondary"], line=dict(color="white", width=2)),
            hovertemplate="<b>%{x}</b><br>Total Births: %{y:,.0f}<extra></extra>",
            name="Monthly Births"
        )
    )

    fig.update_layout(
        **LAYOUT_DEFAULTS,
        title="<b>Monthly Birth Trend (2025 Provisional)</b><br><span style='font-size:11px;color:#64748B;'>Chronological monthly total births (Y-axis zero-anchored for proportional accuracy)</span>",
        xaxis=dict(title="Month", showgrid=True, gridcolor=PALETTE["grid"]),
        yaxis=dict(
            title="Recorded Births (Count)",
            showgrid=True,
            gridcolor=PALETTE["grid"],
            tickformat=",",
            range=[0, max_val * 1.15] if max_val > 0 else [0, 100]
        ),
        showlegend=False
    )
    return fig


def plot_monthly_by_sex_trend(df_monthly_sex: pd.DataFrame) -> go.Figure:
    """Multi-line trend chart comparing Male vs. Female trajectories over the year."""
    if df_monthly_sex.empty:
        fig = go.Figure()
        fig.add_annotation(text="No data available for current selection.", showarrow=False)
        return fig

    max_val = df_monthly_sex["Births"].max()

    fig = go.Figure()
    for sex, color in [("Male", PALETTE["accent_male"]), ("Female", PALETTE["accent_female"])]:
        sub = df_monthly_sex[df_monthly_sex["Sex of Infant"] == sex]
        if not sub.empty:
            fig.add_trace(
                go.Scatter(
                    x=sub["Month"],
                    y=sub["Births"],
                    mode="lines+markers",
                    name=f"{sex} Infants",
                    line=dict(color=color, width=2.5),
                    marker=dict(size=7),
                    hovertemplate=f"<b>%{{x}} - {sex}</b><br>Births: %{{y:,.0f}}<extra></extra>"
                )
            )

    fig.update_layout(
        **LAYOUT_DEFAULTS,
        title="<b>Monthly Birth Trend by Infant Sex</b><br><span style='font-size:11px;color:#64748B;'>Parallel tracking of female and male births across calendar months</span>",
        xaxis=dict(title="Month", showgrid=True, gridcolor=PALETTE["grid"]),
        yaxis=dict(
            title="Recorded Births (Count)",
            showgrid=True,
            gridcolor=PALETTE["grid"],
            tickformat=",",
            range=[0, max_val * 1.15] if max_val > 0 else [0, 100]
        ),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig


def plot_sex_comparison(df_sex: pd.DataFrame) -> go.Figure:
    """Bar chart comparing female vs. male birth counts with percentage shares."""
    if df_sex.empty:
        fig = go.Figure()
        fig.add_annotation(text="No sex data available for current selection.", showarrow=False)
        return fig

    colors = [PALETTE["accent_female"] if s == "Female" else PALETTE["accent_male"] for s in df_sex["Sex of Infant"]]
    max_val = df_sex["Births"].max()

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=df_sex["Sex of Infant"],
            y=df_sex["Births"],
            text=[f"{b:,.0f}<br>({s:.1f}%)" for b, s in zip(df_sex["Births"], df_sex["Share"])],
            textposition="outside",
            marker_color=colors,
            hovertemplate="<b>%{x}</b><br>Births: %{y:,.0f}<extra></extra>"
        )
    )

    fig.update_layout(
        **LAYOUT_DEFAULTS,
        title="<b>Infant Sex Breakdown</b><br><span style='font-size:11px;color:#64748B;'>Total counts and relative proportions for selected filters</span>",
        xaxis=dict(title="Infant Sex"),
        yaxis=dict(
            title="Recorded Births (Count)",
            showgrid=True,
            gridcolor=PALETTE["grid"],
            tickformat=",",
            range=[0, max_val * 1.22] if max_val > 0 else [0, 100]
        ),
        showlegend=False
    )
    return fig


def plot_state_ranking(df_state: pd.DataFrame, max_states: int = 51) -> go.Figure:
    """Horizontal bar chart ranking states by birth counts from highest to lowest."""
    if df_state.empty:
        fig = go.Figure()
        fig.add_annotation(text="No geographic data available for current selection.", showarrow=False)
        return fig

    sub = df_state.head(max_states).sort_values("Births", ascending=True)
    max_val = sub["Births"].max()

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            y=sub["State of Residence"],
            x=sub["Births"],
            orientation="h",
            marker_color=PALETTE["primary"],
            text=[f"{b:,.0f}" for b in sub["Births"]],
            textposition="outside",
            hovertemplate="<b>%{y}</b><br>Rank: %{customdata[0]}<br>Births: %{x:,.0f} (%{customdata[1]:.2f}% of selection)<extra></extra>",
            customdata=list(zip(sub["Rank"], sub["Share"]))
        )
    )

    chart_height = max(400, len(sub) * 22)

    fig.update_layout(
        **LAYOUT_DEFAULTS,
        height=chart_height,
        title=f"<b>Geographic Distribution Ranking (Top {len(sub)} Geographies)</b><br><span style='font-size:11px;color:#64748B;'>Sorted descending by total recorded birth count</span>",
        xaxis=dict(
            title="Recorded Births (Count)",
            showgrid=True,
            gridcolor=PALETTE["grid"],
            tickformat=",",
            range=[0, max_val * 1.18] if max_val > 0 else [0, 100]
        ),
        yaxis=dict(title="", tickfont=dict(size=11)),
        showlegend=False
    )
    return fig


def plot_choropleth_map(df_state: pd.DataFrame) -> go.Figure:
    """Interactive US Choropleth map of birth counts by state."""
    if df_state.empty:
        fig = go.Figure()
        fig.add_annotation(text="No geographic data available for current selection.", showarrow=False)
        return fig

    fig = go.Figure(
        data=go.Choropleth(
            locations=df_state["State Abbreviation"],
            z=df_state["Births"],
            locationmode="USA-states",
            colorscale="Tealgrn",
            colorbar=dict(
                title=dict(text="Births", font=dict(size=11)),
                tickformat=",",
                len=0.75,
                thickness=16
            ),
            text=df_state["State of Residence"],
            customdata=list(zip(df_state["Rank"], df_state["Share"])),
            hovertemplate="<b>%{text} (%{location})</b><br>National Rank: #%{customdata[0]}<br>Birth Count: %{z:,.0f}<br>Share of Selection: %{customdata[1]:.2f}%<extra></extra>"
        )
    )

    fig.update_layout(
        **LAYOUT_DEFAULTS,
        title="<b>US Geographic Birth Volume Map (2025 Provisional)</b><br><span style='font-size:11px;color:#64748B;'>Choropleth visualization by state of maternal residence</span>",
        geo=dict(
            scope="usa",
            projection=dict(type="albers usa"),
            showlakes=True,
            lakecolor="rgb(240, 248, 255)",
            bgcolor="rgba(0,0,0,0)"
        ),
        height=520
    )
    return fig


def plot_state_month_heatmap(matrix: pd.DataFrame) -> go.Figure:
    """State by Month interactive heatmap matrix."""
    if matrix.empty:
        fig = go.Figure()
        fig.add_annotation(text="No heatmap data available for current selection.", showarrow=False)
        return fig

    chart_height = max(400, len(matrix) * 18)

    fig = go.Figure(
        data=go.Heatmap(
            z=matrix.values,
            x=matrix.columns.tolist(),
            y=matrix.index.tolist(),
            colorscale="Viridis",
            colorbar=dict(title=dict(text="Births", font=dict(size=11)), tickformat=","),
            hovertemplate="<b>%{y}</b> - %{x}<br>Recorded Births: %{z:,.0f}<extra></extra>"
        )
    )

    fig.update_layout(
        **LAYOUT_DEFAULTS,
        height=chart_height,
        title="<b>State-by-Month Natality Matrix</b><br><span style='font-size:11px;color:#64748B;'>Cross-tabulated birth density across calendar months</span>",
        xaxis=dict(title="Month", tickangle=-45),
        yaxis=dict(title="", tickfont=dict(size=10), autorange="reversed"),
    )
    return fig


def plot_top_bottom_comparison(df_state: pd.DataFrame, n: int = 5) -> go.Figure:
    """Side-by-side or paired comparison of Top N vs. Bottom N states."""
    if df_state.empty:
        fig = go.Figure()
        fig.add_annotation(text="No geographic data available for current selection.", showarrow=False)
        return fig

    total_avail = len(df_state)
    n = min(n, total_avail // 2) if total_avail > 1 else 1

    top_n = df_state.head(n).copy()
    top_n["Group"] = f"Top {n} Geographies"
    
    bottom_n = df_state.tail(n).copy()
    bottom_n["Group"] = f"Bottom {n} Geographies"

    combined = pd.concat([top_n, bottom_n]).sort_values("Births", ascending=True)

    colors = [PALETTE["bottom_geo"] if g.startswith("Bottom") else PALETTE["top_geo"] for g in combined["Group"]]
    max_val = combined["Births"].max()

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            y=combined["State of Residence"],
            x=combined["Births"],
            orientation="h",
            marker_color=colors,
            text=[f"{b:,.0f} (#{r})" for b, r in zip(combined["Births"], combined["Rank"])],
            textposition="outside",
            hovertemplate="<b>%{y}</b><br>Group: %{customdata[0]}<br>National Rank: #%{customdata[1]}<br>Births: %{x:,.0f}<extra></extra>",
            customdata=list(zip(combined["Group"], combined["Rank"]))
        )
    )

    fig.update_layout(
        **LAYOUT_DEFAULTS,
        height=max(380, len(combined) * 28),
        title=f"<b>Comparative Disparity: Top {n} vs. Bottom {n} Geographies</b><br><span style='font-size:11px;color:#64748B;'>Highlighting geographic volume concentration in US natality</span>",
        xaxis=dict(
            title="Recorded Births (Count)",
            showgrid=True,
            gridcolor=PALETTE["grid"],
            tickformat=",",
            range=[0, max_val * 1.25] if max_val > 0 else [0, 100]
        ),
        yaxis=dict(title=""),
        showlegend=False
    )
    return fig
