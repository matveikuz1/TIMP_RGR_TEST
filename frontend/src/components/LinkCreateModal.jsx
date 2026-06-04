import { useMemo, useState } from 'react';

export default function LinkCreateModal({ open, onClose, onCreate }) {
  const MAX_USES = 100;
  const todayDate = useMemo(() => {
    const today = new Date();
    return today.toISOString().slice(0, 10);
  }, []);
  const defaultDate = useMemo(() => {
    const nextDay = new Date(Date.now() + 24 * 60 * 60 * 1000);
    return nextDay.toISOString().slice(0, 10);
  }, []);
  const [endDate, setEndDate] = useState(defaultDate);
  const [maxUses, setMaxUses] = useState(1);
  const [unlimited, setUnlimited] = useState(false);
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  if (!open) return null;

  const submit = (e) => {
    e.preventDefault();
    setError('');
    if (!endDate) {
      setError('Выберите дату окончания');
      return;
    }
    const end = new Date(endDate);
    const endOfDay = new Date(end.getFullYear(), end.getMonth(), end.getDate(), 23, 59, 59);
    const diffMs = endOfDay.getTime() - Date.now();
    if (diffMs <= 0) {
      setError('Дата окончания должна быть в будущем');
      return;
    }
    const ttlHours = Math.max(1, Math.ceil(diffMs / (1000 * 60 * 60)));
    const uses = unlimited ? 0 : Math.max(1, Math.min(MAX_USES, Number(maxUses) || 1));
    onCreate({
      ttl_hours: Number(ttlHours),
      max_uses: uses,
      password: password.trim() ? password : null,
    });
  };

  return (
    <div className="modal-backdrop">
      <form onSubmit={submit} className="modal-card">
        <h3 className="form-title">Новая ссылка</h3>
        <div className="form-field">
          <label className="form-label">Дата окончания</label>
          <input type="date" value={endDate} min={todayDate} onChange={(e) => setEndDate(e.target.value)} />
        </div>
        <div className="form-field">
          <label className="form-label">Максимум использований</label>
          <div className="table-actions">
            <input
              type="number"
              min="1"
              max={MAX_USES}
              value={unlimited ? '' : maxUses}
              placeholder={unlimited ? '∞' : `1-${MAX_USES}`}
              disabled={unlimited}
              onChange={(e) => setMaxUses(e.target.value)}
            />
            <label className="muted">
              <input
                type="checkbox"
                checked={unlimited}
                onChange={(e) => {
                  const next = e.target.checked;
                  setUnlimited(next);
                  if (next) {
                    setMaxUses(0);
                  } else if (!maxUses || Number(maxUses) < 1) {
                    setMaxUses(1);
                  }
                }}
              />
              Без лимита
            </label>
          </div>
        </div>
        <div className="form-field">
          <label className="form-label">Пароль (необязательно)</label>
          <input value={password} type="password" onChange={(e) => setPassword(e.target.value)} />
        </div>
        {error && <p className="form-error">{error}</p>}
        <div className="table-actions">
          <button type="submit">Создать</button>
          <button type="button" className="secondary" onClick={onClose}>Отмена</button>
        </div>
      </form>
    </div>
  );
}
