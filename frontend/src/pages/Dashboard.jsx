import { useCallback, useEffect, useState } from 'react'
import client from '../api/client'
import { getErrorMessage } from '../api/errors'
import { useAuth } from '../context/AuthContext'
import Banner from '../components/Banner'
import Modal from '../components/Modal'
import TaskForm from '../components/TaskForm'
import TaskRow from '../components/TaskRow'

const PAGE_SIZE = 10

export default function Dashboard() {
  const { user, isAdmin, logout } = useAuth()

  const [tasks, setTasks] = useState([])
  const [meta, setMeta] = useState({ page: 1, total_pages: 1, total_items: 0 })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [successMessage, setSuccessMessage] = useState(null)

  const [page, setPage] = useState(1)
  const [status, setStatus] = useState('')
  const [priority, setPriority] = useState('')
  const [search, setSearch] = useState('')
  const [sortBy, setSortBy] = useState('created_at')
  const [sortOrder, setSortOrder] = useState('desc')

  const [formOpen, setFormOpen] = useState(false)
  const [editingTask, setEditingTask] = useState(null)
  const [submitting, setSubmitting] = useState(false)

  const fetchTasks = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const params = { page, limit: PAGE_SIZE, sort_by: sortBy, sort_order: sortOrder }
      if (status) params.status = status
      if (priority) params.priority = priority
      if (search) params.search = search

      const res = await client.get('/tasks', { params })
      setTasks(res.data.data)
      setMeta(res.data.meta)
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }, [page, status, priority, search, sortBy, sortOrder])

  useEffect(() => {
    fetchTasks()
  }, [fetchTasks])

  // Any filter change resets to page 1 -- staying on page 3 of a
  // now-different result set would silently show the wrong tasks.
  function updateFilter(setter) {
    return (value) => {
      setter(value)
      setPage(1)
    }
  }

  function openCreateForm() {
    setEditingTask(null)
    setFormOpen(true)
  }

  function openEditForm(task) {
    setEditingTask(task)
    setFormOpen(true)
  }

  async function handleFormSubmit(payload) {
    setSubmitting(true)
    setError(null)
    try {
      if (editingTask) {
        await client.patch(`/tasks/${editingTask.id}`, payload)
        setSuccessMessage('Task updated.')
      } else {
        await client.post('/tasks', payload)
        setSuccessMessage('Task created.')
      }
      setFormOpen(false)
      await fetchTasks()
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setSubmitting(false)
    }
  }

  async function handleDelete(task) {
    if (!window.confirm(`Delete "${task.title}"? This can't be undone.`)) {
      return
    }
    setError(null)
    try {
      await client.delete(`/tasks/${task.id}`)
      setSuccessMessage('Task deleted.')
      // If this was the last task on the current page (and we're not
      // already on page 1), step back a page instead of showing an
      // empty page that technically still has earlier pages with tasks.
      if (tasks.length === 1 && page > 1) {
        setPage(page - 1)
      } else {
        await fetchTasks()
      }
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  return (
    <div className="min-h-screen">
      <header className="border-b border-ink-100 bg-canvas-card">
        <div className="mx-auto flex max-w-4xl items-center justify-between px-4 py-4">
          <div>
            <h1 className="text-lg font-semibold text-ink-900">Task Manager</h1>
            <p className="font-mono text-xs text-ink-300">
              {user?.email}
              {isAdmin && ' · admin'}
            </p>
          </div>
          <button
            type="button"
            onClick={logout}
            className="rounded-lg px-3 py-1.5 text-sm font-medium text-ink-500 hover:bg-ink-100 hover:text-ink-900"
          >
            Log out
          </button>
        </div>
      </header>

      <main className="mx-auto max-w-4xl px-4 py-6">
        {successMessage && (
          <div className="mb-4">
            <Banner tone="success" onDismiss={() => setSuccessMessage(null)}>
              {successMessage}
            </Banner>
          </div>
        )}
        {error && (
          <div className="mb-4">
            <Banner tone="error" onDismiss={() => setError(null)}>
              {error}
            </Banner>
          </div>
        )}

        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <h2 className="text-sm font-medium text-ink-500">
            {isAdmin ? 'All tasks' : 'Your tasks'}
            {!loading && ` · ${meta.total_items}`}
          </h2>
          <button
            type="button"
            onClick={openCreateForm}
            className="rounded-lg bg-brand-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-brand-700"
          >
            + New task
          </button>
        </div>

        <div className="mb-6 flex flex-wrap gap-2">
          <input
            type="search"
            value={search}
            onChange={(e) => updateFilter(setSearch)(e.target.value)}
            placeholder="Search title or description..."
            className="min-w-[200px] flex-1 rounded-lg border border-ink-100 bg-canvas-card px-3 py-1.5 text-sm text-ink-900 focus:border-brand-500"
          />
          <select
            value={status}
            onChange={(e) => updateFilter(setStatus)(e.target.value)}
            className="rounded-lg border border-ink-100 bg-canvas-card px-3 py-1.5 text-sm text-ink-900 focus:border-brand-500"
          >
            <option value="">All statuses</option>
            <option value="TODO">To do</option>
            <option value="IN_PROGRESS">In progress</option>
            <option value="DONE">Done</option>
          </select>
          <select
            value={priority}
            onChange={(e) => updateFilter(setPriority)(e.target.value)}
            className="rounded-lg border border-ink-100 bg-canvas-card px-3 py-1.5 text-sm text-ink-900 focus:border-brand-500"
          >
            <option value="">All priorities</option>
            <option value="LOW">Low</option>
            <option value="MEDIUM">Medium</option>
            <option value="HIGH">High</option>
          </select>
          <select
            value={`${sortBy}:${sortOrder}`}
            onChange={(e) => {
              const [by, order] = e.target.value.split(':')
              setSortBy(by)
              setSortOrder(order)
              setPage(1)
            }}
            className="rounded-lg border border-ink-100 bg-canvas-card px-3 py-1.5 text-sm text-ink-900 focus:border-brand-500"
          >
            <option value="created_at:desc">Newest first</option>
            <option value="created_at:asc">Oldest first</option>
            <option value="title:asc">Title A-Z</option>
            <option value="priority:desc">Priority high-low</option>
          </select>
        </div>

        {loading ? (
          <p className="py-12 text-center text-sm text-ink-300">Loading tasks...</p>
        ) : tasks.length === 0 ? (
          <div className="rounded-lg border border-dashed border-ink-100 py-12 text-center">
            <p className="text-sm text-ink-500">
              {search || status || priority
                ? 'No tasks match these filters.'
                : "No tasks yet. Create your first one above."}
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {tasks.map((task) => (
              <TaskRow key={task.id} task={task} onEdit={openEditForm} onDelete={handleDelete} />
            ))}
          </div>
        )}

        {!loading && meta.total_pages > 1 && (
          <div className="mt-6 flex items-center justify-center gap-3 text-sm">
            <button
              type="button"
              disabled={page <= 1}
              onClick={() => setPage(page - 1)}
              className="rounded-md px-3 py-1 font-medium text-ink-500 hover:bg-ink-100 disabled:opacity-40"
            >
              Previous
            </button>
            <span className="text-ink-300">
              Page {meta.page} of {meta.total_pages}
            </span>
            <button
              type="button"
              disabled={page >= meta.total_pages}
              onClick={() => setPage(page + 1)}
              className="rounded-md px-3 py-1 font-medium text-ink-500 hover:bg-ink-100 disabled:opacity-40"
            >
              Next
            </button>
          </div>
        )}
      </main>

      {formOpen && (
        <Modal title={editingTask ? 'Edit task' : 'New task'} onClose={() => setFormOpen(false)}>
          <TaskForm
            initial={editingTask}
            onSubmit={handleFormSubmit}
            onCancel={() => setFormOpen(false)}
            submitting={submitting}
          />
        </Modal>
      )}
    </div>
  )
}
