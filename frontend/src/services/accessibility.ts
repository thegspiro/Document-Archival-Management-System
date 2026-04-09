/** Focus management helpers and ARIA utilities. */

let idCounter = 0;

export function generateAriaId(prefix: string): string {
  return `${prefix}-${++idCounter}`;
}

export function focusElement(selector: string): void {
  const el = document.querySelector<HTMLElement>(selector);
  el?.focus();
}

export function focusFirstError(): void {
  const firstError = document.querySelector<HTMLElement>('[aria-invalid="true"]');
  firstError?.focus();
}

export function announceToScreenReader(message: string): void {
  const region = document.getElementById('aria-live-region');
  if (region) {
    region.textContent = '';
    requestAnimationFrame(() => {
      region.textContent = message;
    });
  }
}
