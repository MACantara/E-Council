import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Link } from 'react-router-dom';
import { toast } from 'sonner';
import { z } from 'zod';
import { api } from '@/api/axios';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';

const forgotPasswordSchema = z.object({
  users_email: z.string().min(1, 'Email is required').email('Enter a valid email'),
});

type ForgotPasswordForm = z.infer<typeof forgotPasswordSchema>;

export const ForgotPassword = () => {
  const { register, handleSubmit, formState } = useForm<ForgotPasswordForm>({
    resolver: zodResolver(forgotPasswordSchema),
  });

  const onSubmit = async (data: ForgotPasswordForm) => {
    try {
      await api.post('/api/v1/auth/forgot-password', data);
      toast.success('Password reset instructions sent.');
    } catch (err) {
      toast.error((err as Error).message || 'Request failed');
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4 dark:bg-gray-900">
      <Card className="w-full max-w-md">
        <h1 className="mb-2 text-2xl font-bold text-gray-900 dark:text-white">Forgot password</h1>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <Input type="email" placeholder="Enter your email" {...register('users_email')} />
          {formState.errors.users_email && (
            <p className="text-sm text-red-600">{formState.errors.users_email.message}</p>
          )}
          <Button type="submit" className="w-full" disabled={formState.isSubmitting}>
            Send reset link
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
