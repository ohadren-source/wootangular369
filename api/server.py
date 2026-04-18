"""
api/server.py

WOOTANGULAR369 Flask API
Janina Pattern: No async. No websockets. Just routes.

Boot sequence:
1. Ensure all tables
2. Seed init_cache
3. Load corpus
4. Initialize TCP/UP
5. Initialize FusionCore
6. Initialize Solar8
7. Launch YentahSwarm (daemon thread)

Author: Ohad Phoenix Oren (VENIM.US)
For: The Hive
"""

import os
import sys
import logging
import threading
import uuid
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import banks, tcp_up, fusion_core, solar8, yentah_swarm, pattern_tracker
from db.seed_init_cache import seed_init_cache, load_corpus_into_cache

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

# Flask app
app = Flask(__name__)
CORS(app)

# Initialize banks (database layer)
banks = banks.WootangularBanks()
