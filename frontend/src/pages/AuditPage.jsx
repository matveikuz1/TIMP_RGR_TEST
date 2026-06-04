import { useEffect, useState } from 'react';
import api from '../api';
import LoadingSpinner from '../components/LoadingSpinner';
import { AUDIT_ACTIONS, formatAuditAction, formatAuditUser } from '../utils/audit';

export default function AuditPage() {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(false);
  const [auditAction, setAuditAction] = useState('');
  const [auditFrom, setAuditFrom] = useState('');
  const [auditTo, setAuditTo] = useState('');

  const loadAudit = async () => {
    setLoading(true);
    const params = { limit: 100, offset: 0 };
    if (auditAction) params.action = auditAction;
    if (auditFrom) params.from = new Date(auditFrom).toISOString();
    if (auditTo) params.to = new Date(auditTo).toISOString();
    try {
      const { data } = await api.get('/audit', { params });
      setRows(data);
    } catch {
      setRows([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAudit();
  }, []);

  return (
    <div className="stack">
      <div className="page-header">
        <div>
          <h2 className="page-title">Журнал аудита</h2>
          <p className="page-subtitle">Контроль ключевых событий системы</p>
        </div>
      </div>
      {loading && <LoadingSpinner />}
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
            {rows.map((r) => (
              <tr key={r.id}>
                <td>{new Date(r.created_at).toLocaleString('ru-RU')}</td>
                <td>{formatAuditAction(r)}</td>
                <td>{r.entity_type}:{r.entity_id}</td>
                <td>{formatAuditUser(r)}</td>
              </tr>
            ))}
            {rows.length === 0 && (
              <tr>
                <td colSpan="4" className="empty-state">Записей пока нет</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
      </div>
    </div>
  );
}
