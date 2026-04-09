/** Badge component for status indicators and completeness levels. */

interface BadgeProps {
  variant?: 'default' | 'success' | 'warning' | 'error' | 'info' | 'none' | 'minimal' | 'standard' | 'full';
  label: string;
  className?: string;
}

const variantStyles: Record<string, string> = {
  default: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300',
  success: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300',
  warning: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300',
  error: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300',
  info: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300',
  none: 'bg-gray-100 text-gray-600',
  minimal: 'bg-amber-100 text-amber-800',
  standard: 'bg-blue-100 text-blue-800',
  full: 'bg-green-100 text-green-800',
};

export default function Badge({ variant = 'default', label, className = '' }: BadgeProps) {
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${variantStyles[variant] || variantStyles.default} ${className}`}
      role="img"
      aria-label={`Status: ${label}`}
    >
      {label}
    </span>
  );
}
