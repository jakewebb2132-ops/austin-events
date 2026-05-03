import EventCard from './EventCard.jsx'

export default function EventsSection({ title, eyebrow, events }) {
  if (!events || events.length === 0) return null

  return (
    <section>
      <div className="mb-2">
        <p
          className="text-xs font-medium uppercase tracking-widest2 mb-2"
          style={{ fontFamily: '"Space Grotesk", sans-serif', color: 'var(--accent)' }}
        >
          {eyebrow}
        </p>
        <h2
          className="text-2xl font-semibold"
          style={{ fontFamily: '"Space Grotesk", sans-serif', color: 'var(--text-primary)' }}
        >
          {title}
        </h2>
      </div>

      {/* List — first item gets a top border, each item adds its own bottom border */}
      <div style={{ borderTop: '1px solid var(--border)' }}>
        {events.map((event, i) => (
          <EventCard key={`${event.title}-${i}`} event={event} />
        ))}
      </div>
    </section>
  )
}
