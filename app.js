// CannaGrudge: global bottom-nav normalizer
document.addEventListener('DOMContentLoaded', () => {
  const NEW_NAV_HTML = `
    <nav class="bottom-nav">
      <a href="event.html">Event Info</a>
      <a href="index.html" class="home" aria-label="Home">
        <svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true">
          <path d="M12 3l9 7-1.5 2L19 11v9h-5v-6H10v6H5v-9l-0.5 1L3 10l9-7z" fill="currentColor"></path>
        </svg>
        <span class="sr-only">Home</span>
      </a>
      <a href="profile.html">Dashboard</a>
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

    // Ensure the home icon renders in brand gold via inline style hook (keeps CSS untouched)
    const homePath = document.querySelector('.bottom-nav a.home svg path');
    if (homePath) {
      homePath.style.fill = 'var(--cg-primary)';
    }
  }

  applyNav();
});
