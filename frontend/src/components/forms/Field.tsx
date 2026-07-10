import { Input } from '@/components/ui/Input';
import { Textarea } from '@/components/ui/Textarea';
import { Select, type SelectOption } from '@/components/ui/Select';
import { type Control, type FieldValues, type Path, Controller } from 'react-hook-form';

export interface FieldConfig {
  name: string;
  label: string;
  type?: 'text' | 'textarea' | 'select' | 'datetime-local' | 'number' | 'email' | 'password' | 'date';
  options?: SelectOption[];
  required?: boolean;
  placeholder?: string;
}

interface FieldProps<T extends FieldValues> {
  config: FieldConfig;
  control: Control<T>;
}

const toInputValue = (value: unknown): string | number => {
  if (value === null || value === undefined) return '';
  if (typeof value === 'number') return value;
  if (typeof value === 'string') return value;
  return String(value);
};

export const Field = <T extends FieldValues>({ config, control }: FieldProps<T>) => {
  return (
    <Controller
      name={config.name as Path<T>}
      control={control}
      rules={{ required: config.required ? `${config.label} is required` : false }}
      render={({ field, fieldState }) => (
        <div className="space-y-1">
          <label htmlFor={config.name} className="block text-sm font-medium text-gray-700">
            {config.label}
            {config.required && <span className="text-red-500"> *</span>}
          </label>
          {config.type === 'textarea' ? (
            <Textarea
              id={config.name}
              placeholder={config.placeholder}
              value={toInputValue(field.value)}
              onChange={(e) => field.onChange(e.target.value)}
            />
          ) : config.type === 'select' ? (
            <Select
              id={config.name}
              options={config.options || []}
              value={toInputValue(field.value)}
              onChange={(e) => field.onChange(e.target.value)}
            />
          ) : (
            <Input
              id={config.name}
              type={config.type || 'text'}
              placeholder={config.placeholder}
              value={toInputValue(field.value)}
              onChange={(e) =>
                field.onChange(config.type === 'number' ? Number(e.target.value) : e.target.value)
              }
            />
          )}
          {fieldState.error && (
            <p className="text-sm text-red-600">{fieldState.error.message}</p>
          )}
        </div>
      )}
    />
  );
};
