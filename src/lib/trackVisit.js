/**
 * trackVisit.js
 * Fires on every page load. Fetches the visitor's IP from a public API,
 * then sends it to our Supabase enrich-ip Edge Function.
 * The Edge Function does the IP-to-Company lookup, filters residential IPs,
 * scores intent, and writes only valid corporate leads to Supabase.
 */

const SUPABASE_URL = 'https://cdbvlnxirrfczxdccwbr.supabase.co';
const ENRICH_FUNCTION_URL = `${SUPABASE_URL}/functions/v1/enrich-ip`;
const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNkYnZsbnhpcnJmY3p4ZGNjd2JyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzMxNzk1NzcsImV4cCI6MjA4ODc1NTU3N30.NrgP_sXz5z_lpDEh4o_3tZY3upSvBv2BOf5OPsRAz0U';

// Respect user privacy — don't track if they've opted out
function isDoNotTrack() {
  return navigator.doNotTrack === '1' || window.doNotTrack === '1';
}

export async function trackVisit() {
  if (isDoNotTrack()) return;

  try {
    // Step 1: Get the visitor's public IP from a free, no-auth API
    const ipResponse = await fetch('https://api.ipify.org?format=json');
    const { ip } = await ipResponse.json();

    if (!ip) return;

    // Step 2: Fire and forget — send to our enrichment Edge Function
    // We don't await the result so we don't block page rendering
    fetch(ENRICH_FUNCTION_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${SUPABASE_ANON_KEY}`,
      },
      body: JSON.stringify({
        ip,
        path: window.location.pathname,
        user_agent: navigator.userAgent,
      }),
    }).catch(() => {
      // Silently fail — never interrupt the user experience for analytics
    });

  } catch {
    // Never throw — tracking must never break the site
  }
}
