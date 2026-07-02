import { useState } from 'react'

const PRIORITIES = ['LOW', 'MEDIUM', 'HIGH']
const STATUSES = ['TODO', 'IN_PROGRESS', 'DONE']

// Same form drives both create and edit -- pass an existing task via
// `initial` for edit mode, omit it for create. The two flows differ
// only in whether a status field shows (a brand-new task is always
// TODO, so there's nothing to choose there) and in the submit label.
export default function TaskForm({ initial, onSubmit, onCancel, submitting }) {
  const isEdit = Boolean(initial)
  const [title, setTitle] = useState(initial?.title ?? '')
  const [description, setDescription] = useState(initial?.description ?? '')
  const [priority, setPriority] = useState(initial?.priority ?? 'MEDIUM')
  const [status, setStatus] = useState(initial?.status ?? 'TODO')

  function handleSubmit(e) {
    e.preventDefault()
    const payload = isEdit
      ? { title, description, priority, status }
      : { title, description, priority }
    onSubmit(payload)
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label htmlFor="title" className="mb-1 block text-sm font-medium text-ink-700">
          Title
        </label>
        <input
          id="title"
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          required
          minLength={3}
          maxLength={200}
          className="w-full rounded-lg border border-ink-100 bg-canvas-card px-3 py-2 text-sm text-ink-900 focus:border-brand-500"
          placeholder="Fix login redirect on mobile Safari"
        />
      </div>

      <div>
        <label htmlFor="description" className="mb-1 block text-sm font-medium text-ink-700">
          Description
        </label>
        <textarea
          id="description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          rows={3}
          className="w-full rounded-lg border border-ink-100 bg-canvas-card px-3 py-2 text-sm text-ink-900 focus:border-brand-500"
          placeholder="Optional -- add any context that isn't obvious from the title."
        />
      </div>

      <div className={`grid gap-4 ${isEdit ? 'grid-cols-2' : 'grid-cols-1'}`}>
        <div>
          <label htmlFor="priority" className="mb-1 block text-sm font-medium text-ink-700">
            Priority
          </label>
          <select
            id="priority"
            value={priority}
            onChange={(e) => setPriority(e.target.value)}
            className="w-full rounded-lg border border-ink-100 bg-canvas-card px-3 py-2 text-sm text-ink-900 focus:border-brand-500"
          >
            {PRIORITIES.map((p) => (
              <option key={p} value={p}>
                {p.charAt(0) + p.slice(1).toLowerCase()}
              </option>
            ))}
          </select>
        </div>

        {isEdit && (
          <div>
            <label htmlFor="status" className="mb-1 block text-sm font-medium text-ink-700">
              Status
            </label>
            <select
              id="status"
              value={status}
              onChange={(e) => setStatus(e.target.value)}
              className="w-full rounded-lg border border-ink-100 bg-canvas-card px-3 py-2 text-sm text-ink-900 focus:border-brand-500"
            >
              {STATUSES.map((s) => (
                <option key={s} value={s}>
                  {s.replace('_', ' ').toLowerCase()}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      <div className="flex items-center gap-3 pt-1">
        <button
          type="submit"
          disabled={submitting}
          className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-60"
        >
          {submitting ? 'Saving...' : isEdit ? 'Save changes' : 'Create task'}
        </button>
        {onCancel && (
          <button
            type="button"
            onClick={onCancel}
            className="rounded-lg px-4 py-2 text-sm font-medium text-ink-500 hover:text-ink-900"
          >
            Cancel
          </button>
        )}
      </div>
    </form>
  )
}
