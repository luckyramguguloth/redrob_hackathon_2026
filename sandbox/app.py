import streamlit as st
import json
import csv
import io
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")

from src.loader import flatten
from src.anomaly_detector import is_invalid_profile
from src.hard_filter import passes_hard_filter
from src.composite_scorer import compute_score
from src.reasoning_generator import generate_reasoning

st.set_page_config(page_title="Candidate Evaluation Dashboard", layout="wide")

st.title("Candidate Evaluation Dashboard")
st.caption("Upload a JSON/JSONL dataset to calculate candidate scores and generate ranked export tables.")

st.markdown("""
This dashboard evaluates candidate profiles for technical role alignment using structured skill matching,
tenure progression checks, and behavioral platform activity signals.

**Supported Formats:**
- JSON Array: `[{"candidate_id": ...}, ...]`
- JSONL: One JSON object per line
""")

uploaded = st.file_uploader("Upload candidate profiles (.json or .jsonl)", type=["json", "jsonl"])

top_n = st.slider("Select number of top candidates to display:", min_value=5, max_value=100, value=20, step=5)

if uploaded:
    raw_bytes = uploaded.read()
    try:
        # Attempt to parse as standard JSON array
        data = json.loads(raw_bytes.decode("utf-8"))
        if isinstance(data, dict):
            data = [data]
    except json.JSONDecodeError:
        # Fallback to parsing line-delimited JSONL
        data = []
        for line in raw_bytes.decode("utf-8").splitlines():
            line = line.strip()
            if line:
                data.append(json.loads(line))

    st.info(f"Successfully loaded {len(data)} profiles.")

    if len(data) > 100:
        st.warning("Preview dashboard is optimized for up to 100 profiles. Truncating dataset.")
        data = data[:100]

    with st.spinner("Processing evaluations..."):
        candidates = [flatten(c) for c in data]

        for c in candidates:
            c["_is_invalid"] = is_invalid_profile(c)

        eligible = [c for c in candidates if not c["_is_invalid"] and passes_hard_filter(c)]

        for c in eligible:
            compute_score(c)

        # Sort descending by final score, breaking ties using candidate_id ascending
        ranked = sorted(
            eligible,
            key=lambda x: (-x.get("_final_score", 0.0), x["candidate_id"])
        )
        top = ranked[:top_n]

        rows = []
        for i, c in enumerate(top, start=1):
            score = c.get("_final_score", 0.0)
            score_str = f"{score:.6f}"
            rows.append({
                "rank": i,
                "candidate_id": c["candidate_id"],
                "score": score_str,
                "current_title": c["current_title"].title(),
                "yoe": c["yoe"],
                "location": c["location"],
                "country": c["country"],
                "skill_score": round(c.get("_skill_score", 0.0), 3),
                "career_score": round(c.get("_career_score", 0.0), 3),
                "modifier": round(c.get("_modifier", 1.0), 3),
                "reasoning": generate_reasoning(c, i),
            })

    st.success(f"Evaluations complete. Ranked {len(eligible)} eligible candidates. Showing top {len(rows)}.")

    anomaly_count = sum(1 for c in candidates if c["_is_invalid"])
    filtered_count = len(candidates) - anomaly_count - len(eligible)
    col1, col2, col3 = st.columns(3)
    col1.metric("Eligible Profiles", len(eligible))
    col2.metric("Anomalous Profiles Flagged", anomaly_count)
    col3.metric("Filtered Out Profiles", filtered_count)

    st.subheader(f"Top {len(rows)} Candidates Shortlist")
    display_cols = ["rank", "candidate_id", "score", "current_title", "yoe",
                    "location", "skill_score", "career_score", "modifier"]
    st.dataframe(
        [{k: r[k] for k in display_cols} for r in rows],
        use_container_width=True
    )

    st.subheader("Factual Justifications")
    for r in rows:
        with st.expander(f"[{r['rank']}] {r['candidate_id']} — {r['current_title']} (score: {r['score']})"):
            st.write(r["reasoning"])

    # Build CSV export in-memory
    csv_buf = io.StringIO()
    writer = csv.DictWriter(csv_buf, fieldnames=["candidate_id", "rank", "score", "reasoning"])
    writer.writeheader()
    for r in rows:
        writer.writerow({
            "candidate_id": r["candidate_id"],
            "rank": r["rank"],
            "score": r["score"],
            "reasoning": r["reasoning"],
        })

    st.download_button(
        label="Download Ranked Shortlist (CSV)",
        data=csv_buf.getvalue().encode("utf-8"),
        file_name="ranked_candidates.csv",
        mime="text/csv",
    )
