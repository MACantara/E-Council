import { useAuth } from '@/providers/AuthProvider';
import { Card } from '@/components/ui/Card';
import { FileUpload } from '@/components/ui/FileUpload';
import { uploadProfilePicture, uploadSignature } from '@/api/uploads';
import { toast } from 'sonner';

export const Profile = () => {
  const { user, refetchUser } = useAuth();

  const handleUpload = async (uploader: (file: File) => Promise<unknown>, file: File) => {
    try {
      await uploader(file);
      toast.success('Upload successful');
      await refetchUser?.();
    } catch (error) {
      toast.error((error as Error)?.message || 'Upload failed');
    }
  };

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Account Profile</h1>
      <Card>
        <dl className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Name</dt>
            <dd className="text-lg text-gray-900 dark:text-gray-100">
              {user?.users_first_name} {user?.users_last_name}
            </dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Username</dt>
            <dd className="text-lg text-gray-900 dark:text-gray-100">{user?.users_username}</dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Email</dt>
            <dd className="text-lg text-gray-900 dark:text-gray-100">{user?.users_email}</dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Role</dt>
            <dd className="text-lg text-gray-900 dark:text-gray-100">{user?.users_role}</dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Department</dt>
            <dd className="text-lg text-gray-900 dark:text-gray-100">
              {user?.users_department_name}
            </dd>
          </div>
        </dl>

        <div className="mt-8 grid grid-cols-1 gap-6 md:grid-cols-2">
          <div>
            <h3 className="mb-2 text-sm font-medium text-gray-700 dark:text-gray-300">
              Profile Picture
            </h3>
            {user?.profile_picture?.url && (
              <img
                src={user.profile_picture.url}
                alt="Profile"
                className="mb-3 h-24 w-24 rounded-full object-cover"
              />
            )}
            <FileUpload
              accept="image/*"
              label="Upload"
              onUpload={(file) => handleUpload(uploadProfilePicture, file)}
            />
          </div>
          <div>
            <h3 className="mb-2 text-sm font-medium text-gray-700 dark:text-gray-300">Signature</h3>
            {user?.signature?.url && (
              <img
                src={user.signature.url}
                alt="Signature"
                className="mb-3 h-24 rounded border object-contain"
              />
            )}
            <FileUpload
              accept="image/*"
              label="Upload"
              onUpload={(file) => handleUpload(uploadSignature, file)}
            />
          </div>
        </div>
      </Card>
    </div>
  );
};
