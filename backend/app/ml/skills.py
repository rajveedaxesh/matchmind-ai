"""Skill taxonomy: canonical names, aliases, related-skill groups and text extraction.

Everything here is a plain, local lookup table - no model downloads, no network.
"""
from __future__ import annotations

import re
from functools import lru_cache
from typing import Iterable

# canonical skill -> aliases (the canonical name itself is always accepted)
_TAXONOMY: dict[str, tuple[str, ...]] = {
    # languages
    "python": ("python3",),
    "javascript": ("js", "ecmascript", "es6"),
    "typescript": ("ts",),
    "java": (),
    "go": ("golang",),
    "rust": (),
    "c++": ("cpp",),
    "c#": ("csharp", "c sharp"),
    "sql": ("structured query language",),
    "r": ("r language", "rlang"),
    "scala": (),
    "kotlin": (),
    "swift": (),
    "bash": ("shell scripting", "shell"),
    "html": ("html5",),
    "css": ("css3",),
    # web
    "react": ("reactjs", "react.js"),
    "vue": ("vue.js", "vuejs"),
    "angular": ("angularjs",),
    "next.js": ("nextjs", "next"),
    "node.js": ("nodejs", "node"),
    "express": ("express.js", "expressjs"),
    "tailwind": ("tailwind css", "tailwindcss"),
    "fastapi": ("fast api",),
    "django": (),
    "flask": (),
    "spring boot": ("springboot", "spring"),
    "graphql": ("graph ql",),
    "rest apis": ("rest api", "restful apis", "restful api", "restful", "rest", "rest services"),
    "microservices": ("microservice architecture", "micro-services"),
    "storybook": (),
    "accessibility": ("a11y", "wcag"),
    "design systems": ("design system",),
    # data & ML
    "pandas": (),
    "numpy": (),
    "scikit-learn": ("sklearn", "scikit learn", "scikitlearn"),
    "tensorflow": ("tf",),
    "pytorch": ("torch",),
    "machine learning": ("ml",),
    "deep learning": ("dl", "neural networks"),
    "nlp": ("natural language processing", "text mining"),
    "computer vision": ("cv", "image recognition"),
    "llms": ("llm", "large language models", "generative ai", "genai"),
    "prompt engineering": (),
    "recommender systems": ("recommendation systems", "recommender engines", "recsys", "recommendation engines"),
    "statistics": ("statistical analysis", "statistical modeling", "statistical modelling"),
    "a/b testing": ("ab testing", "a b testing", "split testing"),
    "experimentation": ("experiment design",),
    "causal inference": (),
    "time series": ("time-series", "forecasting"),
    "feature engineering": (),
    "mlops": ("ml ops", "ml operations"),
    "mlflow": (),
    "xgboost": ("gradient boosting",),
    "spark": ("apache spark", "pyspark"),
    "airflow": ("apache airflow",),
    "dbt": ("data build tool",),
    "kafka": ("apache kafka",),
    "etl": ("elt", "data pipelines", "data pipeline", "etl pipelines"),
    "data modeling": ("data modelling", "dimensional modeling"),
    "data visualization": ("data visualisation", "dataviz", "data viz"),
    "tableau": (),
    "power bi": ("powerbi", "power-bi"),
    "looker": (),
    "excel": ("microsoft excel", "ms excel", "spreadsheets"),
    "elasticsearch": ("elastic search",),
    # infrastructure
    "docker": ("containerization", "containers"),
    "kubernetes": ("k8s",),
    "terraform": ("infrastructure as code", "iac"),
    "aws": ("amazon web services",),
    "gcp": ("google cloud", "google cloud platform"),
    "azure": ("microsoft azure",),
    "ci/cd": ("cicd", "ci cd", "continuous integration", "continuous delivery", "continuous deployment"),
    "github actions": (),
    "linux": ("unix",),
    "prometheus": (),
    "grafana": (),
    "ansible": (),
    "networking": ("tcp/ip",),
    "observability": ("monitoring",),
    "incident response": (),
    "git": ("github", "version control"),
    "jira": (),
    # data stores
    "postgresql": ("postgres", "psql"),
    "mysql": (),
    "mongodb": ("mongo",),
    "redis": (),
    "snowflake": (),
    "bigquery": ("big query",),
    # product & design
    "product strategy": ("product vision",),
    "roadmapping": ("product roadmap", "roadmap planning"),
    "user research": ("ux research", "customer interviews"),
    "usability testing": ("usability studies", "user testing"),
    "stakeholder management": ("stakeholder communication", "stakeholder engagement"),
    "agile": ("agile methodologies",),
    "scrum": (),
    "okrs": ("okr",),
    "figma": (),
    "wireframing": ("wireframes",),
    "prototyping": ("prototypes", "rapid prototyping"),
    # mobile
    "react native": ("react-native",),
    "flutter": (),
    "ios": ("iphone development",),
    "android": ("android sdk",),
    # security
    "application security": ("appsec", "secure coding"),
    "owasp": ("owasp top 10",),
    "penetration testing": ("pentesting", "pen testing", "ethical hacking"),
    "threat modeling": ("threat modelling",),
    "siem": ("security information and event management",),
    "iam": ("identity and access management",),
    # testing
    "test automation": ("automated testing", "qa automation"),
    "selenium": (),
    "cypress": (),
    "pytest": (),
    "jest": (),
}

# Skills that are "close enough" to earn partial credit when the exact skill is absent.
_RELATED_GROUPS: tuple[tuple[str, ...], ...] = (
    ("pytorch", "tensorflow"),
    ("react", "vue", "angular"),
    ("javascript", "typescript"),
    ("node.js", "express"),
    ("postgresql", "mysql"),
    ("sql", "postgresql", "mysql", "snowflake", "bigquery"),
    ("aws", "gcp", "azure"),
    ("tableau", "power bi", "looker"),
    ("fastapi", "flask", "django"),
    ("snowflake", "bigquery"),
    ("terraform", "ansible"),
    ("docker", "kubernetes"),
    ("jest", "pytest", "cypress", "selenium"),
    ("scikit-learn", "xgboost"),
    ("machine learning", "deep learning"),
    ("nlp", "llms"),
    ("statistics", "a/b testing", "experimentation", "causal inference"),
    ("figma", "wireframing", "prototyping"),
    ("user research", "usability testing"),
    ("react native", "flutter"),
    ("ios", "android"),
    ("java", "kotlin"),
    ("agile", "scrum"),
    ("observability", "prometheus", "grafana"),
    ("application security", "owasp", "threat modeling", "penetration testing"),
    ("airflow", "dbt"),
)

RELATED_CREDIT = 0.5

# Aliases that are ordinary English words or too short to be trusted when scanning free text.
_NO_EXTRACT = {
    "go", "r", "rest", "node", "next", "tf", "ts", "cv", "dl", "spring", "shell",
    "torch", "express", "containers", "monitoring", "forecasting", "elt", "ml",
}


def _clean(raw: str) -> str:
    return re.sub(r"\s+", " ", str(raw).strip().lower().replace("_", " "))


def _collapse(text: str) -> str:
    return re.sub(r"[^a-z0-9+#./]", "", text)


_ALIAS_TO_CANON: dict[str, str] = {}
_COLLAPSED_TO_CANON: dict[str, str] = {}
for _canon, _aliases in _TAXONOMY.items():
    for _name in (_canon, *_aliases):
        _ALIAS_TO_CANON[_clean(_name)] = _canon
        _COLLAPSED_TO_CANON.setdefault(_collapse(_clean(_name)), _canon)

_RELATED: dict[str, set[str]] = {}
for _group in _RELATED_GROUPS:
    for _a in _group:
        _RELATED.setdefault(_a, set()).update(s for s in _group if s != _a)


def normalize_skill(raw: str) -> str:
    """Map a free-form skill string to its canonical name (unknown skills are just cleaned)."""
    cleaned = _clean(raw)
    if not cleaned:
        return ""
    if cleaned in _ALIAS_TO_CANON:
        return _ALIAS_TO_CANON[cleaned]
    collapsed = _collapse(cleaned)
    if collapsed in _COLLAPSED_TO_CANON:
        return _COLLAPSED_TO_CANON[collapsed]
    return cleaned


def normalize_skills(skills: Iterable[str]) -> list[str]:
    """Normalise, drop blanks and de-duplicate while preserving order."""
    seen: dict[str, None] = {}
    for raw in skills or ():
        canon = normalize_skill(raw)
        if canon:
            seen.setdefault(canon, None)
    return list(seen)


def related_skills(skill: str) -> set[str]:
    return set(_RELATED.get(normalize_skill(skill), ()))


def is_known_skill(skill: str) -> bool:
    return normalize_skill(skill) in _TAXONOMY


def all_known_skills() -> list[str]:
    return sorted(_TAXONOMY)


@lru_cache(maxsize=1)
def _extraction_patterns() -> tuple[tuple[str, re.Pattern[str]], ...]:
    patterns: list[tuple[str, re.Pattern[str]]] = []
    for canon, aliases in _TAXONOMY.items():
        for name in (canon, *aliases):
            cleaned = _clean(name)
            if cleaned in _NO_EXTRACT or len(cleaned) < 2:
                continue
            body = r"[\s\-]+".join(re.escape(tok) for tok in re.split(r"[\s\-]+", cleaned))
            patterns.append(
                (canon, re.compile(rf"(?<![A-Za-z0-9_+#]){body}(?![A-Za-z0-9_+#])", re.IGNORECASE))
            )
    return tuple(patterns)


def extract_skills(text: str) -> list[str]:
    """Find known skills mentioned in free text (used when a job lists no skills)."""
    if not text:
        return []
    spans: list[tuple[int, int, str]] = []
    for canon, pattern in _extraction_patterns():
        for m in pattern.finditer(text):
            spans.append((m.start(), m.end(), canon))
    # drop matches fully contained in a longer match ("react" inside "react native")
    spans.sort(key=lambda s: (-(s[1] - s[0]), s[0]))
    kept: list[tuple[int, int, str]] = []
    for start, end, canon in spans:
        if any(ks <= start and end <= ke and (ke - ks) > (end - start) for ks, ke, _ in kept):
            continue
        kept.append((start, end, canon))
    kept.sort(key=lambda s: s[0])
    out: dict[str, None] = {}
    for _, _, canon in kept:
        out.setdefault(canon, None)
    return list(out)
