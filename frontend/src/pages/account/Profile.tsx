import { useAuth } from '@/providers/AuthProvider';
import { Card } from '@/components/ui/Card';

export const Profile = () => {
  const { user } = useAuth();

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-gray-900">Account Profile</h1>
      <Card>
        <dl className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <dt className="text-sm font-medium text-gray-500">Name</dt>
            <dd className="text-lg text-gray-900">{user?.users_first_name} {user?.users_last_name}</dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500">Username</dt>
            <dd className="text-lg text-gray-900">{user?.users_username}</dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500">Email</dt>
            <dd className="text-lg text-gray-900">{user?.users_email}</dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500">Role</dt>
            <dd className="text-lg text-gray-900">{user?.users_role}</dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500">Department</dt>
            <dd className="text-lg text-gray-900">{user?.users_department_name}</dd>
          </div>
        </dl>
      </Card>
    </div>
  );
};
