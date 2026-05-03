import { Clock, MapPin, ArrowUpRight } from '@phosphor-icons/react'

const TAG_COLORS = {
  AI:         { bg: 'rgba(58,111,188,0.10)', text: '#3a6fbc' },
  Agents:     { bg: 'rgba(58,111,188,0.10)', text: '#3a6fbc' },
  LLM:        { bg: 'rgba(58,111,188,0.10)', text: '#3a6fbc' },
  Panel:      { bg: 'rgba(26,58,110,0.08)',  text: '#1a3a6e' },
  Workshop:   { bg: 'rgba(26,58,110,0.08)',  text: '#1a3a6e' },
  Hackathon:  { bg: 'rgba(26,58,110,0.08)',  text: '#1a3a6e' },
  Tech:       { bg: 'rgba(26,58,110,0.08)',  text: '#1a3a6e' },
  Startup:    { bg: 'rgba(74,94,122,0.09)',  text: '#4a5e7a' },
  Community:  { bg: 'rgba(74,94,122,0.09)',  text: '#4a5e7a' },
  Networking: { bg: 'rgba(74,94,122,0.09)',  text: '#4a5e7a' },
}

function Tag({ label }) {
  const style = TAG_COLORS[label] || { bg: 'rgba(138,154,181,0.12)', text: '#8a9ab5' }
  return (
    <span
      className="inline-block px-2 py-0.5 rounded text-[10px] font-medium uppercase"
      style={{
        background: style.bg,
        color: style.text,
        fontFamily: '"Space Grotesk", sans-serif',
        letterSpacing: '0.07em',
      }}
    >
      {label}
    </span>
  )
}

function DateBadge({ date }) {
  // Parse "May 5" or "May 8–10" — grab the first number
  const parts = date.split(' ')
  const month = parts[0]?.slice(0, 3).toUpperCase() ?? ''
  const day = parts[1]?.split('–')[0] ?? ''

  return (
    <div
      className="flex-shrink-0 w-14 flex flex-col items-center justify-center py-2 rounded-[6px]"
      style={{ background: 'rgba(58,111,188,0.07)', minHeight: '3.25rem' }}
    >
      <span
        className="text-[10px] font-semibold tracking-widest2 uppercase leading-none"
        style={{ fontFamily: '"Space Grotesk", sans-serif', color: 'var(--accent)' }}
      >
        {month}
      </span>
      <span
        className="text-xl font-bold leading-tight"
        style={{ fontFamily: '"Space Grotesk", sans-serif', color: 'var(--text-primary)' }}
      >
        {day}
      </span>
    </div>
  )
}

export default function EventCard({ event }) {
  const hasUrl = typeof event.url === 'string' && event.url.length > 0

  return (
    <article
      className="flex gap-5 py-6 group"
      style={{ borderBottom: '1px solid var(--border)' }}
    >
      {/* Date badge */}
      <DateBadge date={event.date} />

      {/* Main content */}
      <div className="flex-1 min-w-0">
        <div className="flex flex-wrap items-start gap-x-3 gap-y-1.5 mb-2">
          <h3
            className="text-base font-semibold leading-snug"
            style={{ fontFamily: '"Space Grotesk", sans-serif', color: 'var(--text-primary)' }}
          >
            {event.title}
          </h3>
          <div className="flex flex-wrap gap-1.5">
            {event.tags.map((tag) => (
              <Tag key={tag} label={tag} />
            ))}
          </div>
        </div>

        <div className="flex flex-wrap gap-x-4 gap-y-0.5 mb-2">
          <span className="flex items-center gap-1.5">
            <Clock size={12} weight="light" style={{ color: 'var(--text-muted)', flexShrink: 0 }} />
            <span className="text-xs" style={{ color: 'var(--text-secondary)', fontFamily: 'Inter, sans-serif' }}>
              {event.time}
            </span>
          </span>
          <span className="flex items-center gap-1.5">
            <MapPin size={12} weight="light" style={{ color: 'var(--text-muted)', flexShrink: 0 }} />
            <span className="text-xs" style={{ color: 'var(--text-secondary)', fontFamily: 'Inter, sans-serif' }}>
              {event.location}
            </span>
          </span>
        </div>

        <p
          className="text-sm leading-relaxed"
          style={{ color: 'var(--text-secondary)', fontFamily: 'Inter, sans-serif' }}
        >
          {event.description}
        </p>
      </div>

      {/* CTA — only rendered when a URL exists */}
      {hasUrl && (
        <div className="flex-shrink-0 flex items-start pt-0.5">
          <a
            href={event.url}
            target="_blank"
            rel="noopener noreferrer"
            className="btn-outline inline-flex items-center gap-1.5"
          >
            Details
            <ArrowUpRight size={11} weight="bold" />
          </a>
        </div>
      )}
    </article>
  )
}
