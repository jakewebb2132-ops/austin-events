export default function Footer({ sources, generatedAt }) {
  const year = new Date(generatedAt).getFullYear()

  return (
    <footer
      className="border-t py-12 px-6"
      style={{ borderColor: 'var(--border)', background: 'rgba(255,255,255,0.6)' }}
    >
      <div className="max-w-6xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div
            className="w-7 h-7 flex items-center justify-center rounded-[4px]"
            style={{ background: 'var(--text-primary)' }}
          >
            <span
              className="text-white text-[10px] font-bold"
              style={{ fontFamily: '"Space Grotesk", sans-serif' }}
            >
              JW
            </span>
          </div>
          <div>
            <p
              className="text-xs font-medium"
              style={{ fontFamily: '"Space Grotesk", sans-serif', color: 'var(--text-primary)' }}
            >
              JW AI Consulting
            </p>
            <p className="text-[11px]" style={{ color: 'var(--text-muted)' }}>
              © {year} · Austin, TX
            </p>
          </div>
        </div>

        <div className="text-center sm:text-right">
          <p className="text-[11px]" style={{ color: 'var(--text-muted)', fontFamily: 'Inter, sans-serif' }}>
            Events sourced from{' '}
            {sources.map((s, i) => (
              <span key={s}>
                <span style={{ color: 'var(--text-secondary)' }}>{s}</span>
                {i < sources.length - 1 && ', '}
              </span>
            ))}
          </p>
          <p className="text-[11px] mt-0.5" style={{ color: 'var(--text-muted)', fontFamily: 'Inter, sans-serif' }}>
            Updated every Sunday at 5 PM CT
          </p>
        </div>
      </div>
    </footer>
  )
}
