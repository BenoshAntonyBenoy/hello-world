"""Role catalogue and the demand profiles used to generate the sample corpus.

Two distinct jobs live here:

1. **The role catalogue** (title, aliases, category, summary) — real product
   data that stays exactly as-is when live sources are connected.

2. **Demand profiles** — per-role probabilities that drive the *synthetic*
   corpus generator. These exist only so the MVP has something to analyse
   before a licensed data feed is wired up. They are inputs to a text
   generator, never to the statistics: the extractor reads the generated
   postings like any other text and recomputes every number from scratch.

Deleting the ``core``/``common``/``emerging`` blocks and pointing the
ingestion pipeline at a real connector changes nothing else in the codebase.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class RoleProfile:
    slug: str
    title: str
    category: str
    summary: str
    aliases: tuple[str, ...] = ()

    # canonical skill -> probability of appearing in any given posting
    core: dict[str, float] = field(default_factory=dict)
    common: dict[str, float] = field(default_factory=dict)
    optional: dict[str, float] = field(default_factory=dict)

    # canonical skill -> (probability 12 months ago, probability today)
    emerging: dict[str, tuple[float, float]] = field(default_factory=dict)
    declining: dict[str, tuple[float, float]] = field(default_factory=dict)

    # Distribution of experience bands across postings for this role.
    experience_mix: tuple[tuple[str, float], ...] = (
        ("0-2", 0.4), ("2-5", 0.4), ("5+", 0.2),
    )
    degree_mix: tuple[tuple[str, float], ...] = (
        ("Bachelor's", 0.72), ("Master's", 0.18), (None, 0.10),
    )
    education_fields: tuple[str, ...] = ("Computer Science", "Information Technology")

    def all_skills(self) -> dict[str, float]:
        """Flattened view used for validation and for roadmap seeding."""
        merged: dict[str, float] = {}
        merged.update(self.core)
        merged.update(self.common)
        merged.update(self.optional)
        for name, (_, end) in self.emerging.items():
            merged[name] = end
        for name, (start, _) in self.declining.items():
            merged[name] = start
        return merged


ROLE_PROFILES: tuple[RoleProfile, ...] = (
    RoleProfile(
        slug="software-engineer",
        title="Software Engineer",
        category="Engineering",
        aliases=("sde", "software developer", "sw engineer", "backend engineer"),
        summary="Designs, builds and maintains software systems across the stack.",
        core={
            "Data Structures & Algorithms": 0.88, "Git": 0.85, "REST APIs": 0.66,
            "SQL": 0.62, "Object-Oriented Programming": 0.60, "Python": 0.58,
            "Java": 0.55, "Problem Solving": 0.70, "JavaScript": 0.50,
        },
        common={
            "Teamwork": 0.55, "Agile": 0.48, "AWS": 0.42, "Docker": 0.40,
            "Linux": 0.38, "React": 0.38, "System Design": 0.35, "CI/CD": 0.34,
            "Test-Driven Development": 0.33, "Node.js": 0.32, "MySQL": 0.30,
            "Microservices": 0.30, "Communication": 0.58, "Spring Boot": 0.28,
            "Internship Experience": 0.30,
        },
        optional={
            "TypeScript": 0.26, "MongoDB": 0.22, "C++": 0.20, "Kubernetes": 0.18,
            "Competitive Programming": 0.16, "Open Source Contributions": 0.14,
            "GraphQL": 0.12, "Redis": 0.12, "Kafka": 0.11, "Go": 0.10,
        },
        emerging={"Generative AI": (0.04, 0.22), "Large Language Models": (0.03, 0.18)},
        declining={"PHP": (0.14, 0.07), "Angular": (0.22, 0.14)},
    ),
    RoleProfile(
        slug="data-scientist",
        title="Data Scientist",
        category="Data & AI",
        aliases=("ds", "applied scientist", "research scientist"),
        summary="Turns data into models, experiments and decisions.",
        core={
            "Python": 0.90, "Machine Learning": 0.85, "Statistics": 0.82,
            "SQL": 0.78, "Pandas": 0.62, "Communication": 0.60,
            "Data Visualization": 0.58, "Problem Solving": 0.55, "NumPy": 0.48,
        },
        common={
            "Scikit-learn": 0.48, "Git": 0.45, "Deep Learning": 0.40, "Jupyter": 0.40,
            "R": 0.34, "AWS": 0.32, "Excel": 0.30, "A/B Testing": 0.30,
            "Tableau": 0.28, "Domain Knowledge": 0.26, "Data Modeling": 0.24,
            "Power BI": 0.22,
        },
        optional={
            "PyTorch": 0.26, "TensorFlow": 0.24, "Apache Spark": 0.22,
            "MLOps": 0.16, "Databricks": 0.16, "Snowflake": 0.14, "Publications": 0.12,
        },
        emerging={
            "Generative AI": (0.06, 0.38), "Large Language Models": (0.05, 0.34),
            "RAG": (0.02, 0.20),
        },
        declining={"Hadoop": (0.18, 0.08), "MATLAB": (0.14, 0.08)},
        experience_mix=(("0-2", 0.32), ("2-5", 0.45), ("5+", 0.23)),
        degree_mix=(("Bachelor's", 0.48), ("Master's", 0.40), ("PhD", 0.12)),
        education_fields=("Computer Science", "Statistics", "Mathematics"),
    ),
    RoleProfile(
        slug="data-analyst",
        title="Data Analyst",
        category="Data & AI",
        aliases=("business data analyst", "reporting analyst", "insights analyst"),
        summary="Answers business questions with queries, dashboards and reports.",
        core={
            "SQL": 0.88, "Excel": 0.76, "Data Visualization": 0.70,
            "Communication": 0.64, "Statistics": 0.58, "Python": 0.56,
            "Problem Solving": 0.52,
        },
        common={
            "Power BI": 0.44, "Tableau": 0.42, "Attention to Detail": 0.40,
            "Pandas": 0.34, "Data Modeling": 0.26, "ETL": 0.24,
            "Domain Knowledge": 0.22, "Git": 0.22, "Google Analytics": 0.18,
            "A/B Testing": 0.18, "Business Process Modeling": 0.16,
        },
        optional={
            "R": 0.16, "Looker": 0.14, "BigQuery": 0.14, "Snowflake": 0.12,
            "Internship Experience": 0.26,
        },
        emerging={"dbt": (0.06, 0.18), "Generative AI": (0.03, 0.20)},
        declining={"Oracle": (0.14, 0.08)},
        experience_mix=(("0-2", 0.52), ("2-5", 0.34), ("5+", 0.14)),
        education_fields=("Computer Science", "Statistics", "Business"),
    ),
    RoleProfile(
        slug="ai-ml-engineer",
        title="AI/ML Engineer",
        category="Data & AI",
        aliases=("machine learning engineer", "ml engineer", "ai engineer"),
        summary="Ships machine learning systems into production and keeps them healthy.",
        core={
            "Python": 0.94, "Machine Learning": 0.88, "Deep Learning": 0.70,
            "Git": 0.58, "PyTorch": 0.56, "Statistics": 0.52, "Docker": 0.48,
        },
        common={
            "TensorFlow": 0.46, "Pandas": 0.46, "AWS": 0.44, "Scikit-learn": 0.44,
            "NumPy": 0.42, "SQL": 0.40, "MLOps": 0.38,
            "Natural Language Processing": 0.36, "REST APIs": 0.34, "Linux": 0.34,
            "Computer Vision": 0.30, "Kubernetes": 0.28, "Communication": 0.44,
        },
        optional={
            "Hugging Face": 0.26, "FastAPI": 0.20, "Apache Spark": 0.18,
            "Publications": 0.16, "C++": 0.14,
        },
        emerging={
            "Generative AI": (0.10, 0.52), "Large Language Models": (0.08, 0.48),
            "RAG": (0.03, 0.30), "LangChain": (0.02, 0.22),
        },
        declining={"Hadoop": (0.12, 0.05)},
        experience_mix=(("0-2", 0.30), ("2-5", 0.46), ("5+", 0.24)),
        degree_mix=(("Bachelor's", 0.52), ("Master's", 0.38), ("PhD", 0.10)),
        education_fields=("Computer Science", "Mathematics", "Statistics"),
    ),
    RoleProfile(
        slug="cybersecurity-analyst",
        title="Cybersecurity Analyst",
        category="Security",
        aliases=("security analyst", "soc analyst", "information security analyst"),
        summary="Monitors, investigates and hardens systems against attack.",
        core={
            "Network Security": 0.84, "Vulnerability Assessment": 0.62,
            "Incident Response": 0.58, "Linux": 0.58, "Communication": 0.54,
            "Problem Solving": 0.50,
        },
        common={
            "SIEM": 0.46, "Python": 0.42, "Penetration Testing": 0.40,
            "Cryptography": 0.34, "Splunk": 0.34, "Wireshark": 0.32,
            "Nmap": 0.30, "Threat Intelligence": 0.28,
            "CompTIA Security+": 0.28, "Shell Scripting": 0.26, "AWS": 0.24,
        },
        optional={
            "CEH": 0.22, "Burp Suite": 0.20, "Metasploit": 0.18, "CCNA": 0.18,
            "CISSP": 0.14, "OSCP": 0.10,
        },
        emerging={
            "Identity & Access Management": (0.24, 0.38),
            "Generative AI": (0.02, 0.16),
        },
        declining={"Nmap": (0.34, 0.26)},
        experience_mix=(("0-2", 0.38), ("2-5", 0.40), ("5+", 0.22)),
        education_fields=("Computer Science", "Information Technology"),
    ),
    RoleProfile(
        slug="embedded-systems-engineer",
        title="Embedded Systems Engineer",
        category="Hardware",
        aliases=("firmware engineer", "embedded engineer", "embedded developer"),
        summary="Writes software that runs directly on constrained hardware.",
        core={
            "C": 0.88, "Embedded Systems": 0.84, "Microcontrollers": 0.70,
            "Communication Protocols": 0.62, "Problem Solving": 0.48,
            "Circuit Design": 0.40,
        },
        common={
            "C++": 0.52, "RTOS": 0.44, "Git": 0.42, "Linux": 0.40,
            "ARM Architecture": 0.34, "Python": 0.34, "PCB Design": 0.26,
            "Oscilloscope": 0.24, "Signal Processing": 0.22, "Communication": 0.42,
        },
        optional={
            "MATLAB": 0.18, "Control Systems": 0.16, "FPGA": 0.14,
            "Verilog": 0.12, "Altium Designer": 0.12, "KiCad": 0.10,
        },
        emerging={"IoT": (0.20, 0.34), "Rust": (0.02, 0.12)},
        declining={"Assembly": (0.28, 0.18)},
        experience_mix=(("0-2", 0.34), ("2-5", 0.44), ("5+", 0.22)),
        education_fields=("Electronics", "Electrical", "Computer Science"),
    ),
    RoleProfile(
        slug="electronics-engineer",
        title="Electronics Engineer",
        category="Hardware",
        aliases=("electronics design engineer", "hardware engineer", "ece engineer"),
        summary="Designs and validates electronic circuits and hardware products.",
        core={
            "Circuit Design": 0.78, "PCB Design": 0.60, "Problem Solving": 0.46,
            "Signal Processing": 0.44, "Communication Protocols": 0.40,
            "Oscilloscope": 0.38,
        },
        common={
            "Microcontrollers": 0.48, "MATLAB": 0.44, "Embedded Systems": 0.42,
            "C": 0.40, "Control Systems": 0.30, "Altium Designer": 0.28,
            "Python": 0.26, "KiCad": 0.20, "Communication": 0.44, "Teamwork": 0.38,
        },
        optional={
            "Verilog": 0.18, "FPGA": 0.16, "RTOS": 0.14, "Attention to Detail": 0.34,
        },
        emerging={"IoT": (0.16, 0.30)},
        declining={"VHDL": (0.22, 0.13)},
        experience_mix=(("0-2", 0.40), ("2-5", 0.40), ("5+", 0.20)),
        education_fields=("Electronics", "Electrical"),
    ),
    RoleProfile(
        slug="product-manager",
        title="Product Manager",
        category="Product",
        aliases=("pm", "associate product manager", "technical product manager"),
        summary="Decides what gets built, why, and in what order.",
        core={
            "Communication": 0.84, "Product Roadmapping": 0.70,
            "Stakeholder Management": 0.68, "Requirements Gathering": 0.62,
            "Agile": 0.60, "Problem Solving": 0.58,
        },
        common={
            "Product Analytics": 0.48, "Jira": 0.44, "Leadership": 0.42,
            "User Research": 0.40, "Presentation Skills": 0.38, "SQL": 0.36,
            "A/B Testing": 0.34, "Domain Knowledge": 0.34,
            "Data Visualization": 0.30, "Excel": 0.28, "Figma": 0.22,
        },
        optional={
            "Mixpanel": 0.18, "Financial Modeling": 0.16,
            "Certified Scrum Master": 0.14, "Python": 0.10, "PMP": 0.10,
        },
        emerging={"Generative AI": (0.04, 0.30), "Large Language Models": (0.02, 0.20)},
        declining={"Six Sigma": (0.10, 0.05)},
        experience_mix=(("0-2", 0.24), ("2-5", 0.44), ("5+", 0.32)),
        degree_mix=(("Bachelor's", 0.58), ("Master's", 0.34), (None, 0.08)),
        education_fields=("Computer Science", "Business"),
    ),
    RoleProfile(
        slug="ui-ux-designer",
        title="UI/UX Designer",
        category="Design",
        aliases=("product designer", "ux designer", "ui designer"),
        summary="Designs how a product looks, behaves and feels to use.",
        core={
            "Figma": 0.82, "Wireframing": 0.70, "Prototyping": 0.68,
            "User Research": 0.62, "Portfolio": 0.60, "Communication": 0.58,
            "Interaction Design": 0.52,
        },
        common={
            "Usability Testing": 0.48, "Design Systems": 0.44, "Teamwork": 0.40,
            "Information Architecture": 0.34, "Adobe XD": 0.30, "Agile": 0.28,
            "HTML": 0.24, "CSS": 0.24, "Attention to Detail": 0.36,
        },
        optional={
            "Sketch": 0.22, "Google UX Certificate": 0.12, "Canva": 0.10,
            "React": 0.10, "Internship Experience": 0.28,
        },
        emerging={"Accessibility": (0.26, 0.44), "Generative AI": (0.03, 0.24)},
        declining={"Adobe XD": (0.38, 0.24), "Sketch": (0.32, 0.18)},
        experience_mix=(("0-2", 0.42), ("2-5", 0.40), ("5+", 0.18)),
        degree_mix=(("Bachelor's", 0.60), ("Master's", 0.16), (None, 0.24)),
        education_fields=("Design", "Computer Science"),
    ),
    RoleProfile(
        slug="business-analyst",
        title="Business Analyst",
        category="Business",
        aliases=("ba", "functional analyst", "systems analyst"),
        summary="Translates business needs into requirements engineering can build.",
        core={
            "Communication": 0.80, "Requirements Gathering": 0.78, "Excel": 0.70,
            "SQL": 0.58, "Business Process Modeling": 0.56,
            "Stakeholder Management": 0.54, "Problem Solving": 0.52,
        },
        common={
            "Data Visualization": 0.46, "Agile": 0.44, "Presentation Skills": 0.40,
            "Power BI": 0.38, "Domain Knowledge": 0.38, "Jira": 0.36,
            "Critical Thinking": 0.34, "Tableau": 0.30, "Attention to Detail": 0.32,
        },
        optional={
            "Financial Modeling": 0.22, "Python": 0.18, "Salesforce": 0.16,
            "Six Sigma": 0.14, "A/B Testing": 0.12,
        },
        emerging={"Product Analytics": (0.18, 0.32), "Generative AI": (0.02, 0.18)},
        declining={"Six Sigma": (0.20, 0.11)},
        experience_mix=(("0-2", 0.38), ("2-5", 0.42), ("5+", 0.20)),
        degree_mix=(("Bachelor's", 0.66), ("Master's", 0.28), (None, 0.06)),
        education_fields=("Business", "Computer Science", "Information Technology"),
    ),
    RoleProfile(
        slug="devops-engineer",
        title="DevOps Engineer",
        category="Infrastructure",
        aliases=("site reliability engineer", "sre", "platform engineer"),
        summary="Automates delivery and keeps production reliable.",
        core={
            "Docker": 0.84, "CI/CD": 0.82, "Linux": 0.80, "Git": 0.72,
            "Kubernetes": 0.68, "AWS": 0.66, "Shell Scripting": 0.62,
        },
        common={
            "Python": 0.50, "Terraform": 0.48, "Jenkins": 0.46, "GitHub": 0.40,
            "Microservices": 0.34, "Ansible": 0.32, "GitLab": 0.30,
            "Network Security": 0.30, "Azure": 0.28, "Problem Solving": 0.44,
        },
        optional={
            "Google Cloud": 0.22, "Go": 0.18, "CKA": 0.16, "Kafka": 0.14,
            "Redis": 0.12, "Splunk": 0.18,
        },
        emerging={"Terraform": (0.36, 0.58), "Identity & Access Management": (0.16, 0.30)},
        declining={"Jenkins": (0.56, 0.38)},
        experience_mix=(("0-2", 0.26), ("2-5", 0.46), ("5+", 0.28)),
    ),
    RoleProfile(
        slug="cloud-engineer",
        title="Cloud Engineer",
        category="Infrastructure",
        aliases=("cloud architect", "cloud infrastructure engineer", "aws engineer"),
        summary="Designs and runs workloads on cloud infrastructure.",
        core={
            "AWS": 0.82, "Linux": 0.66, "Docker": 0.58, "Git": 0.56,
            "Terraform": 0.52, "CI/CD": 0.50, "Kubernetes": 0.50,
        },
        common={
            "Shell Scripting": 0.48, "Python": 0.48, "Network Security": 0.48,
            "Azure": 0.44, "AWS Certification": 0.34, "Google Cloud": 0.32,
            "Microservices": 0.28, "Ansible": 0.24, "Communication": 0.40,
        },
        optional={
            "Azure Certification": 0.16, "Google Cloud Certification": 0.12,
            "CKA": 0.12, "Go": 0.12, "Redis": 0.10,
        },
        emerging={
            "Terraform": (0.38, 0.62), "Identity & Access Management": (0.22, 0.38),
        },
        declining={"Ansible": (0.32, 0.20)},
        experience_mix=(("0-2", 0.28), ("2-5", 0.46), ("5+", 0.26)),
    ),
    RoleProfile(
        slug="digital-marketing-specialist",
        title="Digital Marketing Specialist",
        category="Marketing",
        aliases=("digital marketer", "growth marketer", "performance marketer"),
        summary="Grows reach and conversion across search, content and social.",
        core={
            "SEO": 0.74, "Communication": 0.72, "Content Marketing": 0.62,
            "Google Analytics": 0.60, "Social Media Marketing": 0.58,
        },
        common={
            "SEM": 0.52, "Email Marketing": 0.44, "Excel": 0.36,
            "SEMrush": 0.30, "Attention to Detail": 0.30, "Canva": 0.28,
            "Data Visualization": 0.24, "Portfolio": 0.24, "HubSpot": 0.22,
            "Teamwork": 0.38, "Time Management": 0.30,
        },
        optional={
            "Salesforce": 0.14, "Mixpanel": 0.10, "SQL": 0.08,
            "Internship Experience": 0.30,
        },
        emerging={"Generative AI": (0.05, 0.42), "Large Language Models": (0.02, 0.22)},
        declining={"Email Marketing": (0.50, 0.38)},
        experience_mix=(("0-2", 0.50), ("2-5", 0.36), ("5+", 0.14)),
        degree_mix=(("Bachelor's", 0.64), ("Master's", 0.18), (None, 0.18)),
        education_fields=("Marketing", "Business"),
    ),
)

BY_SLUG: dict[str, RoleProfile] = {r.slug: r for r in ROLE_PROFILES}


def find_role(query: str) -> RoleProfile | None:
    """Resolve a free-text search to a role, matching title then aliases."""
    q = query.strip().lower()
    if not q:
        return None
    for role in ROLE_PROFILES:
        if q == role.slug or q == role.title.lower():
            return role
    for role in ROLE_PROFILES:
        if q in {a.lower() for a in role.aliases}:
            return role
    # Loose containment, longest title first so "data scientist" does not
    # get captured by a shorter partial match.
    for role in sorted(ROLE_PROFILES, key=lambda r: -len(r.title)):
        if q in role.title.lower() or role.title.lower() in q:
            return role
        if any(a in q for a in (al.lower() for al in role.aliases)):
            return role
    return None


def validate_catalog() -> list[str]:
    """Check every referenced skill exists in the taxonomy.

    Called at seed time so a typo surfaces immediately instead of quietly
    dropping a skill out of the statistics.
    """
    from app.extraction.taxonomy import BY_CANONICAL

    problems: list[str] = []
    for role in ROLE_PROFILES:
        for name in role.all_skills():
            if name not in BY_CANONICAL:
                problems.append(f"{role.slug}: unknown skill {name!r}")
    return problems
