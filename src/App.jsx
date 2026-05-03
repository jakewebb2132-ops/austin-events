import { useState, useEffect } from 'react'
import Nav from './components/Nav.jsx'
import Hero from './components/Hero.jsx'
import EventsSection from './components/EventsSection.jsx'
import Footer from './components/Footer.jsx'

export default function App() {
  const [data, setData] = useState(null)
  const [error, setError] = useState(false)

  useEffect(() => {
    fetch(`${import.meta.env.BASE_URL}austin-events-data.json`)
      .then((r) => {
        if (!r.ok) throw new Error(r.status)
        return r.json()
      })
      .then(setData)
      .catch(() => setError(true))
  }, [])

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p style={{ color: 'var(--text-muted)', fontFamily: 'Inter, sans-serif' }}>
          Could not load events data. Please try again later.
        </p>
      </div>
    )
  }

  if (!data) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div
          className="w-6 h-6 rounded-full border-2 border-t-transparent animate-spin"
          style={{ borderColor: 'var(--accent)', borderTopColor: 'transparent' }}
        />
      </div>
    )
  }

  return (
    <div className="min-h-screen">
      <Nav />
      <main>
        <Hero weekOf={data.weekOf} generatedAt={data.generatedAt} />
        <div className="max-w-6xl mx-auto px-6 pb-24 space-y-20">
          <EventsSection
            title="AI Events"
            eyebrow="Artificial Intelligence"
            events={data.aiEvents}
          />
          <EventsSection
            title="Business & Community"
            eyebrow="Networking & Awards"
            events={data.otherEvents}
          />
        </div>
      </main>
      <Footer sources={data.sources} generatedAt={data.generatedAt} />
    </div>
  )
}
