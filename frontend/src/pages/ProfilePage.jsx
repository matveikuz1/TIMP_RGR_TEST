import { useEffect, useState } from 'react';
import api from '../api';
import { useAuth } from '../auth';
import LoadingSpinner from '../components/LoadingSpinner';

export default function ProfilePage() {
  const { user } = useAuth();
  const [email, setEmail] = useState(user?.email || '');
  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    setEmail(user?.email || '');
  }, [user]);

  const onSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setMessage('');
    try {
      await api.put('/users/profile', {
        email: email.trim() || null,
        old_password: oldPassword,
        new_password: newPassword.trim() || null,
      });
      setMessage('Профиль обновлён');
      setOldPassword('');
      setNewPassword('');
    } catch (err) {
      setError(err?.response?.data?.message || 'Не удалось обновить профиль');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={onSubmit} className="card form-card">
      <h2 className="form-title">Профиль</h2>
      <div className="form-field">
        <label className="form-label">Email</label>
        <input value={email} onChange={(e) => setEmail(e.target.value)} />
      </div>
      <div className="form-field">
        <label className="form-label">Текущий пароль</label>
        <input type="password" value={oldPassword} onChange={(e) => setOldPassword(e.target.value)} required />
        <span className="muted">Нужен для подтверждения любых изменений профиля.</span>
      </div>
      <div className="form-field">
        <label className="form-label">Новый пароль</label>
        <input type="password" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} />
      </div>
      <button type="submit" disabled={loading}>Сохранить</button>
      {loading && <LoadingSpinner />}
      {message && <p className="form-success">{message}</p>}
      {error && <p className="form-error">{error}</p>}
    </form>
  );
}
