<template>
  <div class="container mt-5 d-flex justify-content-center align-items-center"
       style="min-height: 80vh;">
    <div class="card p-4 shadow-sm" style="max-width: 800px; width: 100%;">
      <h3 class="text-center mb-4">404 - Page Not Found</h3>

      <div class="security-warning">
        <h5 class="text-danger">⚠️ System Security Alert</h5>
        <p class="text-muted small">
          For security purposes, this access attempt has been logged. Any unauthorized activity will be investigated.
        </p>
        <div class="log-details">
          <div class="log-entry"><span class="log-separator">--- Event Details ---</span></div>
          <div class="log-entry"><span class="log-key">EVENT ID:</span><span class="log-value">{{ userInfo.eventId }}</span></div>
          <div class="log-entry"><span class="log-key">TIMESTAMP (UTC):</span><span class="log-value">{{ userInfo.timestamp }}</span></div>
          <div class="log-entry"><span class="log-key">RULE TRIGGERED:</span><span class="log-value">{{ userInfo.rule }}</span></div>

          <div class="log-entry"><span class="log-separator">--- Network Trace ---</span></div>
          <div class="log-entry"><span class="log-key">PROTOCOL:</span><span class="log-value">{{ userInfo.protocol }}</span></div>
          <div class="log-entry"><span class="log-key">IP ADDRESS:</span><span class="log-value">{{ userInfo.ip }}</span></div>
          <div class="log-entry"><span class="log-key">SOURCE PORT:</span><span class="log-value">{{ userInfo.sourcePort }}</span></div>
          <div class="log-entry"><span class="log-key">ISP:</span><span class="log-value">{{ userInfo.isp }}</span></div>

          <div class="log-entry"><span class="log-separator">--- Geolocation &amp; Path ---</span></div>
          <div class="log-entry"><span class="log-key">CITY:</span><span class="log-value">{{ userInfo.city }}</span></div>
          <div class="log-entry"><span class="log-key">LOCATION:</span><span class="log-value">{{ userInfo.location }}</span></div>
          <div class="log-entry"><span class="log-key">ATTEMPTED PATH:</span><span class="log-value">{{ userInfo.path }}</span></div>
          <div class="log-entry"><span class="log-key">REFERER:</span><span class="log-value">{{ userInfo.referer }}</span></div>

          <div class="log-entry"><span class="log-separator">--- Client Fingerprint ---</span></div>
          <div class="log-entry"><span class="log-key">BROWSER:</span><span class="log-value">{{ userInfo.browser }}</span></div>
          <div class="log-entry"><span class="log-key">DEVICE:</span><span class="log-value">{{ userInfo.device }}</span></div>
          <div class="log-entry">
            <span class="log-key">USER-AGENT:</span>
            <pre class="log-value ua-formatted">{{ userInfo.userAgent }}</pre>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import { UAParser } from 'ua-parser-js';

const userInfo = ref({
  city: 'Resolving...',
  location: 'Resolving...',
  browser: 'N/A',
  device: 'N/A',
  userAgent: 'N/A',
  ip: 'Resolving...',
  isp: 'Resolving...',
  timestamp: new Date().toISOString(),
  eventId: crypto.randomUUID(),
  path: 'N/A',
  referer: 'N/A',
  sourcePort: 'N/A',
  protocol: 'TCP/IP',
  rule: '404-ACCESS-VIOLATION',
});

const loading = ref(true);
const error = ref(null);
const route = useRoute();

// 【V7 修改】User Agent格式化逻辑
const formatUserAgent = (ua) => {
  return ua.replace(/\s(\([^)]+\)|[^\s]+\/[^\s]+)/g, '\n  $1');
};

const parseUserAgent = () => {
  userInfo.value.userAgent = formatUserAgent(navigator.userAgent);

  const parser = new UAParser();
  const result = parser.getResult();
  const browserName = result.browser.name || 'Unknown';
  userInfo.value.browser = `${browserName} ${result.browser.version || ''}`.trim();
  const deviceModel = result.device.model || 'Desktop Device';
  userInfo.value.device = `${result.device.vendor || ''} ${deviceModel}`.trim();
};

onMounted(async () => {
  try {
    parseUserAgent();
    userInfo.value.path = route.fullPath;
    userInfo.value.referer = document.referrer || 'Direct Access';
    userInfo.value.sourcePort = Math.floor(Math.random() * (65535 - 10000 + 1)) + 10000;

    const [geoResponse, ipResponse] = await Promise.all([
      fetch('https://api.bigdatacloud.net/data/reverse-geocode-client'),
      fetch('http://ip-api.com/json')
    ]);

    if (geoResponse.ok) {
      const geoData = await geoResponse.json();
      userInfo.value.city = geoData.city || 'Unavailable';
      const locationParts = [geoData.countryName, geoData.principalSubdivision, geoData.city].filter(Boolean);
      userInfo.value.location = locationParts.length > 0 ? locationParts.join(', ') : 'Unavailable';
    } else {
      userInfo.value.city = 'Unavailable';
      userInfo.value.location = 'Unavailable';
    }

    if (ipResponse.ok) {
      const ipData = await ipResponse.json();
      userInfo.value.ip = ipData.query || 'Unavailable';
      userInfo.value.isp = ipData.isp || 'Unavailable';
    } else {
      userInfo.value.ip = 'Unavailable';
      userInfo.value.isp = 'Unavailable';
    }

  } catch (e) {
    error.value = e.message;
    console.error("Error fetching user info:", e);
  } finally {
    loading.value = false;
  }
});
</script>

<style scoped>
.security-warning {
  border: 1px solid #dc3545;
  border-radius: 0.25rem;
  padding: 1rem;
  margin-top: 1rem;
  background-color: #f8f9fa;
}

.security-warning h5 {
  font-weight: bold;
}

.log-details {
  background-color: #e9ecef;
  padding: 0.75rem;
  border-radius: 0.25rem;
  font-family: 'Courier New', Courier, monospace;
  font-size: 0.85em;
  color: #212529;
}

.log-entry {
  display: flex;
  line-height: 1.6;
}

.log-key {
  color: #6c757d;
  font-weight: bold;
  flex-shrink: 0;
  width: 160px;
}

.log-value {
  word-break: break-all;
}

.log-separator {
  flex-basis: 100%;
  text-align: center;
  color: #adb5bd;
  margin: 0.5rem 0;
}

.ua-formatted {
  margin: 0;
  padding: 0;
  font-family: inherit;
  font-size: inherit;
  white-space: pre-wrap;
  line-height: 1.5;
}
</style>
