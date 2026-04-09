/** ARIA attribute helpers. */

let counter = 0;

export function generateId(prefix: string = 'adms'): string {
  return `${prefix}-${++counter}`;
}

export function labelledBy(...ids: (string | undefined | null)[]): string {
  return ids.filter(Boolean).join(' ');
}

export function describedBy(...ids: (string | undefined | null)[]): string {
  return ids.filter(Boolean).join(' ');
}
