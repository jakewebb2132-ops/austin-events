import { CalendarBlank, MapPin, Clock, ArrowUpRight } from '@phosphor-icons/react'

const TAG_COLORS = {
  AI:          { bg: 'rgba(58,111,188,0.08)',  text: '#3a6fbc' },
  Agents:      { bg: 'rgba(58,111,188,0.08)',  text: '#3a6fbc' },
  Panel:       { bg: 'rgba(26,58,110,0.07)',   text: '#1a3a6e' },
  Community:   { bg: 'rgba(74,94,122,0.08)',   text: '#4a5e7a' },
  Networking:  { bg: 'rgba(74,94,122,0.08)',   text: '#4a5e7a' },
}

function Tag({ label }) {
  const style = TAG_COLORS[label] || { bg: 'rgba(138,154,181,0.12)', text: '#8a9ab5' }
  return (
    <span
      className="inline-block px-2.5 py-0.5 rounded-full text-[10px] font-medium tracking-wide uppercase"
      style={{
        background: style.bg,
        color: style.text,
        fontFamily: '"Space Grotesk", sans-serif',
        letterSpacing: '0.08em',
      }}
    >
      {label}
    </span>
  )
}

export default function EventCard({ event }) {
  return (
    <article className="glass-card p-6 flex flex-col gap-4">
      <div className="flex flex-wrap gap-1.5">
        {event.tags.map((tag) => (
          <Tag key={tag} label={tag} />
        ))}
      </div>

      <div>
        <h3
          className="text-lg font-semibold leading-snug mb-1"
          style={{ fontFamily: '"Space Grotesk", sans-serif', color: 'var(--text-primary)' }}
        >
          {event.title}
        </h3>
        <p
          className="text-sm leading-relaxed"
          style={{ color: 'var(--text-secondary)', fontFamily: 'Inter, sans-serif' }}
        >
          {event.description}
        </p>
      </div>

      <div className="space-y-1.5">
        <MetaRow icon={<CalendarBlank size={13} weight="light" />} text={event.date} />
        <MetaRow icon={<Clock size={13} weight="light" />} text={event.time} />
        <MetaRow icon={<MapPin size={13} weight="light" />} text={event.location} />
      </div>

      <div className="pt-1 mt-auto">
        <a
          href={event.url}
          target="_blank"
          rel="noopener noreferrer"
          className="btn-solid inline-flex items-center gap-1.5"
        >
          Register
          <ArrowUpRight size={12} weight="bold" />
        </a>
      </div>
    </article>
  )
}

function MetaRow({ icon, text }) {
  return (
    <div className="flex items-start gap-2">
      <span className="mt-0.5 flex-shrink-0" style={{ color: 'var(--text-muted)' }}>
        {icon}
      </span>
      <span
        className="text-xs leading-snug"
        style={{ color: 'var(--text-secondary)', fontFamily: 'Inter, sans-serif' }}
      >
        {text}
      </span>
    </div>
  )
}
