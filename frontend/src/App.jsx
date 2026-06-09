import { Link, Navigate, Route, Routes } from 'react-router-dom';
import { useAuth } from './auth';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import DashboardPage from './pages/DashboardPage';
import AuditPage from './pages/AuditPage';
import SharePage from './pages/SharePage';
import LinksPage from './pages/LinksPage';
import ProfilePage from './pages/ProfilePage';
import AdminPage from './pages/AdminPage';
import LoadingSpinner from './components/LoadingSpinner';
import NotFoundPage from './pages/NotFoundPage';
import './App.css';

function Protected({ children }) {
  const { user, loading } = useAuth();
  if (loading) return <LoadingSpinner />;
  if (!user) return <Navigate to="/login" replace />;
  return children;
}

function RoleProtected({ roles, children }) {
  const { user, loading } = useAuth();
  if (loading) return <LoadingSpinner />;
  if (!user) return <Navigate to="/login" replace />;
  if (!roles.includes(user.role)) return <Navigate to="/" replace />;
  return children;
}

export default function App() {
  const { user, loading, logout } = useAuth();
  const roleLabel = user ? ({ admin: 'Админ', auditor: 'Аудитор', user: 'Пользователь' }[user.role] || user.role) : '';

  return (
    <div className="app-shell">
      <nav className="navbar">
        <div className="nav-left">
          <Link to="/" className="nav-brand">Secure Share</Link>
          <div className="nav-links">
            {user && <Link className="nav-link" to="/">Файлы</Link>}
            {user && <Link className="nav-link" to="/links">Ссылки</Link>}
            {user && <Link className="nav-link" to="/profile">Профиль</Link>}
            {user && ['admin', 'auditor'].includes(user.role) && <Link className="nav-link" to="/audit">Аудит</Link>}
            {user?.role === 'admin' && <Link className="nav-link" to="/admin">Админ</Link>}
            {!user && <Link className="nav-link" to="/login">Вход</Link>}
            {!user && <Link className="nav-link" to="/register">Регистрация</Link>}
          </div>
        </div>
        <div className="nav-actions">
          {user && <span className="user-pill">{user.username} · {roleLabel}</span>}
          {user && <button className="secondary" onClick={logout}>Выход</button>}
        </div>
      </nav>
      {loading ? (
        <LoadingSpinner />
      ) : (
        <Routes>
          <Route path="/" element={<Protected><DashboardPage /></Protected>} />
          <Route path="/links" element={<Protected><LinksPage /></Protected>} />
          <Route path="/profile" element={<Protected><ProfilePage /></Protected>} />
          <Route path="/admin" element={<RoleProtected roles={['admin']}><AdminPage /></RoleProtected>} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/share/:token" element={<SharePage />} />
          <Route path="/audit" element={<RoleProtected roles={['admin', 'auditor']}><AuditPage /></RoleProtected>} />
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      )}
    </div>
  );
}
