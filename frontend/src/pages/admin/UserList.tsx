import { useQuery } from '@tanstack/react-query';
import { fetchUsers } from '@/api/admin';
import { Card } from '@/components/ui/Card';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { Alert } from '@/components/ui/Alert';
import { Badge } from '@/components/ui/Badge';

export const UserList = () => {
  const { data, isLoading, error } = useQuery({
    queryKey: ['users'],
    queryFn: () => fetchUsers(),
  });

  if (isLoading) return <LoadingSpinner />;
  if (error) return <Alert>{(error as Error).message}</Alert>;

  const users = data?.items ?? [];

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-gray-900">Users</h1>
      <Card>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-gray-200">
              <tr>
                <th className="pb-3">Name</th>
                <th className="pb-3">Username</th>
                <th className="pb-3">Email</th>
                <th className="pb-3">Role</th>
                <th className="pb-3">Verified</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {users.map((user) => (
                <tr key={user.users_id}>
                  <td className="py-3">{user.users_first_name} {user.users_last_name}</td>
                  <td className="py-3">{user.users_username}</td>
                  <td className="py-3">{user.users_email}</td>
                  <td className="py-3">
                    <Badge>{user.users_role}</Badge>
                  </td>
                  <td className="py-3">{user.users_email_verified ? 'Yes' : 'No'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
};
