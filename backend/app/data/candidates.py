"""18 FICTIONAL candidates plus a demo job-seeker profile (synthetic demonstration data).

Display names are neutral code names ("Candidate Aster") rather than personal names, and no
protected attributes (age, gender, ethnicity, photo ...) exist anywhere in the data model.
"""
from __future__ import annotations


def _cand(code, headline, location, years, family, skills, summary, titles, locs, modes, relocate=False):
    return {
        "display_name": f"Candidate {code}", "headline": headline, "location": location,
        "years_experience": years, "skills": skills, "summary": summary, "desired_titles": titles,
        "preferred_locations": locs, "preferred_work_modes": modes, "open_to_relocation": relocate,
        "family": family,  # latent ground-truth tag for the synthetic benchmark; never used for scoring
    }


SEED_CANDIDATES: list[dict] = [
    _cand("Aster", "Backend Engineer", "London, UK", 6, "backend",
          ["python", "fastapi", "postgresql", "docker", "redis", "rest apis", "aws", "ci/cd", "git"],
          "Backend engineer who designs REST APIs and data-heavy services in Python. Has tuned slow PostgreSQL queries, containerised services and set up CI pipelines.",
          ["Senior Backend Engineer"], ["Remote", "London"], ["remote", "hybrid"]),
    _cand("Birch", "Java Backend Developer", "Berlin, DE", 4, "backend",
          ["java", "spring boot", "postgresql", "kafka", "rest apis", "microservices", "docker"],
          "Java developer building event-driven microservices for fintech. Experienced with Kafka consumers, idempotent APIs and transactional workflows.",
          ["Backend Engineer"], ["London", "Berlin"], ["hybrid", "onsite"], True),
    _cand("Cedar", "Frontend Engineer", "Toronto, CA", 5, "frontend",
          ["react", "typescript", "css", "html", "jest", "accessibility", "next.js", "rest apis"],
          "Frontend engineer focused on accessible, performant React applications. Writes component tests and collaborates closely with designers on UI polish.",
          ["Frontend Engineer", "UI Engineer"], ["Remote", "Toronto"], ["remote", "hybrid"]),
    _cand("Dune", "Full-Stack Developer", "Austin, US", 4, "fullstack",
          ["typescript", "react", "node.js", "postgresql", "graphql", "docker", "aws", "git"],
          "Full-stack developer shipping SaaS features from schema to UI. Enjoys small teams and owning features end to end.",
          ["Full-Stack Engineer"], ["Austin", "Remote"], ["hybrid", "remote"]),
    _cand("Ember", "Data Scientist", "London, UK", 3, "data_science",
          ["python", "pandas", "scikit-learn", "statistics", "sql", "a/b testing", "tableau", "time series"],
          "Data scientist with experience in churn modelling and experiment analysis. Communicates results clearly to product and marketing stakeholders.",
          ["Data Scientist"], ["London", "Remote"], ["hybrid", "remote"]),
    _cand("Fjord", "Machine Learning Engineer", "San Francisco, US", 5, "ml_engineering",
          ["python", "pytorch", "machine learning", "docker", "mlops", "kubernetes", "computer vision", "aws", "deep learning"],
          "ML engineer who trains computer-vision models and deploys them on Kubernetes. Builds reproducible pipelines and monitors drift in production.",
          ["Machine Learning Engineer"], ["San Francisco", "Remote"], ["onsite", "hybrid", "remote"]),
    _cand("Garnet", "NLP Engineer", "Remote", 4, "ml_engineering",
          ["python", "nlp", "pytorch", "llms", "prompt engineering", "fastapi", "elasticsearch", "machine learning"],
          "NLP engineer building semantic search and text-classification services. Experienced fine-tuning transformer models and serving them through FastAPI.",
          ["NLP Engineer", "ML Engineer"], ["Remote"], ["remote"]),
    _cand("Heron", "Data Engineer", "Berlin, DE", 6, "data_engineering",
          ["python", "sql", "spark", "airflow", "etl", "snowflake", "dbt", "aws", "kafka", "data modeling"],
          "Data engineer who builds batch and streaming pipelines and keeps warehouse models tidy. Strong on data-quality testing and orchestration.",
          ["Senior Data Engineer", "Data Engineer"], ["Berlin", "Remote"], ["hybrid", "remote"]),
    _cand("Iris", "Data Analyst", "Austin, US", 2, "data_analytics",
          ["sql", "excel", "tableau", "power bi", "data visualization", "python", "statistics"],
          "Analyst who builds weekly dashboards and answers ad-hoc questions with SQL. Keen to grow into experimentation and product analytics.",
          ["Data Analyst", "Business Intelligence Analyst"], ["Austin", "Remote"], ["hybrid", "remote"]),
    _cand("Juniper", "DevOps Engineer", "Toronto, CA", 5, "devops",
          ["docker", "kubernetes", "terraform", "ci/cd", "linux", "aws", "prometheus", "grafana", "python"],
          "DevOps engineer automating infrastructure with Terraform and running Kubernetes clusters. Improves deployment pipelines and on-call experience.",
          ["DevOps Engineer", "Cloud Platform Engineer"], ["Toronto", "Remote"], ["hybrid", "remote"]),
    _cand("Kestrel", "Product Manager", "San Francisco, US", 6, "product",
          ["product strategy", "roadmapping", "user research", "stakeholder management", "agile", "sql", "okrs"],
          "Product manager who runs customer discovery and aligns design and engineering around measurable outcomes. Comfortable with SQL for self-serve analysis.",
          ["Product Manager"], ["San Francisco", "Remote"], ["hybrid", "remote"]),
    _cand("Linden", "Product Designer", "Berlin, DE", 4, "design",
          ["figma", "user research", "wireframing", "prototyping", "design systems", "accessibility", "html", "css"],
          "Designer who moves from interviews to polished prototypes and maintains component libraries. Advocates for accessibility.",
          ["Product Designer", "UX Designer"], ["Berlin", "Remote"], ["hybrid", "remote"]),
    _cand("Maple", "Application Security Engineer", "Singapore, SG", 5, "security",
          ["application security", "owasp", "threat modeling", "python", "penetration testing", "aws"],
          "Security engineer who threat-models new features, runs penetration tests and automates security checks in CI.",
          ["Application Security Engineer"], ["Singapore", "Remote"], ["hybrid", "remote"]),
    _cand("Nova", "QA Automation Engineer", "Bengaluru, IN", 3, "qa",
          ["test automation", "selenium", "python", "pytest", "ci/cd", "cypress", "docker"],
          "QA engineer building automated UI and API regression suites and reducing flaky tests in CI.",
          ["QA Automation Engineer", "SDET"], ["Bengaluru", "Remote"], ["hybrid", "remote"]),
    _cand("Onyx", "Mobile Developer", "Remote", 4, "mobile",
          ["react native", "typescript", "javascript", "ios", "rest apis", "git", "jest"],
          "Mobile developer shipping React Native apps to both stores. Focused on performance and smooth releases.",
          ["Mobile Engineer"], ["Remote"], ["remote"]),
    _cand("Pebble", "Junior Python Developer", "Bengaluru, IN", 1, "backend",
          ["python", "sql", "git", "flask", "rest apis", "pytest"],
          "Early-career developer with a bootcamp background and one year building internal Flask tools. Eager to learn from code review.",
          ["Junior Python Developer", "Backend Engineer"], ["Bengaluru", "Remote"], ["hybrid", "remote"]),
    _cand("Quartz", "Senior Data Scientist", "Remote", 8, "data_science",
          ["python", "statistics", "a/b testing", "causal inference", "sql", "experimentation", "r", "pandas"],
          "Experimentation-focused data scientist who designs power analyses and sequential tests and coaches product teams on causal reasoning.",
          ["Senior Data Scientist"], ["Remote"], ["remote"]),
    _cand("Rowan", "Site Reliability Engineer", "London, UK", 7, "devops",
          ["kubernetes", "linux", "observability", "prometheus", "python", "go", "incident response", "gcp", "terraform"],
          "SRE who defines SLOs, leads incident reviews and automates away toil on large Kubernetes estates.",
          ["Site Reliability Engineer"], ["London", "Remote"], ["hybrid", "remote"]),
]

# The editable profile used in the job-seeker workflow (also fictional).
DEMO_PROFILE: dict = {
    "display_name": "Demo Job Seeker",
    "headline": "Aspiring Data Scientist",
    "location": "Remote",
    "years_experience": 3,
    "skills": ["python", "sql", "pandas", "scikit-learn", "statistics", "data visualization", "machine learning"],
    "summary": ("Analyst turned data scientist with three years of experience building forecasting and churn models "
                "in Python, and communicating results with dashboards. Looking for a role with experimentation and applied ML."),
    "desired_titles": ["Data Scientist", "Applied Data Scientist"],
    "preferred_locations": ["Remote", "London"],
    "preferred_work_modes": ["remote", "hybrid"],
    "open_to_relocation": False,
}
