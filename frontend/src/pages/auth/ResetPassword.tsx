import { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { api } from '@/api/axios';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { Alert } from '@/components/ui/Alert';

export const ResetPassword = () => {
  const { selector, token } = useParams<{ selector: string; token: string }>();
  const [password, setPassword] = useState('');
  const [repeat, setRepeat] = useState('');
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (password !== repeat) {
      setError('Passwords do not match');
      return;
    }
    try {
      await api.post(`/api/v1/auth/reset-password/${selector}/${token}`, {
        users_password: password,
        users_repeat_password: repeat,
      });
      setMessage('Password reset successfully.');
    } catch (err) {
      setError((err as Error).message || 'Reset failed');
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4">
      <Card className="w-full max-w-md">
        <h1 className="mb-2 text-2xl font-bold text-gray-900">Reset password</h1>
        {message && <Alert variant="success" className="mb-4">{message}</Alert>}
        {error && <Alert className="mb-4">{error}</Alert>}
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            type="password"
            placeholder="New password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          <Input
            type="password"
            placeholder="Repeat password"
            value={repeat}
            onChange={(e) => setRepeat(e.target.value)}
            required
          />
          <Button type="submit" className="w-full">Reset password</Button>
        </form>
        <div className="mt-4 text-center text-sm">
          <Link to="/login" className="text-violet-600 hover:underline">Back to login</Link>
        </div>
      </Card>
    </div>
  );
};
