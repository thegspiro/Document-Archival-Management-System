/**
 * Session timeout warning component. Monitors JWT access token expiry
 * (15-minute tokens) and shows a visible, keyboard-accessible warning
 * 2 minutes before expiry, satisfying WCAG 2.2.1 (Timing Adjustable).
 */
import { useState, useEffect, useRef, useCallback } from 'react';
import { useFocusTrap } from '../../hooks/useFocusTrap';
import { useAuthStore } from '../../stores/auth';
import apiClient from '../../api/client';

/** Access token lifetime in milliseconds (15 minutes). */
const TOKEN_LIFETIME_MS = 15 * 60 * 1000;

/** Warning appears this many milliseconds before expiry. */
const WARNING_BEFORE_EXPIRY_MS = 2 * 60 * 1000;

/** Interval for updating the countdown display. */
const COUNTDOWN_INTERVAL_MS = 1000;

export default function SessionTimeout() {
  const { isAuthenticated, logout } = useAuthStore();
  const [showWarning, setShowWarning] = useState(false);
  const [remainingSeconds, setRemainingSeconds] = useState(0);
  const expiryTimestamp = useRef<number>(Date.now() + TOKEN_LIFETIME_MS);
  const warningTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const countdownRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const dialogRef = useFocusTrap<HTMLDivElement>(showWarning);

  const clearTimers = useCallback(() => {
    if (warningTimerRef.current) {
      clearTimeout(warningTimerRef.current);
      warningTimerRef.current = null;
    }
    if (countdownRef.current) {
      clearInterval(countdownRef.current);
      countdownRef.current = null;
    }
  }, []);

  const resetExpiry = useCallback(() => {
    clearTimers();
    setShowWarning(false);
    expiryTimestamp.current = Date.now() + TOKEN_LIFETIME_MS;

    const warningDelay = TOKEN_LIFETIME_MS - WARNING_BEFORE_EXPIRY_MS;
    warningTimerRef.current = setTimeout(() => {
      setShowWarning(true);
      setRemainingSeconds(Math.ceil(WARNING_BEFORE_EXPIRY_MS / 1000));

      countdownRef.current = setInterval(() => {
        const now = Date.now();
        const secondsLeft = Math.max(
          0,
          Math.ceil((expiryTimestamp.current - now) / 1000)
        );
        setRemainingSeconds(secondsLeft);

        if (secondsLeft <= 0) {
          if (countdownRef.current) {
            clearInterval(countdownRef.current);
            countdownRef.current = null;
          }
        }
      }, COUNTDOWN_INTERVAL_MS);
    }, warningDelay);
  }, [clearTimers]);

  useEffect(() => {
    if (!isAuthenticated) {
      clearTimers();
      setShowWarning(false);
      return;
    }
    resetExpiry();
    return () => clearTimers();
  }, [isAuthenticated, resetExpiry, clearTimers]);

  useEffect(() => {
    if (!showWarning) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        handleExtend();
      }
    };
    document.addEventListener('keydown', handler);
    return () => document.removeEventListener('keydown', handler);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [showWarning]);

  const handleExtend = async () => {
    try {
      await apiClient.post('/auth/refresh');
      resetExpiry();
    } catch {
      await logout();
    }
  };

  const handleLogout = async () => {
    clearTimers();
    setShowWarning(false);
    await logout();
  };

  if (!showWarning || !isAuthenticated) return null;

  const minutes = Math.floor(remainingSeconds / 60);
  const seconds = remainingSeconds % 60;
  const timeDisplay =
    minutes > 0
      ? `${minutes} minute${minutes !== 1 ? 's' : ''} and ${seconds} second${seconds !== 1 ? 's' : ''}`
      : `${seconds} second${seconds !== 1 ? 's' : ''}`;

  return (
    <div
      className="fixed inset-0 z-[60] flex items-center justify-center bg-black/50"
      role="dialog"
      aria-modal="true"
      aria-labelledby="session-timeout-title"
      aria-describedby="session-timeout-desc"
    >
      <div
        ref={dialogRef}
        className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-md w-full mx-4 p-6"
      >
        <div className="flex items-center gap-3 mb-4">
          <svg
            className="w-6 h-6 text-[var(--color-warning,#92400e)] flex-shrink-0"
            aria-hidden="true"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <h2
            id="session-timeout-title"
            className="text-lg font-semibold text-gray-900 dark:text-gray-100"
          >
            Session Expiring Soon
          </h2>
        </div>

        <p
          id="session-timeout-desc"
          className="text-sm text-gray-700 dark:text-gray-300 mb-6"
          role="status"
          aria-live="polite"
          aria-atomic="true"
        >
          Your session will expire in{' '}
          <strong className="text-gray-900 dark:text-gray-100">{timeDisplay}</strong>.
          Please extend your session or log out.
        </p>

        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={handleExtend}
            className="min-h-[44px] flex-1 px-4 py-2 rounded bg-blue-700 hover:bg-blue-800 text-white font-medium text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)] focus-visible:ring-offset-2"
          >
            Extend session
          </button>
          <button
            type="button"
            onClick={handleLogout}
            className="min-h-[44px] flex-1 px-4 py-2 rounded border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 font-medium text-sm hover:bg-gray-50 dark:hover:bg-gray-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)] focus-visible:ring-offset-2"
          >
            Log out
          </button>
        </div>
      </div>
    </div>
  );
}
