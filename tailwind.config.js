/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    extend: {
      colors: {
        'jw-primary':   '#1a3a6e',
        'jw-secondary': '#4a5e7a',
        'jw-muted':     '#8a9ab5',
        'jw-accent':    '#3a6fbc',
        'jw-accent-h':  '#225191',
        'jw-border':    'rgba(58,111,188,0.15)',
      },
      fontFamily: {
        grotesk: ['"Space Grotesk"', 'sans-serif'],
        inter:   ['Inter', 'sans-serif'],
      },
      letterSpacing: {
        widest2: '0.15em',
      },
      borderRadius: {
        btn:  '4px',
        card: '12px',
      },
      backdropBlur: {
        nav: '20px',
      },
    },
  },
  plugins: [],
}
