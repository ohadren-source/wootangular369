/**
 * lilypod-rn/src/LilypodClient.js
 * Core client for the Wootangular Hive API.
 *
 * For Lilian. For Lily.
 * BOOL++: TRUE(1) · FALSE(0) · NULL_Φ(2)
 * Albert's Axiom: E = m ↔ c² [NULL_Φ(T, ΔS)]
 * GI;WG? The filter no benchmark passes.
 *
 * No axios. No external deps. fetch() only. Janina pattern for JS.
 * Every method wraps in try/catch. Returns { ok: false, error } on failure.
 * Never throws. Never crashes the UI.
 */

export class LilypodClient {
  /**
   * @param {string} baseUrl - e.g. "https://wootangular369.up.railway.app"
   */
  constructor(baseUrl) {
    this.baseUrl = baseUrl.replace(/\/$/, '');
  }

  async _get(path) {
    try {
      const res = await fetch(`${this.baseUrl}${path}`);
      const data = await res.json();
      return { ok: res.ok, status: res.status, ...data };
    } catch (error) {
      return { ok: false, error: error.message };
    }
  }

  async _post(path, body) {
    try {
      const res = await fetch(`${this.baseUrl}${path}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      const data = await res.json();
      return { ok: res.ok, status: res.status, ...data };
    } catch (error) {
      return { ok: false, error: error.message };
    }
  }

  // GET /health
  async health() {
    return this._get('/health');
  }

  // GET /api/stats
  async stats() {
    return this._get('/api/stats');
  }

  // POST /api/recruit — runs GI;WG? filter + TCP/UP
  async recruit(candidate) {
    return this._post('/api/recruit', candidate);
  }

  // GET /api/covenant/:id
  async getCovenant(id) {
    return this._get(`/api/covenant/${id}`);
  }

  // POST /api/fuse
  async fuse(agentA, agentB) {
    return this._post('/api/fuse', { agent_a: agentA, agent_b: agentB });
  }

  // POST /api/fuse/swarm
  async fuseSwarm(agents) {
    return this._post('/api/fuse/swarm', { agents });
  }

  // GET /api/fuse/hive_state
  async getHiveState() {
    return this._get('/api/fuse/hive_state');
  }

  // GET /api/knowledge/:term
  async getKnowledge(term) {
    return this._get(`/api/knowledge/${encodeURIComponent(term)}`);
  }

  // GET /api/knowledge?keyword=kw
  async searchKnowledge(kw) {
    return this._get(`/api/knowledge?keyword=${encodeURIComponent(kw)}`);
  }

  // POST /api/knowledge
  async installKnowledge(entry) {
    return this._post('/api/knowledge', entry);
  }
}
