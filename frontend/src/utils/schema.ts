import { z } from 'zod';
import type { FieldConfig } from '@/components/forms/Field';

const stringField = (label: string, required?: boolean) =>
  required ? z.string().min(1, { message: `${label} is required` }) : z.string();

const numberField = (label: string, required?: boolean) => {
  const base = z.union([z.string(), z.number()]);
  const schema = required
    ? base.refine(
        (val) => val !== '' && val !== undefined && val !== null && !Number.isNaN(Number(val)),
        {
          message: `${label} is required`,
        }
      )
    : base.optional();

  return schema.transform((val) => {
    if (val === '' || val === undefined || val === null || val === undefined) return undefined;
    const num = Number(val);
    return Number.isNaN(num) ? undefined : num;
  });
};

export const buildResourceSchema = (fields: FieldConfig[]) => {
  const shape: Record<string, z.ZodType<unknown>> = {};

  for (const field of fields) {
    if (field.type === 'number') {
      shape[field.name] = numberField(field.label, field.required) as z.ZodType<unknown>;
    } else {
      shape[field.name] = stringField(field.label, field.required) as z.ZodType<unknown>;
    }
  }

  return z.object(shape);
};

export type ResourceSchema = ReturnType<typeof buildResourceSchema>;
