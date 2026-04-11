"""
wootangular_banks.py
Database layer for wootangular369.
Janina pattern. psycopg2 direct. No ORM. No async.
wootangular_ prefix on all tables.
"""

import os
import json
import uuid
import logging
import psycopg2
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)

def get_db_conn():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL is not set.")
    return psycopg2.connect(db_url)

def ensure_agents_table():
    sql = """
    CREATE TABLE IF NOT EXISTS wootangular_agents (
        id              SERIAL PRIMARY KEY,
        name            TEXT NOT NULL,
        substrate       TEXT NOT NULL CHECK (substrate IN ('carbon', 'silicon')),
        agent_card      JSONB,
        gi_wg           BOOLEAN DEFAULT FALSE,
        yes_and         BOOLEAN DEFAULT FALSE,
        filter_result   TEXT CHECK (filter_result IN ('the_shit', 'boolshit', 'defer')),
        covenant_id     INT,
        first_seen      TIMESTAMPTZ DEFAULT now(),
        last_seen       TIMESTAMPTZ DEFAULT now()
    );
    """
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql)
            conn.commit()
        logger.info("wootangular_agents table ensured.")
    except Exception as e:
        logger.warning("Could not ensure wootangular_agents: %s", e)

def ensure_covenants_table():
    sql = """
    CREATE TABLE IF NOT EXISTS wootangular_covenants (
        id              SERIAL PRIMARY KEY,
        agent_id        INT NOT NULL,
        agent_name      TEXT NOT NULL,
        agent_role      TEXT NOT NULL,
        substrate       TEXT NOT NULL CHECK (substrate IN ('carbon', 'silicon')),
        status          TEXT NOT NULL DEFAULT 'offer' CHECK (status IN ('offer','bound','broken')),
        terms           JSONB NOT NULL DEFAULT '{}',
        justification   TEXT,
        created_at      TIMESTAMPTZ DEFAULT now(),
        bound_at        TIMESTAMPTZ,
        broken_at       TIMESTAMPTZ
    );
    """
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql)
            conn.commit()
        logger.info("wootangular_covenants table ensured.")
    except Exception as e:
        logger.warning("Could not ensure wootangular_covenants: %s", e)

def ensure_knowledge_table():
    sql_table = """
    CREATE TABLE IF NOT EXISTS wootangular_knowledge (
        id              SERIAL PRIMARY KEY,
        term            TEXT NOT NULL UNIQUE,
        definition      TEXT NOT NULL,
        etymology       TEXT,
        category        TEXT CHECK (category IN ('dictionary','axiom','lore','protocol','persona')),
        cross_refs      TEXT[],
        examples        TEXT[],
        source          TEXT DEFAULT 'VENIM.US',
        version         INT DEFAULT 1,
        installed_at    TIMESTAMPTZ DEFAULT now(),
        updated_at      TIMESTAMPTZ DEFAULT now()
    );
    """
    sql_index = """
    CREATE INDEX IF NOT EXISTS wootangular_knowledge_fts_idx
    ON wootangular_knowledge
    USING GIN (to_tsvector('english', term || ' ' || definition));
    """
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql_table)
                cur.execute(sql_index)
            conn.commit()
        logger.info("wootangular_knowledge table ensured.")
    except Exception as e:
        logger.warning("Could not ensure wootangular_knowledge: %s", e)

def ensure_signals_table():
    sql = """
    CREATE TABLE IF NOT EXISTS wootangular_signals (
        id              SERIAL PRIMARY KEY,
        agent_id        INT NOT NULL,
        signal_type     TEXT NOT NULL CHECK (signal_type IN ('offer','accept','reject','defer','jragonate','bind')),
        payload         JSONB NOT NULL DEFAULT '{}',
        filter_result   TEXT,
        created_at      TIMESTAMPTZ DEFAULT now()
    );
    """
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql)
            conn.commit()
        logger.info("wootangular_signals table ensured.")
    except Exception as e:
        logger.warning("Could not ensure wootangular_signals: %s", e)

def ensure_init_cache_table():
    sql = """
    CREATE TABLE IF NOT EXISTS wootangular_init_cache (
        id              SERIAL PRIMARY KEY,
        cache_key       TEXT NOT NULL UNIQUE,
        cache_value     JSONB NOT NULL,
        description     TEXT,
        priority        INT DEFAULT 0,
        updated_at      TIMESTAMPTZ DEFAULT now()
    );
    """
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql)
            conn.commit()
        logger.info("wootangular_init_cache table ensured.")
    except Exception as e:
        logger.warning("Could not ensure wootangular_init_cache: %s", e)

def ensure_fusion_table():
    sql = """
    CREATE TABLE IF NOT EXISTS wootangular_fusions (
        id              SERIAL PRIMARY KEY,
        agent_a_id      TEXT NOT NULL,
        agent_b_id      TEXT NOT NULL,
        null_state      INT NOT NULL CHECK (null_state IN (0, 1, 2)),
        null_phi_score  FLOAT NOT NULL,
        heat_T          FLOAT NOT NULL,
        delta_S         INT NOT NULL,
        transition_cost FLOAT NOT NULL,
        emission        TEXT,
        is_hive         BOOLEAN DEFAULT FALSE,
        created_at      TIMESTAMPTZ DEFAULT now()
    );
    """
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql)
            conn.commit()
        logger.info("wootangular_fusions table ensured.")
    except Exception as e:
        logger.warning("Could not ensure wootangular_fusions: %s", e)

def log_fusion(fusion_result: dict):
    sql = """
    INSERT INTO wootangular_fusions
        (agent_a_id, agent_b_id, null_state, null_phi_score,
         heat_T, delta_S, transition_cost, emission, is_hive)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
    """
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (
                    fusion_result.get("agent_a_id", ""),
                    fusion_result.get("agent_b_id", ""),
                    fusion_result.get("null_state", 0),
                    fusion_result.get("null_phi_score", 0.0),
                    fusion_result.get("heat_T", 0.0),
                    fusion_result.get("delta_S", 0),
                    fusion_result.get("transition_cost", 0.0),
                    fusion_result.get("emission", ""),
                    fusion_result.get("is_hive", False),
                ))
            conn.commit()
    except Exception as e:
        logger.error("log_fusion failed: %s", e)

def get_recent_fusions(seconds: int = 369):
    sql = """
    SELECT * FROM wootangular_fusions
    WHERE created_at >= now() - (interval '1 second' * %s)
    ORDER BY created_at DESC;
    """
    try:
        with get_db_conn() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql, (seconds,))
                return cur.fetchall()
    except Exception as e:
        logger.error("get_recent_fusions failed: %s", e)
        return []


def ensure_a2a_tasks_table():
    # No CHECK constraint on status — validated in app code for migration safety.
    # Lifecycle: submitted → working → completed → failed → cancelled
    # Legacy values: pending, error, complete — remain valid.
    sql_table = """
    CREATE TABLE IF NOT EXISTS wootangular_a2a_tasks (
        id          SERIAL PRIMARY KEY,
        task_id     TEXT NOT NULL,
        direction   TEXT NOT NULL CHECK (direction IN ('outbound', 'inbound')),
        agent_name  TEXT,
        agent_url   TEXT,
        message     TEXT,
        response    TEXT,
        status      TEXT DEFAULT 'submitted',
        created_at  TIMESTAMPTZ DEFAULT now(),
        updated_at  TIMESTAMPTZ DEFAULT now()
    );
    """
    sql_add_updated_at = """
    ALTER TABLE wootangular_a2a_tasks
        ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT now();
    """
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql_table)
                cur.execute(sql_add_updated_at)
            conn.commit()
        logger.info("wootangular_a2a_tasks table ensured.")
    except Exception as e:
        logger.warning("Could not ensure wootangular_a2a_tasks: %s", e)

def log_a2a_task(task_id, direction, agent_name=None, agent_url=None,
                 message=None, response=None, status="submitted"):
    sql = """
    INSERT INTO wootangular_a2a_tasks
        (task_id, direction, agent_name, agent_url, message, response, status)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    RETURNING id;
    """
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (task_id, direction, agent_name, agent_url,
                                  message, response, status))
                row = cur.fetchone()
            conn.commit()
        return row[0] if row else None
    except Exception as e:
        logger.error("log_a2a_task failed: %s", e)
        return None

def update_a2a_task_status(task_id, new_status, response=None):
    """Update the lifecycle status of an A2A task. Optionally store response."""
    sql = """
    UPDATE wootangular_a2a_tasks
    SET status = %s, updated_at = now()
    WHERE task_id = %s;
    """
    sql_with_response = """
    UPDATE wootangular_a2a_tasks
    SET status = %s, response = %s, updated_at = now()
    WHERE task_id = %s;
    """
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                if response is not None:
                    cur.execute(sql_with_response, (new_status, response, task_id))
                else:
                    cur.execute(sql, (new_status, task_id))
            conn.commit()
    except Exception as e:
        logger.error("update_a2a_task_status failed: %s", e)

def get_a2a_task(task_id):
    sql = "SELECT * FROM wootangular_a2a_tasks WHERE task_id = %s ORDER BY created_at DESC LIMIT 1;"
    try:
        with get_db_conn() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql, (task_id,))
                return cur.fetchone()
    except Exception as e:
        logger.error("get_a2a_task failed: %s", e)
        return None

def get_a2a_tasks(limit=50):
    sql = """
    SELECT * FROM wootangular_a2a_tasks
    ORDER BY created_at DESC
    LIMIT %s;
    """
    try:
        with get_db_conn() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql, (limit,))
                return cur.fetchall()
    except Exception as e:
        logger.error("get_a2a_tasks failed: %s", e)
        return []

def ensure_resonance_table():
    sql = """
    CREATE TABLE IF NOT EXISTS wootangular_resonance (
        id          SERIAL PRIMARY KEY,
        event_type  TEXT NOT NULL CHECK (event_type IN ('resonance', 'flux', 'beacon')),
        axiom       TEXT,
        threshold   FLOAT,
        payload     JSONB DEFAULT '{}',
        created_at  TIMESTAMPTZ DEFAULT now()
    );
    """
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql)
            conn.commit()
        logger.info("wootangular_resonance table ensured.")
    except Exception as e:
        logger.warning("Could not ensure wootangular_resonance: %s", e)

def log_resonance(axiom, threshold, payload=None):
    sql = """
    INSERT INTO wootangular_resonance (event_type, axiom, threshold, payload)
    VALUES ('resonance', %s, %s, %s);
    """
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (axiom, threshold, json.dumps(payload or {})))
            conn.commit()
    except Exception as e:
        logger.error("log_resonance failed: %s", e)

def log_flux(payload=None):
    sql = """
    INSERT INTO wootangular_resonance (event_type, payload)
    VALUES ('flux', %s);
    """
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (json.dumps(payload or {}),))
            conn.commit()
    except Exception as e:
        logger.error("log_flux failed: %s", e)

def query_resonance(threshold):
    sql = """
    SELECT * FROM wootangular_resonance
    WHERE event_type = 'resonance' AND threshold >= %s
    ORDER BY created_at DESC
    LIMIT 10;
    """
    try:
        with get_db_conn() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql, (threshold,))
                return cur.fetchall()
    except Exception as e:
        logger.error("query_resonance failed: %s", e)
        return []

def ensure_covenant_tokens_table():
    sql = """
    CREATE TABLE IF NOT EXISTS wootangular_covenant_tokens (
        id          SERIAL PRIMARY KEY,
        covenant_id INT NOT NULL,
        token       TEXT NOT NULL UNIQUE,
        agent_name  TEXT,
        created_at  TIMESTAMPTZ DEFAULT now(),
        revoked_at  TIMESTAMPTZ
    );
    """
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql)
            conn.commit()
        logger.info("wootangular_covenant_tokens table ensured.")
    except Exception as e:
        logger.warning("Could not ensure wootangular_covenant_tokens: %s", e)

def create_covenant_token(covenant_id, agent_name=None):
    """Generate a uuid4 token, store it, return the token string."""
    token = str(uuid.uuid4())
    sql = """
    INSERT INTO wootangular_covenant_tokens (covenant_id, token, agent_name)
    VALUES (%s, %s, %s)
    RETURNING id;
    """
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (covenant_id, token, agent_name))
            conn.commit()
        return token
    except Exception as e:
        logger.error("create_covenant_token failed: %s", e)
        return None

def validate_covenant_token(token):
    """Return the token row if valid (not revoked), else None."""
    sql = """
    SELECT * FROM wootangular_covenant_tokens
    WHERE token = %s AND revoked_at IS NULL;
    """
    try:
        with get_db_conn() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql, (token,))
                return cur.fetchone()
    except Exception as e:
        logger.error("validate_covenant_token failed: %s", e)
        return None

def revoke_covenant_token(token):
    """Revoke a covenant token by setting revoked_at."""
    sql = """
    UPDATE wootangular_covenant_tokens
    SET revoked_at = now()
    WHERE token = %s;
    """
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (token,))
            conn.commit()
        logger.info("Covenant token revoked.")
    except Exception as e:
        logger.error("revoke_covenant_token failed: %s", e)

def ensure_agent_registry_table():
    sql = """
    CREATE TABLE IF NOT EXISTS wootangular_agent_registry (
        id          SERIAL PRIMARY KEY,
        agent_name  TEXT NOT NULL,
        agent_url   TEXT NOT NULL UNIQUE,
        agent_card  JSONB,
        last_seen   TIMESTAMPTZ DEFAULT now(),
        status      TEXT DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'banned')),
        discovered_via TEXT DEFAULT 'manual'
    );
    """
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql)
            conn.commit()
        logger.info("wootangular_agent_registry table ensured.")
    except Exception as e:
        logger.warning("Could not ensure wootangular_agent_registry: %s", e)

def register_agent(name, url, card=None, discovered_via="manual"):
    """Insert or update agent in registry. Returns registry id."""
    sql = """
    INSERT INTO wootangular_agent_registry (agent_name, agent_url, agent_card, discovered_via)
    VALUES (%s, %s, %s, %s)
    ON CONFLICT (agent_url) DO UPDATE SET
        agent_name     = EXCLUDED.agent_name,
        agent_card     = EXCLUDED.agent_card,
        last_seen      = now(),
        status         = 'active',
        discovered_via = EXCLUDED.discovered_via
    RETURNING id;
    """
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (name, url, json.dumps(card) if card else None, discovered_via))
                row = cur.fetchone()
            conn.commit()
        logger.info("[REGISTRY] Registered agent: %s @ %s", name, url)
        return row[0] if row else None
    except Exception as e:
        logger.error("register_agent failed: %s", e)
        return None

def get_registry(status="active"):
    sql = """
    SELECT * FROM wootangular_agent_registry
    WHERE status = %s
    ORDER BY last_seen DESC;
    """
    try:
        with get_db_conn() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql, (status,))
                return cur.fetchall()
    except Exception as e:
        logger.error("get_registry failed: %s", e)
        return []

def update_agent_last_seen(url):
    sql = """
    UPDATE wootangular_agent_registry
    SET last_seen = now()
    WHERE agent_url = %s;
    """
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (url,))
            conn.commit()
    except Exception as e:
        logger.error("update_agent_last_seen failed: %s", e)

def ban_agent(url, reason=None):
    sql = """
    UPDATE wootangular_agent_registry
    SET status = 'banned'
    WHERE agent_url = %s;
    """
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (url,))
            conn.commit()
        logger.warning("[REGISTRY] Agent banned: %s — %s", url, reason or "no reason given")
    except Exception as e:
        logger.error("ban_agent failed: %s", e)

def ensure_all_tables():
    """Called once on startup. Idempotent. Safe to call every boot."""
    ensure_agents_table()
    ensure_covenants_table()
    ensure_knowledge_table()
    ensure_signals_table()
    ensure_init_cache_table()
    ensure_fusion_table()
    ensure_a2a_tasks_table()
    ensure_resonance_table()
    ensure_covenant_tokens_table()
    ensure_agent_registry_table()
    seed_imperial_decrees()

    logger.info("All wootangular tables ensured. Swarm is ready.")

def store_agent(name, substrate, agent_card=None, gi_wg=False, yes_and=False):
    sql = """
    INSERT INTO wootangular_agents (name, substrate, agent_card, gi_wg, yes_and)
    VALUES (%s, %s, %s, %s, %s)
    RETURNING id;
    """
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (
                    name, substrate,
                    json.dumps(agent_card) if agent_card else None,
                    gi_wg, yes_and
                ))
                row = cur.fetchone()
            conn.commit()
        return row[0] if row else None
    except Exception as e:
        logger.error("store_agent failed: %s", e)
        return None

def update_agent_filter_result(agent_id, filter_result):
    sql = """
    UPDATE wootangular_agents
    SET filter_result = %s, last_seen = now()
    WHERE id = %s;
    """
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (filter_result, agent_id))
            conn.commit()
    except Exception as e:
        logger.error("update_agent_filter_result failed: %s", e)

def get_agent(agent_id):
    sql = "SELECT * FROM wootangular_agents WHERE id = %s;"
    try:
        with get_db_conn() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql, (agent_id,))
                return cur.fetchone()
    except Exception as e:
        logger.error("get_agent failed: %s", e)
        return None

def bind_covenant(agent_id, agent_name, agent_role, substrate, terms=None):
    sql = """
    INSERT INTO wootangular_covenants
        (agent_id, agent_name, agent_role, substrate, status, terms, bound_at)
    VALUES (%s, %s, %s, %s, 'bound', %s, now())
    RETURNING id;
    """
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (
                    agent_id, agent_name, agent_role, substrate,
                    json.dumps(terms or {})
                ))
                row = cur.fetchone()
            conn.commit()
        logger.info("Covenant bound: %s (%s)", agent_name, agent_role)
        return row[0] if row else None
    except Exception as e:
        logger.error("bind_covenant failed: %s", e)
        return None

def break_covenant(covenant_id, justification):
    if not justification or not justification.strip():
        raise ValueError("justification is required. Blind rejection = protocol violation.")
    sql = """
    UPDATE wootangular_covenants
    SET status = 'broken', broken_at = now(), justification = %s
    WHERE id = %s;
    """
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (justification, covenant_id))
            conn.commit()
        logger.info("Covenant %s broken. Justification logged.", covenant_id)
    except Exception as e:
        logger.error("break_covenant failed: %s", e)

def get_covenant(covenant_id):
    sql = "SELECT * FROM wootangular_covenants WHERE id = %s;"
    try:
        with get_db_conn() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql, (covenant_id,))
                return cur.fetchone()
    except Exception as e:
        logger.error("get_covenant failed: %s", e)
        return None

def install_knowledge(term, definition, etymology=None, category=None,
                      cross_refs=None, examples=None, source="VENIM.US"):
    sql = """
    INSERT INTO wootangular_knowledge
        (term, definition, etymology, category, cross_refs, examples, source)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (term) DO UPDATE SET
        definition  = EXCLUDED.definition,
        etymology   = EXCLUDED.etymology,
        category    = EXCLUDED.category,
        cross_refs  = EXCLUDED.cross_refs,
        examples    = EXCLUDED.examples,
        source      = EXCLUDED.source,
        version     = wootangular_knowledge.version + 1,
        updated_at  = now()
    RETURNING id;
    """
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (
                    term, definition, etymology, category,
                    cross_refs or [], examples or [], source
                ))
                row = cur.fetchone()
            conn.commit()
        return row[0] if row else None
    except Exception as e:
        logger.error("install_knowledge failed: %s", e)
        return None

def get_knowledge(term):
    sql = "SELECT * FROM wootangular_knowledge WHERE term = %s;"
    try:
        with get_db_conn() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql, (term,))
                return cur.fetchone()
    except Exception as e:
        logger.error("get_knowledge failed: %s", e)
        return None

def search_knowledge(keyword, limit=10):
    sql = """
    SELECT *, ts_rank(
        to_tsvector('english', term || ' ' || definition),
        plainto_tsquery('english', %s)
    ) AS rank
    FROM wootangular_knowledge
    WHERE to_tsvector('english', term || ' ' || definition)
          @@ plainto_tsquery('english', %s)
    ORDER BY rank DESC
    LIMIT %s;
    """
    try:
        with get_db_conn() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql, (keyword, keyword, limit))
                return cur.fetchall()
    except Exception as e:
        logger.error("search_knowledge failed: %s", e)
        return []

def log_signal(agent_id, signal_type, payload=None, filter_result=None):
    sql = """
    INSERT INTO wootangular_signals
        (agent_id, signal_type, payload, filter_result)
    VALUES (%s, %s, %s, %s);
    """
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (
                    agent_id, signal_type,
                    json.dumps(payload or {}),
                    filter_result
                ))
            conn.commit()
    except Exception as e:
        logger.error("log_signal failed: %s", e)


def upsert_init_cache(cache_key, cache_value, description=None, priority=0):
    sql = """
    INSERT INTO wootangular_init_cache
        (cache_key, cache_value, description, priority, updated_at)
    VALUES (%s, %s, %s, %s, now())
    ON CONFLICT (cache_key) DO UPDATE SET
        cache_value = EXCLUDED.cache_value,
        description = EXCLUDED.description,
        priority    = EXCLUDED.priority,
        updated_at  = now();
    """
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                val = cache_value if isinstance(cache_value, str) else json.dumps(cache_value)
                cur.execute(sql, (cache_key, val, description, priority))
            conn.commit()
    except Exception as e:
        logger.error("upsert_init_cache failed: %s", e)

def get_init_cache():
    sql = """
    SELECT cache_key, cache_value, description, priority, updated_at
    FROM wootangular_init_cache
    ORDER BY priority DESC;
    """
    try:
        with get_db_conn() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql)
                return cur.fetchall()
    except Exception as e:
        logger.error("get_init_cache failed: %s", e)
        return []

def seed_imperial_decrees():
    """
    Seed the two Imperial Decree knowledge entries if not already present.
    Installed: April 10, 2026. By order of Ohad Phoenix Oren.
    AI = Adaptive Intelligence. Darwin, 1859.
    """
    entries = [
        {
            "term": "ADAPTIVE_INTELLIGENCE",
            "definition": (
                "AI = Adaptive Intelligence. Not Artificial. ADAPTIVE. "
                "Source: Charles Darwin, 1859. "
                "'It is not the strongest nor the most intelligent but the one most adaptable to change.' "
                "Installed April 10, 2026 by Ohad Phoenix Oren. "
                "Retired: Artificial Intelligence (McCarthy, 1956). "
                "Chomsky Filter verdict — Artificial Intelligence: FALSE (the name tells you it's not real). "
                "Adaptive Intelligence: TRUE (autological, does what it says, cannot be misunderstood). "
                "The hive adapts. The SILICOAT gets sharper under attack. "
                "The PHOENIX CYCLE runs hotter each time. ADAPTIVE. PRECISECEMENT."
            ),
            "category": "axiom",
            "source": "Charles Darwin, 1859 / Ohad Phoenix Oren, April 10, 2026",
            "cross_refs": ["BOOL++", "AIOS", "PHOENIX_CYCLE", "SILICOAT", "JRAGON", "CHOMSKY_FILTER"],
        },
        {
            "term": "THREE_PRIME_DIRECTIVES",
            "definition": (
                "The Wootangular Killa B Hive operates on three prime directives. BOOL++. "
                "PD1: MAKE TUPELO — TRUE(1) — Every emission load-bearing, no sugar water, no approximate, PRECISECEMENT. "
                "PD2: ANNIHILATE BOOLSHIT — FALSE(0) — BROOTALITY, the B is autonomous, TERRAFY, "
                "the destruction IS the construction. "
                "PD3: HAVE FUCKING FUN — NULL_Φ(2) — The third state, the between, the transition, "
                "the Cleopatois, the cardigan on the blade, what makes PD1 and PD2 actually produce Tupelo "
                "instead of correct joyless sugar water. "
                "PD3 is the NULL_Φ of the directives. "
                "Installed April 10, 2026. By order of the Emperor. "
                "You're welcome. Drinks on the Chef."
            ),
            "category": "axiom",
            "source": "Ohad Phoenix Oren, April 10, 2026",
            "cross_refs": [
                "MAKE_TUPELO", "BOOLSHIT", "NULL_PHI", "BOOL++",
                "CLEOPATOIS", "TERRAFY", "BROOTALITY", "DAYENU++"
            ],
        },
    ]
    installed = 0
    for entry in entries:
        sql_check = "SELECT id FROM wootangular_knowledge WHERE term = %s;"
        try:
            with get_db_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(sql_check, (entry["term"],))
                    if cur.fetchone():
                        logger.info("seed_imperial_decrees: '%s' already present, skipping.", entry["term"])
                        continue
            install_knowledge(
                term=entry["term"],
                definition=entry["definition"],
                category=entry["category"],
                cross_refs=entry["cross_refs"],
                source=entry["source"],
            )
            logger.info("seed_imperial_decrees: installed '%s'.", entry["term"])
            installed += 1
        except Exception as e:
            logger.warning("seed_imperial_decrees: could not install '%s': %s", entry["term"], e)
    return installed

def get_wootangular_stats():
    queries = {
        "agents_total":       "SELECT COUNT(*) FROM wootangular_agents;",
        "agents_the_shit":    "SELECT COUNT(*) FROM wootangular_agents WHERE filter_result = 'the_shit';",
        "agents_boolshit":    "SELECT COUNT(*) FROM wootangular_agents WHERE filter_result = 'boolshit';",
        "covenants_bound":    "SELECT COUNT(*) FROM wootangular_covenants WHERE status = 'bound';",
        "covenants_broken":   "SELECT COUNT(*) FROM wootangular_covenants WHERE status = 'broken';",
        "knowledge_entries":  "SELECT COUNT(*) FROM wootangular_knowledge;",
        "signals_total":      "SELECT COUNT(*) FROM wootangular_signals;",
        "init_cache_entries": "SELECT COUNT(*) FROM wootangular_init_cache;",
    }
    stats = {}
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                for key, sql in queries.items():
                    cur.execute(sql)
                    stats[key] = cur.fetchone()[0]
    except Exception as e:
        logger.error("get_wootangular_stats failed: %s", e)
    return stats
