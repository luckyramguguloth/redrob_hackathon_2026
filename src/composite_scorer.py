"""
Composite Scoring Module.
Merges individual evaluation dimensions (technical skills, career relevance,
education tiers, and location preference) into a weighted composite score.
Applies the candidate activity modifier to yield the final ranking score.
"""

from src.skill_scorer import score_skills
from src.career_scorer import score_career
from src.signal_modifier import compute_modifier


EDU_TIER_SCORES = {
    "tier_1": 1.0,
    "tier_2": 0.75,
    "tier_3": 0.50,
}


def _edu_score(c):
    return EDU_TIER_SCORES.get(c["edu_tier"], 0.5)


def compute_score(c):
    skill_s = score_skills(c)
    career_s = score_career(c)
    edu_s = _edu_score(c)

    # Base weighted components: 42% technical skills, 33% career relevance, 5% education tier
    base = (
        skill_s * 0.42 +
        career_s * 0.33 +
        edu_s * 0.05
    )

    modifier = compute_modifier(c)

    # Minor geographic preference adjustments
    location = c["location"].lower()
    country = c["country"].lower()
    loc_bonus = 0.0
    if country == "india":
        if any(city in location for city in ("pune", "noida", "delhi", "gurugram", "gurgaon")):
            loc_bonus = 0.03
        elif any(city in location for city in ("mumbai", "bangalore", "bengaluru",
                                                "hyderabad", "chennai")):
            loc_bonus = 0.02
        else:
            loc_bonus = 0.01
    elif c["willing_relocate"]:
        loc_bonus = -0.01

    final = (base + loc_bonus) * modifier

    # Cache sub-scores for candidate reasoning block generation
    c["_skill_score"] = skill_s
    c["_career_score"] = career_s
    c["_modifier"] = modifier
    c["_final_score"] = final

    return round(final, 6)
