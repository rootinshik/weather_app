import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider } from './context/ThemeContext';
import { UnitsProvider } from './context/UnitsContext';
import { UserProvider } from './context/UserContext';
import { Layout } from './components/Layout';
import { HomePage } from './pages/HomePage';
import { ForecastPage } from './pages/ForecastPage';
import { AdminPage } from './pages/AdminPage';
import { NotFoundPage } from './pages/NotFoundPage';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <UnitsProvider>
          <BrowserRouter>
            <UserProvider>
              <Routes>
                <Route element={<Layout />}>
                  <Route path="/" element={<HomePage />} />
                  <Route path="/forecast" element={<ForecastPage />} />
                  <Route path="/admin" element={<AdminPage />} />
                  <Route path="*" element={<NotFoundPage />} />
                </Route>
              </Routes>
            </UserProvider>
          </BrowserRouter>
        </UnitsProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
}
