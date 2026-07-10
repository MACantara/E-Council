import { useQuery } from '@tanstack/react-query';
import { useNavigate, Link } from 'react-router-dom';
import { fetchResources, deleteResource } from '@/api/resources';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { EmptyState } from '@/components/ui/EmptyState';
import { Alert } from '@/components/ui/Alert';
import { Card } from '@/components/ui/Card';

import { Edit, Trash, Eye, Plus } from 'lucide-react';

export interface CrudListField {
  key: string;
  label: string;
  type?: 'text' | 'status' | 'date';
}

export interface CrudConfig {
  title: string;
  endpoint: string;
  baseRoute: string;
  idField: string;
  listFields: CrudListField[];
  statusField?: string;
}

interface CrudListProps {
  config: CrudConfig;
  createLabel?: string;
}

export const CrudList = ({ config, createLabel = 'Create' }: CrudListProps) => {
  const navigate = useNavigate();
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: [config.endpoint],
    queryFn: () => fetchResources(config.endpoint),
  });

  const handleDelete = async (id: string | number) => {
    if (!confirm('Are you sure you want to delete this item?')) return;
    await deleteResource(config.endpoint, id);
    refetch();
  };

  const renderCell = (item: Record<string, unknown>, field: CrudListField) => {
    const value = item[field.key];
    if (field.type === 'status' && typeof value === 'string') {
      return <Badge>{value}</Badge>;
    }
    if (field.type === 'date' && typeof value === 'string') {
      return new Date(value).toLocaleString();
    }
    return String(value ?? '');
  };

  if (isLoading) return <LoadingSpinner />;
  if (error) return <Alert>Error loading {config.title.toLowerCase()}. {(error as Error).message}</Alert>;

  const items = data?.data?.items ?? [];

  return (
    <Card>
      <div className="mb-6 flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900">{config.title}</h2>
        <Link to={`${config.baseRoute}/create`}>
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            {createLabel}
          </Button>
        </Link>
      </div>

      {items.length === 0 ? (
        <EmptyState
          title={`No ${config.title.toLowerCase()} found`}
          description={`Create your first ${config.title.toLowerCase()} to get started.`}
        />
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-gray-200">
              <tr>
                {config.listFields.map((field) => (
                  <th key={field.key} className="pb-3 font-semibold text-gray-700">
                    {field.label}
                  </th>
                ))}
                <th className="pb-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {items.map((item) => {
                const id = item[config.idField];
                return (
                  <tr key={String(id)}>
                    {config.listFields.map((field) => (
                      <td key={field.key} className="py-3">
                        {renderCell(item as Record<string, unknown>, field)}
                      </td>
                    ))}
                    <td className="py-3 text-right">
                      <div className="flex justify-end gap-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => navigate(`${config.baseRoute}/${id}`)}
                        >
                          <Eye className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => navigate(`${config.baseRoute}/${id}/edit`)}
                        >
                          <Edit className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDelete(String(id))}
                        >
                          <Trash className="h-4 w-4 text-red-600" />
                        </Button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </Card>
  );
};
