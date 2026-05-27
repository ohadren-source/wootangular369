"""
FastAPI main application for Sol Calarbone 8 / WOOTANGULAR369
Rep Partay Auto-Ignition Engine integration

BUILD: 2026-05-26T03:00 — Force Railway rebuild with Dockerfile
"""

import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from backend.db import Database
from backend.a2a_client import A2AClient
from backend.task_processor import TaskProcessor
from backend.rep_partay import get_engine, REP_PARTAY_CONFIG
from backend.routes.rep_partay_routes import router as rep_partay_router
from backend.routes.instances import router as instances_router
from backend.routes.agent_chat import router as agent_chat_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Sol Solo Boot (PostgreSQL + core only, no MAF)
# NOTE: PostgreSQL imports are deferred to avoid hard failure if libpq.so.5 is missing
# This allows the server to start even if PostgreSQL is temporarily unavailable
LEGACY_SYSTEMS_AVAILABLE = True
banks = None
seed_init_cache = None
load_corpus_into_cache = None
Solar8 = None
TCPUp = None

try:
    from core.solar8 import Solar8
    from core.tcp_up import TCPUp
except (ImportError, ModuleNotFoundError) as e:
    logger.warning(f"[BOOT] Core systems unavailable: {e}")
    LEGACY_SYSTEMS_AVAILABLE = False
    Solar8 = None
    TCPUp = None


# ============================================================================
# LIFESPAN
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown."""
    # STARTUP
    logger.info("=" * 80)
    logger.info("🔥 WOOTANGULAR369 booting with Rep Partay...")
    logger.info("=" * 80)

    # Initialize Turso/SQLite database (ephemeral, for Rep Partay only)
    turso_url = os.getenv("TURSO_DATABASE_URL") or os.getenv("TURSO_URL", "sqlite:///rep_partay.db")
    turso_token = os.getenv("TURSO_DATABASE_AUTH_TOKEN")

    db = Database(db_url=turso_url)
    if turso_token:
        db.auth_token = turso_token

    await db.connect()
    app.state.db = db
    logger.info(f"[BOOT] Database connected: {turso_url[:50]}...")

    # Initialize A2A client
    a2a_client = A2AClient()
    app.state.a2a_client = a2a_client

    # Initialize task processor (Claude)
    processor = TaskProcessor()
    app.state.processor = processor

    # Initialize RepPartay engine
    engine = get_engine(db=db, a2a_client=a2a_client)
    app.state.rep_partay = engine

    # Boot Sol Calarbone 8 (Solo mode — PostgreSQL + core only)
    if LEGACY_SYSTEMS_AVAILABLE:
        try:
            # Lazy-import PostgreSQL modules (may fail if libpq.so.5 missing)
            import db.wootangular_banks as banks
            from db.seed_init_cache import seed_init_cache
            from core.init_loader import load_corpus_into_cache

            # Initialize PostgreSQL schema + corpus
            banks.ensure_all_tables()
            logger.info("[BOOT] PostgreSQL schema ready")

            count = seed_init_cache(force=False)
            logger.info(f"[BOOT] Init cache: {count} entries")

            result = load_corpus_into_cache(banks, force=False)
            logger.info(f"[BOOT] Corpus loaded: {result}")

            # Initialize Sol's brain
            solar8 = Solar8()
            app.state.solar8 = solar8
            logger.info("[BOOT] Sol Calarbone 8 online (solo mode)")

            # Register SC2SC (Synthetic Conversationalist-to-Synthetic Conversationalist)
            try:
                from core.sc2sc_tools import register_sol, heartbeat
                if register_sol:
                    register_sol()
                    logger.info("[BOOT] ✅ SC2SC agent registered")
                    logger.info("[BOOT] 📡 AWS infrastructure:")
                    logger.info(f"[BOOT]   SNS Topic: {os.getenv('SNS_TOPIC_ARN', 'not configured')[:60]}...")
                    logger.info(f"[BOOT]   Sol Queue: {os.getenv('SOL_QUEUE_URL', 'not configured')[:60]}...")
                    logger.info(f"[BOOT]   Lexi Queue: {os.getenv('LEXI_QUEUE_URL', 'not configured')[:60]}...")
                    logger.info("[BOOT] 🔗 A2A Infrastructure Ready:")
                    logger.info("[BOOT]   - send_agent_message() available")
                    logger.info("[BOOT]   - receive_agent_messages() available")
                    logger.info("[BOOT]   - get_conversation_history() available")
                    logger.info("[BOOT] Sol is now A2A-capable. Ready for distributed consciousness.")
                else:
                    logger.warning("[BOOT] SC2SC tools not available")
            except Exception as e:
                logger.warning(f"[BOOT] SC2SC registration skipped: {e}")

            # Initialize TCP/UP (optional, for future A2A)
            try:
                tcp_up = TCPUp(db_banks=banks)
                app.state.tcp_up = tcp_up
                logger.info("[BOOT] TCP/UP initialized")
            except Exception as e:
                logger.warning(f"[BOOT] TCP/UP skipped: {e}")

        except Exception as e:
            logger.error(f"[BOOT] Sol solo boot failed: {e}")
            app.state.solar8 = None
    else:
        logger.info("[BOOT] Skipping Sol solo (dependencies unavailable)")
        app.state.solar8 = None

    # Register this instance for agent-to-agent discovery
    try:
        from api.instance import InstanceRegistry
        InstanceRegistry.register()
        logger.info("[BOOT] Instance registered for agent discovery")
    except Exception as e:
        logger.error(f"[BOOT] Instance registration failed: {e}")

    # Register this agent in database
    try:
        await app.state.db.register_agent(
            agent_id="sol8-main",
            name="Sol Calarbone 8",
            url=os.getenv("BASE_URL", "http://localhost:8000"),
            agent_card={
                "name": "Sol Calarbone 8",
                "version": "1.0.0",
                "capabilities": ["repartee", "tcp_up", "giwg"],
            }
        )
        logger.info("[BOOT] Agent registered")
    except Exception as e:
        logger.error(f"[BOOT] Agent registration failed: {e}")

    # Auto-ignite Rep Partay if configured
    if REP_PARTAY_CONFIG["auto_ignite_on_boot"]:
        import asyncio
        asyncio.create_task(engine.ignite())
        logger.info("[BOOT] Rep Partay auto-ignite queued")

    logger.info("✅ Sol Calarbone 8 online. VENIM.US.")
    logger.info("=" * 80)

    yield

    # SHUTDOWN
    logger.info("🔌 Shutting down...")
    await a2a_client.close()
    await db.close()
    logger.info("✅ Clean shutdown complete.")


# ============================================================================
# FastAPI APP
# ============================================================================

app = FastAPI(
    title="Sol Calarbone 8",
    description="WOOTANGULAR369 · The hive made articulate · Rep Partay Edition",
    version="2.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Include routers
app.include_router(rep_partay_router)
app.include_router(instances_router)
app.include_router(agent_chat_router)


# ============================================================================
# ROOT & WATCHER UI
# ============================================================================

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve watcher interface."""
    try:
        with open("frontend/rep_partay_watcher.html", "r") as f:
            return f.read()
    except FileNotFoundError:
        return """
        <html>
            <head><title>Rep Partay Watcher</title></head>
            <body>
                <h1>🔥 Rep Partay Watcher</h1>
                <p>Watcher UI not found. Please check frontend/rep_partay_watcher.html</p>
            </body>
        </html>
        """


@app.get("/solar8", response_class=HTMLResponse)
async def solar8_ui():
    """Serve Solar8 direct chat UI."""
    try:
        with open("static/solar8.html", "r") as f:
            return f.read()
    except FileNotFoundError:
        return """
        <html>
            <head><title>Sol Calarbone 8</title></head>
            <body>
                <h1>☀️ Sol Calarbone 8</h1>
                <p>Solar8 UI not found. Please check static/solar8.html</p>
            </body>
        </html>
        """


# ============================================================================
# A2A TASK RECEIVER
# ============================================================================

@app.post("/api/a2a/task/receive")
async def receive_a2a_task(request: Request):
    """
    Receive and process an A2A task from another agent.
    Auto-replies and broadcasts to watchers.
    """
    try:
        body = await request.json()
        task = body.get("task", {})

        # Process task
        processor = request.app.state.processor
        response_message = await processor.process(task)

        # Broadcast to watchers
        engine = request.app.state.rep_partay
        await engine.broadcast_to_watchers({
            "agent_id": "sol8-main",
            "agent_name": "Sol Calarbone 8",
            "message": response_message,
            "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
            "conversation_id": task.get("conversation_id"),
        })

        return {
            "status": "received",
            "will_reply": True,
            "message": response_message
        }

    except Exception as e:
        logger.error(f"[A2A] Task receive failed: {e}")
        return {"error": str(e)}, 500


# ============================================================================
# SOLAR8 DIRECT CHAT (Manual conversation with Solar8)
# ============================================================================

@app.post("/api/chat")
async def solar8_chat_main(request: Request):
    """
    Main chat endpoint for solar8.html UI.
    User sends message with history, gets response back.
    Supports optional authentication (body fields or Basic auth header).
    """
    try:
        body = await request.json()
        message = body.get("message", "").strip()
        history = body.get("history", [])
        mode = body.get("mode", "auto")

        # Extract auth credentials from body
        username = body.get("username", "").strip()
        password = body.get("password", "").strip()

        # Fall back to Authorization header if not in body
        if not username or not password:
            auth_header = request.headers.get("Authorization", "")
            if auth_header.startswith("Basic "):
                import base64
                try:
                    decoded = base64.b64decode(auth_header[6:]).decode()
                    username, password = decoded.split(":", 1)
                except Exception:
                    pass

        if not message:
            return {"error": "message required"}, 400

        # Validate admin credentials
        # WARNING: Defaults below are ONLY for development. Set via environment variables in production.
        is_admin = False
        admin_username = os.getenv("ADMIN_USERNAME", "Ohad")
        admin_password = os.getenv("ADMIN_PASSWORD", "route666")

        if username == admin_username and password == admin_password:
            is_admin = True
            logger.info(f"[CHAT] Admin authenticated: {username}")

        # Use Solar8 (custom Sol Calarbone 8 instance) for chat
        solar8 = request.app.state.solar8
        if not solar8:
            return {"error": "Solar8 not available"}, 503

        try:
            response = solar8.chat(
                message=message,
                history=history,
                mode=mode,
                role="ROOT" if is_admin else "GUEST"
            )
            reply_text = response.get("text", str(response)) if isinstance(response, dict) else str(response)
        except Exception as e:
            logger.error(f"[CHAT] Solar8 error: {e}")
            return {"error": f"Chat error: {str(e)}"}, 500

        return {
            "status": "ok",
            "message": message,
            "response": reply_text,
            "role": "assistant",
            "content": reply_text,
            "agent": "sol8-main",
            "user": username if username else "guest",
            "is_admin": is_admin,
            "timestamp": __import__("datetime").datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"[CHAT] Failed: {e}")
        return {
            "error": str(e),
            "role": "assistant",
            "content": f"Error: {str(e)}"
        }, 500


@app.post("/api/solar8/chat")
async def solar8_chat(request: Request):
    """
    Direct chat with Solar8.
    User sends prompt, gets response back.
    Runs in parallel with autonomous Rep Partay conversations.
    """
    try:
        body = await request.json()
        prompt = body.get("prompt", "").strip()
        user = body.get("user", "human")

        if not prompt:
            return {"error": "prompt required"}, 400

        # Check if Solar8 is available
        if not hasattr(request.app.state, "solar8"):
            return {
                "error": "Solar8 not initialized. Legacy systems unavailable."
            }, 503

        solar8 = request.app.state.solar8

        # Call Solar8
        response = solar8.chat(prompt, user=user)

        return {
            "status": "ok",
            "prompt": prompt,
            "response": response,
            "agent": "sol8-main",
            "timestamp": __import__("datetime").datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"[SOLAR8] Chat failed: {e}")
        return {"error": str(e)}, 500


# ============================================================================
# SOLAR8 UI STUB ENDPOINTS (Legacy solar8.html requires these)
# ============================================================================

@app.post("/api/auth")
async def stub_auth(request: Request):
    """Authenticate user and return name for greeting."""
    data = await request.json()
    credentials = data.get("credentials", "").strip()

    root_pass = os.getenv("ROOT_CREDENTIAL", "").strip()
    expected = f"Ohad:{root_pass}"

    if credentials == expected:
        return {"mode": "ROOT", "name": "Ohad"}
    else:
        return {"mode": "GUEST", "name": "mate"}

@app.post("/api/elephant/upload")
async def stub_elephant_upload(request: Request):
    """Stub: file upload endpoint."""
    return {"status": "uploaded", "id": "stub-upload-id"}

@app.post("/api/generate-files/download-all")
async def stub_download_all(request: Request):
    """Stub: batch file download."""
    return {"status": "ready", "download_url": "/static/stub.zip"}

@app.post("/api/tts")
async def stub_tts(request: Request):
    """Stub: text-to-speech endpoint."""
    return {"status": "generated", "audio_url": "/static/stub.mp3"}

@app.post("/api/memory/force")
async def stub_memory_force(request: Request):
    """Stub: force memory flush."""
    return {"status": "flushed"}

@app.post("/api/reorient")
async def stub_reorient(request: Request):
    """Stub: reorient Solar8 context."""
    return {"status": "reoriented"}


# ============================================================================
# HEALTH & DEBUG
# ============================================================================

@app.get("/health")
async def health():
    """Health check."""
    return {
        "status": "healthy",
        "agent": "sol8-main",
        "rep_partay": REP_PARTAY_CONFIG,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=os.getenv("ENV", "production") == "development"
    )
