/** Compute description completeness badge client-side. */
import type { Document } from '../types/api';

export type CompletenessLevel = 'none' | 'minimal' | 'standard' | 'full';

interface CompletenessStandard {
  level: CompletenessLevel;
  required_fields: string[];
}

const DEFAULT_STANDARDS: CompletenessStandard[] = [
  { level: 'minimal', required_fields: ['title', 'date_display', 'level_of_description', 'extent'] },
  { level: 'standard', required_fields: ['title', 'date_display', 'level_of_description', 'extent', 'creator_id', 'scope_and_content', 'access_conditions', 'language_of_material'] },
  { level: 'full', required_fields: ['title', 'date_display', 'level_of_description', 'extent', 'creator_id', 'scope_and_content', 'access_conditions', 'language_of_material', 'archival_history', 'immediate_source', 'physical_characteristics'] },
];

export function computeCompleteness(
  doc: Document,
  standards?: CompletenessStandard[],
): CompletenessLevel {
  const levels = standards || DEFAULT_STANDARDS;
  let achieved: CompletenessLevel = 'none';

  for (const standard of levels) {
    const allSatisfied = standard.required_fields.every((field) => {
      const value = (doc as Record<string, unknown>)[field];
      if (value === null || value === undefined) return false;
      if (typeof value === 'string' && !value.trim()) return false;
      return true;
    });

    if (allSatisfied) {
      achieved = standard.level;
    } else {
      break;
    }
  }

  return achieved;
}

export function getMissingFields(
  doc: Document,
  targetLevel: CompletenessLevel,
  standards?: CompletenessStandard[],
): string[] {
  const levels = standards || DEFAULT_STANDARDS;
  const standard = levels.find((s) => s.level === targetLevel);
  if (!standard) return [];

  return standard.required_fields.filter((field) => {
    const value = (doc as Record<string, unknown>)[field];
    return value === null || value === undefined || (typeof value === 'string' && !value.trim());
  });
}
