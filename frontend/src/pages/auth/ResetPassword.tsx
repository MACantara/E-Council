import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useParams, Link } from 'react-router-dom';
import { toast } from 'sonner';
import { z } from 'zod';
import { api } from '@/api/axios';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';

const resetPasswordSchema = z
  .object({
    users_password: z.string().min(8, 'Password must be at least 8 characters'),
    users_repeat_password: z.string().min(1, 'Please repeat your password'),
  })
  .refine((data) => data.users_password === data.users_repeat_password, {
    message: 'Passwords do not match',
    path: ['users_repeat_password'],
  });

type ResetPasswordForm = z.infer<typeof resetPasswordSchema>;

export const ResetPassword = () => {
  const { selector, token } = useParams<{ selector: string; token: string }>();
  const { register, handleSubmit, formState } = useForm<ResetPasswordForm>({
    resolver: zodResolver(resetPasswordSchema),
  });

  const onSubmit = async (data: ResetPasswordForm) => {
    try {
      await api.post(`/api/v1/auth/reset-password/${selector}/${token}`, {
        users_password: data.users_password,
        users_repeat_password: data.users_repeat_password,
      });
      toast.success('Password reset successfully.');
    } catch (err) {
      toast.error((err as Error).message || 'Reset failed');
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4 dark:bg-gray-900">
      <Card className="w-full max-w-md">
        <h1 className="mb-2 text-2xl font-bold text-gray-900 dark:text-white">Reset password</h1>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <Input type="password" placeholder="New password" {...register('users_password')} />
          {formState.errors.users_password && (
            <p className="text-sm text-red-600">{formState.errors.users_password.message}</p>
          )}
          <Input
            type="password"
            placeholder="Repeat password"
            {...register('users_repeat_password')}
          />
          {formState.errors.users_repeat_password && (
            <p className="text-sm text-red-600">{formState.errors.users_repeat_password.message}</p>
          )}
          <Button type="submit" className="w-full" disabled={formState.isSubmitting}>
            Reset password
          </Button>
        </form>
        <div className="mt-4 text-center text-sm">
          <Link to="/login" className="text-violet-600 hover:underline">
            Back to login
          </Link>
        </div>
      </Card>
    </div>
  );
};
