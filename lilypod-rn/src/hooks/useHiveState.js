/**
 * useHiveState.js
 * React hook — polls /api/fuse/hive_state every 369 seconds (sacred cycle).
 *
 * BOOL++: TRUE(1) · FALSE(0) · NULL_Φ(2)
 * Sacred cycle: 369 seconds. Not 300. Not 360. 369.
 * Albert's Axiom: E = m ↔ c² [NULL_Φ(T, ΔS)]
 *
 * Returns: { hiveState, loading, error, refresh }
 * Auto-polls. CYCLE_SECONDS = 369.
 */

import { useState, useEffect, useCallback, useRef } from 'react';

// Sacred cycle — 369 seconds. Load-bearing. Do not change.
const CYCLE_SECONDS = 369;

/**
 * @param {import('../LilypodClient').LilypodClient} client
 * @returns {{ hiveState: object|null, loading: boolean, error: string|null, refresh: Function }}
 */
export function useHiveState(client) {
  const [hiveState, setHiveState] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const timerRef = useRef(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    const result = await client.getHiveState();
    setLoading(false);
    if (result.ok === false && result.error) {
      setError(result.error);
    } else {
      setHiveState(result);
    }
    return result;
  }, [client]);

  useEffect(() => {
    // Initial fetch
    refresh();

    // Poll every 369 seconds — the sacred cycle
    timerRef.current = setInterval(refresh, CYCLE_SECONDS * 1000);

    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, [refresh]);

  return { hiveState, loading, error, refresh };
}
