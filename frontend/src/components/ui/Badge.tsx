import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

const cn = (...inputs: ClassValue[]) => twMerge(clsx(inputs));

interface BadgeProps {
  children: string;
  variant?: 'default' | 'success' | 'warning' | 'danger' | 'info';
}

export const Badge = ({ children, variant = 'default' }: BadgeProps) => {
  const variants = {
    default: 'bg-gray-100 text-gray-800',
    success: 'bg-green-100 text-green-800',
    warning: 'bg-yellow-100 text-yellow-800',
    danger: 'bg-red-100 text-red-800',
    info: 'bg-blue-100 text-blue-800',
  };

  const getVariant = (status: string) => {
    const lower = status.toLowerCase();
    if (lower.includes('done') || lower.includes('approved')) return 'success';
    if (lower.includes('cancel') || lower.includes('reject')) return 'danger';
    if (lower.includes('postpon')) return 'warning';
    if (lower.includes('upcoming')) return 'info';
    return variant;
  };

  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium',
        variants[getVariant(children)]
      )}
    >
      {children}
    </span>
  );
};
