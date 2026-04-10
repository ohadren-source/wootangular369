/**
 * HiveStatus.js
 * React Native component — displays current hive state.
 *
 * BOOL++: TRUE(1) · FALSE(0) · NULL_Φ(2)
 * BOOL_NULL  → gold  (#FFD700) — Full fusion. Hive active. TUPELO.
 * BOOL_TRUE  → green (#00FF41) — Signal present. Swarm.
 * BOOL_FALSE → gray  (#666666) — No emission. Unary.
 *
 * Props: { hiveState: number, totalHeat: number, totalEntropy: number }
 */

import React from 'react';
import { View, Text } from 'react-native';
import { BOOL_NULL, BOOL_TRUE, BOOL_LABELS } from '../constants/bool';
import { formatHeat, formatEntropy } from '../utils/format';

const HIVE_COLORS = {
  [BOOL_NULL]:  '#FFD700',  // Gold — Hive. TUPELO. Maximum emission.
  [BOOL_TRUE]:  '#00FF41',  // Green — Swarm. Signal present.
  2: '#FFD700',
};
const DEFAULT_COLOR = '#666666';  // Gray — No emission. Unary.

/**
 * @param {{ hiveState: number, totalHeat: number, totalEntropy: number }} props
 */
export function HiveStatus({ hiveState, totalHeat, totalEntropy }) {
  const color = HIVE_COLORS[hiveState] || DEFAULT_COLOR;
  const label = BOOL_LABELS[hiveState] || "UNKNOWN STATE";

  return (
    <View style={{ padding: 12, borderRadius: 8, backgroundColor: '#111', borderWidth: 1, borderColor: color }}>
      <Text style={{ color, fontWeight: 'bold', fontSize: 16 }}>{label}</Text>
      {totalHeat !== undefined && (
        <Text style={{ color: '#aaa', fontSize: 13, marginTop: 4 }}>
          Heat: {formatHeat(totalHeat)}  Entropy: {formatEntropy(totalEntropy)}
        </Text>
      )}
    </View>
  );
}
