"""Role families used for (a) synthetic evaluation labels and (b) generating extra synthetic candidates.

The family tag is a *latent ground-truth* for the synthetic benchmark. The matching engine never reads it.
All data in this project is fictional.
"""
from __future__ import annotations

FAMILIES: dict[str, dict] = {
    "backend": {
        "label": "Backend Engineering",
        "titles": ["Backend Engineer", "Software Engineer, Backend", "API Developer"],
        "core": ["python", "rest apis", "postgresql", "docker", "git", "sql"],
        "extra": ["fastapi", "flask", "django", "redis", "kubernetes", "aws", "ci/cd", "java", "spring boot", "kafka", "microservices", "graphql"],
        "blurbs": [
            "Designs and ships REST APIs and services backed by relational databases.",
            "Focuses on service reliability, query performance and clean API contracts.",
            "Experienced with containerized deployments and automated testing for backend services.",
            "Enjoys refactoring legacy services into well-tested, observable modules.",
        ],
    },
    "frontend": {
        "label": "Frontend Engineering",
        "titles": ["Frontend Engineer", "UI Engineer", "Web Developer"],
        "core": ["react", "typescript", "javascript", "html", "css", "rest apis", "git"],
        "extra": ["next.js", "vue", "jest", "accessibility", "graphql", "tailwind", "cypress", "design systems", "storybook"],
        "blurbs": [
            "Builds responsive, accessible interfaces with component-driven development.",
            "Cares about web performance, design fidelity and maintainable component libraries.",
            "Collaborates closely with designers to turn prototypes into production UI.",
            "Writes unit and end-to-end tests for complex front-end state.",
        ],
    },
    "fullstack": {
        "label": "Full-Stack Engineering",
        "titles": ["Full-Stack Engineer", "Software Engineer", "Product Engineer"],
        "core": ["typescript", "react", "node.js", "postgresql", "rest apis", "git", "docker"],
        "extra": ["graphql", "aws", "python", "fastapi", "ci/cd", "terraform", "next.js"],
        "blurbs": [
            "Ships features end to end, from database schema to polished user interface.",
            "Comfortable owning a product area across front end, API and deployment.",
            "Likes small teams, fast iteration and measurable product impact.",
            "Experienced building SaaS products with TypeScript across the stack.",
        ],
    },
    "data_science": {
        "label": "Data Science",
        "titles": ["Data Scientist", "Applied Data Scientist", "Research Scientist"],
        "core": ["python", "statistics", "pandas", "scikit-learn", "sql", "machine learning"],
        "extra": ["a/b testing", "time series", "tableau", "r", "nlp", "experimentation", "causal inference", "xgboost", "feature engineering", "mlflow"],
        "blurbs": [
            "Builds predictive models and communicates findings to non-technical stakeholders.",
            "Designs experiments and statistical analyses to guide product decisions.",
            "Turns messy tabular data into reliable features and validated models.",
            "Strong in exploratory analysis, hypothesis testing and model evaluation.",
        ],
    },
    "ml_engineering": {
        "label": "Machine Learning Engineering",
        "titles": ["Machine Learning Engineer", "ML Engineer", "NLP Engineer"],
        "core": ["python", "machine learning", "pytorch", "docker", "deep learning"],
        "extra": ["mlops", "kubernetes", "aws", "computer vision", "nlp", "llms", "tensorflow", "spark", "mlflow", "fastapi", "recommender systems", "prompt engineering", "elasticsearch"],
        "blurbs": [
            "Trains and deploys deep learning models and serves them behind low-latency APIs.",
            "Builds reproducible training pipelines and monitors models in production.",
            "Works on applied research problems and moves prototypes into production systems.",
            "Optimises model inference and maintains feature and experiment tracking tooling.",
        ],
    },
    "data_engineering": {
        "label": "Data Engineering",
        "titles": ["Data Engineer", "Senior Data Engineer", "Analytics Engineer"],
        "core": ["python", "sql", "etl", "spark", "airflow", "data modeling"],
        "extra": ["kafka", "dbt", "snowflake", "aws", "docker", "terraform", "bigquery", "git"],
        "blurbs": [
            "Builds batch and streaming pipelines that deliver trustworthy analytics data.",
            "Models warehouse schemas and keeps data quality checks automated.",
            "Orchestrates scheduled workflows and optimises large-scale transformations.",
            "Partners with analysts and scientists to productionise datasets.",
        ],
    },
    "data_analytics": {
        "label": "Data & Business Analytics",
        "titles": ["Data Analyst", "Business Intelligence Analyst", "Product Analyst"],
        "core": ["sql", "excel", "data visualization", "tableau", "statistics"],
        "extra": ["power bi", "python", "looker", "a/b testing", "stakeholder management", "experimentation", "data modeling"],
        "blurbs": [
            "Builds dashboards and reports that answer day-to-day business questions.",
            "Translates stakeholder requests into SQL analyses and clear visual stories.",
            "Tracks KPIs, investigates anomalies and presents recommendations.",
            "Enjoys making data accessible to non-technical teams.",
        ],
    },
    "devops": {
        "label": "DevOps & Cloud",
        "titles": ["DevOps Engineer", "Site Reliability Engineer", "Cloud Platform Engineer"],
        "core": ["docker", "kubernetes", "terraform", "ci/cd", "linux", "aws"],
        "extra": ["prometheus", "grafana", "python", "ansible", "github actions", "gcp", "observability", "go", "azure", "incident response"],
        "blurbs": [
            "Automates infrastructure with code and builds reliable deployment pipelines.",
            "Improves observability, on-call health and incident response processes.",
            "Operates container platforms and keeps cloud costs and reliability in balance.",
            "Standardises environments so product teams can ship safely and often.",
        ],
    },
    "product": {
        "label": "Product Management",
        "titles": ["Product Manager", "Technical Product Manager", "Product Owner"],
        "core": ["product strategy", "roadmapping", "user research", "stakeholder management", "agile"],
        "extra": ["sql", "okrs", "a/b testing", "jira", "scrum", "rest apis", "microservices"],
        "blurbs": [
            "Defines product vision, prioritises roadmaps and aligns cross-functional teams.",
            "Runs discovery with customers and turns insights into shippable requirements.",
            "Uses data and experiments to validate product bets and track outcomes.",
            "Comfortable working with engineers on technical trade-offs.",
        ],
    },
    "design": {
        "label": "Product Design & Research",
        "titles": ["Product Designer", "UX Designer", "UX Researcher"],
        "core": ["figma", "user research", "wireframing", "prototyping"],
        "extra": ["design systems", "accessibility", "html", "css", "usability testing", "a/b testing"],
        "blurbs": [
            "Designs end-to-end user flows from research through high-fidelity prototypes.",
            "Maintains design systems and advocates for accessible, inclusive interfaces.",
            "Runs usability studies and synthesises findings into clear recommendations.",
            "Works closely with engineers to keep implementation faithful to the design.",
        ],
    },
    "security": {
        "label": "Security Engineering",
        "titles": ["Application Security Engineer", "Security Engineer", "Security Analyst"],
        "core": ["application security", "owasp", "threat modeling", "penetration testing", "python"],
        "extra": ["aws", "docker", "ci/cd", "siem", "iam", "networking", "incident response", "linux"],
        "blurbs": [
            "Reviews code and architectures for vulnerabilities and drives remediation.",
            "Performs threat modeling and builds security checks into CI pipelines.",
            "Investigates alerts, triages incidents and improves detection coverage.",
            "Educates developers on secure coding practices.",
        ],
    },
    "qa": {
        "label": "Quality Engineering",
        "titles": ["QA Automation Engineer", "Test Engineer", "SDET"],
        "core": ["test automation", "selenium", "python", "ci/cd", "git"],
        "extra": ["pytest", "cypress", "jest", "docker", "rest apis", "java"],
        "blurbs": [
            "Builds automated regression suites and integrates them into CI pipelines.",
            "Designs test strategies covering API, UI and performance testing.",
            "Reduces flaky tests and shortens feedback loops for developers.",
            "Partners with engineers to catch defects early in the lifecycle.",
        ],
    },
    "mobile": {
        "label": "Mobile Engineering",
        "titles": ["Mobile Engineer", "React Native Developer", "Android Engineer"],
        "core": ["react native", "typescript", "javascript", "rest apis", "git"],
        "extra": ["ios", "android", "kotlin", "flutter", "jest", "ci/cd", "swift", "java", "agile"],
        "blurbs": [
            "Ships polished mobile apps and manages store releases.",
            "Optimises app performance, offline behaviour and battery usage.",
            "Builds shared UI components used across iOS and Android.",
            "Instruments apps with analytics and crash reporting.",
        ],
    },
}

# Families a recruiter would reasonably consider "adjacent" when screening (symmetric).
ADJACENT_PAIRS: tuple[tuple[str, str], ...] = (
    ("backend", "fullstack"), ("backend", "data_engineering"), ("backend", "devops"),
    ("backend", "qa"), ("backend", "security"),
    ("frontend", "fullstack"), ("frontend", "mobile"), ("frontend", "design"), ("frontend", "qa"),
    ("data_science", "ml_engineering"), ("data_science", "data_analytics"), ("data_science", "data_engineering"),
    ("ml_engineering", "data_engineering"), ("data_engineering", "data_analytics"),
    ("devops", "security"), ("product", "data_analytics"), ("product", "design"), ("qa", "mobile"),
)


def families_adjacent(a: str, b: str) -> bool:
    return (a, b) in ADJACENT_PAIRS or (b, a) in ADJACENT_PAIRS


LOCATIONS = ["San Francisco, US", "Austin, US", "London, UK", "Berlin, DE", "Bengaluru, IN", "Toronto, CA", "Singapore, SG"]
