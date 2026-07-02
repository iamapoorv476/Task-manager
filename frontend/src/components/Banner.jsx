// A single, consistent way to surface success/error messages -- every
// page uses this instead of ad hoc inline text, so a "task deleted"
// confirmation and a "wrong password" error look and behave the same way.
export default function Banner({ tone = 'error', children, onDismiss }) {
  if (!children) return null

  const styles =
    tone === 'success'
      ? 'bg-brand-100 text-brand-700 border-brand-500/30'
      : 'bg-rose-100 text-rose-600 border-rose-600/30'

  return (
    <div
      role={tone === 'error' ? 'alert' : 'status'}
      className={`flex items-start justify-between gap-3 rounded-lg border px-4 py-3 text-sm ${styles}`}
    >
      <span>{children}</span>
      {onDismiss && (
        <button
          type="button"
          onClick={onDismiss}
          className="shrink-0 font-medium opacity-70 hover:opacity-100"
          aria-label="Dismiss"
        >
          ✕
        </button>
      )}
    </div>
  )
}
