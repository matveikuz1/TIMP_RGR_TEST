import { useEffect, useState } from 'react';
import api from '../api';
import LoadingSpinner from '../components/LoadingSpinner';
import { formatBytes } from '../utils/format';
import { AUDIT_ACTIONS, formatAuditAction, formatAuditUser } from '../utils/audit';

const TABS = [
  { id: 'users', label: 'Пользователи' },
  { id: 'files', label: 'Файлы' },
  { id: 'links', label: 'Ссылки' },
  { id: 'audit', label: 'Аудит' },
];

export default function AdminPage() {
  const [tab, setTab] = useState('users');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [users, setUsers] = useState([]);
  const [files, setFiles] = useState([]);
  const [links, setLinks] = useState([]);
  const [audit, setAudit] = useState([]);
  const [auditAction, setAuditAction] = useState('');
  const [auditFrom, setAuditFrom] = useState('');
  const [auditTo, setAuditTo] = useState('');

  const loadUsers = async () => {
    setLoading(true);
    setError('');
    try {
      const { data } = await api.get('/admin/users', { params: { limit: 50, offset: 0 } });
      setUsers(data);
    } catch (e) {
      setError(e?.response?.data?.message || 'Не удалось загрузить пользователей');
    } finally {
      setLoading(false);
    }
  };

  const loadFiles = async () => {
    setLoading(true);
    setError('');
    try {
      const { data } = await api.get('/admin/files');
      setFiles(data);
    } catch (e) {
      setError(e?.response?.data?.message || 'Не удалось загрузить файлы');
    } finally {
      setLoading(false);
    }
  };

  const loadLinks = async () => {
    setLoading(true);
    setError('');
    try {
      const { data } = await api.get('/links', { params: { limit: 50, offset: 0 } });
      setLinks(data);
    } catch (e) {
      setError(e?.response?.data?.message || 'Не удалось загрузить ссылки');
    } finally {
      setLoading(false);
    }
  };

  const loadAudit = async () => {
    setLoading(true);
    setError('');
    const params = { limit: 100, offset: 0 };
    if (auditAction) params.action = auditAction;
    if (auditFrom) params.from = new Date(auditFrom).toISOString();
    if (auditTo) params.to = new Date(auditTo).toISOString();
    try {
      const { data } = await api.get('/audit', { params });
      setAudit(data);
    } catch (e) {
      setError(e?.response?.data?.message || 'Не удалось загрузить аудит');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (tab === 'users') loadUsers();
    if (tab === 'files') loadFiles();
    if (tab === 'links') loadLinks();
    if (tab === 'audit') loadAudit();
  }, [tab]);

  const blockUser = async (userId, block) => {
    setError('');
    try {
      if (block) {
        await api.post(`/admin/users/${userId}/block`);
      } else {
        await api.post(`/admin/users/${userId}/unblock`);
      }
      await loadUsers();
    } catch (e) {
      setError(e?.response?.data?.message || 'Не удалось обновить пользователя');
    }
  };

  const deleteFile = async (fileId) => {
    setError('');
    try {
      await api.delete(`/files/${fileId}`);
      await loadFiles();
    } catch (e) {
      setError(e?.response?.data?.message || 'Не удалось удалить файл');
    }
  };

  const revokeLink = async (linkId) => {
    setError('');
    try {
      await api.delete(`/files/links/${linkId}`);
      await loadLinks();
    } catch (e) {
      setError(e?.response?.data?.message || 'Не удалось отозвать ссылку');
    }
  };

  return (
    <div className="stack">
      <div className="page-header">
        <div>
          <h2 className="page-title">Панель администратора</h2>
          <p className="page-subtitle">Управление пользователями, файлами и ссылками</p>
        </div>
      </div>
      <div className="tabs">
        {TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => setTab(t.id)}
            className={`tab-button ${tab === t.id ? 'active' : ''}`}
          >
            {t.label}
          </button>
        ))}
      </div>
      {loading && <LoadingSpinner />}
      {error && <p className="form-error">{error}</p>}
      {tab === 'users' && (
        <div className="card table-wrapper">
          <table className="table">
            <thead>
              <tr>
                <th>Пользователь</th>
                <th>Email</th>
                <th>Роль</th>
                <th>Статус</th>
                <th>Действия</th>
              </tr>
            </thead>
            <tbody>
              {users.map((user) => (
                <tr key={user.id}>
                  <td>{user.username}</td>
                  <td>{user.email}</td>
                  <td>{user.role}</td>
                  <td>
                    <span className={`badge ${user.is_blocked ? 'danger' : 'success'}`}>
                      {user.is_blocked ? 'Заблокирован' : 'Активен'}
                    </span>
                  </td>
                  <td>
                    <div className="table-actions">
                      <button
                        type="button"
                        className={user.is_blocked ? 'secondary' : 'danger'}
                        onClick={() => blockUser(user.id, !user.is_blocked)}
                      >
                        {user.is_blocked ? 'Разблокировать' : 'Заблокировать'}
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
              {users.length === 0 && (
                <tr>
                  <td colSpan="5" className="empty-state">Пользователей нет</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
      {tab === 'files' && (
        <div className="card table-wrapper">
          <table className="table">
            <thead>
              <tr>
                <th>Файл</th>
                <th>Владелец</th>
                <th>Размер</th>
                <th>Действия</th>
              </tr>
            </thead>
            <tbody>
              {files.map((file) => (
                <tr key={file.id}>
                  <td>{file.original_name}</td>
                  <td>#{file.owner_id}</td>
                  <td>{formatBytes(file.size_bytes)}</td>
                  <td>
                    <div className="table-actions">
                      <button type="button" className="danger" onClick={() => deleteFile(file.id)}>Удалить</button>
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
      )}
      {tab === 'links' && (
        <div className="card table-wrapper">
          <table className="table">
            <thead>
              <tr>
                <th>Токен</th>
                <th>Файл</th>
                <th>Использования</th>
                <th>Действия</th>
              </tr>
            </thead>
            <tbody>
              {links.map((link) => {
                const usageLimit = link.max_uses > 0 ? link.max_uses : '∞';
                return (
                  <tr key={link.id}>
                    <td>{link.token}</td>
                    <td>#{link.file_id}</td>
                    <td>{link.used_count}/{usageLimit}</td>
                    <td>
                      <div className="table-actions">
                        <button type="button" className="secondary" onClick={() => revokeLink(link.id)}>Отозвать</button>
                      </div>
                    </td>
                  </tr>
                );
              })}
              {links.length === 0 && (
                <tr>
                  <td colSpan="4" className="empty-state">Ссылки отсутствуют</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
      {tab === 'audit' && (
        <div className="card stack">
          <div className="toolbar">
            <select value={auditAction} onChange={(e) => setAuditAction(e.target.value)}>
              {AUDIT_ACTIONS.map((option) => (
                <option key={option.value} value={option.value}>{option.label}</option>
              ))}
            </select>
            <input type="datetime-local" value={auditFrom} onChange={(e) => setAuditFrom(e.target.value)} />
            <input type="datetime-local" value={auditTo} onChange={(e) => setAuditTo(e.target.value)} />
            <button type="button" className="secondary" onClick={loadAudit}>Применить</button>
          </div>
          <div className="table-wrapper">
            <table className="table">
              <thead>
                <tr>
                  <th>Дата</th>
                  <th>Действие</th>
                  <th>Сущность</th>
                  <th>Пользователь</th>
                </tr>
              </thead>
              <tbody>
                {audit.map((row) => (
                  <tr key={row.id}>
                    <td>{new Date(row.created_at).toLocaleString('ru-RU')}</td>
                    <td>{formatAuditAction(row)}</td>
                    <td>{row.entity_type}:{row.entity_id}</td>
                    <td>{formatAuditUser(row)}</td>
                  </tr>
                ))}
                {audit.length === 0 && (
                  <tr>
                    <td colSpan="4" className="empty-state">Записей нет</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
