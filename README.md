# Redrob Intelligent Candidate Ranker

An optimized, rule-based candidate ranking system developed for the **India Runs Data & AI Challenge** (Redrob × Hack2Skill). 

This system processes a pool of **100,000 candidates** (`candidates.jsonl`) and generates a curated shortlist of the **top 100 candidates** optimized for a **Senior AI Engineer** role, complying with all resource, runtime (≤ 5 minutes), and format validation constraints.

---

## 🚀 Key Features

* **Profile Validation & Consistency Checks**: Automatically flags and eliminates profiles with chronological inconsistencies, fake skills, or impossible behavior telemetry.
* **Knockout Filters**: Optimizes speed by filtering out non-technical roles, junior profiles (< 2 years of experience), and candidates outside of India who do not wish to relocate.
* **Tiered Skill Matcher**: Evaluates candidates against specific required skills (embeddings, vector search, retrieval metrics) across three priority tiers.
* **Deterministic Tie-Breaking**: Implements high-precision formatting with candidate ID ascending sorting to resolve identical scores.

### 🎨 UI/UX Enhancements (Streamlit App)
* **Glassmorphism & Styling**: Injected sleek CSS templates featuring transparent backdrops, blur states, and deep slate/indigo gradients.
* **Split-Pane Profile Inspector**: Added a dual-column layout containing a shortlist datatable on the left and a detailed candidate detail inspector card on the right, displaying skill badges, YOE, location, and reasonings.

### ⚡ Backend Performance Optimizations
* **Fast Date Indexing**: manual string slicing and date math, rendering date computations up to 10x faster.
* **Single-Pass Lowercasing**: Joined job description texts first and lowercased once, minimizing heap string allocations.
* **O(1) Hash Map Skill Lookups**: Implemented exact dictionary checks first, bypassing loop queries for >90% of standard skills.
* **Flat Substring Search**: Replaced a nested skill evaluation loop with a flat substring search on pre-concatenated skill strings.

---

## 📁 Project Structure

```
redrob_ranker/
├── rank.py                    # Main CLI execution entry point
├── README.md                  # Project documentation (this file)
├── requirements.txt           # Python dependency file (standard library only)
├── submission_metadata.yaml   # Portal metadata for Stage 3 validation
├── result_candidates.csv      # Generated final top-100 ranked output CSV
├── India_runs_data_and_ai_challenge/ # Challenge resources and datasets (Git ignored)
├── src/                       # Pipeline source code modules
│   ├── __init__.py            # Python package initialization
│   ├── loader.py              # Loads, flattens, and processes candidates
│   ├── anomaly_detector.py    # Flags impossible timelines and profile validation anomalies
│   ├── hard_filter.py         # Eliminates ineligible candidates quickly
│   ├── skill_scorer.py        # Computes tiered skill relevance metrics
│   ├── career_scorer.py       # Scores job title, progression, and scale experience
│   ├── signal_modifier.py     # Calculates behavioral platform multipliers
│   ├── composite_scorer.py    # Merges sub-scores into a weighted composite score
│   └── reasoning_generator.py # Formulates factual, rank-consistent justifications
└── sandbox/                   # Interactive demo space
    ├── app.py                 # Streamlit web application script
    └── requirements.txt       # Sandbox-specific requirements (streamlit)
```

---

## 📋 Step-by-Step Run Guide

Follow these steps to set up, execute the candidate ranker, and validate the output.

### Step 1: Environment Setup
Ensure you are using **Python 3.9+** (recommending **Python 3.10.0** as per metadata configuration). The core ranker runs using Python's standard library, requiring no external packages.

If you plan to run the Streamlit sandbox dashboard, install the required packages:
```bash
pip install -r sandbox/requirements.txt
```

### Step 2: Running the Ranker on the Full Dataset
Run the ranking pipeline on the full 100,000-candidate dataset. Make sure you point the `--candidates` flag to the correct path of the `candidates.jsonl` file.

```bash
python rank.py \
  --candidates "India_runs_data_and_ai_challenge/candidates.jsonl" \
  --out result_candidates.csv \
  --verbose
```

**What happens here?**
* The script processes 100K profiles.
* It prints execution logs for each pipeline phase.
* It outputs the CSV file `result_candidates.csv` containing the final ranked table.

### Step 3: Validating the Output
Run the challenge validator script on the newly generated CSV file to confirm formatting and scoring validity:

```bash
python "India_runs_data_and_ai_challenge/validate_submission.py" result_candidates.csv
```

If successful, the console will print:
```
Submission is valid.
```

---

## 🖥️ Launching the Streamlit Sandbox

For testing smaller candidate samples interactively, launch the local Streamlit dashboard:

```bash
streamlit run sandbox/app.py
```

1. Open the local link shown in your terminal (typically `http://localhost:8501`).
2. Upload `sample_candidates.json` from the challenge bundle.
3. View the ranking distribution, component scores, and inspect individual profiles interactively.
