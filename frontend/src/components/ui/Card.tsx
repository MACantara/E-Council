import { type ReactNode } from 'react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

const cn = (...inputs: ClassValue[]) => twMerge(clsx(inputs));

export const Card = ({ children, className }: { children: ReactNode; className?: string }) => {
  return (
    <div
      className={cn(
        'rounded-xl border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-gray-800',
        className
      )}
    >
      {children}
    </div>
  );
};

export const CardHeader = ({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) => {
  return <div className={cn('mb-4', className)}>{children}</div>;
};

export const CardTitle = ({ children, className }: { children: ReactNode; className?: string }) => {
  return (
    <h3 className={cn('text-xl font-semibold text-gray-900 dark:text-white', className)}>
      {children}
    </h3>
  );
};
