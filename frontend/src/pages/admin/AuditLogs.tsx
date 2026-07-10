import { useQuery } from '@tanstack/react-query';
import { fetchAuditLogs } from '@/api/admin';
import { Card } from '@/components/ui/Card';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { Alert } from '@/components/ui/Alert';

export const AuditLogs = () => {
  const { data, isLoading, error } = useQuery({
    queryKey: ['audit-logs'],
    queryFn: () => fetchAuditLogs(),
  });

  if (isLoading) return <LoadingSpinner />;
  if (error) return <Alert>{(error as Error).message}</Alert>;

  const logs = data?.items ?? [];

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-gray-900">Audit Logs</h1>
      <Card>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-gray-200">
              <tr>
                <th className="pb-3">Timestamp</th>
                <th className="pb-3">Action</th>
                <th className="pb-3">Entity</th>
                <th className="pb-3">User</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {logs.map((log) => (
                <tr key={log.audit_log_id}>
                  <td className="py-3">{new Date(log.audit_log_timestamp).toLocaleString()}</td>
                  <td className="py-3">{log.audit_log_action}</td>
                  <td className="py-3">
                    {log.audit_log_entity_type} #{log.audit_log_entity_id}
                  </td>
                  <td className="py-3">
                    {log.user
                      ? `${log.user.users_first_name} ${log.user.users_last_name}`
                      : 'System'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
};
