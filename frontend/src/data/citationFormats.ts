/** Citation format definitions. */

export interface CitationFormat {
  id: string;
  label: string;
  description: string;
}

export const CITATION_FORMATS: CitationFormat[] = [
  { id: 'chicago_note', label: 'Chicago (Note)', description: 'Footnote/endnote format per Chicago Manual of Style, 17th ed.' },
  { id: 'chicago_bib', label: 'Chicago (Bibliography)', description: 'Bibliography format per Chicago Manual of Style, 17th ed.' },
  { id: 'turabian', label: 'Turabian', description: 'Based on Chicago, commonly used in history.' },
  { id: 'bibtex', label: 'BibTeX', description: 'For LaTeX users and bibliography managers.' },
  { id: 'ris', label: 'RIS', description: 'Import into Zotero, Mendeley, and other reference managers.' },
  { id: 'csl_json', label: 'CSL-JSON', description: 'Machine-readable citation data.' },
];
