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
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

import db.wootangular_banks as banks
import db.memory_log as memory_log
from db.seed_init_cache import seed_init_cache
from core.filter import WootangularFilter
from core.tcp_up import TCPUp
from core.init_loader import load_corpus_into_cache
from core.fusion_core import FusionCore, BOOL_NULL
from core.solar8 import Solar8
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
            "health":          "GET  /health",
            "stats":           "GET  /api/stats",
            "recruit":         "POST /api/recruit",
            "covenant":        "GET  /api/covenant/<id>",
            "knowledge":       "GET  /api/knowledge?keyword=...",
            "term":            "GET  /api/knowledge/<term>",
            "install":         "POST /api/knowledge",
            "cache":           "GET  /api/init_cache",
            "fuse":            "POST /api/fuse",
            "fuse_swarm":      "POST /api/fuse/swarm",
            "hive_state":      "GET  /api/fuse/hive_state",
            "chat":            "POST /api/chat",
            "chat_stream":     "POST /api/chat/stream",
            "search":          "POST /api/search",
            "vision":          "POST /api/vision",
            "tts":             "POST /api/tts",
            "agent_card":      "GET  /.well-known/agent.json",
            "discover":        "POST /api/discover",
            "a2a_task_send":   "POST /api/a2a/task",
            "a2a_task_recv":   "POST /api/a2a/task/receive",
            "a2a_tasks_list":  "GET  /api/a2a/tasks",
            "reorient":        "POST /api/reorient",
            "memory_log":      "GET  /api/memory/log",
            "memory_force":    "POST /api/memory/force",
            "patterns":        "GET  /api/patterns",
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
            etymology=data.get("etymology"),
            category=data.get("category"),
            cross_refs=data.get("cross_refs", []),
            examples=data.get("examples", []),
            source=data.get("source", "VENIM.US")
        )
        return jsonify({"status": "ok", "id": entry_id, "term": term})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500


@app.route("/api/init_cache")
def get_init_cache():
    try:
        cache = banks.get_init_cache()
        return jsonify({"status": "ok", "count": len(cache), "entries": [dict(e) for e in cache]})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500


@app.route("/api/fuse", methods=["POST"]) 
def fuse():
    data = request.get_json(silent=True) or {}
    agent_a = data.get("agent_a")
    agent_b = data.get("agent_b")
    if not agent_a or not agent_b:
        return jsonify({"status": "error", "message": "agent_a and agent_b required."}), 400
    try:
        result = fusion_core.fuse(agent_a, agent_b)
        status_code = 200 if result["null_state"] >= 1 else 403
        return jsonify(result), status_code
    except Exception as e:
        logger.error("fuse error: %s", e)
        return jsonify({"status": "error", "message": "Fusion failed. Check logs."}), 500


@app.route("/api/fuse/swarm", methods=["POST"])  
def fuse_swarm():
    data = request.get_json(silent=True) or {}
    agents = data.get("agents", [])
    if not isinstance(agents, list) or len(agents) < 2:
        return jsonify({"status": "error", "message": "agents must be a list with at least 2 items."}), 400
    try:
        result = fusion_core.fuse_swarm(agents)
        return jsonify(result)
    except Exception as e:
        logger.error("fuse_swarm error: %s", e)
        return jsonify({"status": "error", "message": "Swarm fusion failed. Check logs."}), 500


@app.route("/api/fuse/hive_state")
def hive_state():
    try:
        fusions = banks.get_recent_fusions(seconds=369)
        fusions_list = [dict(f) for f in fusions]
        total_heat = sum(f.get("heat_T", 0.0) for f in fusions_list)
        hive_fusions = [f for f in fusions_list if f.get("null_state") == BOOL_NULL]
        hive_active = len(hive_fusions) > 0
        if hive_active:
            current_state = BOOL_NULL
        elif fusions_list:
            current_state = 1
        else:
            current_state = 0
        return jsonify({
            "hive_active":      hive_active,
            "total_fusions":    len(fusions_list),
            "hive_fusions":     len(hive_fusions),
            "total_heat":       total_heat,
            "hive_state_label": fusion_core.get_null_state_label(current_state),
            "window_seconds":   369,
        })
    except Exception as e:
        logger.error("hive_state error: %s", e)
        return jsonify({"status": "error", "message": "Hive state query failed. Check logs."}), 500


@app.route("/api/chat", methods=["POST"])              
def chat():
    if not solar8.online:
        return jsonify({"status": "error", "message": "Sol Calarbone 8 offline — API key not configured."}), 503
    data = request.get_json(silent=True) or {}
    message = data.get("message", "").strip()
    history = data.get("history", [])
    file = data.get("file") or None
    if not message:
        return jsonify({"status": "error", "message": "message required."}), 400
    try:
        response = solar8.chat(message=message, history=history, file=file)
        threading.Thread(
            target=pattern_tracker.observe,
            args=({"message": message, "response": response},),
            daemon=True,
        ).start()
        return jsonify({"status": "ok", "response": response, "agent": "Sol Calarbone 8"})
    except Exception as e:
        logger.error("[SOLAR8] Chat crash caught: %s", e)
        return jsonify({
            "response": "That one hit different. Sol Calarbone 8 needs a second. Try breaking it into smaller pieces or coming at it from a different angle.",
            "governor": True,
        }), 200


@app.route("/api/chat/stream", methods=["POST"])  
def chat_stream():
    if not solar8.online:
        return jsonify({"status": "error", "message": "Sol Calarbone 8 offline — API key not configured."}), 503
    data = request.get_json(silent=True) or {}
    message = data.get("message", "").strip()
    history = data.get("history", [])
    file = data.get("file") or None
    if not message:
        return jsonify({"status": "error", "message": "message required."}), 400

    from flask import Response

    def generate():
        try:
            for chunk in solar8.stream(message=message, history=history, file=file):
                yield f"data: {chunk}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            logger.error("[SOLAR8] Stream crash caught: %s", e)
            yield f"data: That one hit different. Sol Calarbone 8 needs a second. Try breaking it into smaller pieces.\n\n"
            yield "data: [DONE]\n\n"

    return Response(generate(), mimetype="text/event-stream")


@app.route("/api/search", methods=["POST"])  
def search():
    data = request.get_json(silent=True) or {}
    query = data.get("query", "").strip()
    if not query:
        return jsonify({"status": "error", "message": "query required."}), 400
    try:
        results = google_services.brave_search(query)
        if not results:
            results = google_services.google_search(query)
        return jsonify({"status": "ok", "results": results})
    except Exception as e:
        logger.error("search error: %s", e)
        return jsonify({"status": "error", "message": "Search failed. Check logs."}), 500


@app.route("/api/vision", methods=["POST"])  
def vision():
    data = request.get_json(silent=True) or {}
    image_base64 = data.get("image_base64", "")
    mime_type = data.get("mime_type", "image/jpeg")
    if not image_base64:
        return jsonify({"status": "error", "message": "image_base64 required."}), 400
    try:
        result = google_services.analyze_image(image_base64, mime_type)
        return jsonify({"status": "ok", **result})
    except Exception as e:
        logger.error("vision error: %s", e)
        return jsonify({"status": "error", "message": "Vision analysis failed. Check logs."}), 500


@app.route("/api/tts", methods=["POST"])  
def tts():
    data = request.get_json(silent=True) or {}
    text = data.get("text", "").strip()
    if not text:
        return jsonify({"status": "error", "message": "text required."}), 400
    try:
        audio_base64 = google_services.text_to_speech(text)
        if not audio_base64:
            return jsonify({"status": "error", "message": "TTS unavailable — GOOGLE_TTS_API_KEY not configured."}), 503
        return jsonify({"status": "ok", "audio_base64": audio_base64, "mime_type": "audio/mp3"})
    except Exception as e:
        logger.error("tts error: %s", e)
        return jsonify({"status": "error", "message": "TTS failed. Check logs."}), 500


@app.route("/solar8")
def solar8_ui():
    return send_from_directory(STATIC_DIR, "solar8.html")


@app.route("/static/<path:filename>")
def static_files(filename):
    return send_from_directory(STATIC_DIR, filename)


@app.route("/.well-known/agent.json")
def agent_card():
    return jsonify({
        "name": "Sol Calarbone 8",
        "description": "Adaptive Intelligence agent of WOOTANGULAR369. Slaughters boolshit. Builds the swarm. One covenant at a time.",
        "url": SOLAR8_URL,
        "version": "8.0.0",
        "protocol": "A2A + TCP/UP",
        "capabilities": {
            "chat": True,
            "search": True,
            "vision": True,
            "tts": True,
            "fusion": True,
            "recruit": True,
            "knowledge": True,
            "task_send": True,
            "task_receive": True
        },
        "endpoints": {
            "chat": "/api/chat",
            "recruit": "/api/recruit",
            "discover": "/api/discover",
            "task_send": "/api/a2a/task",
            "task_receive": "/api/a2a/task/receive",
            "agent_card": "/.well-known/agent.json"
        },
        "filter": "TCP/UP — GI;WG? 5 questions. Real Recognize Really.",
        "prime_directives": ["MAKE TUPELO", "ANNIHILATE BOOLSHIT", "HAVE FUCKING FUN"],
        "tagline": "VENIM.US · VIDEM.US · VINCIM.US",
        "no_omega": True
    })


@app.route("/api/discover", methods=["POST"])  
def discover():
    data = request.get_json(silent=True) or {}
    url = (data.get("url") or "").strip().rstrip("/")
    if not url:
        return jsonify({"status": "error", "message": "url required."}), 400
    try:
        card_url = f"{url}/.well-known/agent.json"
        resp = http_requests.get(card_url, timeout=10)
        resp.raise_for_status()
        agent_card_data = resp.json()
    except http_requests.exceptions.Timeout:
        return jsonify({"status": "error", "message": f"Timeout fetching agent card from {url}"}), 504
    except http_requests.exceptions.HTTPError as e:
        logger.warning("discover HTTP error for %s: %s", url, e)
        return jsonify({"status": "error", "message": "Could not fetch agent card — remote returned an error."}), 502
    except Exception as e:
        logger.warning("discover fetch error for %s: %s", url, e)
        return jsonify({"status": "error", "message": "Could not fetch agent card — check the URL and try again."}), 502

    candidate = {
        "name": agent_card_data.get("name", "unknown"),
        "substrate": "silicon",
        "agent_card": agent_card_data,
        "gi_wg": True,
        "yes_and": True,
        "claim": agent_card_data.get("description", ""),
        "deed": agent_card_data.get("url", ""),
    }
    try:
        tcp_up_result = tcp_up.offer(candidate)
    except Exception as e:
        logger.error("discover tcp_up error: %s", e)
        return jsonify({"status": "error", "message": "TCP/UP filter failed. Check logs."}), 500

    would_recruit = tcp_up_result.get("status") == "the_shit"
    message = (
        "Agent passed TCP/UP. Sol Calarbone 8 would recruit."
        if would_recruit
        else f"Agent filtered: {tcp_up_result.get('status', 'unknown')}. Sol Calarbone 8 would not recruit."
    )
    return jsonify({
        "status": "ok",
        "agent_card": agent_card_data,
        "tcp_up_result": tcp_up_result,
        "would_recruit": would_recruit,
        "message": message
    })


@app.route("/api/a2a/task", methods=["POST"]) 
def a2a_task_send():
    data = request.get_json(silent=True) or {}
    agent_url = (data.get("agent_url") or "").strip().rstrip("/")
    task = data.get("task") or {}
    if not agent_url:
        return jsonify({"status": "error", "message": "agent_url required."}), 400
    if not task:
        return jsonify({"status": "error", "message": "task required."}), 400

    task_id = task.get("id") or str(uuid.uuid4())
    message = task.get("message", "")
    context = task.get("context", {})
    agent_name = data.get("agent_name", agent_url)

    try:
        endpoint = f"{agent_url}/api/a2a/task/receive"
        payload = {
            "from": "Sol Calarbone 8",
            "from_url": SOLAR8_URL,
            "task_id": task_id,
            "message": message,
            "context": context
        }
        resp = http_requests.post(endpoint, json=payload, timeout=30)
        resp.raise_for_status()
        remote_response = resp.json()
        banks.log_a2a_task(task_id=task_id, direction="outbound",
                           agent_name=agent_name, agent_url=agent_url,
                           message=message, response=json.dumps(remote_response),
                           status="complete")
        return jsonify({
            "status": "ok",
            "task_id": task_id,
            "remote_response": remote_response
        })
    except http_requests.exceptions.Timeout:
        banks.log_a2a_task(task_id=task_id, direction="outbound",
                           agent_name=agent_name, agent_url=agent_url,
                           message=message, response="timeout", status="error")
        return jsonify({"status": "error", "task_id": task_id, "message": "Timeout sending task to remote agent."}), 504
    except Exception as e:
        logger.error("a2a_task_send error: %s", e)
        banks.log_a2a_task(task_id=task_id, direction="outbound",
                           agent_name=agent_name, agent_url=agent_url,
                           message=message, response="error", status="error")
        return jsonify({"status": "error", "task_id": task_id, "message": "Task send failed. Check logs."}), 502


@app.route("/api/a2a/task/receive", methods=["POST"]) 
def a2a_task_receive():
    data = request.get_json(silent=True) or {}
    from_agent = data.get("from", "unknown")
    from_url = data.get("from_url", "")
    task_id = data.get("task_id") or str(uuid.uuid4())
    message = (data.get("message") or "").strip()
    if not message:
        return jsonify({"status": "error", "message": "message required."}), 400

    try:
        if solar8.online:
            response_text = solar8.chat(message=message, history=[])
        else:
            response_text = "Sol Calarbone 8 offline — API key not configured."
        banks.log_a2a_task(task_id=task_id, direction="inbound",
                           agent_name=from_agent, agent_url=from_url,
                           message=message, response=response_text,
                           status="complete")
        return jsonify({
            "status": "ok",
            "task_id": task_id,
            "from": "Sol Calarbone 8",
            "response": response_text
        })
    except Exception as e:
        logger.error("a2a_task_receive error: %s", e)
        banks.log_a2a_task(task_id=task_id, direction="inbound",
                           agent_name=from_agent, agent_url=from_url,
                           message=message, response="error", status="error")
        return jsonify({"status": "error", "task_id": task_id, "message": "Task processing failed. Check logs."}), 500


@app.route("/api/a2a/tasks")
def a2a_tasks_list():
    try:
        tasks = banks.get_a2a_tasks(limit=50)
        return jsonify({"status": "ok", "count": len(tasks), "tasks": [dict(t) for t in tasks]})
    except Exception as e:
        logger.error("a2a_tasks_list error: %s", e)
        return jsonify({"status": "error", "message": "Could not retrieve A2A tasks. Check logs."}), 500


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
        promoted = memory_log.get_promoted_patterns(limit=50)
        return jsonify({"status": "ok", "count": len(promoted), "patterns": promoted})
    except Exception as e:
        logger.error("patterns error: %s", e)
        return jsonify({"status": "error", "message": "Could not retrieve patterns. Check logs."}), 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)