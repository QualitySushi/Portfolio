export async function trackEvent(eventType: string, payload: Record<string, any>) {
  try {
    // Replace with your Express Gateway telemetry URL or relative path if proxied
    await fetch('/api/telemetry', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        event_type: eventType,
        timestamp: new Date().toISOString(),
        path: window.location.pathname,
        ...payload
      })
    });
  } catch (err) {
    // Fail silently so telemetry network errors never break the portfolio UX
    console.debug('Telemetry dispatch failed:', err);
  }
}