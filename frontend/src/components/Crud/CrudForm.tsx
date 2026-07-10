import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { useNavigate, useParams } from 'react-router-dom';
import { useQuery, useMutation } from '@tanstack/react-query';
import { createResource, updateResource, createMultipartResource, updateMultipartResource, fetchResource } from '@/api/resources';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Alert } from '@/components/ui/Alert';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { Field } from '@/components/forms/Field';
import type { ResourceDefinition } from '@/config/resources';

interface CrudFormProps {
  config: ResourceDefinition;
}

export const CrudForm = ({ config }: CrudFormProps) => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const isEdit = Boolean(id);

  const emptyValues = Object.fromEntries(
    config.fields.map((field) => [field.name, ''])
  );

  const { data: existing, isLoading } = useQuery({
    queryKey: [config.endpoint, id],
    queryFn: () => fetchResource(config.endpoint, id!),
    enabled: isEdit,
  });

  const { control, handleSubmit, formState, reset } = useForm({
    defaultValues: emptyValues,
  });

  useEffect(() => {
    if (existing?.data) {
      reset(existing.data as Record<string, string>);
    }
  }, [existing, reset]);

  const mutation = useMutation({
    mutationFn: (data: Record<string, unknown>) => {
      const isMultipart = config.contentType === 'multipart';
      if (isEdit) {
        return isMultipart
          ? updateMultipartResource(config.endpoint, id!, data)
          : updateResource(config.endpoint, id!, data);
      }
      return isMultipart
        ? createMultipartResource(config.endpoint, data)
        : createResource(config.endpoint, data);
    },
    onSuccess: () => navigate(config.baseRoute),
  });

  const onSubmit = (data: Record<string, unknown>) => {
    mutation.mutate(data);
  };

  if (isEdit && isLoading) return <LoadingSpinner />;

  return (
    <Card>
      <h2 className="mb-6 text-2xl font-bold text-gray-900">
        {isEdit ? `Edit ${config.title}` : `Create ${config.title}`}
      </h2>

      {mutation.error && (
        <Alert className="mb-4">
          {(mutation.error as Error)?.message || 'Something went wrong.'}
        </Alert>
      )}

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        {config.fields.map((field) => (
          <Field key={field.name} config={field} control={control} />
        ))}

        <div className="flex gap-3 pt-4">
          <Button type="submit" disabled={formState.isSubmitting}>
            {formState.isSubmitting ? 'Saving...' : isEdit ? 'Update' : 'Create'}
          </Button>
          <Button
            type="button"
            variant="secondary"
            onClick={() => navigate(config.baseRoute)}
          >
            Cancel
          </Button>
        </div>
      </form>
    </Card>
  );
};
