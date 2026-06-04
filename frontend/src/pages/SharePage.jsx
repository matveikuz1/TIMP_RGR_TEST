import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import api from '../api';
import LoadingSpinner from '../components/LoadingSpinner';
import { formatBytes } from '../utils/format';

export default function SharePage() {
  const { token } = useParams();
  const [info, setInfo] = useState(null);
  const [password, setPassword] = useState('');
  const [passwordOk, setPasswordOk] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    api.get(`/share/${token}`)
      .then(({ data }) => { if (!cancelled) setInfo(data); })
      .catch((err) => { if (!cancelled) setError(err?.response?.data?.message || 'Ссылка недействительна'); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [token]);

  const verifyPassword = async () => {
    setError('');
    try {
      await api.post(`/share/${token}/verify-password`, { password });
      setPasswordOk(true);
      return true;
    } catch (e) {
      setError(e?.response?.data?.message || 'Неверный пароль');
      return false;
    }
  };

  const downloadWithPassword = async () => {
    if (!password) return;
    const ok = await verifyPassword();
    if (ok) download();
  };

  const download = () => {
    const query = password ? `?password=${encodeURIComponent(password)}` : '';
    window.location.href = `/api/share/${token}/download${query}`;
  };

  if (loading) return <LoadingSpinner text="Загрузка..." />;
  if (error && !info) return <p className="form-error">{error}</p>;
  if (!info) return null;

  const expiresAt = info.link?.expires_at ? new Date(info.link.expires_at).toLocaleDateString('ru-RU') : '—';

  return (
    <div className="card" style={{ maxWidth: 560, margin: '0 auto' }}>
      <div className="stack">
        <div>
          <h2 className="page-title">Скачивание файла</h2>
          <p className="page-subtitle">Подготовка одноразовой ссылки</p>
        </div>
        <div className="stack">
          <div><strong>Файл:</strong> {info.file.original_name}</div>
          <div><strong>Размер:</strong> {formatBytes(info.file.size_bytes)}</div>
          <div><strong>Отправитель:</strong> {info.owner?.username || info.owner?.email || 'Неизвестно'}</div>
          <div><strong>Действует до:</strong> {expiresAt}</div>
        </div>
        {info.password_required && !passwordOk ? (
          <div className="stack">
            <input
              placeholder="Пароль ссылки"
              type="password"
              value={password}
              onChange={(e) => {
                setPassword(e.target.value);
                setPasswordOk(false);
              }}
            />
            <button
              type="button"
              onClick={downloadWithPassword}
              disabled={!password}
            >
              {password ? 'Скачать' : 'Проверить пароль'}
            </button>
          </div>
        ) : (
          <button type="button" onClick={download}>Скачать</button>
        )}
        {error && <p className="form-error">{error}</p>}
      </div>
    </div>
  );
}
