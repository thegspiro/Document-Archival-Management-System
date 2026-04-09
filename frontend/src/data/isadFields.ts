/** ISAD(G) field labels and help text for the document edit form. */

export interface IsadField {
  name: string;
  label: string;
  area: string;
  helpText: string;
  type: 'text' | 'textarea' | 'date' | 'select' | 'number';
}

export const ISAD_FIELDS: IsadField[] = [
  // Identity Statement Area
  { name: 'title', label: 'Title', area: 'Identity', helpText: 'The name of the unit of description.', type: 'text' },
  { name: 'reference_code', label: 'Reference Code', area: 'Identity', helpText: 'Country code, repository code, and local reference code.', type: 'text' },
  { name: 'date_display', label: 'Date (Display)', area: 'Identity', helpText: 'Date as written on or associated with the document.', type: 'text' },
  { name: 'date_start', label: 'Date (Start)', area: 'Identity', helpText: 'Normalized start date in YYYY-MM-DD format.', type: 'date' },
  { name: 'date_end', label: 'Date (End)', area: 'Identity', helpText: 'Normalized end date. Same as start for single dates.', type: 'date' },
  { name: 'level_of_description', label: 'Level of Description', area: 'Identity', helpText: 'The position of the unit in the hierarchy.', type: 'select' },
  { name: 'extent', label: 'Extent', area: 'Identity', helpText: 'Physical extent (e.g., "3 pages", "1 photograph").', type: 'text' },

  // Context Area
  { name: 'administrative_history', label: 'Administrative History', area: 'Context', helpText: 'Administrative history of the creator.', type: 'textarea' },
  { name: 'archival_history', label: 'Archival History', area: 'Context', helpText: 'Successive transfers of ownership and custody.', type: 'textarea' },
  { name: 'immediate_source', label: 'Immediate Source of Acquisition', area: 'Context', helpText: 'Source from which the unit was acquired.', type: 'textarea' },

  // Content and Structure Area
  { name: 'scope_and_content', label: 'Scope and Content', area: 'Content', helpText: 'Summary of the scope and content of the unit.', type: 'textarea' },
  { name: 'appraisal_notes', label: 'Appraisal Notes', area: 'Content', helpText: 'Actions taken and criteria applied during appraisal.', type: 'textarea' },
  { name: 'system_of_arrangement', label: 'System of Arrangement', area: 'Content', helpText: 'Internal structure and ordering of the unit.', type: 'textarea' },

  // Conditions of Access Area
  { name: 'access_conditions', label: 'Access Conditions', area: 'Access', helpText: 'Conditions governing access to the unit.', type: 'textarea' },
  { name: 'reproduction_conditions', label: 'Reproduction Conditions', area: 'Access', helpText: 'Conditions governing reproduction.', type: 'textarea' },
  { name: 'language_of_material', label: 'Language', area: 'Access', helpText: 'ISO 639 language codes, comma-separated.', type: 'text' },
  { name: 'physical_characteristics', label: 'Physical Characteristics', area: 'Access', helpText: 'Physical condition and technical requirements.', type: 'textarea' },

  // Allied Materials Area
  { name: 'location_of_originals', label: 'Location of Originals', area: 'Allied', helpText: 'Where the original materials are held.', type: 'textarea' },
  { name: 'related_units', label: 'Related Units', area: 'Allied', helpText: 'Related units of description.', type: 'textarea' },
  { name: 'publication_note', label: 'Publication Note', area: 'Allied', helpText: 'Published references to the unit.', type: 'textarea' },

  // Notes Area
  { name: 'general_note', label: 'General Note', area: 'Notes', helpText: 'Specialized information not covered elsewhere.', type: 'textarea' },
  { name: 'archivists_note', label: "Archivist's Note", area: 'Notes', helpText: 'Notes about the creation of the description.', type: 'textarea' },
];
