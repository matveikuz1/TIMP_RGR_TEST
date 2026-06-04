import { useCallback, useEffect, useState } from 'react';
import api from '../api';
import LoadingSpinner from '../components/LoadingSpinner';

export default function LinksPage() {
  const [links, setLinks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [offset, setOffset] = useState(0);
  const [hasMore, setHasMore] = useState(true);
  const limit = 20;

  const loadLinks = async (nextOffset = 0, append = false) => {
    setLoading(true);
    setError('');
    try {
      const { data } = await api.get('/links', { params: { limit, offset: nextOffset } });
      setLinks((prev) => (append ? [...prev, ...data] : data));
      setOffset(nextOffset);
      setHasMore(data.length === limit);
    } catch (e) {
      setError(e?.response?.data?.message || 'Не удалось загрузить ссылки');
    } finally {
      setLoading(false);
    }
  };

  const refreshLinks = useCallback(async () => {
    const count = Math.max(limit, offset + limit);
    try {
      const { data } = await api.get('/links', { params: { limit: count, offset: 0 } });
      setLinks(data);
      setHasMore(data.length === count);
    } catch (e) {
      // ignore background refresh errors
    }
  }, [limit, offset]);

  useEffect(() => {
    loadLinks(0, false);
  }, []);

  useEffect(() => {
    const intervalId = setInterval(() => {
      refreshLinks();
    }, 10000);
    return () => clearInterval(intervalId);
  }, [refreshLinks]);

  const copyLink = async (token) => {
    const url = `${window.location.origin}/share/${token}`;
    try {
      if (navigator.clipboard) {
        await navigator.clipboard.writeText(url);
      } else {
        window.prompt('Скопируйте ссылку:', url);
      }
    } catch (e) {
      setError('Не удалось скопировать ссылку');
    }
  };

  const revokeLink = async (linkId) => {
    setError('');
    try {
      await api.delete(`/files/links/${linkId}`);
      loadLinks(0, false);
    } catch (e) {
      setError(e?.response?.data?.message || 'Не удалось удалить ссылку');
    }
  };

  return (
    <div className="stack">
      <div className="page-header">
        <div>
          <h2 className="page-title">Мои ссылки</h2>
          <p className="page-subtitle">Последние одноразовые ссылки для скачивания</p>
        </div>
      </div>
      {loading && <LoadingSpinner />}
      {error && <p className="form-error">{error}</p>}
      <div className="card table-wrapper">
        <table className="table">
          <thead>
            <tr>
              <th>Файл</th>
              <th>Ссылка</th>
              <th>Действует до</th>
              <th>Использования</th>
              <th>Действия</th>
            </tr>
          </thead>
          <tbody>
            {links.map((link) => {
              const limitReached = link.max_uses > 0 && link.used_count >= link.max_uses;
              const usageLimit = link.max_uses > 0 ? link.max_uses : '∞';
              return (
                <tr key={link.id}>
                  <td>Файл #{link.file_id}</td>
                  <td>
                    <div className="table-actions">
                      <span className="muted truncate">{`${window.location.origin}/share/${link.token}`}</span>
                      <button type="button" className="secondary" onClick={() => copyLink(link.token)}>Копировать</button>
                    </div>
                  </td>
                  <td>{new Date(link.expires_at).toLocaleDateString('ru-RU')}</td>
                  <td>{link.used_count} / {usageLimit}</td>
                  <td>
                    <button
                      type="button"
                      className={limitReached ? 'danger' : 'secondary'}
                      onClick={() => revokeLink(link.id)}
                    >
                      Удалить
                    </button>
                  </td>
                </tr>
              );
            })}
            {links.length === 0 && (
              <tr>
                <td colSpan="5" className="empty-state">Ссылки отсутствуют</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
      <div>
        <button
          type="button"
          className="secondary"
          onClick={() => loadLinks(offset + limit, true)}
          disabled={!hasMore || loading}
        >
          Загрузить ещё
        </button>
      </div>
    </div>
  );
}
