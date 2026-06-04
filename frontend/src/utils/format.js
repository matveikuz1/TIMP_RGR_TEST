export const formatBytes = (bytes) => {
  if (!Number.isFinite(bytes)) return '—';
  if (bytes < 0) return '—';
  if (bytes === 0) return '0 Б';
  const k = 1024;
  const sizes = ['Б', 'КБ', 'МБ', 'ГБ', 'ТБ'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${(bytes / k ** i).toFixed(i === 0 ? 0 : 2)} ${sizes[i]}`;
};
