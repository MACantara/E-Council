import { useParams, useNavigate, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { fetchResource, deleteResource } from '@/api/resources';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { Alert } from '@/components/ui/Alert';
import { Badge } from '@/components/ui/Badge';
import type { CrudConfig, CrudListField } from './CrudList';

interface CrudDetailProps {
  config: CrudConfig;
}

export const CrudDetail = ({ config }: CrudDetailProps) => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data, isLoading, error } = useQuery({
    queryKey: [config.endpoint, id],
    queryFn: () => fetchResource(config.endpoint, id!),
  });

  const handleDelete = async () => {
    if (!confirm('Are you sure?')) return;
    await deleteResource(config.endpoint, id!);
    navigate(config.baseRoute);
  };

  if (isLoading) return <LoadingSpinner />;
  if (error) return <Alert>{(error as Error).message}</Alert>;

  const item = data?.data as Record<string, unknown>;

  const renderValue = (field: CrudListField) => {
    const value = item[field.key];
    if (field.type === 'status' && typeof value === 'string') {
      return <Badge>{value}</Badge>;
    }
    if (field.type === 'date' && typeof value === 'string') {
      return new Date(value).toLocaleString();
    }
    return String(value ?? '');
  };

  return (
    <Card>
      <div className="mb-6 flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900">{config.title} Details</h2>
        <div className="flex gap-2">
          <Link to={`${config.baseRoute}/${id}/edit`}>
            <Button variant="secondary">Edit</Button>
          </Link>
          <Button variant="danger" onClick={handleDelete}>
            Delete
          </Button>
        </div>
      </div>

      <dl className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        {config.listFields.map((field) => (
          <div key={field.key}>
            <dt className="text-sm font-medium text-gray-500">{field.label}</dt>
            <dd className="mt-1 text-base text-gray-900">{renderValue(field)}</dd>
          </div>
        ))}
      </dl>
    </Card>
  );
};
