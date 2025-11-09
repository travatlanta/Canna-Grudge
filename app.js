// CannaGrudge: global bottom-nav normalizer
document.addEventListener('DOMContentLoaded', () => {
  // --- simple auth guard for protected pages ---
  (function(){
    try {
      /*
       * Determine whether the current page should require authentication.  In
       * addition to checking for exact filenames like `dashboard.html`, also
       * match routes without extensions (e.g. `/dashboard` or `/dashboard/`).
       * This helps when the app is served via a web server that rewrites URLs
       * or when the `.html` extension is omitted.
       */
      const path = location.pathname.toLowerCase();
      // Pages or keywords that require the user to be logged in.  If the
      // pathname contains any of these strings, the user will be redirected
      // to the login page unless localStorage indicates they are logged in.
      const authKeywords = ['dashboard', 'checkout', 'confirmation', 'profile'];
      const requiresAuth = authKeywords.some(k => path.includes(k));
      const loggedIn = localStorage.getItem('isLoggedIn') === '1';
      if (!loggedIn && requiresAuth) {
        // Build a URL to the login page relative to the current directory.  If the
        // app is served from a subdirectory or routes omit the `.html`
        // extension (e.g. `/dashboard`), using simply 'login.html' would
        // incorrectly point into the current route (e.g. `/dashboard/login.html`).
        // Instead, compute the base directory from the current pathname.
        const ret = encodeURIComponent(location.pathname + location.search + location.hash);
        const currentPath = location.pathname;
        const lastSlash = currentPath.lastIndexOf('/');
        const basePath = lastSlash >= 0 ? currentPath.slice(0, lastSlash) : '';
        const loginPath = (basePath ? basePath : '') + '/login.html';
        location.href = loginPath + '?return=' + ret;
      }
    } catch(e) {
      // swallow errors so the page continues to render
    }
  })();

  const NEW_NAV_HTML = `
    <nav class="bottom-nav">
      <a href="event.html">Event Info</a>
      <a href="index.html" class="home" aria-label="Home">
        <img src="assets/Icons/home.png" alt="Home" width="22" height="22" />
        <span class="sr-only">Home</span>
      </a>
      <a href="dashboard.html">Dashboard</a>
    </nav>
  `.trim();

  function applyNav() {
    let nav = document.querySelector('nav.bottom-nav');
    if (!nav) {
      // create at end of body if missing
      nav = document.createElement('nav');
      nav.className = 'bottom-nav';
      document.body.appendChild(nav);
    }
    // Replace with the exact markup
    nav.outerHTML = NEW_NAV_HTML;

    // No need to tint the home icon; the PNG already contains the brand color. Remove inline SVG tinting.
  }

  applyNav();

  // === Social login & modal enhancements ===
  /**
   * Simulate retrieval of a social profile.
   * In a real implementation this would call an OAuth provider.
   * Returns a minimal user object with name and email.
   * The avatar URL is optional and left blank; the dashboard will fall back to initials.
   */
  function simulateUser(provider) {
    const names = ['Jane Smith', 'John Doe', 'Alex Johnson', 'Chris Green', 'Pat Taylor'];
    const name = names[Math.floor(Math.random() * names.length)];
    const slug = name.toLowerCase().replace(/\s+/g, '.');
    const domain = provider === 'google' ? 'gmail.com' :
                   provider === 'facebook' ? 'facebook.com' : 'example.com';
    const email = `${slug}@${domain}`;
    return {
      fullName: name,
      email: email,
      avatarUrl: '' // Leave blank to allow fallback initials
    };
  }

  /**
   * Persist a user to localStorage and redirect appropriately.
   * Called when a social login button is clicked.
   */
  function finishLogin(user) {
    try {
      localStorage.setItem('isLoggedIn', '1');
      localStorage.setItem('fullName', user.fullName);
      localStorage.setItem('email', user.email);
      if (user.avatarUrl) localStorage.setItem('avatarUrl', user.avatarUrl);
      // Set a default ticket tier if not already set
      if (!localStorage.getItem('ticketTier')) {
        localStorage.setItem('ticketTier', 'General Admission');
      }
    } catch(e) {
      // swallow storage errors
    }
    const currentPath = location.pathname;
    const lastSlash = currentPath.lastIndexOf('/');
    const basePath = lastSlash >= 0 ? currentPath.slice(0, lastSlash) : '';
    const dashboardPath = (basePath ? basePath : '') + '/dashboard.html';
    const file = (currentPath.split('/').pop() || '').toLowerCase();
    if (file === 'login.html' || file === 'login') {
      // Respect return parameter if present
      const params = new URLSearchParams(location.search);
      const ret = params.get('return');
      const dest = ret ? decodeURIComponent(ret) : dashboardPath;
      location.href = dest;
    } else {
      // Close modal if present
      const modal = document.getElementById('loginModal');
      if (modal && typeof modal.close === 'function') {
        modal.close();
      }
      // Redirect to dashboard so the user sees their info
      location.href = dashboardPath;
    }
  }

  /**
   * Replace the login modal on pages that include it with a unified template.
   * Adds real Facebook and Google icons and data-provider hooks.
   */
  function updateLoginModal() {
    const dialog = document.getElementById('loginModal');
    if (!dialog) return;
    // Define inline SVGs for Facebook and Google logos
    const fbSvg = '<svg viewBox="0 0 512 512" width="18" height="18" aria-hidden="true"><path fill="currentColor" d="M512 256C512 114.6 397.4 0 256 0S0 114.6 0 256C0 376 82.7 476.8 194.2 504.5V334.2H141.4V256h52.8V222.3c0-87.1 39.4-127.5 125-127.5c16.2 0 44.2 3.2 55.7 6.4V172c-6-.6-16.5-1-29.6-1c-42 0-58.2 15.9-58.2 57.2V256h83.6l-14.4 78.2H287V510.1C413.8 494.8 512 386.9 512 256z" /></svg>';
    const googleSvg = '<svg viewBox="0 0 488 512" width="18" height="18" aria-hidden="true"><path fill="currentColor" d="M488 261.8C488 403.3 391.1 504 248 504C110.8 504 0 393.2 0 256S110.8 8 248 8c66.8 0 123 24.5 166.3 64.9l-67.5 64.9C258.5 52.6 94.3 116.6 94.3 256c0 86.5 69.1 156.6 153.7 156.6 98.2 0 135-70.4 140.8-106.9H248v-85.3h236.1c2.3 12.7 3.9 24.9 3.9 41.4z" /></svg>';
    const modalHTML = `
      <div class="card" style="border:none;">
        <h2 class="display" style="margin-bottom:8px;">Sign in</h2>
        <p class="muted" style="margin:0 0 12px;">Fast login to save your tickets.</p>
        <div style="display:grid; gap:10px; margin-bottom:12px;">
          <button class="button button--primary" data-provider="facebook" style="background:#1877F2; color:#fff;">
            ${fbSvg}<span style="margin-left:8px;">Continue with Facebook</span>
          </button>
          <button class="button button--primary" data-provider="google" style="background:#0F9D58; color:#fff;">
            ${googleSvg}<span style="margin-left:8px;">Continue with Google</span>
          </button>
          <button class="button button--ghost" data-provider="email">Continue with Email</button>
        </div>
        <div style="display:flex; justify-content:flex-end; gap:8px;">
          <button class="button button--ghost" data-close-modal>Close</button>
        </div>
      </div>
    `;
    // Overwrite dialog content
    dialog.innerHTML = modalHTML;
    // Set up close handler
    const closeBtn = dialog.querySelector('[data-close-modal]');
    if (closeBtn) {
      closeBtn.addEventListener('click', () => {
        dialog.close();
      });
    }
  }

  /**
   * Attach click listeners to social login buttons (Google, Facebook).
   * This will simulate retrieving profile info and then call finishLogin.
   */
  function attachSocialListeners() {
    document.querySelectorAll('[data-provider]').forEach(btn => {
      const provider = btn.dataset.provider;
      if (provider === 'google' || provider === 'facebook') {
        btn.addEventListener('click', (e) => {
          e.preventDefault();
          const user = simulateUser(provider);
          finishLogin(user);
        });
      } else if (provider === 'email') {
        // If inside a modal, redirect to login page preserving return
        btn.addEventListener('click', (e) => {
          e.preventDefault();
          // compute return path: if current page is not login, include path; else skip
          const file = (location.pathname.split('/').pop() || '').toLowerCase();
          const current = location.pathname + location.search + location.hash;
          const dest = 'login.html' + (file !== 'login.html' ? ('?return=' + encodeURIComponent(current)) : '');
          location.href = dest;
        });
      }
    });
  }

  // Update login modal if present and attach listeners
  updateLoginModal();
  attachSocialListeners();
});
