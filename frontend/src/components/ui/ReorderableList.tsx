/**
 * Reusable list component with Up/Down buttons for keyboard-accessible
 * reordering. Satisfies WCAG 2.5.7 (Dragging Movements) by providing
 * a non-drag alternative for every reorderable list in the application.
 */
import { useState, useCallback, useRef, type ReactNode } from 'react';

export interface ReorderableItem {
  /** Unique identifier for the item. */
  id: string | number;
  /** Display label for the item, used in ARIA labels for move buttons. */
  label: string;
}

interface ReorderableListProps<T extends ReorderableItem> {
  /** The items to render in the list. */
  items: T[];
  /** Called with the new array after a reorder action. */
  onReorder: (items: T[]) => void;
  /** Render function for each item's content. */
  renderItem: (item: T, index: number) => ReactNode;
  /** Accessible label for the list as a whole. */
  ariaLabel?: string;
}

export default function ReorderableList<T extends ReorderableItem>({
  items,
  onReorder,
  renderItem,
  ariaLabel = 'Reorderable list',
}: ReorderableListProps<T>) {
  const [announcement, setAnnouncement] = useState('');
  const buttonRefs = useRef<Map<string, HTMLButtonElement>>(new Map());

  const setButtonRef = useCallback(
    (key: string) => (el: HTMLButtonElement | null) => {
      if (el) {
        buttonRefs.current.set(key, el);
      } else {
        buttonRefs.current.delete(key);
      }
    },
    []
  );

  const moveItem = useCallback(
    (index: number, direction: 'up' | 'down') => {
      const newIndex = direction === 'up' ? index - 1 : index + 1;
      if (newIndex < 0 || newIndex >= items.length) return;

      const newItems = [...items];
      const [moved] = newItems.splice(index, 1);
      newItems.splice(newIndex, 0, moved);
      onReorder(newItems);

      const position = newIndex + 1;
      const total = items.length;
      setAnnouncement(
        `${moved.label} moved ${direction}. Now at position ${position} of ${total}.`
      );

      // Focus the corresponding button on the moved item at its new position
      requestAnimationFrame(() => {
        const buttonKey = `${moved.id}-${direction}`;
        const button = buttonRefs.current.get(buttonKey);
        if (button && !button.disabled) {
          button.focus();
        } else {
          // If the button is now disabled (item at boundary), focus the other direction button
          const altDirection = direction === 'up' ? 'down' : 'up';
          const altButton = buttonRefs.current.get(`${moved.id}-${altDirection}`);
          altButton?.focus();
        }
      });
    },
    [items, onReorder]
  );

  if (items.length === 0) {
    return (
      <div
        role="list"
        aria-label={ariaLabel}
        className="text-sm text-gray-500 dark:text-gray-400 py-4 text-center"
      >
        No items
      </div>
    );
  }

  return (
    <>
      {/* Screen reader live region for reorder announcements */}
      <div
        role="status"
        aria-live="assertive"
        aria-atomic="true"
        className="sr-only"
      >
        {announcement}
      </div>

      <ul role="list" aria-label={ariaLabel} className="space-y-1">
        {items.map((item, index) => {
          const isFirst = index === 0;
          const isLast = index === items.length - 1;

          return (
            <li
              key={item.id}
              role="listitem"
              className="flex items-center gap-2 rounded border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-3 py-2"
            >
              {/* Move buttons */}
              <div className="flex flex-col gap-0.5 flex-shrink-0">
                <button
                  ref={setButtonRef(`${item.id}-up`)}
                  type="button"
                  disabled={isFirst}
                  onClick={() => moveItem(index, 'up')}
                  aria-label={`Move ${item.label} up`}
                  className="min-h-[24px] min-w-[24px] flex items-center justify-center rounded text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-30 disabled:cursor-not-allowed focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)]"
                >
                  <svg
                    aria-hidden="true"
                    className="w-4 h-4"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth={2}
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M5 15l7-7 7 7"
                    />
                  </svg>
                </button>
                <button
                  ref={setButtonRef(`${item.id}-down`)}
                  type="button"
                  disabled={isLast}
                  onClick={() => moveItem(index, 'down')}
                  aria-label={`Move ${item.label} down`}
                  className="min-h-[24px] min-w-[24px] flex items-center justify-center rounded text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-30 disabled:cursor-not-allowed focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)]"
                >
                  <svg
                    aria-hidden="true"
                    className="w-4 h-4"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth={2}
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M19 9l-7 7-7-7"
                    />
                  </svg>
                </button>
              </div>

              {/* Item content */}
              <div className="flex-1 min-w-0">{renderItem(item, index)}</div>
            </li>
          );
        })}
      </ul>
    </>
  );
}
