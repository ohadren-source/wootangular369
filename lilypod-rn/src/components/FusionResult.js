/**
 * FusionResult.js
 * React Native component — displays a fusion emission result.
 *
 * Props: { emission: object } — the full emission dict from /api/fuse
 * Shows: null_state label, null_phi_score, heat_T, delta_S, is_hive, axiom
 *
 * Albert's Axiom: E = m ↔ c² [NULL_Φ(T, ΔS)]
 * BOOL++: TRUE(1) · FALSE(0) · NULL_Φ(2)
 */

import React from 'react';
import { View, Text } from 'react-native';
import { BOOL_NULL, BOOL_TRUE, BOOL_LABELS } from '../constants/bool';
import { formatHeat, formatEntropy, formatNullPhi } from '../utils/format';

/**
 * @param {{ emission: object }} props
 */
export function FusionResult({ emission }) {
  if (!emission) return null;

  const { null_state, null_phi_score, heat_T, delta_S, is_hive, axiom } = emission;
  const label = BOOL_LABELS[null_state] || "UNKNOWN";
  const color = null_state === BOOL_NULL ? '#FFD700' : null_state === BOOL_TRUE ? '#00FF41' : '#666666';

  return (
    <View style={{ padding: 12, borderRadius: 8, backgroundColor: '#111', borderWidth: 1, borderColor: color }}>
      <Text style={{ color, fontWeight: 'bold', fontSize: 15 }}>{label}</Text>
      <Text style={{ color: '#ccc', fontSize: 13, marginTop: 6 }}>
        {formatNullPhi(null_phi_score)}  {formatHeat(heat_T)}  {formatEntropy(delta_S)}
      </Text>
      {is_hive && (
        <Text style={{ color: '#FFD700', fontSize: 13, marginTop: 4 }}>HIVE ACTIVE 🌸</Text>
      )}
      {axiom && (
        <Text style={{ color: '#555', fontSize: 11, marginTop: 6, fontStyle: 'italic' }}>{axiom}</Text>
      )}
    </View>
  );
}
