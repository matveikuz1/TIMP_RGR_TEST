import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import axios from 'axios';

export default function RegisterPage() {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  // Состояния для двухфакторки
  const [requires2FA, setRequires2FA] = useState(false);
  const [code2FA, setCode2FA] = useState('');

  const validatePassword = (value) => {
    if (value.length < 8) return 'Пароль должен быть не короче 8 символов';
    if (!/[A-Za-z]/.test(value)) return 'Пароль должен содержать латинскую букву';
    if (!/[0-9]/.test(value)) return 'Пароль должен содержать цифру';
    for (const ch of value) {
      if (/\p{L}/u.test(ch) && !/[A-Za-z]/.test(ch)) {
        return 'Пароль должен содержать только латинские буквы';
      }
    }
    return '';
  };

const validateEmail = (email) => {
    const emailRegex = /^[^\s@]+@([^\s@]+\.)+[^\s@]+$/;
    if (!email) {
        return 'Введите email адрес';
    }
    if (!emailRegex.test(email)) {
        return 'Введите адрес в формате email@example.com';
    }
    return '';
};

  const onSubmit = async (e) => {
    e.preventDefault();
    setError('');

const emailError = validateEmail(email);
    if (emailError) {
        setError(emailError);
        return;
    }
    
    const validationError = validatePassword(password);
    if (validationError) {
      setError(validationError);
      return;
    }

    try {
      // ИМЕННО /register, А НЕ /login
      const res = await axios.post('/api/auth/register', { username, email, password });
      
      if (res.data?.requires_2fa) {
        setRequires2FA(true);
      }
    } catch (err) {
      // Выводим ошибку, которую вернул бэкенд
      setError(err?.response?.data?.message || err?.response?.data?.detail || 'Не удалось зарегистрироваться');
    }
  };

  const onVerifyRegister = async (e) => {
    e.preventDefault();
    setError('');
    try {
      await axios.post('/api/auth/verify-register', { email, code: code2FA });
      navigate('/login');
    } catch (err) {
      setError(err?.response?.data?.message || err?.response?.data?.detail || 'Неверный код подтверждения');
    }
  };

  if (requires2FA) {
    return (
      <div className="auth-layout">
        <form onSubmit={onVerifyRegister} className="card form-card auth-card">
          <h2 className="form-title">Подтверждение регистрации</h2>
          <p className="muted">Мы отправили код подтверждения на почту {email}. Введите его ниже для активации аккаунта.</p>
          <div className="form-field">
            <label className="form-label">Код подтверждения</label>
            <input placeholder="123456" value={code2FA} onChange={(e) => setCode2FA(e.target.value)} maxLength={6} />
          </div>
          {error && <p className="form-error">{error}</p>}
          <button type="submit">Активировать аккаунт</button>
        </form>
      </div>
    );
  }

  return (
    <div className="auth-layout">
      <form onSubmit={onSubmit} className="card form-card auth-card">
        <h2 className="form-title">Регистрация</h2>
        <div className="form-field">
          <label className="form-label">Имя пользователя</label>
          <input placeholder="Ваше имя" value={username} onChange={(e) => setUsername(e.target.value)} />
        </div>
        <div className="form-field">
          <label className="form-label">Email</label>
          <input placeholder="name@example.com" value={email} onChange={(e) => setEmail(e.target.value)} />
        </div>
        <div className="form-field">
          <label className="form-label">Пароль</label>
          <input placeholder="Минимум 8 символов" type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
        </div>
        {error && <p className="form-error">{error}</p>}
        <button type="submit">Создать аккаунт</button>
        <p className="muted">
          Уже есть аккаунт? <Link to="/login">Войти</Link>
        </p>
      </form>
    </div>
  );
}
