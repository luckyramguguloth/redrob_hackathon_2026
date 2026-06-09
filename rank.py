"""
Candidate Ranking CLI.
Processes raw candidate profiles, runs validation and knockout filters,
calculates final capability scores, and exports the top ranked candidates to CSV.
"""

import argparse
import csv
import sys
import time

from src.loader import load_candidates
from src.anomaly_detector import is_invalid_profile
from src.hard_filter import passes_hard_filter
from src.composite_scorer import compute_score
from src.reasoning_generator import generate_reasoning


def parse_args():
    p = argparse.ArgumentParser(description="Rank candidates for the Senior AI Engineer role")
    p.add_argument("--candidates", required=True, help="Path to candidates JSONL dataset")
    p.add_argument("--out", required=True, help="Output destination CSV path")
    p.add_argument("--top", type=int, default=100, help="Number of ranked candidates to output (default: 100)")
    p.add_argument("--verbose", action="store_true", help="Print pipeline progress logs")
    return p.parse_args()


def log(msg, verbose):
    if verbose:
        print(msg, flush=True)


def main():
    args = parse_args()
    t0 = time.time()

    log(f"Loading candidate profiles from {args.candidates}...", args.verbose)
    candidates = load_candidates(args.candidates)
    log(f"  Loaded {len(candidates):,} candidate profiles in {time.time()-t0:.1f}s", args.verbose)

    t1 = time.time()
    log("Running profile validation checks...", args.verbose)
    anomalies = 0
    for c in candidates:
        if is_invalid_profile(c):
            c["_is_invalid"] = True
            anomalies += 1
        else:
            c["_is_invalid"] = False
    log(f"  Flagged {anomalies} anomalous profiles in {time.time()-t1:.1f}s", args.verbose)

    t2 = time.time()
    log("Applying knockout filters...", args.verbose)
    eligible = [c for c in candidates if not c["_is_invalid"] and passes_hard_filter(c)]
    log(f"  {len(eligible):,} candidates passed filters in {time.time()-t2:.1f}s", args.verbose)

    t3 = time.time()
    log("Calculating capability scores...", args.verbose)
    for c in eligible:
        compute_score(c)
    log(f"  Scored {len(eligible):,} candidates in {time.time()-t3:.1f}s", args.verbose)

    t4 = time.time()
    log("Sorting and selecting top candidates...", args.verbose)
    # Sort primarily by final score descending, breaking ties using candidate_id ascending
    ranked = sorted(
        eligible,
        key=lambda x: (-x.get("_final_score", 0.0), x["candidate_id"])
    )
    top = ranked[:args.top]
    log(f"  Done in {time.time()-t4:.1f}s", args.verbose)

    if len(top) < args.top:
        print(f"WARNING: only {len(top)} eligible candidates available (requested {args.top})", file=sys.stderr)

    log(f"Generating justifications for top {len(top)} candidates...", args.verbose)
    rows = []
    for rank_idx, c in enumerate(top, start=1):
        reasoning = generate_reasoning(c, rank_idx)
        score = c.get("_final_score", 0.0)
        # Format scores to 6 decimal places to prevent sorting collisions
        score_str = f"{score:.6f}"
        rows.append({
            "candidate_id": c["candidate_id"],
            "rank": rank_idx,
            "score": score_str,
            "reasoning": reasoning,
        })

    log(f"Writing output CSV to {args.out}...", args.verbose)
    with open(args.out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["candidate_id", "rank", "score", "reasoning"])
        writer.writeheader()
        writer.writerows(rows)

    elapsed = time.time() - t0
    log(f"\nCompleted. {len(rows)} candidates written to {args.out}", args.verbose)
    log(f"Total runtime: {elapsed:.1f}s", args.verbose)

    if args.verbose and top:
        print("\n--- Preview of Top Ranks ---")
        for r in rows[:5]:
            print(f"  [{r['rank']:3d}] {r['candidate_id']}  score={r['score']}  {r['reasoning'][:80]}...")


if __name__ == "__main__":
    main()
