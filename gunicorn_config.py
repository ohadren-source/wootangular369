# gunicorn_config.py
# WOOTANGULAR369 Production Config — Sol Calarbone 8
# Configured for long-running tool calls (file fetches, API calls, Claude processing)

import multiprocessing
import os

# ============================================================================
# BINDING
# ============================================================================

bind = "0.0.0.0:8080"

# ============================================================================
# WORKER CONFIGURATION
# ============================================================================

workers = 1  # Single worker = stateful agent session (no session splitting)
worker_class = "sync"  # Blocking I/O for tool calls and async event loops
worker_connections = 1000

# ============================================================================
# TIMEOUTS — CRITICAL FOR TOOL CALLS
# ============================================================================

timeout = 200  # Max request time in seconds
# Covers: fetch_webpage (up to 180s) + Claude processing + overhead
graceful_timeout = 210  # Graceful shutdown window (allow in-flight requests to finish)
keepalive = 5  # Keep-alive timeout for idle connections

# ============================================================================
# LOGGING
# ============================================================================

accesslog = "-"  # stdout
errorlog = "-"   # stderr
loglevel = "info"

# ============================================================================
# PROCESS NAMING & DAEMON SETTINGS
# ============================================================================

proc_name = "solar8_wootangular369"
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# ============================================================================
# REQUEST SIZE LIMITS
# ============================================================================

limit_request_line = 0  # No limit on request line size
limit_request_fields = 100
limit_request_field_size = 0  # No limit (for large payloads from file processing)

# ============================================================================
# WORKER LIFECYCLE & MEMORY MANAGEMENT
# ============================================================================

max_requests = 1000  # Restart worker after 1000 requests (prevents memory leaks)
max_requests_jitter = 50  # Random jitter to avoid thundering herd on restart

preload_app = False  # Don't preload (keeps startup fast, trades memory for speed)

# ============================================================================
# LIFECYCLE HOOKS — LOGGING, DEBUGGING, INSTANCE REGISTRATION
# ============================================================================

def on_starting(server):
    """Called before master process is initialized."""
    server.log.info("🔥 WOOTANGULAR369 server starting — Sol Calarbone 8 online")

def on_reload(server):
    """Called when workers are reloaded."""
    server.log.info("🔄 Server reloading — swarm reconfiguring")

def post_worker_init(worker):
    """Called after worker process is initialized."""
    try:
        from api.instance import InstanceRegistry, INSTANCE_ID
        worker.log.info(f"[GUNICORN] Worker {worker.pid} initialized as {INSTANCE_ID}")
        InstanceRegistry.register()
    except Exception as e:
        worker.log.error(f"[GUNICORN] Failed to register instance: {e}")

def worker_exit(server, worker):
    """Called when a worker is exiting."""
    try:
        from api.instance import InstanceRegistry, INSTANCE_ID
        server.log.info(f"💀 Worker {worker.pid} ({INSTANCE_ID}) shutting down")
        InstanceRegistry.deregister()
    except Exception as e:
        server.log.error(f"[GUNICORN] Failed to deregister instance: {e}")

# ============================================================================
# SSL / TLS (commented out — configure if needed)
# ============================================================================

# keyfile = None
# certfile = None
# ssl_version = None
# cert_reqs = 0
# ca_certs = None
# ciphers = None

# ============================================================================
# ADDITIONAL OPTIONS
# ============================================================================

forwarded_allow_ips = "*"  # Trust X-Forwarded-* headers from all proxies
# (adjust if behind reverse proxy with specific IPs)
