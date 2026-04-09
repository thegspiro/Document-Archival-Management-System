/** Accession number parsing and formatting. */

export function parseAccessionNumber(accession: string): {
  base: string;
  version: number | null;
} {
  const parts = accession.split('.');
  if (parts.length === 2 && /^\d+$/.test(parts[1])) {
    return { base: parts[0], version: parseInt(parts[1], 10) };
  }
  return { base: accession, version: null };
}

export function formatAccessionNumber(base: string, version?: number | null): string {
  if (version != null) {
    return `${base}.${version}`;
  }
  return base;
}
