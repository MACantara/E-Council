import { useForm } from 'react-hook-form';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '@/providers/AuthProvider';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { Alert } from '@/components/ui/Alert';
import { useState } from 'react';

interface LoginForm {
  users_username_or_email: string;
  users_password: string;
}

export const Login = () => {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [error, setError] = useState<string | null>(null);
  const { register, handleSubmit, formState } = useForm<LoginForm>();

  const onSubmit = async (data: LoginForm) => {
    try {
      await login(data);
      navigate('/');
    } catch (err) {
      setError((err as Error).message || 'Login failed');
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4">
      <Card className="w-full max-w-md">
        <h1 className="mb-2 text-2xl font-bold text-gray-900">Log in</h1>
        <p className="mb-6 text-sm text-gray-600">
          Welcome back to {import.meta.env.VITE_APP_TITLE || 'E-Council'}.
        </p>

        {error && <Alert className="mb-4">{error}</Alert>}

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">Username or Email</label>
            <Input {...register('users_username_or_email', { required: true })} />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Password</label>
            <Input type="password" {...register('users_password', { required: true })} />
          </div>
          <Button type="submit" className="w-full" disabled={formState.isSubmitting}>
            {formState.isSubmitting ? 'Logging in...' : 'Log in'}
          </Button>
        </form>

        <div className="mt-4 text-center text-sm text-gray-600">
          Don&apos;t have an account?{' '}
          <Link to="/register" className="text-violet-600 hover:underline">
            Sign up
          </Link>
        </div>
      </Card>
    </div>
  );
};
