/**
 * Visual column mapping interface for CSV imports in "mapped" mode.
 *
 * Allows users to map source CSV column names to ADMS field names
 * via dropdown selection. Provides a preview of the first 3 rows
 * of mapped data and validates that required fields are mapped.
 * All interactions have keyboard-accessible button alternatives
 * per WCAG 2.5.7.
 */
import { useCallback, useMemo, useState } from 'react';

/** ADMS fields available for mapping, grouped by category. */
const ADMS_FIELDS: { value: string; label: string; required: boolean; group: string }[] = [
  // Identity
  { value: 'accession_number', label: 'Accession Number', required: false, group: 'Identity' },
  { value: 'title', label: 'Title', required: true, group: 'Identity' },
  { value: 'date_display', label: 'Date (Display)', required: false, group: 'Identity' },
  { value: 'date_start', label: 'Date Start (YYYY-MM-DD)', required: false, group: 'Identity' },
  { value: 'date_end', label: 'Date End (YYYY-MM-DD)', required: false, group: 'Identity' },
  { value: 'extent', label: 'Extent', required: false, group: 'Identity' },
  { value: 'level_of_description', label: 'Level of Description', required: false, group: 'Identity' },
  // Context
  { value: 'creator_name', label: 'Creator Name', required: false, group: 'Context' },
  { value: 'scope_and_content', label: 'Scope and Content', required: false, group: 'Context' },
  { value: 'archival_history', label: 'Archival History', required: false, group: 'Context' },
  { value: 'immediate_source', label: 'Immediate Source', required: false, group: 'Context' },
  // Access
  { value: 'language_of_material', label: 'Language', required: false, group: 'Access' },
  { value: 'access_conditions', label: 'Access Conditions', required: false, group: 'Access' },
  { value: 'reproduction_conditions', label: 'Reproduction Conditions', required: false, group: 'Access' },
  // Rights
  { value: 'copyright_status', label: 'Copyright Status', required: false, group: 'Rights' },
  { value: 'rights_holder', label: 'Rights Holder', required: false, group: 'Rights' },
  { value: 'rights_note', label: 'Rights Note', required: false, group: 'Rights' },
  // Physical
  { value: 'document_type', label: 'Document Type', required: false, group: 'Physical' },
  { value: 'physical_format', label: 'Physical Format', required: false, group: 'Physical' },
  { value: 'condition', label: 'Condition', required: false, group: 'Physical' },
  { value: 'original_location', label: 'Original Location', required: false, group: 'Physical' },
  // Allied materials
  { value: 'location_of_originals', label: 'Location of Originals', required: false, group: 'Allied Materials' },
  // Notes
  { value: 'general_note', label: 'General Note', required: false, group: 'Notes' },
  { value: 'archivists_note', label: "Archivist's Note", required: false, group: 'Notes' },
  // Tags and categories
  { value: 'tags', label: 'Tags (pipe-separated)', required: false, group: 'Tags' },
  { value: 'subject_categories', label: 'Subject Categories (pipe-separated)', required: false, group: 'Tags' },
  // Geolocation
  { value: 'geo_location_name', label: 'Location Name', required: false, group: 'Geolocation' },
  { value: 'geo_latitude', label: 'Latitude', required: false, group: 'Geolocation' },
  { value: 'geo_longitude', label: 'Longitude', required: false, group: 'Geolocation' },
  // Scanning
  { value: 'scan_date', label: 'Scan Date (YYYY-MM-DD)', required: false, group: 'Scanning' },
  // Content advisory
  { value: 'has_content_advisory', label: 'Content Advisory (TRUE/FALSE)', required: false, group: 'Advisory' },
  { value: 'content_advisory_note', label: 'Content Advisory Note', required: false, group: 'Advisory' },
];

const REQUIRED_FIELDS = ADMS_FIELDS.filter((f) => f.required).map((f) => f.value);

interface ColumnMapperProps {
  /** Column headers from the uploaded CSV file. */
  csvHeaders: string[];
  /** First few rows of data for preview. */
  sampleRows: Record<string, string>[];
  /** Callback invoked when the user finalizes the mapping. */
  onMappingComplete: (mapping: Record<string, string>) => void;
}

/**
 * ColumnMapper provides a visual mapping UI for CSV imports.
 * Each source CSV column can be mapped to an ADMS field via a dropdown.
 * Required fields are validated before the mapping can be confirmed.
 */
export default function ColumnMapper({ csvHeaders, sampleRows, onMappingComplete }: ColumnMapperProps) {
  // mapping: csvColumnName -> admsFieldValue
  const [mapping, setMapping] = useState<Record<string, string>>(() => {
    // Auto-match columns that share names with ADMS fields
    const initial: Record<string, string> = {};
    const fieldValues = new Set(ADMS_FIELDS.map((f) => f.value));
    for (const header of csvHeaders) {
      const normalized = header.toLowerCase().replace(/\s+/g, '_').replace(/[^a-z0-9_]/g, '');
      if (fieldValues.has(normalized)) {
        initial[header] = normalized;
      }
    }
    return initial;
  });

  const handleFieldChange = useCallback((csvColumn: string, admsField: string) => {
    setMapping((prev) => {
      const updated = { ...prev };
      if (admsField === '') {
        delete updated[csvColumn];
      } else {
        // If another column already maps to the same ADMS field, unmap it
        for (const [key, value] of Object.entries(updated)) {
          if (value === admsField && key !== csvColumn) {
            delete updated[key];
          }
        }
        updated[csvColumn] = admsField;
      }
      return updated;
    });
  }, []);

  const clearMapping = useCallback((csvColumn: string) => {
    setMapping((prev) => {
      const updated = { ...prev };
      delete updated[csvColumn];
      return updated;
    });
  }, []);

  // Validation
  const mappedAdmsFields = useMemo(() => new Set(Object.values(mapping)), [mapping]);
  const missingRequired = useMemo(
    () => REQUIRED_FIELDS.filter((f) => !mappedAdmsFields.has(f)),
    [mappedAdmsFields],
  );
  const isValid = missingRequired.length === 0;

  // Available ADMS fields for each dropdown (excluding already mapped ones)
  const getAvailableFields = useCallback(
    (currentCsvColumn: string) => {
      const currentlyMapped = mapping[currentCsvColumn];
      return ADMS_FIELDS.filter(
        (f) => !mappedAdmsFields.has(f.value) || f.value === currentlyMapped,
      );
    },
    [mapping, mappedAdmsFields],
  );

  // Group available fields for the dropdown
  const renderFieldOptions = useCallback(
    (currentCsvColumn: string) => {
      const available = getAvailableFields(currentCsvColumn);
      const groups = new Map<string, typeof available>();
      for (const field of available) {
        const existing = groups.get(field.group) ?? [];
        existing.push(field);
        groups.set(field.group, existing);
      }
      return Array.from(groups.entries()).map(([group, fields]) => (
        <optgroup key={group} label={group}>
          {fields.map((f) => (
            <option key={f.value} value={f.value}>
              {f.label}{f.required ? ' (required)' : ''}
            </option>
          ))}
        </optgroup>
      ));
    },
    [getAvailableFields],
  );

  // Preview data
  const previewRows = sampleRows.slice(0, 3);
  const mappedEntries = Object.entries(mapping).filter(([, v]) => v);

  const handleConfirm = useCallback(() => {
    if (isValid) {
      onMappingComplete(mapping);
    }
  }, [isValid, mapping, onMappingComplete]);

  return (
    <div className="space-y-6">
      {/* Mapping interface */}
      <div>
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-1">
          Map CSV Columns to ADMS Fields
        </h3>
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
          For each CSV column, select the corresponding ADMS field from the dropdown. Fields marked
          &quot;(required)&quot; must be mapped before you can proceed.
        </p>

        <div
          className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden"
          role="group"
          aria-label="Column mapping"
        >
          <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-0 text-sm">
            {/* Header row */}
            <div className="px-4 py-3 bg-gray-50 dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700 font-medium text-gray-500 dark:text-gray-400">
              CSV Column
            </div>
            <div className="px-2 py-3 bg-gray-50 dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700 text-center text-gray-400 dark:text-gray-500" aria-hidden="true">
              &rarr;
            </div>
            <div className="px-4 py-3 bg-gray-50 dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700 font-medium text-gray-500 dark:text-gray-400">
              ADMS Field
            </div>

            {/* Mapping rows */}
            {csvHeaders.map((header) => {
              const fieldId = `mapper-field-${header.replace(/\s+/g, '-').replace(/[^a-zA-Z0-9-]/g, '')}`;
              const currentMapping = mapping[header] ?? '';
              return [
                <div
                  key={`${header}-label`}
                  className="px-4 py-3 border-b border-gray-100 dark:border-gray-700 text-gray-900 dark:text-gray-100 font-mono text-xs break-all"
                >
                  <label htmlFor={fieldId} className="cursor-pointer">
                    {header}
                  </label>
                </div>,
                <div
                  key={`${header}-arrow`}
                  className="px-2 py-3 border-b border-gray-100 dark:border-gray-700 text-center text-gray-300 dark:text-gray-600"
                  aria-hidden="true"
                >
                  &rarr;
                </div>,
                <div
                  key={`${header}-select`}
                  className="px-4 py-3 border-b border-gray-100 dark:border-gray-700 flex items-center gap-2"
                >
                  <select
                    id={fieldId}
                    value={currentMapping}
                    onChange={(e) => handleFieldChange(header, e.target.value)}
                    className="flex-1 min-h-[44px] rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-[var(--color-focus,#005fcc)]"
                    aria-label={`ADMS field for CSV column "${header}"`}
                  >
                    <option value="">-- Skip this column --</option>
                    {renderFieldOptions(header)}
                  </select>
                  {currentMapping && (
                    <button
                      type="button"
                      onClick={() => clearMapping(header)}
                      className="min-h-[44px] min-w-[44px] inline-flex items-center justify-center rounded border border-gray-300 dark:border-gray-600 text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-[var(--color-focus,#005fcc)]"
                      aria-label={`Clear mapping for ${header}`}
                    >
                      <span aria-hidden="true">&times;</span>
                    </button>
                  )}
                </div>,
              ];
            })}
          </div>
        </div>
      </div>

      {/* Validation messages */}
      {missingRequired.length > 0 && (
        <div
          role="alert"
          className="p-4 rounded bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 text-amber-800 dark:text-amber-200"
        >
          <p className="font-medium text-sm">Required fields not yet mapped:</p>
          <ul className="mt-1 list-disc list-inside text-sm">
            {missingRequired.map((f) => {
              const fieldDef = ADMS_FIELDS.find((af) => af.value === f);
              return <li key={f}>{fieldDef?.label ?? f}</li>;
            })}
          </ul>
        </div>
      )}

      {/* Mapping summary */}
      {mappedEntries.length > 0 && (
        <div className="text-sm text-gray-600 dark:text-gray-400">
          <span className="font-medium">{mappedEntries.length}</span> of{' '}
          <span className="font-medium">{csvHeaders.length}</span> columns mapped.{' '}
          {csvHeaders.length - mappedEntries.length > 0 && (
            <span>{csvHeaders.length - mappedEntries.length} column{csvHeaders.length - mappedEntries.length !== 1 ? 's' : ''} will be skipped.</span>
          )}
        </div>
      )}

      {/* Preview */}
      {mappedEntries.length > 0 && previewRows.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-3">
            Data Preview
          </h3>
          <p className="text-sm text-gray-500 dark:text-gray-400 mb-2">
            Showing first {previewRows.length} row{previewRows.length !== 1 ? 's' : ''} with mapped fields.
          </p>
          <div className="overflow-x-auto border border-gray-200 dark:border-gray-700 rounded-lg">
            <table className="w-full text-left text-sm">
              <thead className="bg-gray-50 dark:bg-gray-900">
                <tr>
                  <th scope="col" className="px-3 py-2 text-xs text-gray-500 dark:text-gray-400 font-medium border-b border-gray-200 dark:border-gray-700">
                    Row
                  </th>
                  {mappedEntries.map(([csvCol, admsField]) => {
                    const fieldDef = ADMS_FIELDS.find((f) => f.value === admsField);
                    return (
                      <th
                        key={csvCol}
                        scope="col"
                        className="px-3 py-2 text-xs text-gray-500 dark:text-gray-400 font-medium border-b border-gray-200 dark:border-gray-700"
                      >
                        <span className="block text-gray-900 dark:text-gray-100">
                          {fieldDef?.label ?? admsField}
                        </span>
                        <span className="block text-gray-400 dark:text-gray-500 font-normal">
                          from: {csvCol}
                        </span>
                      </th>
                    );
                  })}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                {previewRows.map((row, idx) => (
                  <tr key={idx} className="bg-white dark:bg-gray-800">
                    <td className="px-3 py-2 text-gray-400 dark:text-gray-500 text-xs font-mono">
                      {idx + 1}
                    </td>
                    {mappedEntries.map(([csvCol]) => (
                      <td
                        key={csvCol}
                        className="px-3 py-2 text-gray-700 dark:text-gray-300 text-xs max-w-[200px] truncate"
                      >
                        {row[csvCol] ?? ''}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Confirm button */}
      <div className="flex justify-end">
        <button
          type="button"
          onClick={handleConfirm}
          disabled={!isValid}
          className="min-h-[44px] inline-flex items-center px-6 py-2 rounded bg-blue-700 hover:bg-blue-800 text-white font-medium text-sm disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-[var(--color-focus,#005fcc)] focus:ring-offset-2"
          aria-describedby={!isValid ? 'mapper-validation-hint' : undefined}
        >
          Confirm Mapping
        </button>
      </div>
      {!isValid && (
        <p id="mapper-validation-hint" className="sr-only">
          Cannot confirm mapping because required fields are not yet mapped.
        </p>
      )}
    </div>
  );
}
