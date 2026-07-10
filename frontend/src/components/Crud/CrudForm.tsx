import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useNavigate, useParams } from 'react-router-dom';
import { useQuery, useMutation } from '@tanstack/react-query';
import { toast } from 'sonner';
import {
  createResource,
  updateResource,
  createMultipartResource,
  updateMultipartResource,
  fetchResource,
} from '@/api/resources';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { Field } from '@/components/forms/Field';
import { buildResourceSchema } from '@/utils/schema';
import type { ResourceDefinition } from '@/config/resources';

interface CrudFormProps {
  config: ResourceDefinition;
}

export const CrudForm = ({ config }: CrudFormProps) => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const isEdit = Boolean(id);

  const emptyValues = Object.fromEntries(config.fields.map((field) => [field.name, '']));

  const { data: existing, isLoading } = useQuery({
    queryKey: [config.endpoint, id],
    queryFn: () => fetchResource(config.endpoint, id!),
    enabled: isEdit,
  });

  const schema = buildResourceSchema(config.fields);

  const { control, handleSubmit, formState, reset } = useForm({
    resolver: zodResolver(schema),
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
    onSuccess: () => {
      toast.success(`${config.title} ${isEdit ? 'updated' : 'created'} successfully`);
      navigate(config.baseRoute);
    },
    onError: (error) => {
      toast.error(error?.message || 'Something went wrong while saving.');
    },
  });

  const onSubmit = (data: Record<string, unknown>) => {
    const cleaned = Object.fromEntries(
      Object.entries(data).filter(
        ([, value]) => value !== '' && value !== null && value !== undefined
      )
    );
    mutation.mutate(cleaned);
  };

  if (isEdit && isLoading) return <LoadingSpinner />;

  return (
    <Card>
      <h2 className="mb-6 text-2xl font-bold text-gray-900 dark:text-white">
        {isEdit ? `Edit ${config.title}` : `Create ${config.title}`}
      </h2>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        {config.fields.map((field) => (
          <Field key={field.name} config={field} control={control} />
        ))}

        <div className="flex gap-3 pt-4">
          <Button type="submit" disabled={formState.isSubmitting}>
            {formState.isSubmitting ? 'Saving...' : isEdit ? 'Update' : 'Create'}
          </Button>
          <Button type="button" variant="secondary" onClick={() => navigate(config.baseRoute)}>
            Cancel
          </Button>
        </div>
      </form>
    </Card>
  );
};
