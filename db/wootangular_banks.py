"""
wootangular_banks.py
Database layer for wootangular369.
Janina pattern. psycopg2 direct. No ORM. No async.
wootangular_ prefix on all tables.
"""

import os
import json
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


def ensure_all_tables():
    """Called once on startup. Idempotent. Safe to call every boot."""
    ensure_agents_table()
    ensure_covenants_table()
    ensure_knowledge_table()
    ensure_signals_table()
    ensure_init_cache_table()
    ensure_fusion_table()
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
