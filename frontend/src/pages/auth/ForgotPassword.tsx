import { useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '@/api/axios';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { Alert } from '@/components/ui/Alert';

export const ForgotPassword = () => {
  const [email, setEmail] = useState('');
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.post('/api/v1/auth/forgot-password', { users_email: email });
      setMessage('Password reset instructions sent.');
    } catch (err) {
      setError((err as Error).message || 'Request failed');
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4">
      <Card className="w-full max-w-md">
        <h1 className="mb-2 text-2xl font-bold text-gray-900">Forgot password</h1>
        {message && <Alert variant="success" className="mb-4">{message}</Alert>}
        {error && <Alert className="mb-4">{error}</Alert>}
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            type="email"
            placeholder="Enter your email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          <Button type="submit" className="w-full">Send reset link</Button>
        </form>
        <div className="mt-4 text-center text-sm">
          <Link to="/login" className="text-violet-600 hover:underline">Back to login</Link>
        </div>
      </Card>
    </div>
  );
};
