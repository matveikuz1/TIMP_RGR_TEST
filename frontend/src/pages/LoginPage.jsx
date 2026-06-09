import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../auth';
// Удалите импорт axios - он не нужен, так как verifyLogin уже использует api

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const { login, verifyLogin } = useAuth();  // ✅ Используем verifyLogin
  const navigate = useNavigate();
  const [requires2FA, setRequires2FA] = useState(false);
  const [code2FA, setCode2FA] = useState('');

  const onSubmit = async (e) => {
    e.preventDefault();
    setError('');
    try {
      const res = await login(email, password);  // ✅ Используем login из контекста

      if (res?.requires_2fa) {
        setRequires2FA(true);
      } else {
        navigate('/');
      }
    } catch (err) {
      setError(err?.response?.data?.message || 'Неверный логин или пароль');
    }
  };

  const onVerify2FA = async (e) => {
    e.preventDefault();
    setError('');
    
    try {
      // ✅ Используем verifyLogin из контекста - ОДИН ЗАПРОС!
      await verifyLogin(email, code2FA);
      
      // ✅ После успешной верификации переходим на главную
      navigate('/');
      
    } catch (err) {
      setError(err?.response?.data?.message || 'Неверный код подтверждения');
    }
  };

  if (requires2FA) {
    return (
      <div className="auth-layout">
        <form onSubmit={onVerify2FA} className="card form-card auth-card">
          <h2 className="form-title">Двухфакторная аутентификация</h2>
          <p className="muted">Код подтверждения был отправлен на ваш Email: {email}</p>
          <div className="form-field">
            <label className="form-label">Код из письма</label>
            <input 
              placeholder="123456" 
              value={code2FA} 
              onChange={(e) => setCode2FA(e.target.value)} 
              maxLength={6} 
            />
          </div>
          {error && <p className="form-error">{error}</p>}
          <button type="submit">Подтвердить</button>
        </form>
      </div>
    );
  }

  return (
    <div className="auth-layout">
      <form onSubmit={onSubmit} className="card form-card auth-card">
        <h2 className="form-title">Вход в аккаунт</h2>
        <div className="form-field">
          <label className="form-label">Email</label>
          <input placeholder="name@example.com" value={email} onChange={(e) => setEmail(e.target.value)} />
        </div>
        <div className="form-field">
          <label className="form-label">Пароль</label>
          <input placeholder="Введите пароль" type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
        </div>
        {error && <p className="form-error">{error}</p>}
        <button type="submit">Войти</button>
        <p className="muted">
          Нет аккаунта? <Link to="/register">Создайте его</Link>
        </p>
      </form>
    </div>
  );
}
