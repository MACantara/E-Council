import { forwardRef, type InputHTMLAttributes } from 'react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

const cn = (...inputs: ClassValue[]) => twMerge(clsx(inputs));

export const Input = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement>>(
  ({ className, name, ...props }, ref) => {
    return (
      <input
        ref={ref}
        name={name}
        className={cn(
          'w-full rounded-lg border border-gray-300 bg-white px-4 py-2 text-gray-900 placeholder-gray-400 focus:border-violet-500 focus:outline-none focus:ring-2 focus:ring-violet-500/20 dark:border-gray-600 dark:bg-gray-800 dark:text-white dark:placeholder-gray-500',
          className
        )}
        {...props}
      />
    );
  }
);

Input.displayName = 'Input';
