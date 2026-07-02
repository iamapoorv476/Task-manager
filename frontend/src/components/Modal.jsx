export default function Modal({ title, onClose, children }) {
  return (
    <div className="fixed inset-0 z-10 flex items-center justify-center bg-ink-900/40 px-4">
      <div className="w-full max-w-md rounded-xl bg-canvas-card p-6 shadow-lg">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-ink-900">{title}</h2>
          <button
            type="button"
            onClick={onClose}
            className="rounded-md p-1 text-ink-500 hover:bg-ink-100 hover:text-ink-900"
            aria-label="Close"
          >
            ✕
          </button>
        </div>
        {children}
      </div>
    </div>
  )
}
