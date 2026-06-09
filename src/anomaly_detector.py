"""
Profile Anomaly Detector.
Scans profiles for data inconsistencies (timeline mismatches, inflated expertises,
unlisted skill assessments, or statistical anomalies) to validate profile legitimacy.
"""


def _check_timeline(c):
    yoe_months = c["yoe"] * 12
    for job in c["career_raw"]:
        dur = job.get("duration_months", 0)
        if dur > yoe_months + 6:
            return True

    total = c["total_career_months"]
    if yoe_months > 0 and total > yoe_months * 1.5 + 12:
        return True

    return False


def _check_fake_expertise(c):
    expert_zero_dur = sum(
        1 for s in c["skills_raw"]
        if s.get("proficiency") == "expert" and s.get("duration_months", 1) == 0
    )
    if expert_zero_dur >= 3:
        return True

    expert_count = sum(
        1 for s in c["skills_raw"] if s.get("proficiency") == "expert"
    )
    if expert_count >= 10:
        return True

    return False


def _check_assessment_mismatch(c):
    skill_names_lower = set(c["skill_names"])
    mismatches = 0
    for skill_name in c["assessment_scores"]:
        if skill_name.lower() not in skill_names_lower:
            mismatches += 1
    if mismatches >= 3:
        return True
    return False


def _check_impossible_signals(c):
    flags = 0
    if c["response_rate"] >= 1.0:
        flags += 1
    if c["interview_completion"] >= 1.0:
        flags += 1
    if c["github_score"] >= 100:
        flags += 1
    if c["profile_completeness"] >= 100:
        flags += 1
    if c["offer_acceptance"] >= 1.0:
        flags += 1
    return flags >= 4


def is_invalid_profile(c):
    score = 0
    if _check_timeline(c):
        score += 2
    if _check_fake_expertise(c):
        score += 2
    if _check_assessment_mismatch(c):
        score += 1
    if _check_impossible_signals(c):
        score += 2
    return score >= 2
