import { useState, type ChangeEvent } from 'react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { Upload } from 'lucide-react';
import { Button } from './Button';

const cn = (...inputs: ClassValue[]) => twMerge(clsx(inputs));

interface FileUploadProps {
  accept?: string;
  onUpload: (file: File) => void | Promise<void>;
  label?: string;
  disabled?: boolean;
  className?: string;
}

export const FileUpload = ({
  accept,
  onUpload,
  label = 'Choose file',
  disabled,
  className,
}: FileUploadProps) => {
  const [file, setFile] = useState<File | null>(null);

  const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files?.[0] || null;
    setFile(selected);
  };

  const handleUpload = async () => {
    if (!file) return;
    await onUpload(file);
    setFile(null);
  };

  return (
    <div className={cn('flex items-center gap-3', className)}>
      <input
        type="file"
        accept={accept}
        onChange={handleChange}
        disabled={disabled}
        className="block w-full text-sm text-gray-700 file:mr-4 file:rounded-lg file:border-0 file:bg-violet-50 file:px-4 file:py-2 file:text-sm file:font-semibold file:text-violet-700 hover:file:bg-violet-100 dark:text-gray-300 dark:file:bg-gray-700 dark:file:text-violet-300"
      />
      <Button type="button" size="sm" disabled={!file || disabled} onClick={handleUpload}>
        <Upload className="mr-2 h-4 w-4" />
        {label}
      </Button>
    </div>
  );
};
