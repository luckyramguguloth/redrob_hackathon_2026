"""
Knockout Filters.
Applies basic pre-qualification checks to filter out profiles that do not
meet minimum role requirements, ensuring optimization during detailed scoring.
"""

CONSULTING_FIRMS = {
    "tcs", "tata consultancy", "infosys", "wipro", "accenture",
    "cognizant", "capgemini", "hcl", "mphasis", "tech mahindra",
    "hexaware", "ltimindtree", "mindtree", "l&t technology",
    "persistent systems", "zensar", "birlasoft", "mastek"
}

AI_TITLE_KEYWORDS = {
    "machine learning", "ml engineer", "ai engineer", "data scientist",
    "nlp", "research engineer", "applied scientist", "ml ops", "mlops",
    "search engineer", "ranking engineer", "recommendation", "recsys",
    "retrieval", "llm", "deep learning", "computer vision engineer",
    "speech engineer", "backend engineer", "software engineer",
    "full stack", "platform engineer", "data engineer", "analytics engineer",
    "senior engineer", "staff engineer", "principal engineer",
    "python developer", "python engineer"
}

# Skills that indicate at least some technical AI/ML relevance
MIN_RELEVANT_SKILLS = {
    "python", "machine learning", "deep learning", "nlp", "pytorch", "tensorflow",
    "scikit-learn", "transformers", "bert", "gpt", "llm", "embedding",
    "faiss", "pinecone", "weaviate", "qdrant", "milvus", "elasticsearch",
    "opensearch", "vector", "rag", "fine-tuning", "lora", "hugging face",
    "spark", "sql", "data science", "statistics", "pandas", "numpy",
    "recommendation", "ranking", "retrieval", "search", "xgboost",
    "lightgbm", "scikit", "keras", "neural", "attention", "bm25",
    "docker", "kubernetes", "aws", "gcp", "azure", "java", "scala",
    "golang", "rust", "c++", "kafka", "airflow", "dbt", "sql alchemy"
}

CLEARLY_WRONG_TITLES = {
    "accountant", "hr manager", "human resources", "marketing manager",
    "content writer", "graphic designer", "social media", "seo",
    "sales manager", "business development", "finance manager",
    "operations manager", "supply chain", "procurement", "customer support",
    "civil engineer", "mechanical engineer", "electrical engineer",
    "architect", "interior designer", "teacher", "professor",
    "medical", "doctor", "nurse", "pharmacist", "lawyer", "legal"
}

INDIA_ADJACENT_COUNTRIES = {"india"}


def _is_consulting_only(career_raw):
    if not career_raw:
        return False
    companies = [j.get("company", "").lower() for j in career_raw]
    industries = [j.get("industry", "").lower() for j in career_raw]

    # Verify if entire work history is in IT consulting/services
    non_it = [ind for ind in industries if ind not in ("it services", "consulting")]
    if non_it:
        return False

    # Check companies against known list
    all_consulting = all(
        any(firm in c for firm in CONSULTING_FIRMS)
        for c in companies
    )
    return all_consulting and len(companies) >= 2


def _has_any_tech_signal(c):
    # Search job title
    title = c["current_title"]
    for kw in AI_TITLE_KEYWORDS:
        if kw in title:
            return True

    # Search declared skills using pre-concatenated string
    skills_concat = c["skills_concat"]
    for rel in MIN_RELEVANT_SKILLS:
        if rel in skills_concat:
            return True

    # Search overall job history text
    job_text = c["job_text"]
    for rel in ("python", "machine learning", "data", "engineer", "software", "ml"):
        if rel in job_text:
            return True

    return False


def _is_clearly_wrong_title(c):
    title = c["current_title"]
    for bad in CLEARLY_WRONG_TITLES:
        if bad in title:
            # Allow to pass only if they show significant hands-on technical ML skills
            strong_ml = sum(
                1 for sk in c["skill_names"]
                if any(k in sk for k in (
                    "machine learning", "deep learning", "nlp", "pytorch",
                    "tensorflow", "embedding", "vector", "rag", "retrieval",
                    "faiss", "pinecone", "weaviate", "milvus", "qdrant",
                    "sentence-transformer", "transformers", "lora", "fine-tuning"
                ))
            )
            if strong_ml >= 3:
                return False
            return True
    return False


def _has_meaningful_ai_exp(c):
    # Require at least two relevant technical skills
    tech_skill_count = sum(
        1 for sk in c["skill_names"]
        if any(k in sk for k in MIN_RELEVANT_SKILLS)
    )
    if tech_skill_count < 2:
        return False
    return True


def _is_accessible(c):
    if c["country"].lower() in INDIA_ADJACENT_COUNTRIES:
        return True
    if c["willing_relocate"]:
        return True
    return False


def passes_hard_filter(c):
    if not _has_any_tech_signal(c):
        return False
    if not _has_meaningful_ai_exp(c):
        return False
    if _is_clearly_wrong_title(c):
        return False
    if c["yoe"] < 2.0:
        return False
    return True
