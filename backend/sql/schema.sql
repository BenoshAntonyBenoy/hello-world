-- ---------------------------------------------------------------------------
-- hello-world — PostgreSQL schema (production target)
--
-- The application creates these tables automatically through SQLAlchemy, so
-- this file is not required to run the project. It exists as the canonical,
-- reviewable definition of the data model and as the starting point for a
-- migration tool (Alembic) once the schema begins to evolve.
--
--   psql -U postgres -c "CREATE DATABASE helloworld;"
--   psql -U postgres -d helloworld -f sql/schema.sql
-- ---------------------------------------------------------------------------

BEGIN;

-- Where postings come from, and under what legal basis -----------------------
CREATE TABLE job_sources (
    id               SERIAL PRIMARY KEY,
    key              VARCHAR(64)  NOT NULL UNIQUE,
    name             VARCHAR(128) NOT NULL,
    kind             VARCHAR(32)  NOT NULL
                     CHECK (kind IN ('api','licensed_dataset','public_feed',
                                     'user_submitted','synthetic')),
    base_url         VARCHAR(512),
    terms_url        VARCHAR(512),
    requires_license BOOLEAN      NOT NULL DEFAULT FALSE,
    is_enabled       BOOLEAN      NOT NULL DEFAULT TRUE,
    notes            TEXT,
    created_at       TIMESTAMP    NOT NULL DEFAULT NOW()
);

CREATE TABLE companies (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(256) NOT NULL,
    normalized_name VARCHAR(256) NOT NULL UNIQUE,
    industry        VARCHAR(128),
    created_at      TIMESTAMP    NOT NULL DEFAULT NOW()
);

CREATE TABLE roles (
    id         SERIAL PRIMARY KEY,
    slug       VARCHAR(96)  NOT NULL UNIQUE,
    title      VARCHAR(128) NOT NULL,
    category   VARCHAR(64)  NOT NULL,
    summary    TEXT,
    aliases    JSONB        NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMP    NOT NULL DEFAULT NOW()
);

-- The canonical requirement vocabulary --------------------------------------
CREATE TABLE skills (
    id            SERIAL PRIMARY KEY,
    slug          VARCHAR(96)  NOT NULL UNIQUE,
    canonical     VARCHAR(128) NOT NULL,
    category      VARCHAR(32)  NOT NULL
                  CHECK (category IN ('language','framework','tool','platform',
                                      'concept','soft','certification',
                                      'education','experience','other')),
    tier          VARCHAR(16)  NOT NULL DEFAULT 'intermediate'
                  CHECK (tier IN ('beginner','intermediate','advanced')),
    aliases       JSONB        NOT NULL DEFAULT '[]'::jsonb,
    prerequisites JSONB        NOT NULL DEFAULT '[]'::jsonb,
    description   TEXT,
    learn_url     VARCHAR(512)
);

CREATE INDEX ix_skills_category ON skills (category);

-- One normalized posting -----------------------------------------------------
CREATE TABLE jobs (
    id                     SERIAL PRIMARY KEY,
    source_id              INTEGER NOT NULL REFERENCES job_sources (id),
    company_id             INTEGER REFERENCES companies (id),
    role_id                INTEGER REFERENCES roles (id),

    external_id            VARCHAR(128),
    title                  VARCHAR(256) NOT NULL,
    raw_title              VARCHAR(256) NOT NULL,
    location               VARCHAR(128),
    country                VARCHAR(64),
    employment_type        VARCHAR(48),

    description_raw        TEXT NOT NULL,
    description_normalized TEXT NOT NULL,
    content_hash           VARCHAR(64) NOT NULL,
    -- 64-bit simhash as hex; unsigned 64-bit does not fit in a signed BIGINT.
    fingerprint            VARCHAR(16) NOT NULL DEFAULT '0',

    seniority              VARCHAR(32),
    min_years              INTEGER,
    max_years              INTEGER,
    education_level        VARCHAR(48),
    education_fields       JSONB NOT NULL DEFAULT '[]'::jsonb,

    salary_min             INTEGER,
    salary_max             INTEGER,
    salary_currency        VARCHAR(8),
    salary_period          VARCHAR(16),

    url                    VARCHAR(1024),
    posted_at              DATE,
    ingested_at            TIMESTAMP NOT NULL DEFAULT NOW(),

    is_relevant            BOOLEAN NOT NULL DEFAULT TRUE,
    relevance_score        DOUBLE PRECISION NOT NULL DEFAULT 1.0,
    is_duplicate           BOOLEAN NOT NULL DEFAULT FALSE,
    duplicate_of_id        INTEGER REFERENCES jobs (id),

    CONSTRAINT uq_jobs_source_hash UNIQUE (source_id, content_hash)
);

CREATE INDEX ix_jobs_role_posted ON jobs (role_id, posted_at);
CREATE INDEX ix_jobs_relevant    ON jobs (is_relevant, is_duplicate);

-- Requirements extracted from a single posting -------------------------------
CREATE TABLE job_skills (
    id               SERIAL PRIMARY KEY,
    job_id           INTEGER NOT NULL REFERENCES jobs (id) ON DELETE CASCADE,
    skill_id         INTEGER NOT NULL REFERENCES skills (id),
    requirement_type VARCHAR(16) NOT NULL DEFAULT 'required'
                     CHECK (requirement_type IN ('required','preferred','mentioned')),
    mention_count    INTEGER NOT NULL DEFAULT 1,
    confidence       DOUBLE PRECISION NOT NULL DEFAULT 1.0,
    evidence         TEXT,

    CONSTRAINT uq_job_skill UNIQUE (job_id, skill_id)
);

-- Aggregate: how often a skill appears across a role's postings --------------
CREATE TABLE role_skill_statistics (
    id              SERIAL PRIMARY KEY,
    role_id         INTEGER NOT NULL REFERENCES roles (id) ON DELETE CASCADE,
    skill_id        INTEGER NOT NULL REFERENCES skills (id),
    total_jobs      INTEGER NOT NULL,
    jobs_mentioning INTEGER NOT NULL,
    frequency_pct   DOUBLE PRECISION NOT NULL,
    required_pct    DOUBLE PRECISION NOT NULL DEFAULT 0,
    preferred_pct   DOUBLE PRECISION NOT NULL DEFAULT 0,
    confidence      VARCHAR(16) NOT NULL DEFAULT 'medium'
                    CHECK (confidence IN ('high','medium','low')),
    rank            INTEGER NOT NULL DEFAULT 0,
    window_start    DATE,
    window_end      DATE,
    computed_at     TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_role_skill_stat UNIQUE (role_id, skill_id)
);

CREATE INDEX ix_stats_role_freq ON role_skill_statistics (role_id, frequency_pct DESC);

-- Time series for trend detection --------------------------------------------
CREATE TABLE skill_trends (
    id              SERIAL PRIMARY KEY,
    role_id         INTEGER NOT NULL REFERENCES roles (id) ON DELETE CASCADE,
    skill_id        INTEGER NOT NULL REFERENCES skills (id),
    period          CHAR(7) NOT NULL,          -- YYYY-MM
    total_jobs      INTEGER NOT NULL,
    jobs_mentioning INTEGER NOT NULL,
    frequency_pct   DOUBLE PRECISION NOT NULL,

    CONSTRAINT uq_skill_trend UNIQUE (role_id, skill_id, period)
);

-- Anonymous profiles. No email, no name, no login, no PII. -------------------
CREATE TABLE users (
    id             SERIAL PRIMARY KEY,
    token          VARCHAR(64) NOT NULL UNIQUE,
    target_role_id INTEGER REFERENCES roles (id),
    created_at     TIMESTAMP NOT NULL DEFAULT NOW(),
    last_seen_at   TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE user_skills (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    skill_id    INTEGER NOT NULL REFERENCES skills (id),
    proficiency VARCHAR(16) NOT NULL DEFAULT 'working'
                CHECK (proficiency IN ('learning','working','strong')),
    updated_at  TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_user_skill UNIQUE (user_id, skill_id)
);

COMMIT;
