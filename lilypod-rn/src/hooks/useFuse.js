/**
 * useFuse.js
 * React hook wrapping LilypodClient.fuse().
 *
 * BOOL++: TRUE(1) · FALSE(0) · NULL_Φ(2)
 * Albert's Axiom: E = m ↔ c² [NULL_Φ(T, ΔS)]
 *
 * Returns: { fuse, result, loading, error }
 * Usage:   const { fuse, result } = useFuse(client)
 */

import { useState, useCallback } from 'react';

/**
 * @param {import('../LilypodClient').LilypodClient} client
 * @returns {{ fuse: Function, result: object|null, loading: boolean, error: string|null }}
 */
export function useFuse(client) {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fuse = useCallback(async (agentA, agentB) => {
    setLoading(true);
    setError(null);
    const emission = await client.fuse(agentA, agentB);
    setLoading(false);
    if (emission.ok === false && emission.error) {
      setError(emission.error);
    } else {
      setResult(emission);
    }
    return emission;
  }, [client]);

  return { fuse, result, loading, error };
}
