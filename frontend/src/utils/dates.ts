/** Date formatting and partial date handling. */

export function formatDate(dateStr: string | null | undefined): string {
  if (!dateStr) return '';
  try {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  } catch {
    return dateStr;
  }
}

export function formatDateRange(start: string | null, end: string | null): string {
  if (!start && !end) return '';
  if (start && end && start === end) return formatDate(start);
  if (start && end) return `${formatDate(start)} – ${formatDate(end)}`;
  if (start) return `${formatDate(start)} –`;
  return `– ${formatDate(end)}`;
}

export function toISODate(date: Date): string {
  return date.toISOString().split('T')[0];
}
