/**
 * Schema.org JSON-LD structured data generators.
 *
 * Produces JSON-LD objects for documents, exhibitions, and collections
 * following the Dublin Core crosswalk defined in CLAUDE.md section 22.
 * These objects are embedded as <script type="application/ld+json"> in
 * public-facing pages to enable search engine understanding of archival content.
 */

import type { Document, Exhibition, ArrangementNode } from '../types/api';

interface JsonLdBase {
  '@context': string;
  '@type': string;
  [key: string]: unknown;
}

/**
 * Generate Schema.org ArchiveComponent JSON-LD for a document.
 *
 * Maps ADMS document fields to Schema.org properties following the
 * Dublin Core crosswalk: name from title, creator from authority record,
 * dateCreated from date_start, description from scope_and_content,
 * identifier from accession_number, inLanguage from language_of_material,
 * holdingArchive from institution name, rights from copyright_status.
 */
export function generateDocumentLD(
  doc: Document,
  institutionName: string,
): JsonLdBase {
  const ld: JsonLdBase = {
    '@context': 'https://schema.org',
    '@type': 'ArchiveComponent',
    name: doc.title,
    identifier: doc.accession_number ?? undefined,
  };

  if (doc.creator) {
    ld.creator = {
      '@type': doc.creator.entity_type === 'organization' ? 'Organization' : 'Person',
      name: doc.creator.authorized_name,
    };
  }

  if (doc.date_start) {
    ld.dateCreated = doc.date_start;
  }

  if (doc.scope_and_content) {
    ld.description = doc.scope_and_content;
  }

  if (doc.language_of_material) {
    ld.inLanguage = doc.language_of_material;
  }

  if (institutionName) {
    ld.holdingArchive = {
      '@type': 'ArchiveOrganization',
      name: institutionName,
    };
  }

  // Rights from copyright_status and rights_note
  const rightsParts: string[] = [];
  if (doc.copyright_status && doc.copyright_status !== 'unknown') {
    rightsParts.push(doc.copyright_status.replace(/_/g, ' '));
  }
  if (doc.rights_note) {
    rightsParts.push(doc.rights_note);
  }
  if (rightsParts.length > 0) {
    ld.rights = rightsParts.join('; ');
  }

  // Geographic location if available
  if (doc.geo_location_name) {
    ld.spatialCoverage = {
      '@type': 'Place',
      name: doc.geo_location_name,
      ...(doc.geo_latitude && doc.geo_longitude
        ? {
            geo: {
              '@type': 'GeoCoordinates',
              latitude: doc.geo_latitude,
              longitude: doc.geo_longitude,
            },
          }
        : {}),
    };
  }

  // Date range as temporal coverage
  if (doc.date_start && doc.date_end && doc.date_start !== doc.date_end) {
    ld.temporalCoverage = `${doc.date_start}/${doc.date_end}`;
  }

  // Extent
  if (doc.extent) {
    ld.materialExtent = doc.extent;
  }

  // Clean undefined values
  return cleanJsonLd(ld);
}

/**
 * Generate Schema.org ExhibitionEvent JSON-LD for an exhibition.
 *
 * Maps exhibition metadata to the ExhibitionEvent type with name, description,
 * organizer (institution), and publication status.
 */
export function generateExhibitionLD(
  exhibition: Exhibition,
  institutionName: string,
): JsonLdBase {
  const ld: JsonLdBase = {
    '@context': 'https://schema.org',
    '@type': 'ExhibitionEvent',
    name: exhibition.title,
  };

  if (exhibition.subtitle) {
    ld.alternateName = exhibition.subtitle;
  }

  if (exhibition.description) {
    ld.description = exhibition.description;
  }

  if (institutionName) {
    ld.organizer = {
      '@type': 'ArchiveOrganization',
      name: institutionName,
    };
  }

  if (exhibition.published_at) {
    ld.startDate = exhibition.published_at;
  }

  if (exhibition.cover_image_path) {
    ld.image = exhibition.cover_image_path;
  }

  return cleanJsonLd(ld);
}

/**
 * Generate Schema.org Collection JSON-LD for an arrangement node.
 *
 * Maps collection hierarchy nodes to the Collection type with name,
 * description, and date range.
 */
export function generateCollectionLD(
  node: ArrangementNode,
  institutionName: string,
): JsonLdBase {
  const ld: JsonLdBase = {
    '@context': 'https://schema.org',
    '@type': 'Collection',
    name: node.title,
    collectionSize: node.level_type,
  };

  if (node.description) {
    ld.description = node.description;
  }

  if (node.identifier) {
    ld.identifier = node.identifier;
  }

  if (institutionName) {
    ld.holdingArchive = {
      '@type': 'ArchiveOrganization',
      name: institutionName,
    };
  }

  // Temporal coverage
  if (node.date_start && node.date_end) {
    ld.temporalCoverage = `${node.date_start}/${node.date_end}`;
  } else if (node.date_start) {
    ld.temporalCoverage = node.date_start;
  }

  return cleanJsonLd(ld);
}

/**
 * Remove undefined values from a JSON-LD object so they do not appear
 * in the serialized output.
 */
function cleanJsonLd(ld: JsonLdBase): JsonLdBase {
  const cleaned: JsonLdBase = { '@context': ld['@context'], '@type': ld['@type'] };
  for (const [key, value] of Object.entries(ld)) {
    if (value !== undefined && value !== null && value !== '') {
      cleaned[key] = value;
    }
  }
  return cleaned;
}
