const express = require('express');
const cors = require('cors');
const { createProxyMiddleware } = require('http-proxy-middleware');
const { createClient } = require('@supabase/supabase-js');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 4000;

// Initialize Supabase Client
const supabaseUrl = process.env.SUPABASE_URL;
const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.SUPABASE_ANON_KEY || process.env.SUPABASE_KEY;
const supabase = createClient(supabaseUrl, supabaseKey);

// Global Middleware
app.use(cors());

// Target URLs for your two separate microservices using Docker container names
const ESTIMATOR_URL = process.env.ESTIMATOR_SERVICE_URL || 'http://efficiency-estimator:8000';
const GCODE_URL = process.env.GCODE_SERVICE_URL || 'http://gcode-generator:8000';

// 1. Proxy Route: Efficiency Estimator
app.use('/api/estimator', (req, res, next) => {
    console.log(`[Gateway Proxy] Estimator -> ${req.method} ${req.url}`);
    next();
}, createProxyMiddleware({
    target: ESTIMATOR_URL,
    changeOrigin: true,
    pathRewrite: { '^/api/estimator': '' },
    onError: (err, req, res) => {
        console.error('[Estimator Proxy Error]:', err);
        res.status(502).json({ error: 'Estimator service unavailable' });
    }
}));

// 2. Proxy Route: G-Code Generator
app.use('/api/gcode', (req, res, next) => {
    console.log(`[Gateway Proxy] G-Code -> ${req.method} ${req.url}`);
    next();
}, createProxyMiddleware({
    target: GCODE_URL,
    changeOrigin: true,
    pathRewrite: { '^/api/gcode': '' },
    onError: (err, req, res) => {
        console.error('[G-Code Proxy Error]:', err);
        res.status(502).json({ error: 'G-Code service unavailable' });
    }
}));

// 3. JSON Body Parser Middleware: Applied ONLY to local gateway routes after the proxy
app.use(express.json());

// 4. Telemetry Route: Catches frontend engagement/simulation tracking events
app.post('/api/telemetry', async (req, res) => {
  // Extract client IP (checking proxies like X-Forwarded-For or direct remote address)
  const rawIp = req.headers['x-forwarded-for'] || req.socket.remoteAddress;
  const clientIp = rawIp ? rawIp.replace(/^.*:/, '') : ''; // Clean up IPv6 mapped IPv4 if present

  // Define loopback defaults and load additional IPs from .env
  const defaultIgnored = ['127.0.0.1', '::1', 'localhost'];
  const envIgnored = process.env.IGNORED_IPS ? process.env.IGNORED_IPS.split(',').map(ip => ip.trim()) : [];
  const ignoredIps = [...defaultIgnored, ...envIgnored];

  // If the request comes from your configured IP, acknowledge it but don't write to Supabase
  if (ignoredIps.includes(clientIp)) {
    return res.status(200).json({ success: true, filtered: true });
  }

  const { event_type, timestamp, path, ...metadata } = req.body;
  
  try {
    const { data, error } = await supabase
      .from('visitor_telemetry')
      .insert([{ event_type, path, metadata, created_at: timestamp }]);

    if (error) throw error;
    res.status(200).json({ success: true });
  } catch (err) {
    console.error('Error logging telemetry to Supabase:', err.message);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// 5. Admin Analytics Endpoint: Retrieves aggregated telemetry metrics
app.get('/api/analytics', async (req, res) => {
  try {
    // Fetch raw recent events or grouped metrics
    const { data: recentEvents, error: recentError } = await supabase
      .from('visitor_telemetry')
      .select('*')
      .order('created_at', { ascending: false })
      .limit(50);

    if (recentError) throw recentError;

    // Fetch total event count
    const { count, error: countError } = await supabase
      .from('visitor_telemetry')
      .select('*', { count: 'exact', head: true });

    if (countError) throw countError;

    res.status(200).json({
      total_events: count,
      recent_activity: recentEvents
    });
  } catch (err) {
    console.error('Error fetching telemetry analytics:', err.message);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Health check endpoint
app.get('/health', (req, res) => {
    res.status(200).json({ status: 'Gateway is healthy', timestamp: new Date() });
});

app.listen(PORT, () => {
    console.log(`API Gateway running on port ${PORT}`);
});