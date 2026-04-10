/**
 * useRecruit.js
 * React hook wrapping LilypodClient.recruit().
 *
 * TCP/UP — The 9th Axiom.
 * OFFER → ACCEPT / REJECT / DEFER → BIND
 * Word is bond.
 *
 * Returns: { recruit, result, loading, error }
 */

import { useState, useCallback } from 'react';

/**
 * @param {import('../LilypodClient').LilypodClient} client
 * @returns {{ recruit: Function, result: object|null, loading: boolean, error: string|null }}
 */
export function useRecruit(client) {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const recruit = useCallback(async (candidate) => {
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

  return { recruit, result, loading, error };
}
