import streamlit as st
import pandas as pd
import plotly.express as px
import re

st.set_page_config(page_title="Daily Evaluation Summary App", layout="wide")
st.title("📊 Daily Evaluation Summary App")

# -------------------------
# Helpers
# -------------------------
@st.cache_data
def load_file(uploaded_file):
    """Read CSV or Excel file and clean unnamed columns."""
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)
    return df.loc[:, ~df.columns.str.contains('^Unnamed')]


def categorize_columns(df):
    """Categorize columns into predefined categories."""
    categories = {
        "PROGRAM MANAGEMENT": [],
        "TRAINING VENUE": [],
        "FOOD/MEALS": [],
        "ACCOMMODATION": [],
        "SESSION": []
    }
    for col in df.columns:
        col_str = str(col).upper()
        if "PROGRAM MANAGEMENT" in col_str:
            categories["PROGRAM MANAGEMENT"].append(col)
        elif "TRAINING VENUE" in col_str:
            categories["TRAINING VENUE"].append(col)
        elif "FOOD/MEALS" in col_str:
            categories["FOOD/MEALS"].append(col)
        elif "ACCOMMODATION" in col_str:
            categories["ACCOMMODATION"].append(col)
        elif any(key in col_str for key in [
            "PROGRAM OBJECTIVES", "LR MATERIALS",
            "CONTENT RELEVANCE", "RP/SUBJECT MATTER EXPERT KNOWLEDGE"
        ]):
            categories["SESSION"].append(col)
    return categories


def compute_category_averages(df, categories, file_name):
    """Compute averages for non-session categories."""
    category_averages = {}
    for cat in ["PROGRAM MANAGEMENT", "TRAINING VENUE", "FOOD/MEALS", "ACCOMMODATION"]:
        cols = categories[cat]
        if cols:
            category_averages[cat] = df[cols].mean().mean().round(2)

    if category_averages:
        summary_df = pd.DataFrame.from_dict(category_averages, orient="index", columns=["Average Score"])
        summary_df["File"] = file_name
        return summary_df
    return None


def compute_session_averages(df, session_cols, file_name):
    """Group session columns by DAY/LM and compute averages."""
    session_groups = {}
    for col in session_cols:
        col_str = str(col)

        # Match Qxx + DAY + LM
        match = re.search(r"Q\d+[_-]?\s*DAY\s*\d+\s*[-–]?\s*LM\s*\d+", col_str, re.IGNORECASE)
        if match:
            session_key = match.group(0).upper().replace(" ", "")
        else:
            # fallback: only DAY + LM
            match_day_lm = re.search(r"DAY\s*\d+\s*[-–]?\s*LM\s*\d+", col_str, re.IGNORECASE)
            session_key = match_day_lm.group(0).upper().replace(" ", "") if match_day_lm else None

        if session_key:
            session_groups.setdefault(session_key, []).append(col)
        else:
            st.warning(f"Skipped column (no session match): {col}")

    if not session_groups:
        return None

    session_averages = {s: df[cols].mean().mean().round(2) for s, cols in session_groups.items()}
    session_df = pd.DataFrame.from_dict(session_averages, orient="index", columns=["Average Score"])
    session_df["File"] = file_name
    return session_df


def plot_bar_chart(df, title):
    """Reusable bar chart generator."""
    return px.bar(
        df.reset_index(),
        x="index",
        y="Average Score",
        color="File",
        title=title,
        text="Average Score"
    )


# -------------------------
# Main App
# -------------------------
uploaded_files = st.file_uploader(
    "📂 Upload one or more CSV/XLSX files",
    type=["csv", "xlsx"],
    accept_multiple_files=True
)

if uploaded_files:
    combined_summary, combined_sessions = [], []

    for uploaded_file in uploaded_files:
        df = load_file(uploaded_file)
        categories = categorize_columns(df)

        # Categories
        summary_df = compute_category_averages(df, categories, uploaded_file.name)
        if summary_df is not None:
            combined_summary.append(summary_df)

        # Sessions
        session_df = compute_session_averages(df, categories["SESSION"], uploaded_file.name)
        if session_df is not None:
            combined_sessions.append(session_df)

    # ---- Display category table ----
    if combined_summary:
        final_summary = pd.concat(combined_summary)
        st.subheader("📌 Category Averages (Program Management, Venue, Food, Accommodation)")
        st.dataframe(final_summary.style.format({"Average Score": "{:.2f}"}))
        st.plotly_chart(plot_bar_chart(final_summary, "Average Scores by Category Across Files"))

    # ---- Display sessions table ----
    if combined_sessions:
        final_sessions = pd.concat(combined_sessions)
        st.subheader("📌 Session-wise Averages")
        st.dataframe(final_sessions.style.format({"Average Score": "{:.2f}"}))
        st.plotly_chart(plot_bar_chart(final_sessions, "Average Scores by Session Across Files"))

    # ---- Combined table ----
    if combined_summary and combined_sessions:
        final_combined = pd.concat([final_summary, final_sessions])
        st.subheader("📌 Combined Averages (Categories + Sessions)")
        st.dataframe(final_combined.style.format({"Average Score": "{:.2f}"}))
        st.plotly_chart(plot_bar_chart(final_combined, "Overall Average Scores (Categories + Sessions)"))
