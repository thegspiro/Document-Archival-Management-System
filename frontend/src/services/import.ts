/** CSV import validation helpers. */

const REQUIRED_TEMPLATE_COLUMNS = [
  'title',
  'accession_number',
  'date_display',
];

const VALID_DATE_PATTERN = /^\d{4}-\d{2}-\d{2}$/;

const VALID_COPYRIGHT_STATUSES = [
  'copyrighted',
  'public_domain',
  'unknown',
  'orphan_work',
  'creative_commons',
];

export interface ValidationMessage {
  level: 'error' | 'warning' | 'info';
  field: string;
  message: string;
}

export function validateRow(
  row: Record<string, string>,
  rowNumber: number,
): ValidationMessage[] {
  const messages: ValidationMessage[] = [];

  // Title is required
  if (!row.title?.trim()) {
    messages.push({ level: 'error', field: 'title', message: `Row ${rowNumber}: Title is required.` });
  }

  // Date validation
  if (row.date_start && !VALID_DATE_PATTERN.test(row.date_start)) {
    messages.push({ level: 'error', field: 'date_start', message: `Row ${rowNumber}: Invalid date format. Use YYYY-MM-DD.` });
  }
  if (row.date_end && !VALID_DATE_PATTERN.test(row.date_end)) {
    messages.push({ level: 'error', field: 'date_end', message: `Row ${rowNumber}: Invalid date format. Use YYYY-MM-DD.` });
  }

  // Copyright status
  if (row.copyright_status && !VALID_COPYRIGHT_STATUSES.includes(row.copyright_status)) {
    messages.push({ level: 'warning', field: 'copyright_status', message: `Row ${rowNumber}: Unknown copyright status "${row.copyright_status}".` });
  }

  // Boolean fields
  if (row.has_content_advisory && !['TRUE', 'FALSE', 'true', 'false', '1', '0'].includes(row.has_content_advisory)) {
    messages.push({ level: 'warning', field: 'has_content_advisory', message: `Row ${rowNumber}: Expected TRUE or FALSE.` });
  }

  return messages;
}

export function validateTemplateColumns(headers: string[]): ValidationMessage[] {
  const messages: ValidationMessage[] = [];
  for (const col of REQUIRED_TEMPLATE_COLUMNS) {
    if (!headers.includes(col)) {
      messages.push({ level: 'error', field: col, message: `Required column "${col}" is missing.` });
    }
  }
  return messages;
}
