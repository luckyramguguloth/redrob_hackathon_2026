"""
Quick test script to run the ranker on the sample JSON (50 candidates).
This verifies everything works before pointing at the full 100K file.
"""

import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Convert sample_candidates.json to a temp .jsonl for the ranker
base = r'..\[PUB] India_runs_data_and_ai_challenge\[PUB] India_runs_data_and_ai_challenge\India_runs_data_and_ai_challenge'

sample_json = os.path.join(base, 'sample_candidates.json')
temp_jsonl = 'sample_candidates.jsonl'

print(f"Converting {sample_json} to {temp_jsonl}...")
with open(sample_json, 'r', encoding='utf-8') as f:
    data = json.load(f)

with open(temp_jsonl, 'w', encoding='utf-8') as f:
    for c in data:
        f.write(json.dumps(c) + '\n')

print(f"Written {len(data)} candidates to {temp_jsonl}")
print("Now run:")
print(f"  python rank.py --candidates {temp_jsonl} --out sample_output.csv --top 50 --verbose")
