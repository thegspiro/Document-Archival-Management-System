/** Client-side citation formatting. */
import type { Document } from '../types/api';

export function formatChicagoNote(doc: Document, institution: string): string {
  const parts: string[] = [];
  parts.push(doc.title);

  if (doc.version_group_id && doc.version_label) {
    parts.push(`${doc.version_label} [version ${doc.version_number}]`);
  }

  if (doc.date_display) parts.push(doc.date_display);
  if (doc.accession_number) parts.push(`Accession ${doc.accession_number}`);
  parts.push(institution);

  return parts.filter(Boolean).join(', ') + '.';
}

export function formatChicagoBib(doc: Document, institution: string): string {
  const parts: string[] = [];
  if (doc.creator) parts.push(`${doc.creator.authorized_name}.`);
  parts.push(`"${doc.title}."`);
  if (doc.date_display) parts.push(`${doc.date_display}.`);
  if (doc.accession_number) parts.push(`Accession ${doc.accession_number}.`);
  parts.push(`${institution}.`);
  return parts.filter(Boolean).join(' ');
}

export function formatBibtex(doc: Document, institution: string): string {
  const key = (doc.accession_number || String(doc.id)).replace(/-/g, '_');
  const lines = [`@misc{${key},`];
  lines.push(`  title = {${doc.title}},`);
  if (doc.creator) lines.push(`  author = {${doc.creator.authorized_name}},`);
  if (doc.date_start) lines.push(`  year = {${doc.date_start.substring(0, 4)}},`);
  lines.push(`  howpublished = {${institution}},`);
  lines.push('}');
  return lines.join('\n');
}
