export default function LoadingSpinner({ text = 'Загрузка...' }) {
  return (
    <div className="spinner">
      <span className="spinner-circle" aria-hidden="true" />
      <span>{text}</span>
    </div>
  );
}
