"""
Candidate Activity & Engagement Modifier.
Analyzes user platform signals (availability, response rate, notice period,
location fit) and calculates a composite score modifier in the range [0.25, 1.15].
"""


def _availability_score(c):
    score = 1.0

    # Availability flag
    if not c["open_to_work"]:
        score *= 0.60

    # Activity recency
    days = c["days_since_active"]
    if days <= 7:
        score *= 1.05
    elif days <= 30:
        score *= 1.0
    elif days <= 60:
        score *= 0.90
    elif days <= 90:
        score *= 0.75
    elif days <= 180:
        score *= 0.55
    else:
        score *= 0.30

    return score


def _responsiveness_score(c):
    score = 1.0

    # Recruiter response rate
    rr = c["response_rate"]
    if rr >= 0.7:
        score *= 1.10
    elif rr >= 0.5:
        score *= 1.0
    elif rr >= 0.3:
        score *= 0.90
    elif rr >= 0.15:
        score *= 0.75
    else:
        score *= 0.55

    # Average reply speed
    hours = c["avg_response_hours"]
    if hours <= 6:
        score *= 1.05
    elif hours <= 24:
        score *= 1.0
    elif hours <= 72:
        score *= 0.95
    elif hours <= 168:
        score *= 0.85
    else:
        score *= 0.75

    return score


def _reliability_score(c):
    score = 1.0

    # Interview attendance rate
    ic = c["interview_completion"]
    if ic >= 0.8:
        score *= 1.05
    elif ic >= 0.6:
        score *= 1.0
    elif ic >= 0.4:
        score *= 0.90
    else:
        score *= 0.75

    # Offer acceptance rate
    oa = c["offer_acceptance"]
    if oa == -1:  # Baseline default (no prior offers recorded)
        pass
    elif oa >= 0.7:
        score *= 1.05
    elif oa >= 0.4:
        score *= 1.0
    elif oa >= 0.1:
        score *= 0.92
    else:
        score *= 0.82

    return score


def _engagement_score(c):
    score = 1.0

    # Developer activity score
    gh = c["github_score"]
    if gh >= 70:
        score *= 1.10
    elif gh >= 40:
        score *= 1.04
    elif gh == -1:
        score *= 0.95  # Baseline default (no github profile)
    elif gh < 10:
        score *= 0.97

    # Verification checks
    if c["verified_email"] and c["verified_phone"]:
        score *= 1.02
    elif not c["verified_email"]:
        score *= 0.96

    # Profile completion
    if c["profile_completeness"] >= 85:
        score *= 1.02
    elif c["profile_completeness"] < 50:
        score *= 0.95

    return score


def _notice_score(c):
    nd = c["notice_days"]
    if nd <= 15:
        return 1.10
    if nd <= 30:
        return 1.0
    if nd <= 60:
        return 0.92
    if nd <= 90:
        return 0.85
    return 0.75


def _location_score(c):
    country = c["country"].lower()
    location = c["location"].lower()

    if country == "india":
        if any(city in location for city in ("pune", "noida", "delhi", "gurugram", "gurgaon")):
            return 1.10
        if any(city in location for city in ("mumbai", "bangalore", "bengaluru",
                                               "hyderabad", "chennai", "kolkata")):
            return 1.05
        return 1.0
    elif c["willing_relocate"]:
        return 0.90
    else:
        return 0.70


def compute_modifier(c):
    avail = _availability_score(c)
    resp = _responsiveness_score(c)
    rel = _reliability_score(c)
    eng = _engagement_score(c)
    notice = _notice_score(c)
    loc = _location_score(c)

    modifier = avail * resp * rel * eng * notice * loc

    # Clamping range bounds
    return max(0.25, min(1.15, modifier))
