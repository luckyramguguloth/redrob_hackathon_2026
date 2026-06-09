"""
Skill Scorer.
Evaluates candidate skills against core technical requirements,
taking into account self-reported proficiency, years of usage,
skill endorsements, and standardized assessment results.
"""

# Core required skills (high relevance weight)
TIER_A = {
    "embedding": 1.0,
    "embeddings": 1.0,
    "sentence-transformer": 1.0,
    "sentence transformer": 1.0,
    "bge": 0.9,
    " e5 ": 0.9,
    "bi-encoder": 0.9,
    "semantic search": 1.0,
    "faiss": 1.0,
    "pinecone": 1.0,
    "weaviate": 1.0,
    "qdrant": 1.0,
    "milvus": 1.0,
    "opensearch": 1.0,
    "elasticsearch": 1.0,
    "vector database": 1.0,
    "vector search": 1.0,
    "vector store": 0.9,
    "hybrid search": 1.0,
    "hybrid retrieval": 1.0,
    "dense retrieval": 0.9,
    "ndcg": 1.0,
    "mrr": 0.9,
    "mean average precision": 0.9,
    "ranking evaluation": 0.9,
    "retrieval evaluation": 0.9,
    "information retrieval": 1.0,
    "learning to rank": 1.0,
    "ltr": 0.9,
    "offline evaluation": 0.9,
    "a/b test": 0.9,
    "ab test": 0.9,
}

# Preferred optional skills (medium relevance weight)
TIER_B = {
    "lora": 0.7,
    "qlora": 0.7,
    "peft": 0.7,
    "fine-tuning": 0.7,
    "fine tuning": 0.7,
    "instruction tuning": 0.6,
    "rag": 0.8,
    "retrieval-augmented": 0.8,
    "retrieval augmented": 0.8,
    "bm25": 0.8,
    "sparse retrieval": 0.7,
    "lambdamart": 0.7,
    "ranknet": 0.7,
    "xgboost": 0.5,
    "lightgbm": 0.5,
    "model serving": 0.6,
    "inference optim": 0.6,
    "onnx": 0.5,
    "triton": 0.6,
    "mlops": 0.6,
    "ml ops": 0.6,
    "recommendation": 0.7,
    "recsys": 0.7,
}

# General technical skills (low relevance weight)
TIER_C = {
    "pytorch": 0.4,
    "tensorflow": 0.3,
    "hugging face": 0.4,
    "transformers": 0.4,
    "bert": 0.4,
    "gpt": 0.3,
    "llm": 0.5,
    "nlp": 0.5,
    "text classification": 0.3,
    "scikit-learn": 0.3,
    "scikit learn": 0.3,
    "python": 0.4,
    "machine learning": 0.4,
    "deep learning": 0.4,
    "neural network": 0.3,
    "data science": 0.3,
    "spark": 0.2,
    "kafka": 0.2,
    "airflow": 0.2,
}

# Excluded or out-of-scope domain tags
NEGATIVE_DOMINANT = {
    "computer vision", "image classification", "object detection",
    "speech recognition", "asr", "tts", "text-to-speech",
    "robotics", "ros", "autonomous driving",
    "photoshop", "figma", "illustrator", "marketing",
    "excel", "powerpoint", "accounting", "seo", "crm",
}


def _proficiency_multiplier(proficiency):
    mapping = {
        "expert": 1.0,
        "advanced": 0.85,
        "intermediate": 0.65,
        "beginner": 0.35,
    }
    return mapping.get(proficiency, 0.5)


def _endorsement_boost(endorsements):
    if endorsements >= 20:
        return 1.15
    if endorsements >= 10:
        return 1.08
    if endorsements >= 5:
        return 1.03
    return 1.0


def _assessment_boost(skill_name, assessment_scores):
    for k, v in assessment_scores.items():
        if k.lower() in skill_name or skill_name in k.lower():
            if v >= 80:
                return 1.2
            if v >= 60:
                return 1.1
            if v < 40:
                return 0.85
    return 1.0


def score_skills(c):
    skill_names = c["skill_names"]
    skills_raw = c["skills_raw"]
    job_text = c["job_text"]
    summary = c["summary"]
    assessment = c["assessment_scores"]

    full_text = job_text + " " + summary

    tier_a_score = 0.0
    tier_b_score = 0.0
    tier_c_score = 0.0
    negative_count = 0

    # Calculate score based on explicit skills listed in profile
    for s in skills_raw:
        sname = s["name"].lower()
        prof_mult = _proficiency_multiplier(s.get("proficiency", "intermediate"))
        end_boost = _endorsement_boost(s.get("endorsements", 0))
        dur_months = s.get("duration_months", 0)
        dur_mult = min(1.0, 0.5 + dur_months / 24.0)  # Ramps up over 2 years (24 months)
        assess_boost = _assessment_boost(sname, assessment)

        effective = prof_mult * end_boost * dur_mult * assess_boost

        matched_tier = None
        matched_val = 0.0
        for kw, val in TIER_A.items():
            if kw in sname:
                matched_tier = "A"
                matched_val = max(matched_val, val)
        if not matched_tier:
            for kw, val in TIER_B.items():
                if kw in sname:
                    matched_tier = "B"
                    matched_val = max(matched_val, val)
        if not matched_tier:
            for kw, val in TIER_C.items():
                if kw in sname:
                    matched_tier = "C"
                    matched_val = max(matched_val, val)

        if matched_tier == "A":
            tier_a_score += matched_val * effective
        elif matched_tier == "B":
            tier_b_score += matched_val * effective
        elif matched_tier == "C":
            tier_c_score += matched_val * effective

        for neg in NEGATIVE_DOMINANT:
            if neg in sname:
                negative_count += 1

    # Scan career descriptions for core technical keywords not explicitly added to skills list
    text_a_bonus = 0.0
    for kw, val in TIER_A.items():
        if kw in full_text:
            text_a_bonus += val * 0.4  # Slightly lower weight for textual keywords vs declared skills

    # Combine technical scores
    raw = (
        min(tier_a_score, 4.0) * 0.50 +
        min(tier_b_score, 2.5) * 0.25 +
        min(tier_c_score, 2.0) * 0.10 +
        min(text_a_bonus, 2.0) * 0.15
    )

    # Apply penalty for out-of-scope domain keywords
    neg_penalty = min(0.4, negative_count * 0.08)
    raw = max(0.0, raw - neg_penalty)

    # Normalize final technical score between 0.0 and 1.0
    return min(1.0, raw / 3.5)
