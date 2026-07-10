import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Link, useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { z } from 'zod';
import { useAuth } from '@/providers/AuthProvider';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';

const loginSchema = z.object({
  users_username_or_email: z.string().min(1, 'Username or email is required'),
  users_password: z.string().min(1, 'Password is required'),
});

type LoginForm = z.infer<typeof loginSchema>;

export const Login = () => {
  const navigate = useNavigate();
  const { login } = useAuth();
  const { register, handleSubmit, formState } = useForm<LoginForm>({
    resolver: zodResolver(loginSchema),
  });

  const onSubmit = async (data: LoginForm) => {
    try {
      await login(data);
      toast.success('Logged in successfully');
      navigate('/');
    } catch (err) {
      toast.error((err as Error).message || 'Login failed');
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4 dark:bg-gray-900">
      <Card className="w-full max-w-md">
        <h1 className="mb-2 text-2xl font-bold text-gray-900 dark:text-white">Log in</h1>
        <p className="mb-6 text-sm text-gray-600 dark:text-gray-300">
          Welcome back to {import.meta.env.VITE_APP_TITLE || 'E-Council'}.
        </p>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Username or Email
            </label>
            <Input {...register('users_username_or_email')} />
            {formState.errors.users_username_or_email && (
              <p className="mt-1 text-sm text-red-600">
                {formState.errors.users_username_or_email.message}
              </p>
            )}
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Password
            </label>
            <Input type="password" {...register('users_password')} />
            {formState.errors.users_password && (
              <p className="mt-1 text-sm text-red-600">{formState.errors.users_password.message}</p>
            )}
          </div>
          <Button type="submit" className="w-full" disabled={formState.isSubmitting}>
            {formState.isSubmitting ? 'Logging in...' : 'Log in'}
          </Button>
        </form>

        <div className="mt-4 text-center text-sm text-gray-600 dark:text-gray-300">
          Don&apos;t have an account?{' '}
          <Link to="/register" className="text-violet-600 hover:underline">
            Sign up
          </Link>
        </div>
      </Card>
    </div>
  );
};
