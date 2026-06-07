import streamlit as st
import anthropic
import os
import csv
import plotly.express as px
import pandas as pd
from collections import defaultdict
from dotenv import load_dotenv

load_dotenv()

# ---- Page config (must be first st call) ----
st.set_page_config(
    page_title="User Insights Analyzer",
    page_icon="📊",
    layout="wide"
)

# ---- Custom CSS ----
st.markdown("""
    <style>
        /* Wider padding, full width */
        .block-container {
            padding-left: 3rem;
            padding-right: 3rem;
            max-width: 100%;
        }

        /* Larger metric values */
        [data-testid="metric-container"] [data-testid="stMetricValue"] {
            font-size: 2.4rem;
            font-weight: 700;
        }

        /* Larger metric labels */
        [data-testid="metric-container"] [data-testid="stMetricLabel"] {
            font-size: 1rem;
        }

        /* Larger metric delta */
        [data-testid="metric-container"] [data-testid="stMetricDelta"] {
            font-size: 1rem;
        }

        /* Bigger subheaders */
        h2, h3 {
            font-size: 1.6rem !important;
        }

        /* Bigger tab labels */
        [data-testid="stTab"] p {
            font-size: 1.05rem;
        }
    </style>
""", unsafe_allow_html=True)


def get_client():
    api_key = os.getenv("ANTHROPIC_API_KEY")
    return anthropic.Anthropic(api_key=api_key)


# ---- Helper functions ----

def classify_reviews(reviews_text):
    reviews = [r.strip() for r in reviews_text.split("\n\n") if r.strip() != ""]
    category_counts = defaultdict(int)
    signals_by_category = defaultdict(list)
    rows = []
    progress = st.progress(0, text="Classifying reviews...")

    for i, review in enumerate(reviews):
        message = get_client().messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            messages=[{
                "role": "user",
                "content": f"""You are a market intelligence analyst.

Identify ALL categories present in this customer feedback:
- Compeller: drives decisive action to buy or adopt
- Accelerator: amplifies momentum and usage once adopted
- Differentiator: sets the product apart from alternatives
- Stabilizer: table stakes that enable basic consideration
- Inhibitor: blocks or slows adoption

Return exactly this format:
Categories: [list all that apply, comma separated]
Signals:
- [category]: [one sentence explaining this specific signal]
Primary Theme: [2-3 word label]

Feedback:
{review}"""
            }]
        )

        response = message.content[0].text
        lines = response.strip().split("\n")
        categories = ""
        signals = []
        primary_theme = ""

        for line in lines:
            if line.startswith("Categories:"):
                categories = line.replace("Categories:", "").strip()
            elif line.startswith("- "):
                signals.append(line.strip())
            elif line.startswith("Primary Theme:"):
                primary_theme = line.replace("Primary Theme:", "").strip()

        for cat in categories.split(","):
            cat = cat.strip()
            if cat:
                category_counts[cat] += 1

        for signal in signals:
            if ":" in signal:
                cat = signal.split(":")[0].replace("-", "").strip()
                explanation = signal.split(":", 1)[1].strip()
                signals_by_category[cat].append(explanation)

        rows.append({
            "Review": review[:150],
            "Categories": categories,
            "Primary Theme": primary_theme
        })

        progress.progress(
            (i + 1) / len(reviews),
            text=f"Classifying review {i+1} of {len(reviews)}..."
        )

    progress.empty()
    return category_counts, signals_by_category, rows


def get_inhibitor_themes(signals_by_category):
    import json
    inhibitor_signals = "\n".join(signals_by_category.get("Inhibitor", []))
    if not inhibitor_signals:
        return []

    message = get_client().messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[{
            "role": "user",
            "content": f"""You are a market intelligence analyst.

Group these inhibitor signals into 3-5 distinct themes.
Return ONLY a JSON array, no other text, no markdown.

Format:
[
  {{
    "name": "Theme name",
    "count": 5,
    "pattern": "One sentence describing the pattern",
    "signal": "Most representative signal"
  }}
]

Inhibitor signals:
{inhibitor_signals}"""
        }]
    )

    try:
        text = message.content[0].text
        start = text.find("[")
        end = text.rfind("]") + 1
        return json.loads(text[start:end])
    except:
        return []


def get_strategic_summary(signals_by_category, company_name):
    import json
    all_signals = ""
    for category, signals in signals_by_category.items():
        all_signals += f"\n{category}:\n"
        for signal in signals:
            all_signals += f"- {signal}\n"

    message = get_client().messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        messages=[{
            "role": "user",
            "content": f"""You are a senior brand strategist.

Write a strategic summary for {company_name}.
Return ONLY a JSON object, no other text, no markdown.

Format:
{{
  "problem": "One paragraph describing the core strategic problem",
  "recommendations": [
    {{"title": "Recommendation title", "body": "2-3 sentence explanation"}},
    {{"title": "Recommendation title", "body": "2-3 sentence explanation"}},
    {{"title": "Recommendation title", "body": "2-3 sentence explanation"}}
  ],
  "ceo_insight": "The single most important insight"
}}

Customer signals:
{all_signals}"""
        }]
    )

    try:
        text = message.content[0].text
        start = text.find("{")
        end = text.rfind("}") + 1
        return json.loads(text[start:end])
    except:
        return None


def show_results(category_counts, signals_by_category, rows, company_name):

    # ---- Section 1: Distribution ----
    st.subheader("📊 Category Distribution")

    total = sum(category_counts.values())
    df = pd.DataFrame([
        {
            "Category": cat,
            "Signals": count,
            "Percentage": f"{round(count/total*100)}%"
        }
        for cat, count in sorted(
            category_counts.items(), key=lambda x: x[1], reverse=True)
    ])

    color_map = {
        "Accelerator": "#2D9CDB",
        "Compeller": "#27AE60",
        "Differentiator": "#9B59B6",
        "Inhibitor": "#E74C3C",
        "Stabilizer": "#F39C12"
    }

    colors_icon = {
        "Accelerator": "🔵",
        "Compeller": "🟢",
        "Differentiator": "🟣",
        "Inhibitor": "🔴",
        "Stabilizer": "🟡"
    }

    # Metric row
    cols = st.columns(len(df))
    for i, row in df.iterrows():
        with cols[i]:
            icon = colors_icon.get(row["Category"], "⚪")
            st.metric(
                label=f"{icon} {row['Category']}",
                value=row["Signals"],
                delta=row["Percentage"]
            )

    st.markdown("<br>", unsafe_allow_html=True)

    # Charts — wider and taller
    col1, col2 = st.columns([3, 2])

    with col1:
        fig = px.bar(
            df, x="Signals", y="Category",
            orientation="h",
            color="Category",
            color_discrete_map=color_map,
            text="Signals",
            title="Signal Count by Category"
        )
        fig.update_layout(
            showlegend=False,
            height=420,
            plot_bgcolor="white",
            paper_bgcolor="white",
            margin=dict(l=0, r=20, t=50, b=20),
            title_font_size=18,
            font=dict(size=14),
            xaxis=dict(title_font_size=14, tickfont_size=13),
            yaxis=dict(title_font_size=14, tickfont_size=13),
        )
        fig.update_xaxes(showgrid=True, gridcolor="#F0F0F0")
        fig.update_traces(textfont_size=14)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig2 = px.pie(
            df, values="Signals", names="Category",
            color="Category",
            color_discrete_map=color_map,
            hole=0.5,
            title="Signal Distribution"
        )
        fig2.update_layout(
            height=420,
            paper_bgcolor="white",
            margin=dict(l=0, r=0, t=50, b=20),
            title_font_size=18,
            font=dict(size=14),
            legend=dict(font=dict(size=13)),
        )
        fig2.update_traces(textfont_size=13)
        st.plotly_chart(fig2, use_container_width=True)

    st.divider()

    # ---- Section 2: Inhibitor Themes ----
    st.subheader("🚧 Inhibitor Theme Analysis")

    with st.spinner("Analyzing inhibitor themes..."):
        themes = get_inhibitor_themes(signals_by_category)

    if themes:
        # Two columns for theme cards when there are multiple themes
        if len(themes) > 2:
            theme_cols = st.columns(2)
            for idx, theme in enumerate(themes):
                with theme_cols[idx % 2]:
                    with st.container(border=True):
                        col_a, col_b = st.columns([4, 1])
                        with col_a:
                            st.markdown(f"**{theme['name']}**")
                        with col_b:
                            st.markdown(f"🔴 **{theme['count']} signals**")
                        st.markdown(theme['pattern'])
                        st.caption(f"💬 \"{theme['signal']}\"")
        else:
            for theme in themes:
                with st.container(border=True):
                    col_a, col_b = st.columns([4, 1])
                    with col_a:
                        st.markdown(f"**{theme['name']}**")
                    with col_b:
                        st.markdown(f"🔴 **{theme['count']} signals**")
                    st.markdown(theme['pattern'])
                    st.caption(f"💬 \"{theme['signal']}\"")
    else:
        st.info("No inhibitor themes found.")

    st.divider()

    # ---- Section 3: Strategic Summary ----
    st.subheader("💡 Strategic Summary & Recommendations")

    with st.spinner("Generating strategic summary..."):
        summary = get_strategic_summary(signals_by_category, company_name)

    if summary:
        with st.container(border=True):
            st.markdown("**🎯 Core Strategic Problem**")
            st.markdown(summary['problem'])

        st.markdown("#### Recommendations")

        # Three columns for recommendations
        rec_cols = st.columns(len(summary['recommendations']))
        for i, rec in enumerate(summary['recommendations']):
            with rec_cols[i]:
                with st.container(border=True):
                    st.markdown(f"**Priority {i+1} — {rec['title']}**")
                    st.markdown(rec['body'])

        st.info(f"⚡ **CEO Insight:** {summary['ceo_insight']}")

    st.divider()

    # ---- Section 4: Raw data ----
    with st.expander("📋 View Classified Reviews"):
        st.dataframe(pd.DataFrame(rows), use_container_width=True)


# ---- App layout ----

st.title("📊 User Insights Analyzer")
st.caption(
    "5-Dynamics Framework — Compellers · Accelerators · "
    "Differentiators · Stabilizers · Inhibitors"
)
st.divider()

tab1, tab2 = st.tabs(["📌 Glean Analysis", "🔍 Analyze Your Own"])

# Tab 1 — Glean
with tab1:
    st.markdown("**Glean — Enterprise AI Search**")
    st.caption("Analysis based on 20 customer reviews from G2")
    st.divider()

    if os.path.exists("results.csv"):
        category_counts = defaultdict(int)
        signals_by_category = defaultdict(list)
        rows = []

        with open("results.csv", "r") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                cats = row["Categories"].replace(
                    "[", "").replace("]", "").split(",")
                for cat in cats:
                    cat = cat.strip()
                    if cat:
                        category_counts[cat] += 1

                signals = row["Signals"].split("|")
                for signal in signals:
                    signal = signal.strip()
                    if ":" in signal:
                        cat = signal.split(
                            ":")[0].replace("-", "").strip()
                        explanation = signal.split(":", 1)[1].strip()
                        signals_by_category[cat].append(explanation)

                rows.append({
                    "Review": row["Review"],
                    "Categories": row["Categories"],
                    "Primary Theme": row["Primary Theme"]
                })

        show_results(category_counts, signals_by_category, rows, "Glean")

    else:
        st.warning("results.csv not found. Please run analyzer.py first.")

# Tab 2 — Analyze your own
with tab2:
    st.markdown("**Analyze Any Company**")
    st.caption(
        "Paste customer reviews — separate each review with a blank line")
    st.divider()

    company_name = st.text_input(
        "Company name",
        placeholder="e.g. Notion, Linear, Glean"
    )
    reviews_input = st.text_area(
        "Paste reviews here",
        height=250,
        placeholder="Review 1:\nPaste first review...\n\nReview 2:\nPaste second review..."
    )

    if st.button("🔍 Run Analysis", type="primary"):
        if not reviews_input.strip():
            st.error("Please paste some reviews first.")
        elif not company_name.strip():
            st.error("Please enter a company name.")
        else:
            category_counts, signals_by_category, rows = classify_reviews(
                reviews_input)
            show_results(
                category_counts, signals_by_category, rows, company_name)
