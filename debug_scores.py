import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8')

from src.loader import load_candidates
from src.anomaly_detector import is_invalid_profile
from src.hard_filter import passes_hard_filter
from src.skill_scorer import score_skills
from src.career_scorer import score_career
from src.signal_modifier import compute_modifier
from src.composite_scorer import compute_score

candidates = load_candidates('sample_candidates.jsonl')

print(f"Loaded: {len(candidates)}")
print()

for c in candidates:
    c['_is_invalid'] = is_invalid_profile(c)

eligible = [c for c in candidates if not c['_is_invalid'] and passes_hard_filter(c)]
print(f"Eligible: {len(eligible)}")
print()

print(f"{'ID':15s} {'Title':30s} {'YOE':5s} {'Skill':6s} {'Career':6s} {'Mod':6s} {'Final':6s}")
print("-" * 80)
for c in eligible:
    sc = compute_score(c)
    print(f"{c['candidate_id']:15s} {c['current_title'].title()[:30]:30s} {c['yoe']:5.1f} "
          f"{c['_skill_score']:.3f}  {c['_career_score']:.3f}  {c['_modifier']:.3f}  {c['_final_score']:.4f}")
