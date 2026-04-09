/**
 * Document file viewer with WCAG 2.2 AA compliance.
 * Supports paginated images and PDF display with OCR transcript panel.
 */
import { useState, useCallback } from 'react';
import type { DocumentFile } from '../../types/api';
import Button from './Button';
import Spinner from './Spinner';

interface FileViewerProps {
  documentId: number;
  files: DocumentFile[];
  title: string;
  onRetryOcr?: (fileId: number) => void;
}

export default function FileViewer({ documentId, files, title, onRetryOcr }: FileViewerProps) {
  const [currentFileIndex, setCurrentFileIndex] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [zoom, setZoom] = useState(100);
  const [showTranscript, setShowTranscript] = useState(false);
  const [showAnnotations, setShowAnnotations] = useState(true);

  const currentFile = files[currentFileIndex];
  if (!currentFile) {
    return (
      <div className="bg-gray-100 dark:bg-gray-800 rounded-lg p-8 text-center">
        <p className="text-gray-500">No files available for this document.</p>
      </div>
    );
  }

  const totalPages = currentFile.page_count || 1;
  const isPdf = currentFile.mime_type === 'application/pdf';
  const isImage = currentFile.mime_type?.startsWith('image/');

  const thumbnailUrl = currentFile.thumbnail_path
    ? `/api/v1/documents/${documentId}/files/${currentFile.id}/thumbnail`
    : undefined;
  const fileUrl = `/api/v1/documents/${documentId}/files/${currentFile.id}/download`;

  const getAltText = useCallback(() => {
    if (currentFile.ocr_status === 'complete') {
      return `Page ${currentPage} of ${totalPages}. Transcript available below.`;
    }
    if (currentFile.ocr_status === 'failed') {
      return `Page ${currentPage} of ${totalPages}. No transcript available.`;
    }
    return `Page ${currentPage} of ${totalPages}.`;
  }, [currentFile.ocr_status, currentPage, totalPages]);

  return (
    <div
      role="region"
      aria-label={`Document viewer: ${title}`}
      className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden"
    >
      {/* Toolbar */}
      <div className="flex items-center justify-between p-2 bg-gray-50 dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center gap-2">
          {/* File selector */}
          {files.length > 1 && (
            <select
              value={currentFileIndex}
              onChange={(e) => { setCurrentFileIndex(Number(e.target.value)); setCurrentPage(1); }}
              className="text-sm border border-gray-300 dark:border-gray-600 rounded px-2 py-1 bg-white dark:bg-gray-800 min-h-touch"
              aria-label="Select file"
            >
              {files.map((f, i) => (
                <option key={f.id} value={i}>{f.filename}</option>
              ))}
            </select>
          )}

          {/* Zoom controls */}
          <button
            onClick={() => setZoom((z) => Math.max(25, z - 25))}
            aria-label="Zoom out"
            className="p-2 rounded hover:bg-gray-200 dark:hover:bg-gray-700 min-h-touch min-w-touch flex items-center justify-center"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
            </svg>
          </button>
          <span className="text-sm text-gray-600 dark:text-gray-400 min-w-[3rem] text-center">{zoom}%</span>
          <button
            onClick={() => setZoom((z) => Math.min(400, z + 25))}
            aria-label="Zoom in"
            className="p-2 rounded hover:bg-gray-200 dark:hover:bg-gray-700 min-h-touch min-w-touch flex items-center justify-center"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
          </button>
        </div>

        <div className="flex items-center gap-2">
          {/* Annotation toggle */}
          <button
            onClick={() => setShowAnnotations(!showAnnotations)}
            aria-pressed={showAnnotations}
            aria-label={showAnnotations ? 'Hide annotations' : 'Show annotations'}
            className={`px-3 py-1.5 rounded text-sm min-h-touch ${
              showAnnotations ? 'bg-primary-100 text-primary-700 dark:bg-primary-900/30 dark:text-primary-300' : 'bg-gray-100 dark:bg-gray-700'
            }`}
          >
            Annotations
          </button>

          {/* Transcript toggle */}
          <button
            onClick={() => setShowTranscript(!showTranscript)}
            aria-pressed={showTranscript}
            aria-label={showTranscript ? 'Hide transcript' : 'View transcript'}
            className={`px-3 py-1.5 rounded text-sm min-h-touch ${
              showTranscript ? 'bg-primary-100 text-primary-700 dark:bg-primary-900/30 dark:text-primary-300' : 'bg-gray-100 dark:bg-gray-700'
            }`}
          >
            View Transcript
          </button>
        </div>
      </div>

      {/* Main viewer area */}
      <div className="flex">
        {/* Page thumbnails sidebar */}
        {totalPages > 1 && (
          <div className="w-24 border-r border-gray-200 dark:border-gray-700 overflow-y-auto max-h-[600px] bg-gray-50 dark:bg-gray-900 p-2 space-y-2">
            {Array.from({ length: Math.min(totalPages, 50) }, (_, i) => (
              <button
                key={i + 1}
                onClick={() => setCurrentPage(i + 1)}
                aria-label={`Go to page ${i + 1}`}
                aria-current={currentPage === i + 1 ? 'page' : undefined}
                className={`w-full aspect-[3/4] rounded border text-xs flex items-center justify-center min-h-[24px] ${
                  currentPage === i + 1
                    ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/30'
                    : 'border-gray-300 dark:border-gray-600 hover:border-primary-300'
                }`}
              >
                {i + 1}
              </button>
            ))}
          </div>
        )}

        {/* Image/PDF display */}
        <div className="flex-1 overflow-auto max-h-[600px] flex items-center justify-center bg-gray-100 dark:bg-gray-900 p-4">
          {isPdf ? (
            <iframe
              src={`${fileUrl}#page=${currentPage}`}
              title={getAltText()}
              className="w-full h-[580px] border-0"
              style={{ transform: `scale(${zoom / 100})`, transformOrigin: 'top center' }}
            />
          ) : isImage ? (
            <img
              src={thumbnailUrl || fileUrl}
              alt={getAltText()}
              style={{ width: `${zoom}%`, maxWidth: 'none' }}
              className="object-contain"
            />
          ) : (
            <div className="text-center text-gray-500 p-8">
              <p className="text-lg font-medium">{currentFile.filename}</p>
              <p className="text-sm mt-2">{currentFile.mime_type}</p>
              <a
                href={fileUrl}
                download
                className="mt-4 inline-block px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 min-h-touch"
              >
                Download File
              </a>
            </div>
          )}
        </div>

        {/* Transcript panel */}
        {showTranscript && (
          <div className="w-80 border-l border-gray-200 dark:border-gray-700 overflow-y-auto max-h-[600px] p-4">
            <h3 className="text-sm font-semibold mb-2">OCR Transcript</h3>
            {currentFile.ocr_status === 'complete' && currentFile.ocr_text ? (
              <div className="text-sm whitespace-pre-wrap font-mono text-gray-700 dark:text-gray-300 leading-relaxed">
                {currentFile.ocr_text}
              </div>
            ) : currentFile.ocr_status === 'processing' ? (
              <div className="flex items-center gap-2 text-sm text-gray-500">
                <Spinner size="sm" label="OCR in progress" />
                <span>OCR processing...</span>
              </div>
            ) : currentFile.ocr_status === 'failed' ? (
              <div role="alert" className="space-y-2">
                <p className="text-sm text-red-600 dark:text-red-400">
                  OCR failed: {currentFile.ocr_error || 'Unknown error'}
                </p>
                {onRetryOcr && (
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => onRetryOcr(currentFile.id)}
                  >
                    Retry OCR
                  </Button>
                )}
              </div>
            ) : (
              <p className="text-sm text-gray-500">No transcript available.</p>
            )}
          </div>
        )}
      </div>

      {/* Page navigation */}
      {totalPages > 1 && (
        <nav
          aria-label="Document pages"
          className="flex items-center justify-center gap-4 p-3 bg-gray-50 dark:bg-gray-900 border-t border-gray-200 dark:border-gray-700"
        >
          <button
            onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
            aria-label="Previous page"
            aria-disabled={currentPage <= 1}
            disabled={currentPage <= 1}
            className="p-2 rounded hover:bg-gray-200 dark:hover:bg-gray-700 disabled:opacity-50 min-h-touch min-w-touch flex items-center justify-center"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </button>
          <span aria-current="page" className="text-sm text-gray-700 dark:text-gray-300">
            Page {currentPage} of {totalPages}
          </span>
          <button
            onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
            aria-label="Next page"
            aria-disabled={currentPage >= totalPages}
            disabled={currentPage >= totalPages}
            className="p-2 rounded hover:bg-gray-200 dark:hover:bg-gray-700 disabled:opacity-50 min-h-touch min-w-touch flex items-center justify-center"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </button>
        </nav>
      )}
    </div>
  );
}
