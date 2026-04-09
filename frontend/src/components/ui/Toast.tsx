/** Toast notification region with aria-live="polite". */
import { useUIStore, type Toast as ToastType } from '../../stores/ui';

const typeStyles = {
  success: 'bg-green-50 border-green-500 text-green-800 dark:bg-green-900/30 dark:text-green-200',
  error: 'bg-red-50 border-red-500 text-red-800 dark:bg-red-900/30 dark:text-red-200',
  warning: 'bg-yellow-50 border-yellow-500 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-200',
  info: 'bg-blue-50 border-blue-500 text-blue-800 dark:bg-blue-900/30 dark:text-blue-200',
};

function ToastItem({ toast }: { toast: ToastType }) {
  const { removeToast } = useUIStore();

  return (
    <div
      className={`flex items-center justify-between p-3 border-l-4 rounded-md shadow-md mb-2 ${typeStyles[toast.type]}`}
      role="status"
    >
      <span>{toast.message}</span>
      <button
        onClick={() => removeToast(toast.id)}
        aria-label="Dismiss notification"
        className="ml-3 p-1 hover:opacity-70 min-h-[24px] min-w-[24px]"
      >
        <span aria-hidden="true">&times;</span>
      </button>
    </div>
  );
}

export default function ToastContainer() {
  const { toasts } = useUIStore();

  return (
    <div
      aria-live="polite"
      aria-atomic="true"
      className="fixed bottom-4 right-4 z-50 w-96 max-w-[calc(100vw-2rem)]"
    >
      {toasts.map((toast) => (
        <ToastItem key={toast.id} toast={toast} />
      ))}
    </div>
  );
}
