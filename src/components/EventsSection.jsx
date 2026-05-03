import EventCard from './EventCard.jsx'

export default function EventsSection({ title, eyebrow, events }) {
  if (!events || events.length === 0) return null

  return (
    <section>
      <div className="mb-8">
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
        <div
          className="mt-3 h-px w-12"
          style={{ background: 'var(--accent)', opacity: 0.4 }}
        />
      </div>

      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {events.map((event, i) => (
          <EventCard key={`${event.title}-${i}`} event={event} />
        ))}
      </div>
    </section>
  )
}
