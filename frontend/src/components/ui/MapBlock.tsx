/**
 * Interactive map block using Leaflet.js and OpenStreetMap tiles.
 * Renders geolocated documents as markers on a map with optional popups.
 * Used by ExhibitionBlockRenderer for 'map' block types and by the
 * public document detail page for single-document geolocation display.
 *
 * Keyboard controls and a text list alternative are required per WCAG 2.2
 * and CLAUDE.md section 31.8.
 */
import { useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import { useQuery } from '@tanstack/react-query';
import apiClient from '../../api/client';
import type { Document } from '../../types/api';
import Spinner from './Spinner';
import 'leaflet/dist/leaflet.css';

interface MapBlockProps {
  centerLat: number;
  centerLon: number;
  zoom: number;
  documentIds?: number[];
  showPopups?: boolean;
  basemap?: 'openstreetmap' | 'satellite';
}

interface MapDocument {
  id: number;
  title: string;
  lat: number;
  lon: number;
  date_display: string | null;
  thumbnail_url: string | null;
}

function toMapDocument(doc: Document): MapDocument | null {
  if (doc.geo_latitude === null || doc.geo_longitude === null) return null;

  const firstFile = doc.files?.[0];
  const thumbnailUrl = firstFile?.thumbnail_path
    ? `/api/v1/public/documents/${doc.id}/files/${firstFile.id}/thumbnail`
    : null;

  return {
    id: doc.id,
    title: doc.title,
    lat: doc.geo_latitude,
    lon: doc.geo_longitude,
    date_display: doc.date_display,
    thumbnail_url: thumbnailUrl,
  };
}

export default function MapBlock({
  centerLat,
  centerLon,
  zoom,
  documentIds,
  showPopups = true,
  basemap = 'openstreetmap',
}: MapBlockProps) {
  const [showListView, setShowListView] = useState(false);

  const { data, isLoading, isError } = useQuery({
    queryKey: ['public-map-documents', documentIds],
    queryFn: () =>
      apiClient
        .get<{ items: Document[] }>('/public/search', {
          params: {
            ids: documentIds?.join(','),
            per_page: documentIds?.length ?? 100,
            is_public: 1,
          },
        })
        .then((r) => r.data),
    enabled: documentIds !== undefined && documentIds.length > 0,
  });

  const documents = (data?.items ?? [])
    .map(toMapDocument)
    .filter((d): d is MapDocument => d !== null);

  const tileUrl =
    basemap === 'satellite'
      ? 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'
      : 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png';

  const tileAttribution =
    basemap === 'satellite'
      ? 'Tiles &copy; Esri'
      : '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors';

  if (isLoading) {
    return <Spinner label="Loading map data" />;
  }

  if (isError) {
    return (
      <div
        className="rounded-md border border-[var(--color-error)] bg-red-50 p-4 text-sm text-[var(--color-error)] dark:bg-red-900/20"
        role="alert"
      >
        <p>Unable to load map data.</p>
      </div>
    );
  }

  return (
    <div>
      {/* Toggle between map and list view for accessibility (WCAG 2.2 / section 31.8) */}
      <div className="mb-2 flex justify-end">
        <button
          onClick={() => setShowListView((prev) => !prev)}
          className="text-sm text-[var(--color-link)] underline hover:text-[var(--color-link-visited)] min-h-[44px] px-2 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--color-focus)]"
          aria-pressed={showListView}
        >
          {showListView ? 'View as map' : 'View as list'}
        </button>
      </div>

      {showListView ? (
        <ul
          className="divide-y divide-[var(--color-border)] rounded-lg border border-[var(--color-border)]"
          aria-label="Documents shown on map"
        >
          {documents.map((doc) => (
            <li key={doc.id} className="p-3">
              <a
                href={`/public/documents/${doc.id}`}
                className="text-[var(--color-link)] underline hover:text-[var(--color-link-visited)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--color-focus)]"
              >
                {doc.title}
              </a>
              {doc.date_display && (
                <span className="ml-2 text-sm text-[var(--color-text-muted)]">
                  ({doc.date_display})
                </span>
              )}
            </li>
          ))}
          {documents.length === 0 && (
            <li className="p-3 text-sm text-[var(--color-text-muted)]">
              No geolocated documents available.
            </li>
          )}
        </ul>
      ) : (
        <div
          role="application"
          aria-label={`Map showing ${documents.length} document locations`}
          className="h-[400px] rounded-lg overflow-hidden border border-[var(--color-border)]"
        >
          <MapContainer
            center={[centerLat, centerLon]}
            zoom={zoom}
            className="h-full w-full"
            scrollWheelZoom={false}
          >
            <TileLayer url={tileUrl} attribution={tileAttribution} />
            {documents.map((doc) => (
              <Marker key={doc.id} position={[doc.lat, doc.lon]}>
                {showPopups && (
                  <Popup>
                    <a
                      href={`/public/documents/${doc.id}`}
                      className="font-medium text-[var(--color-link)]"
                    >
                      {doc.title}
                    </a>
                    {doc.date_display && (
                      <p className="text-xs mt-1">{doc.date_display}</p>
                    )}
                  </Popup>
                )}
              </Marker>
            ))}
          </MapContainer>
        </div>
      )}
    </div>
  );
}
