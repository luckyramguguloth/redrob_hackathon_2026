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

# Custom Premium Styling Injection
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');

/* Apply font globally */
html, body, [class*="css"], .stApp {
    font-family: 'Outfit', sans-serif;
}

/* Gradient Hero Banner */
.hero-header {
    background: linear-gradient(135deg, #8b5cf6 0%, #4f46e5 100%);
    padding: 30px;
    border-radius: 12px;
    margin-bottom: 25px;
    box-shadow: 0 4px 20px rgba(79, 70, 229, 0.15);
    border: 1px solid rgba(255, 255, 255, 0.08);
}
.hero-title {
    color: #ffffff !important;
    font-weight: 700;
    font-size: 2.2rem;
    margin: 0;
}
.hero-subtitle {
    color: #e0e7ff !important;
    font-size: 1rem;
    margin-top: 5px;
    opacity: 0.9;
}

/* Custom Metric Cards */
.metric-card {
    background: rgba(255, 255, 255, 0.02);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 10px;
    padding: 20px;
    text-align: center;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
.metric-card:hover {
    transform: translateY(-3px);
    background: rgba(255, 255, 255, 0.04);
    border-color: rgba(99, 102, 241, 0.3);
    box-shadow: 0 8px 25px rgba(99, 102, 241, 0.1);
}
.metric-label {
    font-size: 0.85rem;
    font-weight: 500;
    color: #9ca3af;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}
.metric-val {
    font-size: 2rem;
    font-weight: 700;
    margin-top: 8px;
}

/* Profiles Inspector Card */
.profile-card {
    background: rgba(255, 255, 255, 0.01);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 12px;
    padding: 24px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}
.profile-title {
    font-weight: 600;
    font-size: 1.3rem;
    color: #818cf8;
    margin-bottom: 5px;
}
.profile-meta {
    font-size: 0.88rem;
    color: #9ca3af;
    margin-bottom: 15px;
}
.score-badge {
    background: rgba(99, 102, 241, 0.12);
    border: 1px solid rgba(99, 102, 241, 0.25);
    color: #a5b4fc;
    padding: 2px 8px;
    border-radius: 4px;
    font-weight: 600;
    font-size: 0.85rem;
}

/* Premium Buttons styling */
div.stButton > button {
    background: linear-gradient(135deg, #8b5cf6 0%, #4f46e5 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 6px !important;
    padding: 8px 20px !important;
    font-weight: 600 !important;
    box-shadow: 0 3px 10px rgba(79, 70, 229, 0.3) !important;
    transition: all 0.2s ease !important;
    width: 100%;
}
div.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 5px 15px rgba(99, 102, 241, 0.5) !important;
}

/* Custom Section Header */
.section-header {
    font-size: 1.2rem;
    font-weight: 600;
    border-bottom: 2px solid rgba(99, 102, 241, 0.2);
    padding-bottom: 6px;
    margin-bottom: 15px;
    color: #e2e8f0;
}

.badge-tech {
    background: rgba(99, 102, 241, 0.12);
    color: #a5b4fc;
    border: 1px solid rgba(99, 102, 241, 0.25);
    padding: 4px 10px;
    border-radius: 9999px;
    font-size: 0.82rem;
    font-weight: 500;
    margin-right: 6px;
    margin-bottom: 6px;
    display: inline-block;
    white-space: nowrap;
}
</style>
""", unsafe_allow_html=True)

# Custom Banner Hero Section
st.markdown("""
<div class="hero-header">
    <div class="hero-title">Candidate Evaluation Dashboard</div>
    <div class="hero-subtitle">Optimize candidate alignments with tiered skill scoring, career trajectory validation, and platform telemetry modifiers.</div>
</div>
""", unsafe_allow_html=True)

# File Uploader and configurations
col_config_left, col_config_right = st.columns([3, 1])
with col_config_left:
    uploaded = st.file_uploader("Upload candidate profiles (.json or .jsonl)", type=["json", "jsonl"], label_visibility="collapsed")
with col_config_right:
    top_n = st.selectbox("Top Candidates to show:", options=[10, 20, 50, 100], index=1)

if uploaded:
    raw_bytes = uploaded.read()
    try:
        # Standard JSON array load
        data = json.loads(raw_bytes.decode("utf-8"))
        if isinstance(data, dict):
            data = [data]
    except json.JSONDecodeError:
        # Line-delimited JSONL fallback load
        data = []
        for line in raw_bytes.decode("utf-8").splitlines():
            line = line.strip()
            if line:
                data.append(json.loads(line))

    st.success(f"Dataset successfully loaded. Identified {len(data)} candidate profiles.")

    # Limit UI preview complexity
    if len(data) > 100:
        st.warning("Preview dashboard is optimized for up to 100 profiles. Truncating dataset.")
        data = data[:100]

    with st.spinner("Analyzing candidate capability profiles..."):
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
                # Keep raw candidate record for detailed inspect
                "_raw": c
            })

    anomaly_count = sum(1 for c in candidates if c["_is_invalid"])
    filtered_count = len(candidates) - anomaly_count - len(eligible)

    # Render Custom Dashboard Metric Cards in HTML
    m_col1, m_col2, m_col3 = st.columns(3)
    with m_col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Eligible Profiles</div>
            <div class="metric-val" style="color: #34d399;">{len(eligible)}</div>
        </div>
        """, unsafe_allow_html=True)
    with m_col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Anomalous Profiles</div>
            <div class="metric-val" style="color: #f87171;">{anomaly_count}</div>
        </div>
        """, unsafe_allow_html=True)
    with m_col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Filtered Out</div>
            <div class="metric-val" style="color: #60a5fa;">{filtered_count}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='margin-bottom: 25px;'></div>", unsafe_allow_html=True)

    # Split Pane layout
    col_table, col_inspect = st.columns([3, 2])

    with col_table:
        st.markdown('<div class="section-header">Evaluation Shortlist</div>', unsafe_allow_html=True)
        display_cols = ["rank", "candidate_id", "score", "current_title", "yoe", "location"]
        st.dataframe(
            [{k: r[k] for k in display_cols} for r in rows],
            use_container_width=True,
            height=400
        )

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
            label="💾 Download Ranked Shortlist (CSV)",
            data=csv_buf.getvalue().encode("utf-8"),
            file_name="ranked_candidates.csv",
            mime="text/csv",
        )

    with col_inspect:
        st.markdown('<div class="section-header">Candidate Profile Inspector</div>', unsafe_allow_html=True)
        
        # Selectbox to determine which candidate profile to view
        c_ids = [r["candidate_id"] for r in rows]
        if c_ids:
            selected_id = st.selectbox("Inspect profile details:", options=c_ids)
            # Fetch the selected record
            selected_record = next(r for r in rows if r["candidate_id"] == selected_id)
            c = selected_record["_raw"]

            # Display styled profile card
            st.markdown(f"""
            <div class="profile-card">
                <div class="profile-title">{selected_record['current_title']}</div>
                <div class="profile-meta">
                    ID: <b>{c['candidate_id']}</b> &nbsp;|&nbsp; 
                    Experience: <b>{selected_record['yoe']} Years</b> &nbsp;|&nbsp; 
                    Location: <b>{selected_record['location']}, {c['country']}</b>
                </div>
                <div style="margin-bottom: 15px;">
                    <span class="score-badge">Final Score: {selected_record['score']}</span>
                    <span class="score-badge" style="background: rgba(16, 185, 129, 0.12); color: #34d399; border-color: rgba(16, 185, 129, 0.25);">
                        Skill Alignment: {selected_record['skill_score']:.2f}
                    </span>
                    <span class="score-badge" style="background: rgba(245, 158, 11, 0.12); color: #fbbf24; border-color: rgba(245, 158, 11, 0.25);">
                        Behavioral Mod: {selected_record['modifier']:.2f}
                    </span>
                </div>
                <div style="font-size: 0.95rem; line-height: 1.6; color: #cbd5e1; border-top: 1px solid rgba(255, 255, 255, 0.05); padding-top: 15px;">
                    <b>Factual Reasoning Justification:</b><br/>
                    <i>"{selected_record['reasoning']}"</i>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Detailed skills listing as sub-badges
            st.markdown("<div style='margin-top: 15px; margin-bottom: 8px;'><b>Declared Skills:</b></div>", unsafe_allow_html=True)
            skills_html = "".join([f'<span class="badge-tech">{sname}</span>' for sname in c["skill_names"]])
            st.markdown(f'<div style="display: flex; flex-wrap: wrap; gap: 4px;">{skills_html}</div>', unsafe_allow_html=True)
            
            # Timeline Summary
            st.markdown("<div style='margin-top: 15px;'><b>Notice Period:</b></div>", unsafe_allow_html=True)
            st.write(f"{c['notice_days']} Days notice")
        else:
            st.info("No candidates available for inspection.")
else:
    st.info("Please upload a candidate profile file (.json or .jsonl) to start the evaluation pipeline.")
