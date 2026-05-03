export default function Nav() {
  return (
    <nav className="glass-nav fixed top-0 left-0 right-0 z-50">
      <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
        <a
          href="https://jwaiconsulting.com"
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-3 group"
        >
          <div
            className="w-8 h-8 flex items-center justify-center rounded-[4px] flex-shrink-0"
            style={{ background: 'var(--text-primary)' }}
          >
            <span
              className="text-white text-xs font-bold tracking-tight"
              style={{ fontFamily: '"Space Grotesk", sans-serif' }}
            >
              JW
            </span>
          </div>
          <span
            className="text-sm font-medium hidden sm:block"
            style={{
              fontFamily: '"Space Grotesk", sans-serif',
              color: 'var(--text-primary)',
              letterSpacing: '0.01em',
            }}
          >
            JW AI Consulting
          </span>
        </a>

        <a
          href="https://jwaiconsulting.com/#contact"
          target="_blank"
          rel="noopener noreferrer"
          className="btn-outline"
        >
          Book a Discovery Call
        </a>
      </div>
    </nav>
  )
}
