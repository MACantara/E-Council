import { type ReactNode } from 'react';

export const EmptyState = ({
  title,
  description,
  children,
}: {
  title: string;
  description?: string;
  children?: ReactNode;
}) => {
  return (
    <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-gray-300 bg-gray-50 p-12 text-center">
      <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
      {description && <p className="mt-2 text-sm text-gray-600">{description}</p>}
      {children && <div className="mt-6">{children}</div>}
    </div>
  );
};
