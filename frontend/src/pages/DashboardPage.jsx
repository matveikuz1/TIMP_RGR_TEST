import { useCallback, useEffect, useState } from 'react';
import api from '../api';
import { useAuth } from '../auth';
import LoadingSpinner from '../components/LoadingSpinner';
import LinkCreateModal from '../components/LinkCreateModal';
import { formatBytes } from '../utils/format';

export default function DashboardPage() {
  const { user } = useAuth();
  const [files, setFiles] = useState([]);
  const [links, setLinks] = useState([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [linkModalOpen, setLinkModalOpen] = useState(false);
  const [selectedFileId, setSelectedFileId] = useState(null);

  const loadFiles = async () => {
    setLoading(true);
    try {
      const { data } = await api.get('/files');
      setFiles(data);
    } catch (e) {
      setError(e?.response?.data?.message || 'Не удалось загрузить файлы');
    } finally {
      setLoading(false);
    }
  };

  const loadLinks = async () => {
    setLoading(true);
    try {
      const { data } = await api.get('/links');
      setLinks(data);
    } catch (e) {
      setError(e?.response?.data?.message || 'Не удалось загрузить ссылки');
    } finally {
      setLoading(false);
    }
  };

  const refreshLinks = useCallback(async () => {
    if (!user) return;
    try {
      const { data } = await api.get('/links');
      setLinks(data);
    } catch (e) {
      // ignore background refresh errors
    }
  }, [user]);

  const upload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const fd = new FormData();
    fd.append('upload', file);
    setError('');
    setLoading(true);
    try {
      await api.post('/files/upload', fd);
      await loadFiles();
      await loadLinks();
    } catch (err) {
      setError(err?.response?.data?.message || 'Не удалось загрузить файл');
    } finally {
      setLoading(false);
    }
  };

  const openCreateLink = (fileId) => {
    setSelectedFileId(fileId);
    setLinkModalOpen(true);
  };

  const createLink = async (payload) => {
    if (!selectedFileId) return;
    setError('');
    setLoading(true);
    try {
      await api.post(`/files/${selectedFileId}/links`, payload);
      await loadLinks();
      setLinkModalOpen(false);
      setSelectedFileId(null);
    } catch (err) {
      setError(err?.response?.data?.message || 'Не удалось создать ссылку');
    } finally {
      setLoading(false);
    }
  };

  const remove = async (fileId) => {
    setError('');
    setLoading(true);
    try {
      await api.delete(`/files/${fileId}`);
      await loadFiles();
      await loadLinks();
    } catch (err) {
      setError(err?.response?.data?.message || 'Не удалось удалить файл');
    } finally {
      setLoading(false);
    }
  };

  const revokeLink = async (linkId) => {
    setError('');
    setLoading(true);
    try {
      await api.delete(`/files/links/${linkId}`);
      await loadLinks();
    } catch (err) {
      setError(err?.response?.data?.message || 'Не удалось отозвать ссылку');
    } finally {
      setLoading(false);
    }
  };

  const restoreLink = async (linkId) => {
    setError('');
    setLoading(true);
    try {
      await api.post(`/files/links/${linkId}/restore`);
      await loadLinks();
    } catch (err) {
      setError(err?.response?.data?.message || 'Не удалось восстановить ссылку');
    } finally {
      setLoading(false);
    }
  };

  const permanentDeleteLink = async (linkId) => {
    setError('');
    setLoading(true);
    try {
      await api.delete(`/files/links/${linkId}/permanent`);
      await loadLinks();
    } catch (err) {
      setError(err?.response?.data?.message || 'Не удалось удалить ссылку');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!user) return;
    let cancelled = false;
    setLoading(true);
    Promise.all([api.get('/files'), api.get('/links')])
      .then(([filesResponse, linksResponse]) => {
        if (cancelled) return;
        setFiles(filesResponse.data);
        setLinks(linksResponse.data);
      })
      .catch((e) => { if (!cancelled) setError(e?.response?.data?.message || 'Ошибка загрузки данных'); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [user]);

  useEffect(() => {
    if (!user) return undefined;
    const intervalId = setInterval(() => {
      refreshLinks();
    }, 10000);
    return () => clearInterval(intervalId);
  }, [user, refreshLinks]);

  const totalSize = files.reduce((sum, file) => sum + file.size_bytes, 0);
  const fileLookup = files.reduce((acc, file) => {
    acc[file.id] = file;
    return acc;
  }, {});

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

  return (
    <div className="stack">
      <div className="page-header">
        <div>
          <h2 className="page-title">Мои файлы</h2>
          <p className="page-subtitle">
            Файлов: {files.length} · Общий размер: {formatBytes(totalSize)}
          </p>
        </div>
        <label className="form-field" style={{ maxWidth: 640 }}>
          <span className="form-label">Загрузить файл</span>
          <input type="file" onChange={upload} />
        </label>
      </div>
      {loading && <LoadingSpinner />}
      {error && <p className="form-error">{error}</p>}
      
      <div className="card table-wrapper">
        <table className="table">
          <thead>
            <tr>
              <th>Файл</th>
              <th>Размер</th>
              <th>Загружен</th>
              <th>Действия</th>
            </tr>
          </thead>
          <tbody>
            {files.map((f) => (
              <tr key={f.id}>
                <td>{f.original_name}</td>
                <td>{formatBytes(f.size_bytes)}</td>
                <td>{new Date(f.uploaded_at).toLocaleDateString('ru-RU')}</td>
                <td>
                  <div className="table-actions">
                    <button onClick={() => openCreateLink(f.id)}>Создать ссылку</button>
                    <button className="danger" onClick={() => remove(f.id)}>Удалить</button>
                  </div>
                </td>
              </tr>
            ))}
            {files.length === 0 && (
              <tr>
                <td colSpan="4" className="empty-state">Файлы отсутствуют</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
      
      <div className="stack">
        <div className="card-header">
          <h3 className="page-title">Мои ссылки</h3>
        </div>
        <div className="card table-wrapper">
          <table className="table">
            <thead>
              <tr>
                <th>Файл</th>
                <th>Ссылка</th>
                <th>Действует до</th>
                <th>Использования</th>
                <th>Статус</th>
                <th>Действия</th>
              </tr>
            </thead>
            <tbody>
              {links.map((link) => {
                const file = fileLookup[link.file_id];
                const expiresDate = new Date(link.expires_at);
                const expired = expiresDate.getTime() < Date.now();
                const limitReached = link.max_uses > 0 && link.used_count >= link.max_uses;
                const isRevoked = link.revoked;
                
                let status = 'Активна';
                let badgeClass = 'success';
                
                if (isRevoked) {
                  status = 'Отозвана';
                  badgeClass = 'warning';
                } else if (expired) {
                  status = 'Истекла';
                  badgeClass = 'danger';
                } else if (limitReached) {
                  status = 'Лимит исчерпан';
                  badgeClass = 'danger';
                }
                
                const usageLimit = link.max_uses > 0 ? link.max_uses : '∞';
                
                return (
                  <tr key={link.id}>
                    <td>{file?.original_name || `Файл #${link.file_id}`}</td>
                    <td>
                      <div className="table-actions">
                        <span className="muted truncate">{`${window.location.origin}/share/${link.token}`}</span>
                        <button type="button" className="secondary" onClick={() => copyLink(link.token)}>Копировать</button>
                      </div>
                    </td>
                    <td>{expiresDate.toLocaleDateString('ru-RU')}</td>
                    <td>{link.used_count} / {usageLimit}</td>
                    <td><span className={`badge ${badgeClass}`}>{status}</span></td>
                    <td>
                      <div className="table-actions">
                        {!isRevoked && !expired && !limitReached && (
                          <button type="button" className="warning" onClick={() => revokeLink(link.id)}>
                            Отозвать
                          </button>
                        )}
                        {isRevoked && !expired && !limitReached && (
                          <button type="button" className="success" onClick={() => restoreLink(link.id)}>
                            Восстановить
                          </button>
                        )}
                        {(isRevoked || expired || limitReached) && (
                          <button type="button" className="danger" onClick={() => permanentDeleteLink(link.id)}>
                            Удалить
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })}
              {links.length === 0 && (
                <tr>
                  <td colSpan="6" className="empty-state">Ссылки отсутствуют</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
      
      <LinkCreateModal
        open={linkModalOpen}
        onClose={() => {
          setLinkModalOpen(false);
          setSelectedFileId(null);
        }}
        onCreate={createLink}
      />
    </div>
  );
}
