import { BrowserRouter } from 'react-router-dom';
import { Toaster } from 'sonner';
import { AuthProvider } from '@/providers/AuthProvider';
import { QueryProvider } from '@/providers/QueryProvider';
import { ThemeProvider } from '@/providers/ThemeProvider';
import { ErrorBoundary } from '@/components/layout/ErrorBoundary';
import { AppRoutes } from '@/routes';

function App() {
  return (
    <BrowserRouter>
      <QueryProvider>
        <ThemeProvider>
          <AuthProvider>
            <ErrorBoundary>
              <AppRoutes />
            </ErrorBoundary>
            <Toaster position="top-right" richColors />
          </AuthProvider>
        </ThemeProvider>
      </QueryProvider>
    </BrowserRouter>
  );
}

export default App;
