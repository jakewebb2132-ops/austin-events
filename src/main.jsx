import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'
import { trackVisit } from './lib/trackVisit.js'

// Fire the IP enrichment tracker — non-blocking, never breaks the site
trackVisit();

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)
