import { useQuery } from '@tanstack/react-query';
import { fetchDashboardStats } from '@/api/dashboard';
import { Card, CardHeader, CardTitle } from '@/components/ui/Card';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { Alert } from '@/components/ui/Alert';
import { useAuth } from '@/providers/AuthProvider';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts';

const COLORS = ['#7c3aed', '#22c55e', '#f59e0b', '#ef4444', '#3b82f6'];

export const Dashboard = () => {
  const { user } = useAuth();
  const { data, isLoading, error } = useQuery({
    queryKey: ['dashboard'],
    queryFn: fetchDashboardStats,
  });

  if (isLoading) return <LoadingSpinner />;
  if (error) return <Alert>{(error as Error).message}</Alert>;

  const stats = data!;

  const resourceChartData = Object.entries(stats.resource_counts).map(([key, value]) => ({
    name: key.replace(/_/g, ' '),
    value: value as number,
  }));

  const roleChartData = Object.entries(stats.user_stats.by_role).map(([key, value]) => ({
    name: key,
    value,
  }));

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
      <p className="text-gray-600">Welcome back, {user?.users_first_name}.</p>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader>
            <CardTitle>Total Users</CardTitle>
            <p className="text-3xl font-bold text-violet-600">{stats.user_stats.total}</p>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Verified Users</CardTitle>
            <p className="text-3xl font-bold text-green-600">{stats.user_stats.verified}</p>
          </CardHeader>
        </Card>
        {resourceChartData.map((resource) => (
          <Card key={resource.name}>
            <CardHeader>
              <CardTitle className="capitalize">{resource.name}</CardTitle>
              <p className="text-3xl font-bold text-gray-900">{resource.value}</p>
            </CardHeader>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Resources</CardTitle>
          </CardHeader>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={resourceChartData}>
                <XAxis dataKey="name" hide />
                <YAxis />
                <Tooltip />
                <Bar dataKey="value">
                  {resourceChartData.map((_entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Users by Role</CardTitle>
          </CardHeader>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={roleChartData} dataKey="value" nameKey="name" outerRadius={80}>
                  {roleChartData.map((_entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>
    </div>
  );
};
