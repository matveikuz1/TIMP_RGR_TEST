export const AUDIT_ACTIONS = [
  { value: '', label: 'Все действия' },
  { value: 'LOGIN', label: 'Вход в систему' },
  { value: 'CREATE_USER', label: 'Создание пользователя' },
  { value: 'UPLOAD_FILE', label: 'Загрузка файла' },
  { value: 'DELETE_FILE', label: 'Удаление файла' },
  { value: 'CREATE_LINK', label: 'Создание ссылки' },
  { value: 'DOWNLOAD_FILE', label: 'Скачивание файла' },
  { value: 'ACCESS_DENIED', label: 'Отказ в доступе' },
];

const ACTION_LABELS = AUDIT_ACTIONS.reduce((acc, item) => {
  if (item.value) acc[item.value] = item.label;
  return acc;
}, {});

export const formatAuditAction = (row) => {
  const base = ACTION_LABELS[row.action] || row.action;
  if (row.action === 'LOGIN') {
    if (row.details?.status === 'failed') return `${base} (ошибка)`;
    if (row.details?.status === 'success') return `${base} (успешно)`;
  }
  return base;
};

export const formatAuditUser = (row) => {
  if (row.user) {
    const title = row.user.username || row.user.email;
    if (row.user.username && row.user.email) {
      return `${row.user.username} (${row.user.email})`;
    }
    return title || `#${row.user.id}`;
  }
  if (row.user_id) return `#${row.user_id}`;
  return 'Система';
};
