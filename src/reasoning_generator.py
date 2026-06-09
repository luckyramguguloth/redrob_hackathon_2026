"""
Reasoning generator.
Writes specific, factual, rank-consistent 1-2 sentence justifications.
Uses only real data from the candidate profile - no placeholder values.
"""


def _top_relevant_skills(c, n=3):
    from src.skill_scorer import TIER_A, TIER_B

    relevant = []
    for s in c["skills_raw"]:
        sname = s["name"].lower()
        for kw in list(TIER_A.keys()) + list(TIER_B.keys()):
            if kw in sname:
                relevant.append(s["name"])
                break
    return relevant[:n]


def _most_recent_title_company(c):
    if not c["career_raw"]:
        return c["current_title"].title(), c["current_company"]
    # sort by start_date descending
    sorted_jobs = sorted(
        c["career_raw"],
        key=lambda j: j.get("start_date", "0000"),
        reverse=True
    )
    j = sorted_jobs[0]
    return j.get("title", c["current_title"]).title(), j.get("company", c["current_company"])


def _yoe_str(yoe):
    return f"{yoe:.0f}" if yoe == int(yoe) else f"{yoe:.1f}"


def _signal_phrase(c):
    parts = []
    if c["days_since_active"] <= 7:
        parts.append("active this week")
    elif c["days_since_active"] <= 30:
        parts.append(f"active {c['days_since_active']}d ago")
    elif c["days_since_active"] > 90:
        parts.append(f"last active {c['days_since_active']}d ago")

    rr = c["response_rate"]
    if rr >= 0.7:
        parts.append(f"high response rate ({rr:.0%})")
    elif rr < 0.2:
        parts.append(f"low response rate ({rr:.0%})")

    if c["notice_days"] <= 15:
        parts.append("immediate availability")
    elif c["notice_days"] > 90:
        parts.append(f"{c['notice_days']}d notice")

    if c["github_score"] >= 60:
        parts.append(f"GitHub score {c['github_score']:.0f}")

    return "; ".join(parts[:2]) if parts else ""


def _location_phrase(c):
    loc = c["location"]
    country = c["country"]
    if country == "India":
        return loc
    elif c["willing_relocate"]:
        return f"{loc} (open to relocate)"
    return f"{loc}, {country}"


def _concern_phrase(c, rank):
    concerns = []
    if c["days_since_active"] > 90:
        concerns.append(f"last active {c['days_since_active']}d ago")
    if c["response_rate"] < 0.2:
        concerns.append(f"low recruiter response rate ({c['response_rate']:.0%})")
    if c["notice_days"] > 90:
        concerns.append(f"long notice period ({c['notice_days']} days)")
    if c["country"].lower() != "india" and not c["willing_relocate"]:
        concerns.append(f"based in {c['country']}, relocation unknown")
    if c["_skill_score"] < 0.25:
        concerns.append("limited core skill match")
    if c["_career_score"] < 0.35:
        concerns.append("career history only partially relevant")
    return "; ".join(concerns[:2]) if concerns else ""


def generate_reasoning(c, rank):
    yoe = _yoe_str(c["yoe"])
    title = c["current_title"].title()
    company = c["current_company"]
    location = _location_phrase(c)
    rel_skills = _top_relevant_skills(c)
    signal = _signal_phrase(c)
    concern = _concern_phrase(c, rank)

    skill_str = ", ".join(rel_skills) if rel_skills else "general ML background"

    if rank <= 10:
        # strong: lead with specific strengths
        sentence1 = (
            f"{title} with {yoe} yrs experience at {company}; "
            f"relevant skills: {skill_str}; {location}."
        )
        if signal:
            sentence2 = f"Platform signals are strong: {signal}."
        elif concern:
            sentence2 = f"Minor concern: {concern}."
        else:
            sentence2 = (
                f"Career history shows applied ML/AI work and production system experience."
            )
        return f"{sentence1} {sentence2}"

    elif rank <= 30:
        # good fit with a noted gap or signal
        sentence1 = (
            f"{yoe} yrs total; currently {title} at {company} ({location}); "
            f"relevant skills include {skill_str}."
        )
        if concern:
            sentence2 = f"Concern: {concern}."
        elif signal:
            sentence2 = f"Behavioral signals: {signal}."
        else:
            sentence2 = "Solid fit for the core engineering requirements."
        return f"{sentence1} {sentence2}"

    elif rank <= 60:
        # partial match
        if rel_skills:
            sentence1 = (
                f"{title} ({yoe} yrs, {location}); has {skill_str} "
                f"but career history is only partially aligned to search/ranking systems."
            )
        else:
            sentence1 = (
                f"{title} with {yoe} yrs at {company}; skill overlap is limited "
                f"for the AI engineering profile in the JD."
            )
        if concern:
            sentence2 = f"Additional concern: {concern}."
        else:
            sentence2 = "Included as a marginal match given partial technical overlap."
        return f"{sentence1} {sentence2}"

    else:
        # marginal / borderline
        sentence1 = (
            f"Borderline candidate: {title} ({yoe} yrs, {location}); "
            f"limited direct match to the Senior AI Engineer requirements."
        )
        if concern:
            sentence2 = f"Key gaps: {concern}."
        else:
            sentence2 = (
                f"Ranked here due to adjacent technical background; "
                f"skill and career scores are both below the main cohort."
            )
        return f"{sentence1} {sentence2}"
