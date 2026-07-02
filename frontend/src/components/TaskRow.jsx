import { StatusBadge, PRIORITY_BORDER, PRIORITY_LABELS } from './badges'

export default function TaskRow({ task, onEdit, onDelete }) {
  return (
    <div
      className={`flex items-start justify-between gap-4 rounded-lg border-l-4 bg-canvas-card p-4 shadow-sm ${PRIORITY_BORDER[task.priority]}`}
    >
      <div className="min-w-0">
        <div className="flex flex-wrap items-center gap-2">
          <h3 className="truncate font-medium text-ink-900">{task.title}</h3>
          <StatusBadge status={task.status} />
        </div>
        {task.description && (
          <p className="mt-1 line-clamp-2 text-sm text-ink-500">{task.description}</p>
        )}
        <p className="mt-2 font-mono text-xs text-ink-300">
          {PRIORITY_LABELS[task.priority]} priority · updated{' '}
          {new Date(task.updated_at).toLocaleDateString()}
        </p>
      </div>
      <div className="flex shrink-0 items-center gap-2">
        <button
          type="button"
          onClick={() => onEdit(task)}
          className="rounded-md px-2 py-1 text-sm font-medium text-ink-500 hover:bg-ink-100 hover:text-ink-900"
        >
          Edit
        </button>
        <button
          type="button"
          onClick={() => onDelete(task)}
          className="rounded-md px-2 py-1 text-sm font-medium text-rose-600 hover:bg-rose-100"
        >
          Delete
        </button>
      </div>
    </div>
  )
}
