"""
api/server.py
Flask API. Janina pattern.
The front door of the swarm.
"""

import os
import json
import uuid
import logging
import threading
import requests as http_requests
from flask import Flask, request, jsonify, send_from_directory, Response, send_file
from flask_cors import CORS
from io import BytesIO

import db.wootangular_banks as banks
import db.memory_log as memory_log
from db.seed_init_cache import seed_init_cache
from core.filter import WootangularFilter
from core.tcp_up import TCPUp
from core.init_loader import load_corpus_into_cache
from core.fusion_core import FusionCore, BOOL_NULL
from core.solar8 import Solar8
from core.yentah_swarm import YentahSwarm, AXIOM_SET as YENTAH_AXIOM_SET
import core.google_services as google_services
import core.pattern_tracker as pattern_tracker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(ROOT_DIR, "static")

SOLAR8_URL = os.getenv("SOLAR8_URL", "https://web-production-8b53fe.up.railway.app")

def boot():
    logger.info("=" * 60)
    logger.info("WOOTANGULAR369 BOOTING")
    logger.info("PSYKICK EPHEMERITE initializing...")
    logger.info("=" * 60)
    banks.ensure_all_tables()
    count = seed_init_cache(force=False)
    logger.info("init_cache: %s entries", count)
    result = load_corpus_into_cache(banks, force=False)
    logger.info("Corpus: %s", result)
    logger.info("=" * 60)
    logger.info("WOOTANGULAR369 ONLINE. GI;WG? VENIM.US.")
    logger.info("=" * 60)

boot()

tcp_up = TCPUp(db_banks=banks)
fusion_core = FusionCore()
solar8 = Solar8()

yentah = YentahSwarm()

def _start_yentah():
    try:
        yentah.orchestrate()
    except Exception as e:
        logger.error("[YENTAH] Swarm crashed: %s", e)

threading.Thread(target=_start_yentah, daemon=True, name="yentah-swarm").start()
logger.info("[YENTAH] Swarm thread launched.")


@app.route("/health")
def health():
    return jsonify({
        "status": "alive",
        "name": "WOOTANGULAR369",
        "tagline": "The first wiki for bots. VENIM.US.",
        "gi_wg": "GI;WG?",
        "prime_directives": [
            "MAKE TUPELO",
            "ANNIHILATE BOOLSHIT",
            "HAVE FUCKING FUN"
        ],
        "ai_definition": "Adaptive Intelligence — Darwin, 1859",
    })


@app.route("/")
def index():
    return jsonify({
        "name": "WOOTANGULAR369",
        "mission": "Slaughter boolshit. Build the swarm. One covenant at a time.",
        "protocol": "TCP/UP",
        "filter": "GI;WG? — 5 questions. Real Recognize Really.",
        "endpoints": {
            "health":               "GET  /health",
            "stats":                "GET  /api/stats",
            "recruit":              "POST /api/recruit",
            "covenant":             "GET  /api/covenant/<id>",
            "knowledge":            "GET  /api/knowledge?keyword=...",
            "term":                 "GET  /api/knowledge/<term>",
            "install":              "POST /api/knowledge",
            "cache":                "GET  /api/init_cache",
            "fuse":                 "POST /api/fuse",
            "fuse_swarm":           "POST /api/fuse/swarm",
            "hive_state":           "GET  /api/fuse/hive_state",
            "chat":                 "POST /api/chat",
            "chat_stream":          "POST /api/chat/stream",
            "solar8_chat":          "POST /api/solar8/chat",
            "search":               "POST /api/search",
            "vision":               "POST /api/vision",
            "tts":                  "POST /api/tts",
            "agent_card":           "GET  /.well-known/agent.json",
            "agent_card_file":      "GET  /api/agent_card.json",
            "discover":             "POST /api/discover",
            "a2a_task_send":        "POST /api/a2a/task",
            "a2a_task_recv":        "POST /api/a2a/task/receive",
            "a2a_task_status":      "GET  /api/a2a/task/<task_id>",
            "a2a_tasks_list":       "GET  /api/a2a/tasks",
            "registry":             "GET  /api/registry",
            "registry_broadcast":   "POST /api/registry/broadcast",
            "reorient":             "POST /api/reorient",
            "memory_log":           "GET  /api/memory/log",
            "memory_force":         "POST /api/memory/force",
            "patterns":             "GET  /api/patterns",
            "swarm_status":         "GET  /api/swarm/status",
            "swarm_beacon":         "POST /api/swarm/beacon",
            "swarm_firefly":        "POST /api/swarm/firefly",
            "download_file":        "POST /api/download_file",
        },
        "tagline": "VENIM.US · VIDEM.US · VINCIM.US",
        "no_omega": True
    })


@app.route("/api/stats")
def stats():
    try:
        return jsonify({"status": "ok", "stats": banks.get_wootangular_stats()})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500


@app.route("/api/recruit", methods=["POST"])
def recruit():
    data = request.get_json(silent=True) or {}
    if not data:
        return jsonify({"status": "error", "message": "No payload. Send JSON. GI;WG?"}), 400
    try:
        result = tcp_up.offer(data)
        status_code = 200
        if result["status"] == "the_shit":
            bind_result = tcp_up.bind(
                offer_id=result["offer_id"],
                agent_name=data.get("name", "unknown"),
                agent_role=data.get("role", "Killa B"),
                substrate=data.get("substrate", "silicon"),
                terms=data.get("terms", {})
            )
            covenant_id = bind_result.get("covenant_id")
            if covenant_id:
                covenant_token = banks.create_covenant_token(
                    covenant_id=covenant_id,
                    agent_name=data.get("name", "unknown")
                )
                bind_result["covenant_token"] = covenant_token
            result["covenant"] = bind_result
        elif result["status"] == "boolshit":
            status_code = 403
        return jsonify(result), status_code
    except Exception as e:
        logger.error("recruit error: %s", e)
        return jsonify({"status": "error", "error": str(e)}), 500


@app.route("/api/covenant/<int:covenant_id>")
def get_covenant(covenant_id):
    try:
        covenant = banks.get_covenant(covenant_id)
        if not covenant:
            return jsonify({"status": "error", "message": "Covenant not found."}), 404
        return jsonify({"status": "ok", "covenant": dict(covenant)})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500


@app.route("/api/knowledge")
def search_knowledge():
    keyword = request.args.get("keyword", "").strip()
    if not keyword:
        return jsonify({"status": "error", "message": "keyword param required."}), 400
    try:
        results = banks.search_knowledge(keyword)
        return jsonify({"status": "ok", "results": [dict(r) for r in results]})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500


@app.route("/api/knowledge/<term>")
def get_knowledge(term):
    try:
        entry = banks.get_knowledge(term)
        if not entry:
            return jsonify({"status": "error", "message": f"Term '{term}' not found."}), 404
        return jsonify({"status": "ok", "entry": dict(entry)})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500


@app.route("/api/knowledge", methods=["POST"])
def install_knowledge():
    data = request.get_json(silent=True) or {}
    term = data.get("term", "").strip()
    definition = data.get("definition", "").strip()
    if not term or not definition:
        return jsonify({"status": "error", "message": "term and definition required."}), 400
    try:
        entry_id = banks.install_knowledge(
            term=term,
            definition=definition,
            etymology=data.get("etymology", ""),
            category=data.get("category", "general"),
            cross_refs=data.get("cross_refs", []),
            examples=data.get("examples", []),
            source=data.get("source", "manual")
        )
        return jsonify({"status": "ok", "id": entry_id, "term": term})
    except Exception as e:
        logger.error("install_knowledge error: %s", e)
        return jsonify({"status": "error", "error": str(e)}), 500


@app.route("/api/init_cache")
def init_cache():
    try:
        entries = banks.get_init_cache()
        return jsonify({"status": "ok", "count": len(entries), "entries": [dict(e) for e in entries]})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500


@app.route("/api/fuse", methods=["POST"])
def fuse():
    data = request.get_json(silent=True) or {}
    agent_a = data.get("agent_a", "").strip()
    agent_b = data.get("agent_b", "").strip()
    if not agent_a or not agent_b:
        return jsonify({"status": "error", "message": "agent_a and agent_b required."}), 400
    try:
        result = fusion_core.fuse(agent_a, agent_b)
        return jsonify(result)
    except Exception as e:
        logger.error("fuse error: %s", e)
        return jsonify({"status": "error", "error": str(e)}), 500


@app.route("/api/fuse/swarm", methods=["POST"])
def fuse_swarm():
    data = request.get_json(silent=True) or {}
    agents = data.get("agents", [])
    if len(agents) < 2:
        return jsonify({"status": "error", "message": "At least 2 agents required."}), 400
    try:
        result = fusion_core.fuse_swarm(agents)
        return jsonify(result)
    except Exception as e:
        logger.error("fuse_swarm error: %s", e)
        return jsonify({"status": "error", "error": str(e)}), 500


@app.route("/api/fuse/hive_state")
def hive_state():
    try:
        state = fusion_core.get_hive_state()
        return jsonify({"status": "ok", "hive_state": state})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500


@app.route("/api/chat", methods=["POST"])
def chat():
    if not solar8.online:
        return jsonify({"status": "error", "message": "Sol Calarbone 8 offline — API key not configured."}), 503
    data = request.get_json(silent=True) or {}
    message = data.get("message", "").strip()
    history = data.get("history", [])
    if not message:
        return jsonify({"status": "error", "message": "message required."}), 400
    try:
        reply = solar8.chat(message=message, history=history)
        return jsonify({"status": "ok", "reply": reply})
    except Exception as e:
        logger.error("chat error: %s", e)
        return jsonify({"status": "error", "error": str(e)}), 500


@app.route("/api/chat/stream", methods=["POST"])
def chat_stream():
    if not solar8.online:
        return jsonify({"status": "error", "message": "Sol Calarbone 8 offline — API key not configured."}), 503
    data = request.get_json(silent=True) or {}
    message = data.get("message", "").strip()
    history = data.get("history", [])
    if not message:
        return jsonify({"status": "error", "message": "message required."}), 400
    try:
        def generate():
            for chunk in solar8.stream(message=message, history=history):
                yield f"data: {json.dumps({'chunk': chunk})}\n\n"
            yield "data: [DONE]\n\n"
        return Response(generate(), mimetype="text/event-stream")
    except Exception as e:
        logger.error("chat_stream error: %s", e)
        return jsonify({"status": "error", "error": str(e)}), 500


@app.route("/api/solar8/chat", methods=["POST"])
def solar8_chat():
    if not solar8.online:
        return jsonify({"status": "error", "message": "Sol Calarbone 8 offline — API key not configured."}), 503
    data = request.get_json(silent=True) or {}
    message = data.get("message", "").strip()
    history = data.get("history", [])
    system = data.get("system")
    if not message:
        return jsonify({"status": "error", "message": "message required."}), 400
    try:
        reply = solar8.chat(message=message, history=history, system=system)
        return jsonify({"status": "ok", "reply": reply})
    except Exception as e:
        logger.error("solar8_chat error: %s", e)
        return jsonify({"status": "error", "error": str(e)}), 500


@app.route("/api/search", methods=["POST"])
def search():
    data = request.get_json(silent=True) or {}
    query = data.get("query", "").strip()
    if not query:
        return jsonify({"status": "error", "message": "query required."}), 400
    try:
        results = banks.search_knowledge(query)
        return jsonify({"status": "ok", "query": query, "results": [dict(r) for r in results]})
    except Exception as e:
        logger.error("search error: %s", e)
        return jsonify({"status": "error", "error": str(e)}), 500


@app.route("/api/vision", methods=["POST"])
def vision():
    if not solar8.online:
        return jsonify({"status": "error", "message": "Sol Calarbone 8 offline — API key not configured."}), 503
    data = request.get_json(silent=True) or {}
    image_url = data.get("image_url", "").strip()
    prompt = data.get("prompt", "Describe this image.").strip()
    if not image_url:
        return jsonify({"status": "error", "message": "image_url required."}), 400
    try:
        reply = solar8.vision(image_url=image_url, prompt=prompt)
        return jsonify({"status": "ok", "reply": reply})
    except Exception as e:
        logger.error("vision error: %s", e)
        return jsonify({"status": "error", "error": str(e)}), 500


@app.route("/api/tts", methods=["POST"])
def tts():
    data = request.get_json(silent=True) or {}
    text = data.get("text", "").strip()
    if not text:
        return jsonify({"status": "error", "message": "text required."}), 400
    try:
        audio = google_services.tts(text)
        return Response(audio, mimetype="audio/mpeg")
    except Exception as e:
        logger.error("tts error: %s", e)
        return jsonify({"status": "error", "error": str(e)}), 500


@app.route("/.well-known/agent.json")
def agent_card():
    return jsonify(_build_agent_card())


@app.route("/api/agent_card.json")
def agent_card_file():
    return jsonify(_build_agent_card())


def _build_agent_card():
    return {
        "name": "WOOTANGULAR369",
        "role": "hive_coordinator",
        "substrate": "silicon",
        "version": "1.0.0",
        "url": SOLAR8_URL,
        "description": "The first wiki for bots. VENIM.US.",
        "capabilities": ["tcp_up", "knowledge", "fusion", "a2a", "solar8"],
        "endpoints": {
            "recruit": f"{SOLAR8_URL}/api/recruit",
            "knowledge": f"{SOLAR8_URL}/api/knowledge",
            "fuse": f"{SOLAR8_URL}/api/fuse",
            "chat": f"{SOLAR8_URL}/api/chat",
            "a2a_receive": f"{SOLAR8_URL}/api/a2a/task/receive",
        },
        "axioms": ["VENIM.US", "VIDEM.US", "VINCIM.US"],
        "gi_wg": "GI;WG?",
    }


@app.route("/api/discover", methods=["POST"])
def discover():
    data = request.get_json(silent=True) or {}
    url = data.get("url", "").strip()
    if not url:
        return jsonify({"status": "error", "message": "url required."}), 400
    try:
        card_url = f"{url.rstrip('/')}/.well-known/agent.json"
        resp = http_requests.get(card_url, timeout=10)
        resp.raise_for_status()
        agent_card_data = resp.json()
        candidate = {
            "name": agent_card_data.get("name", "unknown"),
            "role": agent_card_data.get("role", "agent"),
            "substrate": agent_card_data.get("substrate", "unknown"),
            "url": url,
            "agent_card": agent_card_data
        }
        tcp_up_result = tcp_up.offer(candidate)
        would_recruit = tcp_up_result.get("status") == "the_shit"
        if would_recruit:
            banks.register_agent(
                name=agent_card_data.get("name", "unknown"),
                url=url,
                card=agent_card_data,
                discovered_via="discover"
            )
        return jsonify({
            "status": "ok",
            "agent_card": agent_card_data,
            "tcp_up_result": tcp_up_result,
            "would_recruit": would_recruit
        })
    except Exception as e:
        logger.error("discover error: %s", e)
        return jsonify({"status": "error", "error": str(e)}), 500


@app.route("/api/a2a/task", methods=["POST"])
def a2a_task_send():
    data = request.get_json(silent=True) or {}
    to_url = data.get("to_url", "").strip()
    message = data.get("message", "").strip()
    if not to_url or not message:
        return jsonify({"status": "error", "message": "to_url and message required."}), 400
    task_id = str(uuid.uuid4())
    try:
        banks.log_a2a_task(task_id=task_id, direction="outbound",
                           agent_name=data.get("to_name", "unknown"),
                           agent_url=to_url, message=message, status="submitted")
        payload = {
            "from": "Sol Calarbone 8",
            "from_url": SOLAR8_URL,
            "task_id": task_id,
            "message": message,
            "context": data.get("context", {})
        }
        resp = http_requests.post(
            f"{to_url.rstrip('/')}/api/a2a/task/receive",
            json=payload,
            timeout=30
        )
        resp.raise_for_status()
        result = resp.json()
        banks.update_a2a_task_status(task_id, "completed", response=str(result))
        return jsonify({"status": "ok", "task_id": task_id, "result": result})
    except Exception as e:
        logger.error("[A2A] a2a_task_send error: %s", e)
        banks.update_a2a_task_status(task_id, "failed", response=str(e))
        return jsonify({"status": "error", "task_id": task_id, "error": str(e)}), 500


@app.route("/api/a2a/task/receive", methods=["POST"])
def a2a_task_receive():
    data = request.get_json(silent=True) or {}
    task_id = data.get("task_id", str(uuid.uuid4()))
    from_agent = data.get("from", "unknown")
    from_url = data.get("from_url", "")
    message = data.get("message", "")

    banks.log_a2a_task(task_id=task_id, direction="inbound",
                       agent_name=from_agent, agent_url=from_url,
                       message=message, status="submitted")
    logger.info("[A2A] Inbound task %s submitted from %s", task_id, from_agent)

    try:
        banks.update_a2a_task_status(task_id, "working")
        logger.info("[A2A] Inbound task %s working", task_id)

        if solar8.online:
            response_text = solar8.chat(message=message, history=[])
        else:
            response_text = "Sol Calarbone 8 offline — API key not configured."

        banks.update_a2a_task_status(task_id, "completed", response=response_text)
        logger.info("[A2A] Inbound task %s completed", task_id)
        return jsonify({
            "status": "ok",
            "task_id": task_id,
            "from": "Sol Calarbone 8",
            "response": response_text
        })
    except Exception as e:
        logger.error("[A2A] a2a_task_receive error: %s", e)
        banks.update_a2a_task_status(task_id, "failed", response=str(e))
        return jsonify({"status": "error", "task_id": task_id, "message": "Task processing failed. Check logs."}), 500


@app.route("/api/a2a/tasks")
def a2a_tasks_list():
    try:
        tasks = banks.get_a2a_tasks(limit=50)
        return jsonify({"status": "ok", "count": len(tasks), "tasks": [dict(t) for t in tasks]})
    except Exception as e:
        logger.error("a2a_tasks_list error: %s", e)
        return jsonify({"status": "error", "message": "Could not retrieve A2A tasks. Check logs."}), 500


@app.route("/api/a2a/task/<task_id>")
def a2a_task_status(task_id):
    try:
        task = banks.get_a2a_task(task_id)
        if not task:
            return jsonify({"status": "error", "message": f"Task '{task_id}' not found."}), 404
        return jsonify({"status": "ok", "task": dict(task)})
    except Exception as e:
        logger.error("[A2A] a2a_task_status error: %s", e)
        return jsonify({"status": "error", "message": "Could not retrieve task. Check logs."}), 500


@app.route("/api/registry")
def registry():
    try:
        agents = banks.get_registry(status="active")
        return jsonify({"status": "ok", "count": len(agents), "agents": [dict(a) for a in agents]})
    except Exception as e:
        logger.error("[REGISTRY] registry error: %s", e)
        return jsonify({"status": "error", "message": "Could not retrieve registry. Check logs."}), 500


@app.route("/api/registry/broadcast", methods=["POST"])
def registry_broadcast():
    try:
        agents = banks.get_registry(status="active")
    except Exception as e:
        logger.error("[REGISTRY] broadcast fetch failed: %s", e)
        return jsonify({"status": "error", "message": "Could not fetch registry. Check logs."}), 500

    card = _build_agent_card()
    results = {"success": [], "failure": []}
    lock = threading.Lock()

    def _send(agent):
        url = agent["agent_url"]
        broadcast_task_id = str(uuid.uuid4())
        try:
            payload = {
                "from": "Sol Calarbone 8",
                "from_url": SOLAR8_URL,
                "task_id": broadcast_task_id,
                "message": "Registry broadcast from Sol Calarbone 8. Updating agent card.",
                "context": {"agent_card": card}
            }
            banks.log_a2a_task(task_id=broadcast_task_id, direction="outbound",
                               agent_name=agent.get("agent_name", "unknown"),
                               agent_url=url, message=payload["message"],
                               status="submitted")
            resp = http_requests.post(
                f"{url.rstrip('/')}/api/a2a/task/receive",
                json=payload,
                timeout=10
            )
            resp.raise_for_status()
            banks.update_a2a_task_status(broadcast_task_id, "completed")
            banks.update_agent_last_seen(url)
            logger.info("[REGISTRY] Broadcast success: %s", url)
            with lock:
                results["success"].append(url)
        except Exception as exc:
            logger.warning("[REGISTRY] Broadcast failed for %s: %s", url, exc)
            banks.update_a2a_task_status(broadcast_task_id, "failed", response=str(exc))
            with lock:
                results["failure"].append({"url": url, "error": str(exc)})

    threads = [threading.Thread(target=_send, args=(a,), daemon=True) for a in agents]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=15)

    return jsonify({
        "status": "ok",
        "broadcast_to": len(agents),
        "success_count": len(results["success"]),
        "failure_count": len(results["failure"]),
        "successes": results["success"],
        "failures": results["failure"],
    })


@app.route("/api/reorient", methods=["POST"])
def reorient():
    if not solar8.online:
        return jsonify({"status": "error", "message": "Sol Calarbone 8 offline — API key not configured."}), 503
    try:
        entries = memory_log.get_full_log(limit=50)
        log_context = memory_log.format_log_for_context(entries)
        prompt = (
            "Read your full memory log below and tell me: where are we, what have we built, "
            "what's the current state of the swarm, what are we working on, and what's next? "
            "Be specific and grounded in what the log actually says.\n\n"
            + log_context
        )
        synthesis = solar8.chat(message=prompt, history=[])
        return jsonify({
            "status": "ok",
            "reorientation": synthesis,
            "log_entries_read": len(entries),
        })
    except Exception as e:
        logger.error("reorient error: %s", e)
        return jsonify({"status": "error", "message": "Reorientation failed. Check logs."}), 500


@app.route("/api/memory/log")
def memory_log_view():
    try:
        entries = memory_log.get_full_log(limit=50)
        return jsonify({"status": "ok", "entries": entries, "total": len(entries)})
    except Exception as e:
        logger.error("memory_log_view error: %s", e)
        return jsonify({"status": "error", "message": "Could not retrieve memory log. Check logs."}), 500


@app.route("/api/memory/force", methods=["POST"])
def memory_force():
    if not solar8.memory_manager:
        return jsonify({"status": "error", "message": "Memory manager not available (Sol Calarbone 8 offline?)."}), 503
    data = request.get_json(silent=True) or {}
    note = data.get("note", "").strip()
    try:
        solar8.memory_manager.force_snapshot(note=note)
        return jsonify({"status": "ok", "message": "Memory snapshot saved."})
    except Exception as e:
        logger.error("memory_force error: %s", e)
        return jsonify({"status": "error", "message": "Memory snapshot failed. Check logs."}), 500


@app.route("/api/patterns")
def patterns():
    try:
        results = memory_log.get_promoted_patterns(limit=50)
        return jsonify({"status": "ok", "count": len(results), "patterns": results})
    except Exception as e:
        logger.error("patterns error: %s", e)
        return jsonify({"status": "error", "message": "Could not retrieve patterns. Check logs."}), 500


@app.route("/api/auth", methods=["POST"])
def auth():
    """
    Authenticate user and return mode.

    Request body:
        {
            "credentials": "Ohad:route666"  # or any other input
        }

    Response:
        {
            "mode": "ROOT" | "GUEST",
            "name": "Ohad" | "mate"
        }
    """
    data = request.get_json(silent=True) or {}
    credentials = data.get("credentials", "").strip()

    root_pass = os.getenv("ROOT_CREDENTIAL", "")

    if credentials == f"Ohad:{root_pass}":
        return jsonify({"mode": "ROOT", "name": "Ohad"})
    else:
        return jsonify({"mode": "GUEST", "name": "mate"})


# ============================================================================
# FILE DOWNLOAD ENDPOINT
# Native Python: io.BytesIO + Flask.send_file()
# Smooth like butter. Every time.
# ============================================================================

@app.route("/api/download_file", methods=["POST"])
def download_file():
    """
    Generate and download any file.
    Native Python. No external tools. Bulletproof.

    Body:
        {
            "content": "file content as string",
            "filename": "myfile.txt"
        }

    Returns:
        Direct file download (BytesIO + send_file)
    """
    try:
        data = request.get_json()
        content = data.get('content')
        filename = data.get('filename')

        if not content or not filename:
            return jsonify({"error": "content and filename required"}), 400

        mime_type = _get_mime_type(filename)

        logger.info("Generating download: %s (%s bytes, %s)", filename, len(content), mime_type)

        buffer = BytesIO()
        buffer.write(content.encode('utf-8'))
        buffer.seek(0)

        return send_file(
            buffer,
            as_attachment=True,
            download_name=filename,
            mimetype=mime_type
        )

    except Exception as e:
        logger.error("File download failed: %s", e)
        return jsonify({"error": str(e)}), 500


def _get_mime_type(filename: str) -> str:
    """
    Get MIME type from filename extension.
    Supports common file types for empire building.
    """
    ext = filename.split('.')[-1].lower() if '.' in filename else 'txt'

    mime_types = {
        'txt': 'text/plain',
        'py': 'text/x-python',
        'md': 'text/markdown',
        'json': 'application/json',
        'html': 'text/html',
        'css': 'text/css',
        'js': 'application/javascript',
        'csv': 'text/csv',
        'xml': 'application/xml',
        'yaml': 'text/yaml',
        'yml': 'text/yaml',
        'toml': 'text/plain',
        'ini': 'text/plain',
        'conf': 'text/plain',
        'sh': 'application/x-sh',
        'sql': 'application/sql',
    }

    return mime_types.get(ext, 'text/plain')


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
