import { useForm } from 'react-hook-form';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '@/providers/AuthProvider';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { Alert } from '@/components/ui/Alert';
import { useState } from 'react';
import { ROLE_OPTIONS } from '@/config/resources';

interface RegisterForm {
  users_first_name: string;
  users_last_name: string;
  users_username: string;
  users_email: string;
  users_password: string;
  users_repeat_password: string;
  users_role: string;
  users_department_name: string;
}

export const Register = () => {
  const navigate = useNavigate();
  const { register: registerUser } = useAuth();
  const [error, setError] = useState<string | null>(null);
  const { register, handleSubmit, formState } = useForm<RegisterForm>();

  const onSubmit = async (data: RegisterForm) => {
    if (data.users_password !== data.users_repeat_password) {
      setError('Passwords do not match');
      return;
    }
    try {
      await registerUser(data);
      navigate('/login');
    } catch (err) {
      setError((err as Error).message || 'Registration failed');
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4 py-12">
      <Card className="w-full max-w-lg">
        <h1 className="mb-2 text-2xl font-bold text-gray-900">Create an account</h1>
        <p className="mb-6 text-sm text-gray-600">
          Join {import.meta.env.VITE_APP_TITLE || 'E-Council'}.
        </p>

        {error && <Alert className="mb-4">{error}</Alert>}

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">First Name</label>
              <Input {...register('users_first_name', { required: true })} />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Last Name</label>
              <Input {...register('users_last_name', { required: true })} />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Username</label>
            <Input {...register('users_username', { required: true })} />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Email</label>
            <Input type="email" {...register('users_email', { required: true })} />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Department</label>
            <Input {...register('users_department_name', { required: true })} />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Role</label>
            <Select
              options={ROLE_OPTIONS}
              {...register('users_role', { required: true })}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Password</label>
            <Input type="password" {...register('users_password', { required: true })} />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Repeat Password</label>
            <Input type="password" {...register('users_repeat_password', { required: true })} />
          </div>
          <Button type="submit" className="w-full" disabled={formState.isSubmitting}>
            {formState.isSubmitting ? 'Creating account...' : 'Sign up'}
          </Button>
        </form>

        <div className="mt-4 text-center text-sm text-gray-600">
          Already have an account?{' '}
          <Link to="/login" className="text-violet-600 hover:underline">
            Log in
          </Link>
        </div>
      </Card>
    </div>
  );
};
