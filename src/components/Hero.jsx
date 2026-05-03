import { MapPin, CalendarBlank } from '@phosphor-icons/react'

export default function Hero({ weekOf, generatedAt }) {
  const updatedDate = new Date(generatedAt).toLocaleDateString('en-US', {
    month: 'long',
    day: 'numeric',
    year: 'numeric',
    timeZone: 'America/Chicago',
  })

  return (
    <section className="pt-40 pb-20 px-6 text-center">
      <div className="max-w-3xl mx-auto">
        <div className="inline-flex items-center gap-2 mb-6 px-4 py-1.5 rounded-full border"
          style={{
            borderColor: 'var(--border)',
            background: 'rgba(58,111,188,0.06)',
          }}
        >
          <MapPin
            size={14}
            weight="light"
            style={{ color: 'var(--accent)' }}
          />
          <span
            className="text-xs font-medium tracking-widest2 uppercase"
            style={{ fontFamily: '"Space Grotesk", sans-serif', color: 'var(--accent)' }}
          >
            Austin, Texas
          </span>
        </div>

        <h1
          className="text-5xl sm:text-6xl font-semibold leading-tight mb-6"
          style={{ fontFamily: '"Space Grotesk", sans-serif', color: 'var(--text-primary)' }}
        >
          This Week in{' '}
          <span style={{ color: 'var(--accent)' }}>Austin</span>
        </h1>

        <p
          className="text-lg sm:text-xl leading-relaxed mb-10 max-w-xl mx-auto"
          style={{ color: 'var(--text-secondary)', fontFamily: 'Inter, sans-serif' }}
        >
          The week's top AI and business events, curated every Sunday morning so
          you never miss what's happening in your city.
        </p>

        <div
          className="inline-flex items-center gap-2 px-5 py-3 rounded-card border"
          style={{
            borderColor: 'var(--border)',
            background: 'var(--bg-card)',
            backdropFilter: 'blur(12px)',
          }}
        >
          <CalendarBlank size={16} weight="light" style={{ color: 'var(--accent)' }} />
          <span
            className="text-sm font-medium"
            style={{ fontFamily: '"Space Grotesk", sans-serif', color: 'var(--text-primary)' }}
          >
            Week of {weekOf}
          </span>
          <span className="mx-2" style={{ color: 'var(--border)' }}>·</span>
          <span
            className="text-xs"
            style={{ color: 'var(--text-muted)', fontFamily: 'Inter, sans-serif' }}
          >
            Updated {updatedDate}
          </span>
        </div>
      </div>
    </section>
  )
}
