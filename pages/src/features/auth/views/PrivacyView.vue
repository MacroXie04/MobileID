<template>
  <div class="privacy-container">
    <div class="privacy-content">
      <header class="privacy-header">
        <img src="/images/mobileid.svg" alt="catcard.online logo" class="privacy-logo" />
        <h1>Privacy Policy for catcard.online</h1>
        <p class="last-updated">Last updated: December 2025</p>
      </header>

      <main class="privacy-main">
        <section>
          <h2>1. Cookies and Google Ads</h2>
          <p>
            We use Google AdSense to display ads. Google may use cookies or similar technologies to
            serve personalized ads based on your visits to this and other websites.
          </p>
          <p>
            You can opt out of personalized advertising by visiting
            <a href="https://adssettings.google.com/" target="_blank" rel="noopener noreferrer"
              >Google Ads Settings</a
            >.
          </p>

          <h2>2. Data Usage</h2>
          <p>
            We do not collect or store any personal information beyond what is required by our
            analytics and advertising providers (e.g., Google Analytics, AdSense).
          </p>

          <h2>3. Third-Party Links</h2>
          <p>
            Our website may contain links to external websites. We are not responsible for the
            content or privacy practices of those sites.
          </p>

          <h2>4. Contact Us</h2>
          <p>
            If you have any questions about this Privacy Policy, please contact us at:
            <a href="mailto:contact@catcard.online">contact@catcard.online</a>.
          </p>
        </section>
      </main>

      <footer class="privacy-footer">
        <p>
          <a href="/" @click.prevent="goBack">← Back to catcard.online</a>
        </p>
        <p>© 2025 catcard.online. All rights reserved.</p>
      </footer>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router';

const router = useRouter();

const goBack = () => {
  // If there's history, go back; otherwise fall back to home
  if (window.history.length > 1) {
    router.back();
  } else {
    router.push('/');
  }
};
</script>

<style scoped>
.privacy-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #f5f7fa 0%, #e4e8ec 100%);
  padding: 2rem 1rem;
}

.privacy-content {
  max-width: 800px;
  margin: 0 auto;
  padding: 2rem;
  background: #fff;
  min-height: calc(100vh - 4rem);
  box-shadow: 0 0 40px rgba(0, 0, 0, 0.05);
  border-radius: 8px;
}

.privacy-header {
  text-align: center;
  margin-bottom: 2.5rem;
  padding-bottom: 1.5rem;
  border-bottom: 2px solid #f0f0f0;
}

.privacy-logo {
  width: 60px;
  height: 60px;
  margin-bottom: 1rem;
}

.privacy-header h1 {
  font-size: 1.8rem;
  font-weight: 700;
  color: #1a1a2e;
  margin-bottom: 0.5rem;
}

.last-updated {
  color: #666;
  font-size: 0.95rem;
  font-style: italic;
}

.privacy-main h2 {
  font-size: 1.25rem;
  font-weight: 600;
  color: #1a1a2e;
  margin: 2rem 0 0.75rem;
  padding-left: 0.75rem;
  border-left: 4px solid #4361ee;
}

.privacy-main p {
  font-size: 1.05rem;
  color: #444;
  margin-bottom: 1rem;
  text-align: justify;
}

.privacy-main a {
  color: #4361ee;
  text-decoration: none;
  transition: color 0.2s ease;
}

.privacy-main a:hover {
  color: #3a0ca3;
  text-decoration: underline;
}

.privacy-footer {
  text-align: center;
  margin-top: 3rem;
  padding-top: 1.5rem;
  border-top: 1px solid #eee;
  color: #888;
  font-size: 0.9rem;
}

.privacy-footer a {
  color: #666;
  text-decoration: none;
}

.privacy-footer a:hover {
  color: #4361ee;
  text-decoration: underline;
}

@media (max-width: 600px) {
  .privacy-content {
    padding: 1.25rem;
  }

  .privacy-header h1 {
    font-size: 1.5rem;
  }

  .privacy-main h2 {
    font-size: 1.1rem;
  }

  .privacy-main p {
    font-size: 1rem;
  }
}
</style>
