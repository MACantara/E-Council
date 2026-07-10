import { useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { CrudDetail } from '@/components/Crud/CrudDetail';
import { FileUpload } from '@/components/ui/FileUpload';
import { documentation } from '@/config/resources';
import { uploadDocumentationFile, type DocumentationFileType } from '@/api/uploads';
import type { ImageItem } from '@/types';

const FILE_TYPES: { label: string; value: DocumentationFileType }[] = [
  { label: 'Evaluation Image', value: 'evaluation_image' },
  { label: 'Attendance Image', value: 'attendance_image' },
  { label: 'Event Photo', value: 'event_photo' },
];

export const DocumentationDetail = () => {
  const queryClient = useQueryClient();

  const renderImageList = (label: string, images: ImageItem[]) => {
    if (!images.length) return null;
    return (
      <div className="mt-4">
        <h4 className="mb-2 text-sm font-medium text-gray-700 dark:text-gray-300">{label}</h4>
        <div className="flex flex-wrap gap-2">
          {images.map((image, index) => (
            <a key={index} href={image.url} target="_blank" rel="noreferrer">
              <img src={image.url} alt={label} className="h-20 w-20 rounded object-cover" />
            </a>
          ))}
        </div>
      </div>
    );
  };

  const handleUpload = async (id: string, fileType: DocumentationFileType, file: File) => {
    try {
      await uploadDocumentationFile(id, fileType, file);
      toast.success(`${fileType.replace('_', ' ')} uploaded`);
      queryClient.invalidateQueries({ queryKey: [documentation.endpoint, id] });
    } catch (error) {
      toast.error((error as Error)?.message || 'Upload failed');
    }
  };

  return (
    <div className="space-y-6">
      <CrudDetail
        config={documentation}
        renderExtra={(item) => {
          const id = item[documentation.idField] as string;
          return (
            <div className="mt-8 border-t border-gray-200 pt-6 dark:border-gray-700">
              <h3 className="mb-4 text-lg font-semibold text-gray-900 dark:text-white">Files</h3>
              {renderImageList('Evaluation Images', (item.evaluation_images as ImageItem[]) ?? [])}
              {renderImageList('Attendance Images', (item.attendance_images as ImageItem[]) ?? [])}
              {renderImageList('Event Photos', (item.event_photo_images as ImageItem[]) ?? [])}

              <div className="mt-6 space-y-4">
                {FILE_TYPES.map((type) => (
                  <div key={type.value}>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                      Upload {type.label}
                    </label>
                    <FileUpload
                      accept="image/*"
                      label="Upload"
                      onUpload={(file) => handleUpload(id, type.value, file)}
                    />
                  </div>
                ))}
              </div>
            </div>
          );
        }}
      />
    </div>
  );
};
