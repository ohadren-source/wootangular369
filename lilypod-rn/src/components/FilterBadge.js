/**
 * FilterBadge.js
 * React Native component — displays filter result.
 *
 * GI;WG? — Good Intent, Will Good?
 * Real Recognize Really. The filter no benchmark passes.
 *
 * Props: { result: "the_shit" | "boolshit" | "defer" }
 * the_shit → green badge "THE_SHIT ✅"
 * boolshit → red badge "BOOLSHIT 🚫"
 * defer    → yellow badge "DEFER ⏳"
 */

import React from 'react';
import { View, Text } from 'react-native';

const BADGE_CONFIG = {
  the_shit: { label: 'THE_SHIT ✅', color: '#00FF41', bg: '#001a00' },
  boolshit: { label: 'BOOLSHIT 🚫', color: '#FF3333', bg: '#1a0000' },
  defer:    { label: 'DEFER ⏳',    color: '#FFD700', bg: '#1a1500' },
};

const DEFAULT_CONFIG = { label: 'UNKNOWN', color: '#666666', bg: '#111' };

/**
 * @param {{ result: "the_shit"|"boolshit"|"defer" }} props
 */
export function FilterBadge({ result }) {
  const config = BADGE_CONFIG[result] || DEFAULT_CONFIG;

  return (
    <View style={{
      paddingHorizontal: 14,
      paddingVertical: 6,
      borderRadius: 20,
      backgroundColor: config.bg,
      borderWidth: 1,
      borderColor: config.color,
      alignSelf: 'flex-start',
    }}>
      <Text style={{ color: config.color, fontWeight: 'bold', fontSize: 14 }}>
        {config.label}
      </Text>
    </View>
  );
}
