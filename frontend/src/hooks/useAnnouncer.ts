/** Programmatic ARIA live region announcements. */
import { useCallback } from 'react';

export function useAnnouncer() {
  const announce = useCallback((message: string, politeness: 'polite' | 'assertive' = 'polite') => {
    const region = document.getElementById('aria-live-region');
    if (region) {
      region.setAttribute('aria-live', politeness);
      region.textContent = message;
      // Clear after announcement
      setTimeout(() => {
        region.textContent = '';
      }, 1000);
    }
  }, []);

  return { announce };
}
