export const LoadingSpinner = ({ className }: { className?: string }) => {
  return (
    <div className={`flex items-center justify-center ${className || ''}`}>
      <div className="h-8 w-8 animate-spin rounded-full border-2 border-gray-300 border-t-violet-600" />
    </div>
  );
};
