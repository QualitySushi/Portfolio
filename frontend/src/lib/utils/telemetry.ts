export async function trackEvent(eventType: string, payload: Record<string, any>) {
  try {
    const baseUrl = import.meta.env.PUBLIC_API_URL || 'http://localhost:4000';
    
    await fetch(`${baseUrl}/api/telemetry`, {
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