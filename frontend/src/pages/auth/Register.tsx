import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Link, useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { z } from 'zod';
import { useAuth } from '@/providers/AuthProvider';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { ROLE_OPTIONS } from '@/config/resources';

const registerSchema = z
  .object({
    users_first_name: z.string().min(1, 'First name is required'),
    users_last_name: z.string().min(1, 'Last name is required'),
    users_username: z.string().min(1, 'Username is required'),
    users_email: z.string().min(1, 'Email is required').email('Enter a valid email'),
    users_password: z.string().min(8, 'Password must be at least 8 characters'),
    users_repeat_password: z.string().min(1, 'Please repeat your password'),
    users_role: z.string().min(1, 'Role is required'),
    users_department_name: z.string().min(1, 'Department is required'),
  })
  .refine((data) => data.users_password === data.users_repeat_password, {
    message: 'Passwords do not match',
    path: ['users_repeat_password'],
  });

type RegisterForm = z.infer<typeof registerSchema>;

export const Register = () => {
  const navigate = useNavigate();
  const { register: registerUser } = useAuth();
  const { register, handleSubmit, formState } = useForm<RegisterForm>({
    resolver: zodResolver(registerSchema),
  });

  const onSubmit = async (data: RegisterForm) => {
    try {
      await registerUser(data);
      toast.success('Account created successfully. Please log in.');
      navigate('/login');
    } catch (err) {
      toast.error((err as Error).message || 'Registration failed');
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4 py-12 dark:bg-gray-900">
      <Card className="w-full max-w-lg">
        <h1 className="mb-2 text-2xl font-bold text-gray-900 dark:text-white">Create an account</h1>
        <p className="mb-6 text-sm text-gray-600 dark:text-gray-300">
          Join {import.meta.env.VITE_APP_TITLE || 'E-Council'}.
        </p>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                First Name
              </label>
              <Input {...register('users_first_name')} />
              {formState.errors.users_first_name && (
                <p className="mt-1 text-sm text-red-600">
                  {formState.errors.users_first_name.message}
                </p>
              )}
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                Last Name
              </label>
              <Input {...register('users_last_name')} />
              {formState.errors.users_last_name && (
                <p className="mt-1 text-sm text-red-600">
                  {formState.errors.users_last_name.message}
                </p>
              )}
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Username
            </label>
            <Input {...register('users_username')} />
            {formState.errors.users_username && (
              <p className="mt-1 text-sm text-red-600">{formState.errors.users_username.message}</p>
            )}
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Email
            </label>
            <Input type="email" {...register('users_email')} />
            {formState.errors.users_email && (
              <p className="mt-1 text-sm text-red-600">{formState.errors.users_email.message}</p>
            )}
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Department
            </label>
            <Input {...register('users_department_name')} />
            {formState.errors.users_department_name && (
              <p className="mt-1 text-sm text-red-600">
                {formState.errors.users_department_name.message}
              </p>
            )}
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Role
            </label>
            <Select options={ROLE_OPTIONS} {...register('users_role')} />
            {formState.errors.users_role && (
              <p className="mt-1 text-sm text-red-600">{formState.errors.users_role.message}</p>
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
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Repeat Password
            </label>
            <Input type="password" {...register('users_repeat_password')} />
            {formState.errors.users_repeat_password && (
              <p className="mt-1 text-sm text-red-600">
                {formState.errors.users_repeat_password.message}
              </p>
            )}
          </div>
          <Button type="submit" className="w-full" disabled={formState.isSubmitting}>
            {formState.isSubmitting ? 'Creating account...' : 'Sign up'}
          </Button>
        </form>

        <div className="mt-4 text-center text-sm text-gray-600 dark:text-gray-300">
          Already have an account?{' '}
          <Link to="/login" className="text-violet-600 hover:underline">
            Log in
          </Link>
        </div>
      </Card>
    </div>
  );
};
