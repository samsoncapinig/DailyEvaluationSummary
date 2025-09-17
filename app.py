import streamlit as st
import pandas as pd
import plotly.express as px
import re

st.title("Daily Evaluation Summary App")

uploaded_files = st.file_uploader(
    "Upload one or more CSV/XLSX files",
    type=["csv", "xlsx"],
    accept_multiple_files=True
)

if uploaded_files:
    combined_summary = []   # For program management, venue, food, accommodation
    combined_sessions = []  # For sessions

    for uploaded_file in uploaded_files:
        # Handle CSV or Excel
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]

        # Define categories
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

        # ---- Non-session categories in one table ----
        category_averages = {}
        for cat in ["PROGRAM MANAGEMENT", "TRAINING VENUE", "FOOD/MEALS", "ACCOMMODATION"]:
            cols = categories[cat]
            if cols:
                category_averages[cat] = df[cols].mean().mean().round(2)

        if category_averages:
            summary_df = pd.DataFrame.from_dict(category_averages, orient='index', columns=['Average Score'])
            summary_df['Average Score'] = summary_df['Average Score'].round(2)
            summary_df['File'] = uploaded_file.name
            combined_summary.append(summary_df)

        # ---- Sessions ----
        session_cols = categories["SESSION"]
        session_groups = {}
        for col in session_cols:
            col_str = str(col)

            # Match Qxx + DAY + LM
            match = re.search(r"Q\d+[_-]?\s*DAY\s*\d+\s*[-–]?\s*LM\s*\d+", col_str, re.IGNORECASE)

            if match:
                session_key = match.group(0).upper().replace(" ", "")
                session_groups.setdefault(session_key, []).append(col)
            else:
                # fallback: only DAY + LM
                match_day_lm = re.search(r"DAY\s*\d+\s*[-–]?\s*LM\s*\d+", col_str, re.IGNORECASE)
                if match_day_lm:
                    session_key = match_day_lm.group(0).upper().replace(" ", "")
                    session_groups.setdefault(session_key, []).append(col)
                else:
                    st.write("⚠️ Skipped column (no session match):", col)

        session_averages = {}
        for session, cols in session_groups.items():
            session_averages[session] = df[cols].mean().mean().round(2)

        if session_averages:
            session_df = pd.DataFrame.from_dict(session_averages, orient='index', columns=['Average Score'])
            session_df['Average Score'] = session_df['Average Score'].round(2)
            session_df['File'] = uploaded_file.name
            combined_sessions.append(session_df)

    # ---- Display category table ----
    if combined_summary:
        final_summary = pd.concat(combined_summary)
        final_summary['Average Score'] = final_summary['Average Score'].round(2)
        st.subheader("Category Averages Across Files (Program Management, Venue, Food, Accommodation)")
        st.dataframe(final_summary)

        fig1 = px.bar(
            final_summary,
            x=final_summary.index,
            y="Average Score",
            color="File",
            title="Average Scores by Category Across Files"
        )
        st.plotly_chart(fig1)

    # ---- Display sessions table ----
    if combined_sessions:
        final_sessions = pd.concat(combined_sessions)
        final_sessions['Average Score'] = final_sessions['Average Score'].round(2)
        st.subheader("Session-wise Averages Across Files")
        st.dataframe(final_sessions)

        fig2 = px.bar(
            final_sessions,
            x=final_sessions.index,
            y="Average Score",
            color="File",
            title="Average Scores by Session Across Files"
        )
        st.plotly_chart(fig2)

    # ---- Display combined table (Table 3) ----
    if combined_summary and combined_sessions:
        final_combined = pd.concat([final_summary, final_sessions])
        final_combined['Average Score'] = final_combined['Average Score'].round(2)
        st.subheader("Combined Averages (Categories + Sessions)")
        st.dataframe(final_combined)

        fig3 = px.bar(
            final_combined,
            x=final_combined.index,
            y="Average Score",
            color="File",
            title="Overall Average Scores (Categories + Sessions)"
        )
        st.plotly_chart(fig3)
