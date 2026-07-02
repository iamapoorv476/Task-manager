const STATUS_STYLES = {
  TODO: 'bg-ink-100 text-ink-700',
  IN_PROGRESS: 'bg-amber-100 text-amber-600',
  DONE: 'bg-brand-100 text-brand-700',
}

const STATUS_LABELS = {
  TODO: 'To do',
  IN_PROGRESS: 'In progress',
  DONE: 'Done',
}

export function StatusBadge({ status }) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${STATUS_STYLES[status]}`}
    >
      {STATUS_LABELS[status] ?? status}
    </span>
  )
}

// Priority reads as a left-border stripe on the task card itself (see
// TaskRow), not a separate badge -- one signal per property, so the
// eye can scan status vs. priority at a glance instead of parsing two
// pills that look the same.
export const PRIORITY_BORDER = {
  LOW: 'border-l-ink-300',
  MEDIUM: 'border-l-amber-600',
  HIGH: 'border-l-rose-600',
}

export const PRIORITY_LABELS = {
  LOW: 'Low',
  MEDIUM: 'Medium',
  HIGH: 'High',
}
