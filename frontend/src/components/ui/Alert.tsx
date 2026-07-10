import { type ReactNode } from 'react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

const cn = (...inputs: ClassValue[]) => twMerge(clsx(inputs));

interface AlertProps {
  children: ReactNode;
  variant?: 'error' | 'success' | 'warning' | 'info';
  className?: string;
}

export const Alert = ({ children, variant = 'error', className }: AlertProps) => {
  const variants = {
    error: 'bg-red-50 text-red-800 border-red-200',
    success: 'bg-green-50 text-green-800 border-green-200',
    warning: 'bg-yellow-50 text-yellow-800 border-yellow-200',
    info: 'bg-blue-50 text-blue-800 border-blue-200',
  };

  return (
    <div className={cn('rounded-lg border p-4 text-sm', variants[variant], className)} role="alert">
      {children}
    </div>
  );
};
