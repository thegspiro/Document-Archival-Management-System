/** WCAG contrast ratios and focus colors — mirrors CSS tokens for JS reference. */

export const WCAG_TOKENS = {
  focus: {
    color: '#005fcc',
    colorDark: '#66b3ff',
    outlineWidth: '3px',
    outlineOffset: '3px',
  },
  contrast: {
    textPrimaryOnWhite: 16,
    textSecondaryOnWhite: 7,
    textMutedOnWhite: 4.5,
    errorOnWhite: 5.9,
    warningOnWhite: 4.5,
    successOnWhite: 7.1,
    linkOnWhite: 4.7,
  },
  minTargetSize: {
    aa: 24,
    preferred: 44,
  },
} as const;
