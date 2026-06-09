"""
Career Trajectory Scorer.
Evaluates the relevance of candidate job titles, quality of previous companies
(startup/product vs. consulting/services), production deployment experience,
tenure stability, and experience level fit.
"""

TARGET_TITLES = {
    "ml engineer": 1.0,
    "machine learning engineer": 1.0,
    "ai engineer": 1.0,
    "applied scientist": 1.0,
    "research engineer": 0.9,
    "applied ml": 0.95,
    "search engineer": 1.0,
    "ranking engineer": 1.0,
    "nlp engineer": 0.95,
    "data scientist": 0.8,
    "senior engineer": 0.75,
    "staff engineer": 0.85,
    "principal engineer": 0.85,
    "software engineer": 0.7,
    "platform engineer": 0.7,
    "backend engineer": 0.65,
    "ml platform": 0.9,
    "mlops": 0.8,
    "recommendation": 0.9,
    "retrieval": 0.9,
}

WEAK_TITLES = {
    "data engineer": 0.5,
    "analytics engineer": 0.45,
    "data analyst": 0.35,
    "bi engineer": 0.3,
    "devops": 0.4,
    "frontend": 0.2,
    "full stack": 0.4,
}

BAD_TITLES = {
    "marketing", "hr", "human resources", "accountant", "finance",
    "operations manager", "supply chain", "legal", "civil", "mechanical",
    "customer support", "sales", "product manager", "graphic"
}

# Service-oriented/IT consulting industries
IT_SERVICES_INDUSTRIES = {"it services", "consulting"}

# Product-oriented engineering industries
PRODUCT_INDUSTRIES = {
    "ai/ml", "fintech", "e-commerce", "software", "food delivery",
    "transportation", "saas", "edtech", "healthtech", "gaming"
}

# Keywords indicating production, deployment, or scaling experience
PRODUCTION_SIGNALS = [
    "deployed to production", "deployed in production", "shipped to",
    "at scale", "million", "billion", "latency", "throughput",
    "a/b test", "ab test", "real-time", "real time", "online serving",
    "model serving", "inference", "production system", "live system",
    "serving layer", "api endpoint", "horizontal scaling", "load balanc"
]


def _title_score(title):
    title = title.lower()
    for kw, val in TARGET_TITLES.items():
        if kw in title:
            return val
    for kw, val in WEAK_TITLES.items():
        if kw in title:
            return val
    for bad in BAD_TITLES:
        if bad in title:
            return 0.1
    return 0.35  # Default baseline for unspecified titles



def _career_relevance(career_raw):
    # Assess overall career history
    scores = []
    for job in career_raw:
        title = job.get("title", "").lower()
        industry = job.get("industry", "").lower()
        dur = job.get("duration_months", 0)

        ts = _title_score(title)

        ind_mult = 1.0
        if industry in PRODUCT_INDUSTRIES:
            ind_mult = 1.15
        elif industry in IT_SERVICES_INDUSTRIES:
            ind_mult = 0.8

        # Weight by duration of tenure
        weight = min(1.0, dur / 24.0)
        scores.append(ts * ind_mult * max(0.3, weight))

    if not scores:
        return 0.0
    # Average of top 3 career roles
    scores.sort(reverse=True)
    return sum(scores[:3]) / min(3, len(scores))


def _production_evidence(career_raw):
    # Check job descriptions for indicators of production execution
    all_desc = " ".join(j.get("description", "") for j in career_raw).lower()
    hits = sum(1 for sig in PRODUCTION_SIGNALS if sig in all_desc)
    return min(1.0, hits / 4.0)


def _tenure_score(career_raw):
    if not career_raw:
        return 0.3
    durations = [j.get("duration_months", 0) for j in career_raw]
    # Penalize if every single role is under 18 months (excessive job-hopping)
    long_roles = sum(1 for d in durations if d >= 18)
    if long_roles == 0:
        return 0.2
    if long_roles >= 2:
        return 1.0
    return 0.65


def _yoe_band_score(yoe):
    # Target experience band is 5 to 9 years, with solid score for adjacent ranges
    if 5 <= yoe <= 9:
        return 1.0
    if 4 <= yoe < 5:
        return 0.85
    if 9 < yoe <= 12:
        return 0.85
    if 3 <= yoe < 4:
        return 0.65
    if 12 < yoe <= 15:
        return 0.70
    if 2 <= yoe < 3:
        return 0.45
    if yoe > 15:
        return 0.55
    return 0.2


def score_career(c):
    current_title_s = _title_score(c["current_title"])
    career_relevance = _career_relevance(c["career_raw"])
    prod_evidence = _production_evidence(c["career_raw"])
    tenure = _tenure_score(c["career_raw"])
    yoe_band = _yoe_band_score(c["yoe"])

    raw = (
        current_title_s * 0.25 +
        career_relevance * 0.35 +
        prod_evidence * 0.20 +
        tenure * 0.10 +
        yoe_band * 0.10
    )
    return min(1.0, raw)
