def compute_category_averages(df, categories, file_name):
    """Compute averages + respondent counts for non-session categories."""
    stats = {}
    for cat in ["PROGRAM MANAGEMENT", "TRAINING VENUE", "FOOD/MEALS", "ACCOMMODATION"]:
        cols = categories[cat]
        if cols:
            avg_score = df[cols].mean().mean().round(2)
            respondent_count = df[cols].count().max()
            stats[cat] = {f"{file_name} Avg": avg_score, f"{file_name} N": respondent_count}

    return pd.DataFrame(stats).T if stats else None


def compute_session_averages(df, session_cols, file_name):
    """Group session columns by DAY/LM and compute averages + respondent counts."""
    session_groups = {}
    for col in session_cols:
        col_str = str(col)
        match = re.search(r"Q\d+[_-]?\s*DAY\s*\d+\s*[-–]?\s*LM\s*\d+", col_str, re.IGNORECASE)
        if match:
            session_key = match.group(0).upper().replace(" ", "")
        else:
            match_day_lm = re.search(r"DAY\s*\d+\s*[-–]?\s*LM\s*\d+", col_str, re.IGNORECASE)
            session_key = match_day_lm.group(0).upper().replace(" ", "") if match_day_lm else None

        if session_key:
            session_groups.setdefault(session_key, []).append(col)
        else:
            st.warning(f"Skipped column (no session match): {col}")

    if not session_groups:
        return None

    stats = {}
    for session, cols in session_groups.items():
        avg_score = df[cols].mean().mean().round(2)
        respondent_count = df[cols].count().max()
        stats[session] = {f"{file_name} Avg": avg_score, f"{file_name} N": respondent_count}

    return pd.DataFrame(stats).T


# -------------------------
# Main Display Update
# -------------------------
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

    # ---- Category comparison (side-by-side columns) ----
    if combined_summary:
        final_summary = pd.concat(combined_summary, axis=1)
        st.subheader("📌 Category Averages Comparison")
        st.dataframe(final_summary.style.format("{:.2f}"))

    # ---- Session comparison (side-by-side columns) ----
    if combined_sessions:
        final_sessions = pd.concat(combined_sessions, axis=1)
        st.subheader("📌 Session Averages Comparison")
        st.dataframe(final_sessions.style.format("{:.2f}"))
