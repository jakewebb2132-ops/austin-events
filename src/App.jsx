import eventsData from '../austin-events-data.json'
import Nav from './components/Nav.jsx'
import Hero from './components/Hero.jsx'
import EventsSection from './components/EventsSection.jsx'
import Footer from './components/Footer.jsx'

export default function App() {
  return (
    <div className="min-h-screen">
      <Nav />
      <main>
        <Hero weekOf={eventsData.weekOf} generatedAt={eventsData.generatedAt} />
        <div className="max-w-6xl mx-auto px-6 pb-24 space-y-20">
          <EventsSection
            title="AI Events"
            eyebrow="Artificial Intelligence"
            events={eventsData.aiEvents}
            accentColor="ai"
          />
          <EventsSection
            title="Business & Community"
            eyebrow="Networking & Awards"
            events={eventsData.otherEvents}
            accentColor="other"
          />
        </div>
      </main>
      <Footer sources={eventsData.sources} generatedAt={eventsData.generatedAt} />
    </div>
  )
}
