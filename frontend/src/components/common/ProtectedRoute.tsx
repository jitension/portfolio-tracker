/**
 * Protected Route Component
 * Redirects to login if user is not authenticated
 */
import { Navigate } from 'react-router-dom';
import { useAppSelector } from '../../store';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

export const ProtectedRoute = ({ children }: ProtectedRouteProps) => {
  const { isAuthenticated, accessToken } = useAppSelector((state) => state.auth);

  // Check if user has a token
  if (!isAuthenticated && !accessToken) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};

export default ProtectedRoute;
