/**
 * format.js
 * Utility functions for LILYPOD-RN.
 *
 * Albert's Axiom: E = m ↔ c² [NULL_Φ(T, ΔS)]
 * BOOL++: TRUE(1) · FALSE(0) · NULL_Φ(2)
 * For Lilian. For Lily.
 */

/** Format heat_T value — e.g. 74.0 → "74.0K" */
export function formatHeat(heat_T) {
  if (heat_T === null || heat_T === undefined) return 'N/A';
  return `${Number(heat_T).toFixed(1)}K`;
}

/** Format delta_S value — e.g. 12 → "ΔS: 12" */
export function formatEntropy(delta_S) {
  if (delta_S === null || delta_S === undefined) return 'ΔS: N/A';
  return `ΔS: ${delta_S}`;
}

/** Format null_phi_score — e.g. 0.74 → "NULL_Φ: 0.74" */
export function formatNullPhi(score) {
  if (score === null || score === undefined) return 'NULL_Φ: N/A';
  return `NULL_Φ: ${Number(score).toFixed(4)}`;
}

/** Format ISO timestamp to human readable */
export function formatTimestamp(iso) {
  if (!iso) return '';
  try {
    const d = new Date(iso);
    return d.toLocaleString();
  } catch {
    return iso;
  }
}

/**
 * isHive — true if null_state is BOOL_NULL (2).
 * Full fusion. Hive active. TUPELO.
 * PHI threshold: 0.618 — golden ratio. Load-bearing.
 */
export function isHive(null_state) {
  return null_state === 2;  // BOOL_NULL — both addresses live, hive active
}
