import { Component, type ErrorInfo, type ReactNode } from 'react';
import { toast } from 'sonner';
import { AlertTriangle } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardTitle } from '@/components/ui/Card';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, info);
    toast.error('An unexpected error occurred. Please refresh the page.');
  }

  handleReload = () => {
    window.location.reload();
  };

  handleGoHome = () => {
    window.location.href = '/';
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex min-h-screen items-center justify-center bg-gray-50 p-6 dark:bg-gray-900">
          <Card className="max-w-md text-center">
            <CardHeader>
              <AlertTriangle className="mx-auto h-12 w-12 text-red-500" />
              <CardTitle>Something went wrong</CardTitle>
            </CardHeader>
            <p className="mb-6 text-gray-600 dark:text-gray-300">
              {this.state.error?.message || 'An unexpected error occurred.'}
            </p>
            <div className="flex justify-center gap-3">
              <Button variant="secondary" onClick={this.handleGoHome}>
                Go home
              </Button>
              <Button onClick={this.handleReload}>Reload page</Button>
            </div>
          </Card>
        </div>
      );
    }

    return this.props.children;
  }
}
