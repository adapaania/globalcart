function formatTs(ts) {
  if (!ts) return ''
  try {
    return new Date(ts).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  } catch {
    return ts
  }
}

export default function Timeline({ events }) {
  if (!events || events.length === 0) {
    return <p className="text-sm text-slate-400">No timeline events recorded.</p>
  }

  return (
    <ol className="relative border-l-2 border-slate-200 ml-2">
      {events.map((ev, idx) => (
        <li key={ev.id ?? idx} className="mb-6 ml-6 last:mb-0">
          <span className="absolute -left-[9px] flex items-center justify-center w-4 h-4 rounded-full bg-accent ring-4 ring-white" />
          <div className="flex flex-wrap items-center gap-2">
            <span className="inline-block px-2 py-0.5 rounded text-xs font-semibold bg-slate-100 text-slate-700 border border-slate-200">
              {ev.event_type}
            </span>
            <span className="text-xs text-slate-400">{formatTs(ev.timestamp)}</span>
          </div>
          <p className="mt-1 text-sm text-slate-800">{ev.description}</p>
          <p className="text-xs text-slate-400 mt-0.5">by {ev.actor}</p>
        </li>
      ))}
    </ol>
  )
}
