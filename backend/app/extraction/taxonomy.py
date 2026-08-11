"""The canonical requirement vocabulary.

Everything the extractor can recognise is declared here exactly once. A skill
carries:

``canonical``     the single name we report to users
``aliases``       surface forms seen in real postings ("ReactJS" -> "React")
``category``      how it is grouped in the dashboard
``tier``          where it lands in a learning roadmap
``prerequisites`` canonical names that should be learned first
``strict``        the token is short/ambiguous ("R", "Go", "C") and only counts
                  when a supporting context word appears nearby
``context_words`` the supporting words used by that check

Adding a skill is a one-line change here; nothing else needs to know about it.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass(frozen=True)
class SkillDef:
    canonical: str
    category: str
    tier: str = "intermediate"
    aliases: tuple[str, ...] = ()
    prerequisites: tuple[str, ...] = ()
    strict: bool = False
    context_words: tuple[str, ...] = ()
    description: str = ""

    @property
    def slug(self) -> str:
        s = self.canonical.lower()
        s = s.replace("+", "plus").replace("#", "sharp").replace(".", "dot")
        s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
        return s

    @property
    def surface_forms(self) -> list[str]:
        return [self.canonical, *self.aliases]


_DATA_CTX = ("data", "statistic", "analytics", "analysis", "model", "research")
_CODE_CTX = ("programming", "language", "develop", "software", "code", "coding")


CATALOG: tuple[SkillDef, ...] = (
    # -- Programming languages ---------------------------------------------
    SkillDef("Python", "language", "beginner",
             ("python3", "python 3"),
             description="General-purpose language dominant in data, ML and backend work."),
    SkillDef("SQL", "language", "beginner",
             ("structured query language", "sql queries"),
             description="Query language for relational databases."),
    SkillDef("JavaScript", "language", "beginner", ("js", "java script", "es6", "ecmascript")),
    SkillDef("TypeScript", "language", "intermediate", ("ts",), ("JavaScript",)),
    SkillDef("Java", "language", "beginner", ("core java", "java se", "java 8", "java 17")),
    SkillDef("C++", "language", "intermediate", ("cpp", "c plus plus", "c/c++")),
    SkillDef("C#", "language", "intermediate", ("c sharp", "csharp", "dotnet c#")),
    SkillDef("C", "language", "beginner", (),
             strict=True,
             context_words=("embedded", "firmware", "microcontroller", "c++", "kernel",
                            "driver", "systems", *_CODE_CTX)),
    SkillDef("Go", "language", "intermediate", ("golang",),
             strict=True,
             context_words=("backend", "microservice", "concurrency", "kubernetes", *_CODE_CTX)),
    SkillDef("Rust", "language", "advanced", ("rust lang",)),
    SkillDef("R", "language", "intermediate", ("r programming", "r language"),
             strict=True,
             context_words=("python", "sas", "spss", "matlab", "regression", *_DATA_CTX)),
    SkillDef("Scala", "language", "advanced", (), ("Java",)),
    SkillDef("Kotlin", "language", "intermediate", (), ("Java",)),
    SkillDef("Swift", "language", "intermediate", ("swiftui",)),
    SkillDef("PHP", "language", "beginner", ()),
    SkillDef("Ruby", "language", "intermediate", ("ruby on rails", "rails")),
    SkillDef("MATLAB", "language", "intermediate", ("mat lab", "simulink")),
    SkillDef("Verilog", "language", "advanced", ("system verilog", "systemverilog")),
    SkillDef("VHDL", "language", "advanced", ()),
    SkillDef("Assembly", "language", "advanced", ("assembly language", "asm")),
    SkillDef("Shell Scripting", "language", "beginner",
             ("bash", "shell script", "shell scripting", "powershell", "zsh")),
    SkillDef("HTML", "language", "beginner", ("html5",)),
    SkillDef("CSS", "language", "beginner", ("css3", "scss", "sass")),

    # -- Frameworks and libraries -------------------------------------------
    SkillDef("React", "framework", "intermediate",
             ("react.js", "reactjs", "react js", "react native"), ("JavaScript",)),
    SkillDef("Angular", "framework", "intermediate", ("angularjs", "angular.js"), ("TypeScript",)),
    SkillDef("Vue", "framework", "intermediate", ("vue.js", "vuejs", "vue js"), ("JavaScript",)),
    SkillDef("Next.js", "framework", "intermediate", ("nextjs", "next js"), ("React",)),
    SkillDef("Node.js", "framework", "intermediate", ("nodejs", "node js", "node"), ("JavaScript",)),
    SkillDef("Express", "framework", "intermediate", ("express.js", "expressjs"), ("Node.js",)),
    SkillDef("Django", "framework", "intermediate", (), ("Python",)),
    SkillDef("Flask", "framework", "intermediate", (), ("Python",)),
    SkillDef("FastAPI", "framework", "intermediate", ("fast api",), ("Python",)),
    SkillDef("Spring Boot", "framework", "intermediate", ("spring", "springboot"), ("Java",)),
    SkillDef(".NET", "framework", "intermediate", ("dotnet", "asp.net", "net core"), ("C#",)),
    SkillDef("Tailwind CSS", "framework", "beginner", ("tailwind", "tailwindcss"), ("CSS",)),
    SkillDef("TensorFlow", "framework", "advanced", ("tensor flow", "tf2", "keras"),
             ("Python", "Machine Learning")),
    SkillDef("PyTorch", "framework", "advanced", ("py torch", "torch"),
             ("Python", "Machine Learning")),
    SkillDef("Scikit-learn", "framework", "intermediate",
             ("sklearn", "scikit learn", "sci-kit learn"), ("Python", "Machine Learning")),
    SkillDef("Pandas", "framework", "beginner", ("pandas dataframe",), ("Python",)),
    SkillDef("NumPy", "framework", "beginner", ("num py",), ("Python",)),
    SkillDef("Hugging Face", "framework", "advanced",
             ("huggingface", "transformers library"), ("PyTorch",)),
    SkillDef("LangChain", "framework", "advanced", ("lang chain", "llamaindex"),
             ("Python", "Large Language Models")),
    SkillDef("OpenCV", "framework", "advanced", ("open cv",), ("Python", "Computer Vision")),
    SkillDef("Apache Spark", "framework", "advanced", ("spark", "pyspark"), ("Python",)),
    SkillDef("Hadoop", "framework", "advanced", ("hdfs", "map reduce", "mapreduce")),
    SkillDef("Kafka", "framework", "advanced", ("apache kafka",)),
    SkillDef("Airflow", "framework", "intermediate", ("apache airflow",), ("Python",)),
    SkillDef("dbt", "framework", "intermediate", ("data build tool",), ("SQL",)),

    # -- Tools ---------------------------------------------------------------
    SkillDef("Git", "tool", "beginner", ("version control", "git version control")),
    SkillDef("GitHub", "tool", "beginner", ("github actions",), ("Git",)),
    SkillDef("GitLab", "tool", "beginner", ("gitlab ci",), ("Git",)),
    SkillDef("Docker", "tool", "intermediate", ("containerization", "containers", "docker compose")),
    SkillDef("Kubernetes", "tool", "advanced", ("k8s", "kubernetes cluster"), ("Docker",)),
    SkillDef("Jenkins", "tool", "intermediate", (), ("CI/CD",)),
    SkillDef("Terraform", "tool", "advanced", ("infrastructure as code", "iac", "hcl")),
    SkillDef("Ansible", "tool", "advanced", ()),
    SkillDef("Jira", "tool", "beginner", ("atlassian jira", "confluence")),
    SkillDef("Postman", "tool", "beginner", (), ("REST APIs",)),
    SkillDef("Jupyter", "tool", "beginner", ("jupyter notebook", "jupyter notebooks", "colab")),
    SkillDef("Linux", "tool", "beginner", ("unix", "ubuntu", "linux administration")),
    SkillDef("Excel", "tool", "beginner", ("microsoft excel", "ms excel", "advanced excel", "spreadsheets")),
    SkillDef("Tableau", "tool", "intermediate", ()),
    SkillDef("Power BI", "tool", "intermediate", ("powerbi", "power-bi", "microsoft power bi")),
    SkillDef("Looker", "tool", "intermediate", ("looker studio", "google data studio")),
    SkillDef("Figma", "tool", "beginner", ()),
    SkillDef("Adobe XD", "tool", "beginner", ("adobe experience design",)),
    SkillDef("Sketch", "tool", "beginner", ("sketch app",)),
    SkillDef("Wireshark", "tool", "intermediate", ("packet capture", "packet analysis")),
    SkillDef("Burp Suite", "tool", "advanced", ("burpsuite",), ("Penetration Testing",)),
    SkillDef("Metasploit", "tool", "advanced", (), ("Penetration Testing",)),
    SkillDef("Nmap", "tool", "intermediate", ("network mapper",)),
    SkillDef("Splunk", "tool", "advanced", (), ("SIEM",)),
    SkillDef("Altium Designer", "tool", "advanced", ("altium",), ("PCB Design",)),
    SkillDef("KiCad", "tool", "intermediate", ("kicad eda",), ("PCB Design",)),
    SkillDef("Oscilloscope", "tool", "beginner", ("cro", "digital oscilloscope")),
    SkillDef("Google Analytics", "tool", "beginner", ("ga4", "google analytics 4")),
    SkillDef("HubSpot", "tool", "beginner", ()),
    SkillDef("Salesforce", "tool", "intermediate", ("crm", "salesforce crm")),
    SkillDef("Mixpanel", "tool", "intermediate", ("amplitude",)),
    SkillDef("SEMrush", "tool", "beginner", ("ahrefs", "semrush")),
    SkillDef("Canva", "tool", "beginner", ()),

    # -- Cloud platforms and datastores --------------------------------------
    SkillDef("AWS", "platform", "advanced",
             ("amazon web services", "aws cloud", "ec2", "s3", "lambda")),
    SkillDef("Azure", "platform", "advanced", ("microsoft azure", "azure cloud")),
    SkillDef("Google Cloud", "platform", "advanced", ("gcp", "google cloud platform")),
    SkillDef("PostgreSQL", "platform", "intermediate", ("postgres", "psql"), ("SQL",)),
    SkillDef("MySQL", "platform", "beginner", ("my sql", "mariadb"), ("SQL",)),
    SkillDef("MongoDB", "platform", "intermediate", ("mongo", "nosql")),
    SkillDef("Redis", "platform", "intermediate", ()),
    SkillDef("Elasticsearch", "platform", "advanced", ("elastic search", "opensearch")),
    SkillDef("Snowflake", "platform", "advanced", (), ("SQL",)),
    SkillDef("BigQuery", "platform", "intermediate", ("big query", "google bigquery"), ("SQL",)),
    SkillDef("Databricks", "platform", "advanced", (), ("Apache Spark",)),
    SkillDef("Firebase", "platform", "beginner", ()),
    SkillDef("Oracle", "platform", "intermediate", ("oracle db", "pl/sql"), ("SQL",)),
    SkillDef("SQL Server", "platform", "intermediate", ("mssql", "t-sql", "microsoft sql server"), ("SQL",)),

    # -- Concepts ------------------------------------------------------------
    SkillDef("Machine Learning", "concept", "intermediate",
             ("ml", "supervised learning", "unsupervised learning", "predictive modeling"),
             ("Python", "Statistics")),
    SkillDef("Deep Learning", "concept", "advanced",
             ("neural networks", "cnn", "rnn", "transformers"), ("Machine Learning",)),
    SkillDef("Natural Language Processing", "concept", "advanced",
             ("nlp", "text mining", "text analytics"), ("Machine Learning",)),
    SkillDef("Computer Vision", "concept", "advanced",
             ("image processing", "object detection"), ("Deep Learning",)),
    SkillDef("Generative AI", "concept", "advanced",
             ("gen ai", "genai", "generative artificial intelligence", "diffusion models"),
             ("Deep Learning",)),
    SkillDef("Large Language Models", "concept", "advanced",
             ("llm", "llms", "prompt engineering", "fine-tuning"), ("Deep Learning",)),
    SkillDef("RAG", "concept", "advanced",
             ("retrieval augmented generation", "retrieval-augmented generation", "vector database"),
             ("Large Language Models",)),
    SkillDef("MLOps", "concept", "advanced",
             ("ml ops", "model deployment", "model monitoring"), ("Machine Learning", "Docker")),
    SkillDef("Statistics", "concept", "beginner",
             ("statistical analysis", "hypothesis testing", "probability", "regression analysis")),
    SkillDef("Data Structures & Algorithms", "concept", "beginner",
             ("dsa", "data structures", "algorithms")),
    SkillDef("Object-Oriented Programming", "concept", "beginner", ("oop", "oops concepts")),
    SkillDef("System Design", "concept", "advanced",
             ("distributed systems", "scalable systems", "high level design"),
             ("Data Structures & Algorithms",)),
    SkillDef("Microservices", "concept", "advanced", ("micro services", "service oriented architecture"),
             ("REST APIs",)),
    SkillDef("REST APIs", "concept", "beginner", ("rest api", "restful", "api development", "api integration")),
    SkillDef("GraphQL", "concept", "intermediate", ("graph ql",), ("REST APIs",)),
    SkillDef("CI/CD", "concept", "intermediate",
             ("ci cd", "continuous integration", "continuous deployment", "continuous delivery"),
             ("Git",)),
    SkillDef("Agile", "concept", "beginner", ("scrum", "agile methodology", "kanban", "sprint planning")),
    SkillDef("Test-Driven Development", "concept", "intermediate",
             ("tdd", "unit testing", "automated testing", "pytest", "jest")),
    SkillDef("Data Modeling", "concept", "intermediate", ("dimensional modeling", "star schema"), ("SQL",)),
    SkillDef("ETL", "concept", "intermediate", ("etl pipelines", "elt", "data pipelines"), ("SQL",)),
    SkillDef("Data Warehousing", "concept", "advanced", ("data warehouse", "data lake"), ("ETL",)),
    # "reporting" and "charts" were tempting aliases but match almost any
    # business-y sentence; kept out so the percentage stays meaningful.
    SkillDef("Data Visualization", "concept", "beginner",
             ("dashboards", "data storytelling", "dashboarding")),
    SkillDef("A/B Testing", "concept", "intermediate",
             ("ab testing", "experimentation", "split testing"), ("Statistics",)),
    SkillDef("Product Analytics", "concept", "intermediate", ("funnel analysis", "cohort analysis")),
    SkillDef("SEO", "concept", "beginner", ("search engine optimization", "on-page seo")),
    SkillDef("SEM", "concept", "beginner",
             ("search engine marketing", "google ads", "ppc", "paid search")),
    SkillDef("Content Marketing", "concept", "beginner", ("content strategy", "copywriting")),
    SkillDef("Social Media Marketing", "concept", "beginner", ("smm", "social media management")),
    SkillDef("Email Marketing", "concept", "beginner", ("marketing automation", "drip campaigns")),
    SkillDef("Network Security", "concept", "intermediate",
             ("networking", "tcp/ip", "firewalls", "vpn")),
    SkillDef("Penetration Testing", "concept", "advanced",
             ("pen testing", "pentesting", "ethical hacking", "red teaming"), ("Network Security",)),
    SkillDef("Incident Response", "concept", "advanced", ("incident handling", "soc operations")),
    SkillDef("SIEM", "concept", "advanced", ("security information and event management",)),
    SkillDef("Cryptography", "concept", "advanced", ("encryption", "pki", "tls")),
    SkillDef("Vulnerability Assessment", "concept", "intermediate",
             ("vulnerability management", "vapt", "security assessment"), ("Network Security",)),
    SkillDef("Threat Intelligence", "concept", "advanced", ("threat hunting", "malware analysis")),
    SkillDef("Identity & Access Management", "concept", "advanced",
             ("iam", "access control", "rbac", "zero trust")),
    SkillDef("Embedded Systems", "concept", "intermediate",
             ("embedded c", "embedded development", "firmware development"), ("C",)),
    SkillDef("RTOS", "concept", "advanced",
             ("real time operating system", "freertos"), ("Embedded Systems",)),
    SkillDef("Microcontrollers", "concept", "beginner",
             ("mcu", "arduino", "stm32", "esp32", "8051", "raspberry pi")),
    SkillDef("ARM Architecture", "concept", "advanced", ("arm cortex", "cortex-m"), ("Microcontrollers",)),
    SkillDef("PCB Design", "concept", "intermediate", ("pcb layout", "schematic design")),
    SkillDef("Signal Processing", "concept", "advanced", ("dsp", "digital signal processing")),
    SkillDef("Control Systems", "concept", "advanced", ("control theory", "pid control")),
    SkillDef("Circuit Design", "concept", "beginner",
             ("analog circuits", "digital circuits", "circuit analysis")),
    SkillDef("IoT", "concept", "intermediate", ("internet of things", "iot devices")),
    SkillDef("Communication Protocols", "concept", "intermediate",
             ("i2c", "spi", "uart", "can bus", "modbus")),
    SkillDef("FPGA", "concept", "advanced", ("field programmable gate array",), ("Verilog",)),
    SkillDef("Wireframing", "concept", "beginner", ("wireframes", "low fidelity mockups")),
    SkillDef("Prototyping", "concept", "beginner", ("interactive prototypes", "high fidelity prototypes")),
    SkillDef("User Research", "concept", "intermediate",
             ("ux research", "user interviews", "persona development")),
    SkillDef("Usability Testing", "concept", "intermediate", ("user testing",), ("User Research",)),
    SkillDef("Design Systems", "concept", "advanced", ("component library", "style guide")),
    SkillDef("Accessibility", "concept", "intermediate", ("a11y", "wcag", "inclusive design")),
    SkillDef("Interaction Design", "concept", "intermediate", ("ixd", "micro-interactions")),
    SkillDef("Information Architecture", "concept", "intermediate", ("ia", "site mapping")),
    SkillDef("Product Roadmapping", "concept", "intermediate", ("roadmap", "product roadmap")),
    SkillDef("Stakeholder Management", "concept", "intermediate", ("stakeholder communication",)),
    SkillDef("Requirements Gathering", "concept", "beginner",
             ("requirement analysis", "brd", "frd", "user stories")),
    SkillDef("Business Process Modeling", "concept", "intermediate",
             ("process mapping", "bpmn", "gap analysis")),
    SkillDef("Financial Modeling", "concept", "advanced", ("financial analysis", "forecasting")),

    # -- Soft skills ----------------------------------------------------------
    SkillDef("Communication", "soft", "beginner",
             ("communication skills", "verbal communication", "written communication")),
    SkillDef("Problem Solving", "soft", "beginner", ("analytical thinking", "analytical skills")),
    SkillDef("Teamwork", "soft", "beginner", ("collaboration", "team player", "cross-functional")),
    SkillDef("Leadership", "soft", "intermediate", ("team leadership", "people management")),
    SkillDef("Adaptability", "soft", "beginner", ("flexibility", "learning agility")),
    SkillDef("Time Management", "soft", "beginner", ("prioritization", "meeting deadlines")),
    SkillDef("Critical Thinking", "soft", "intermediate", ("logical reasoning",)),
    SkillDef("Attention to Detail", "soft", "beginner", ("detail oriented", "detail-oriented")),
    SkillDef("Ownership", "soft", "intermediate", ("self-driven", "self starter", "proactive")),
    SkillDef("Mentoring", "soft", "advanced", ("coaching", "mentorship")),
    SkillDef("Presentation Skills", "soft", "intermediate", ("presenting", "public speaking")),

    # -- Certifications --------------------------------------------------------
    SkillDef("AWS Certification", "certification", "advanced",
             ("aws certified", "aws certified solutions architect",
              "aws certified cloud practitioner", "aws certification"), ("AWS",)),
    SkillDef("Azure Certification", "certification", "advanced",
             ("az-900", "azure fundamentals", "microsoft certified azure"), ("Azure",)),
    SkillDef("Google Cloud Certification", "certification", "advanced",
             ("google cloud certified", "gcp certification"), ("Google Cloud",)),
    SkillDef("CompTIA Security+", "certification", "intermediate",
             ("security+", "comptia security plus")),
    SkillDef("CEH", "certification", "advanced",
             ("certified ethical hacker",), ("Penetration Testing",)),
    SkillDef("CISSP", "certification", "advanced", ("certified information systems security professional",)),
    SkillDef("OSCP", "certification", "advanced",
             ("offensive security certified professional",), ("Penetration Testing",)),
    SkillDef("CCNA", "certification", "intermediate",
             ("cisco certified network associate",), ("Network Security",)),
    SkillDef("CKA", "certification", "advanced",
             ("certified kubernetes administrator",), ("Kubernetes",)),
    SkillDef("PMP", "certification", "advanced", ("project management professional",)),
    SkillDef("Certified Scrum Master", "certification", "intermediate", ("csm", "scrum master certification"),
             ("Agile",)),
    SkillDef("Six Sigma", "certification", "intermediate", ("lean six sigma", "green belt")),
    SkillDef("Google UX Certificate", "certification", "beginner",
             ("google ux design certificate",), ("User Research",)),

    # -- Other requirements ----------------------------------------------------
    SkillDef("Internship Experience", "other", "beginner",
             ("internship", "internships", "prior internship")),
    SkillDef("Portfolio", "other", "beginner",
             ("portfolio of work", "design portfolio", "github portfolio", "case studies")),
    SkillDef("Open Source Contributions", "other", "intermediate",
             ("open source", "oss contributions", "contributions to open source")),
    SkillDef("Competitive Programming", "other", "intermediate",
             ("codeforces", "leetcode", "hackerrank", "competitive coding")),
    SkillDef("Publications", "other", "advanced",
             ("research papers", "published research", "conference papers")),
    SkillDef("Domain Knowledge", "other", "intermediate",
             ("domain expertise", "industry knowledge", "business acumen")),
    SkillDef("Side Projects", "other", "beginner", ("personal projects", "hobby projects")),
)


# --- Derived lookup structures ------------------------------------------------

BY_CANONICAL: dict[str, SkillDef] = {s.canonical: s for s in CATALOG}
BY_SLUG: dict[str, SkillDef] = {s.slug: s for s in CATALOG}

TIER_ORDER = {"beginner": 0, "intermediate": 1, "advanced": 2}

CATEGORY_LABELS = {
    "language": "Technical Skills",
    "framework": "Technical Skills",
    "concept": "Technical Skills",
    "tool": "Tools & Technologies",
    "platform": "Tools & Technologies",
    "soft": "Soft Skills",
    "certification": "Certifications",
    "education": "Education",
    "experience": "Experience",
    "other": "Other Requirements",
}


def resolve(name: str) -> SkillDef | None:
    """Resolve any surface form to its canonical definition."""
    needle = name.strip().lower()
    for skill in CATALOG:
        if needle == skill.canonical.lower() or needle in {a.lower() for a in skill.aliases}:
            return skill
    return BY_SLUG.get(needle)


def prerequisite_depth(canonical: str, _seen: frozenset[str] = frozenset()) -> int:
    """How many prerequisite layers sit beneath a skill.

    Used to order the roadmap so nothing is suggested before its foundation.
    Cycles are broken by the ``_seen`` guard rather than raising.
    """
    skill = BY_CANONICAL.get(canonical)
    if skill is None or not skill.prerequisites or canonical in _seen:
        return 0
    nxt = _seen | {canonical}
    return 1 + max(prerequisite_depth(p, nxt) for p in skill.prerequisites)
