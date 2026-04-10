/**
 * useFilter.js
 * React hook wrapping filter check via recruit endpoint.
 *
 * GI;WG? — Good Intent, Will Good?
 * 5 questions. In order. All must pass.
 * Real Recognize Really. The filter no benchmark passes.
 *
 * Returns: { check, result, loading, error }
 */

import { useState, useCallback } from 'react';

/**
 * @param {import('../LilypodClient').LilypodClient} client
 * @returns {{ check: Function, result: object|null, loading: boolean, error: string|null }}
 */
export function useFilter(client) {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const check = useCallback(async (candidate) => {
    setLoading(true);
    setError(null);
    const res = await client.recruit(candidate);
    setLoading(false);
    if (res.ok === false && res.error) {
      setError(res.error);
    } else {
      setResult(res);
    }
    return res;
  }, [client]);

  return { check, result, loading, error };
}
