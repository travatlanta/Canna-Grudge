document.addEventListener('DOMContentLoaded', () => {
  const page = location.pathname.split('/').pop() || 'index';

  window.getCart = function() {
    try {
      return JSON.parse(localStorage.getItem('cg_cart') || '[]');
    } catch { return []; }
  };

  window.saveCart = function(cart) {
    localStorage.setItem('cg_cart', JSON.stringify(cart));
    updateCartBadge();
    if (typeof window.onCartChange === 'function') window.onCartChange();
  };

  window.addToCart = function(id, name, price, qty) {
    const cart = getCart();
    const existing = cart.find(i => i.id === id);
    if (existing) {
      existing.qty += qty;
    } else {
      cart.push({ id, name, price, qty });
    }
    saveCart(cart);
    if (typeof window.openCartDrawer === 'function') window.openCartDrawer();
  };

  window.updateCartItem = function(id, newQty) {
    let cart = getCart();
    if (newQty <= 0) {
      cart = cart.filter(i => i.id !== id);
    } else {
      const item = cart.find(i => i.id === id);
      if (item) item.qty = newQty;
    }
    saveCart(cart);
    renderCartDrawer();
  };

  window.clearCart = function() {
    localStorage.removeItem('cg_cart');
    updateCartBadge();
  };

  function updateCartBadge() {
    const badge = document.getElementById('cartBadge');
    if (!badge) return;
    const cart = getCart();
    const count = cart.reduce((s, i) => s + i.qty, 0);
    badge.textContent = count;
    badge.dataset.count = count;
    badge.style.display = count > 0 ? 'flex' : 'none';
  }

  function buildNav() {
    const loggedIn = localStorage.getItem('isLoggedIn') === '1' && !!(localStorage.getItem('fullName') || localStorage.getItem('email'));
    if (!loggedIn) {
      try { ['isLoggedIn','fullName','email','avatar','avatarUrl'].forEach(k => localStorage.removeItem(k)); } catch(e) {}
    }
    const cart = getCart();
    const cartCount = cart.reduce((s, i) => s + i.qty, 0);

    const nav = document.createElement('nav');
    nav.className = 'navbar';
    nav.id = 'mainNav';

    let ctaBtn;
    if (loggedIn) {
      const name = localStorage.getItem('fullName') || 'Account';
      const first = name.split(' ')[0];
      ctaBtn = `<a href="/dashboard" class="btn btn-primary btn-sm nav-tickets-cta">${first}</a>`;
    } else {
      ctaBtn = `<a href="/login" class="btn btn-primary btn-sm nav-tickets-cta">Sign In</a>`;
    }

    nav.innerHTML = `
      <div class="nav-inner">
        <a href="/" class="nav-brand">
          Canna<span>Grudge</span>
        </a>
        <div class="nav-links">
          <a href="/" class="${page === 'index' || page === '' ? 'active' : ''}">Home</a>
          <a href="/tickets" class="${page === 'tickets' ? 'active' : ''}">Tickets</a>
          <a href="/sponsors" class="${page === 'sponsors' ? 'active' : ''}">Sponsors</a>
        </div>
        <div class="nav-actions">
          <button class="nav-cart-btn" id="cartToggle" aria-label="Cart">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="9" cy="21" r="1"/><circle cx="20" cy="21" r="1"/><path d="M1 1h4l2.68 13.39a2 2 0 002 1.61h9.72a2 2 0 002-1.61L23 6H6"/></svg>
            <span class="nav-cart-badge" id="cartBadge" data-count="${cartCount}">${cartCount}</span>
          </button>
          ${ctaBtn}
          <button class="hamburger" id="hamburgerBtn" aria-label="Menu">
            <span></span><span></span><span></span>
          </button>
        </div>
      </div>
    `;
    document.body.prepend(nav);

    const mobileMenu = document.createElement('div');
    mobileMenu.className = 'mobile-menu';
    mobileMenu.id = 'mobileMenu';
    mobileMenu.innerHTML = `
      <a href="/">Home</a>
      <a href="/tickets">Tickets</a>
      <a href="/sponsors">Sponsors</a>
      ${loggedIn ? '<a href="/dashboard">My Account</a>' : '<a href="/login">Sign In</a>'}
      <a href="/tickets" style="color: var(--cg-gold); margin-top: 16px;">Get Tickets &rarr;</a>
    `;
    document.body.appendChild(mobileMenu);

    const hamburger = document.getElementById('hamburgerBtn');
    hamburger.addEventListener('click', () => {
      hamburger.classList.toggle('open');
      mobileMenu.classList.toggle('open');
      document.body.style.overflow = mobileMenu.classList.contains('open') ? 'hidden' : '';
    });

    mobileMenu.querySelectorAll('a').forEach(a => {
      a.addEventListener('click', () => {
        hamburger.classList.remove('open');
        mobileMenu.classList.remove('open');
        document.body.style.overflow = '';
      });
    });

    let ticking = false;
    window.addEventListener('scroll', () => {
      if (!ticking) {
        requestAnimationFrame(() => {
          nav.classList.toggle('scrolled', window.scrollY > 20);
          ticking = false;
        });
        ticking = true;
      }
    });
  }

  buildNav();

  function buildCartDrawer() {
    const overlay = document.createElement('div');
    overlay.className = 'cart-overlay';
    overlay.id = 'cartOverlay';
    document.body.appendChild(overlay);

    const drawer = document.createElement('div');
    drawer.className = 'cart-drawer';
    drawer.id = 'cartDrawer';
    drawer.innerHTML = `
      <div class="cart-header">
        <h3>Your Cart</h3>
        <button class="cart-close" id="cartClose">&times;</button>
      </div>
      <div class="cart-body" id="cartBody"></div>
      <div class="cart-footer" id="cartFooter"></div>
    `;
    document.body.appendChild(drawer);

    const toggle = document.getElementById('cartToggle');
    const close = document.getElementById('cartClose');

    function openCart() {
      drawer.classList.add('open');
      overlay.classList.add('open');
      document.body.style.overflow = 'hidden';
      renderCartDrawer();
    }

    function closeCart() {
      drawer.classList.remove('open');
      overlay.classList.remove('open');
      document.body.style.overflow = '';
    }

    toggle.addEventListener('click', openCart);
    close.addEventListener('click', closeCart);
    overlay.addEventListener('click', closeCart);

    window.openCartDrawer = openCart;
    window.closeCartDrawer = closeCart;
  }

  buildCartDrawer();

  function renderCartDrawer() {
    const body = document.getElementById('cartBody');
    const footer = document.getElementById('cartFooter');
    const cart = getCart();

    if (cart.length === 0) {
      body.innerHTML = '<div class="cart-empty"><p>Your cart is empty</p><p style="margin-top:8px;font-size:14px;">Browse tickets to get started</p></div>';
      footer.innerHTML = '';
      return;
    }

    let total = 0;
    body.innerHTML = cart.map(item => {
      const itemTotal = item.price * item.qty;
      total += itemTotal;
      return `
        <div class="cart-item">
          <div class="cart-item-info">
            <h4>${item.name}</h4>
            <div class="price">$${(item.price / 100).toFixed(2)} each</div>
          </div>
          <div class="cart-item-qty">
            <button onclick="updateCartItem('${item.id}', ${item.qty - 1})">-</button>
            <span>${item.qty}</span>
            <button onclick="updateCartItem('${item.id}', ${item.qty + 1})">+</button>
          </div>
        </div>
      `;
    }).join('');

    footer.innerHTML = `
      <div class="cart-total">
        <span class="total-label">Total</span>
        <span class="total-amount">$${(total / 100).toFixed(2)}</span>
      </div>
      <a href="/checkout" class="btn btn-primary btn-block">Checkout</a>
    `;
  }

  window.renderCartDrawer = renderCartDrawer;

  updateCartBadge();

  // Hero carousel auto-rotation
  const carousel = document.querySelector('.hero-carousel');
  if (carousel) {
    let currentSlide = 0;
    const slides = carousel.querySelectorAll('.carousel-slide');
    const dots = carousel.querySelectorAll('.carousel-dots .dot');
    const totalSlides = slides.length;

    function showSlide(index) {
      slides.forEach(s => s.classList.remove('active'));
      dots.forEach(d => d.classList.remove('active'));
      slides[index].classList.add('active');
      dots[index].classList.add('active');
      currentSlide = index;
    }

    // Auto-rotate every 6 seconds
    let carouselInterval = setInterval(() => {
      showSlide((currentSlide + 1) % totalSlides);
    }, 6000);

    // Manual dot navigation
    dots.forEach((dot, idx) => {
      dot.addEventListener('click', () => {
        clearInterval(carouselInterval);
        showSlide(idx);
        carouselInterval = setInterval(() => {
          showSlide((currentSlide + 1) % totalSlides);
        }, 6000);
      });
    });
  }

  // Scroll progress bar
  const progressBar = document.createElement('div');
  progressBar.className = 'scroll-progress';
  document.body.appendChild(progressBar);
  window.addEventListener('scroll', () => {
    const docHeight = document.documentElement.scrollHeight - window.innerHeight;
    const progress = docHeight > 0 ? (window.scrollY / docHeight) * 100 : 0;
    progressBar.style.width = progress + '%';
  });

  // Parallax effect for elements with data-parallax attribute
  let parallaxTicking = false;
  window.addEventListener('scroll', () => {
    if (!parallaxTicking) {
      requestAnimationFrame(() => {
        document.querySelectorAll('[data-parallax]').forEach(el => {
          const speed = parseFloat(el.dataset.parallax) || 0.1;
          const rect = el.getBoundingClientRect();
          const progress = (window.innerHeight - rect.top) / (window.innerHeight + rect.height);
          const offset = (progress - 0.5) * 40 * speed;
          el.style.transform = `translate3d(0, ${offset}px, 0)`;
        });
        parallaxTicking = false;
      });
      parallaxTicking = true;
    }
  });

  if ('IntersectionObserver' in window) {
    const obs = new IntersectionObserver((entries, o) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          o.unobserve(entry.target);
        }
      });
    }, { threshold: 0.1 });
    document.querySelectorAll('[data-animate]').forEach(el => obs.observe(el));
  } else {
    document.querySelectorAll('[data-animate]').forEach(el => el.classList.add('visible'));
  }

  // ─── Comprehensive Analytics Tracker ──────────────────────
  (function(){
    if (location.pathname.startsWith('/admin') || location.pathname.startsWith('/scanner')) return;

    // ── Floating Chat Bubble ──
    (function buildChatBubble() {
      if (location.pathname === '/messages') return; // already on messages page
      var bubble = document.createElement('div');
      bubble.id = 'cg-chat-bubble';
      bubble.innerHTML = '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="#050505" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/></svg>';
      bubble.style.cssText = 'position:fixed;bottom:24px;right:24px;z-index:9999;width:56px;height:56px;border-radius:50%;background:#d4a843;display:flex;align-items:center;justify-content:center;cursor:pointer;box-shadow:0 4px 20px rgba(212,168,67,.35);transition:transform .2s ease,box-shadow .2s ease;';
      bubble.onmouseenter = function(){ bubble.style.transform='scale(1.1)'; bubble.style.boxShadow='0 6px 28px rgba(212,168,67,.5)'; };
      bubble.onmouseleave = function(){ bubble.style.transform='scale(1)'; bubble.style.boxShadow='0 4px 20px rgba(212,168,67,.35)'; };

      var panel = document.createElement('div');
      panel.id = 'cg-chat-panel';
      panel.style.cssText = 'position:fixed;bottom:92px;right:24px;z-index:9998;width:360px;max-width:calc(100vw - 32px);max-height:480px;background:#111;border:1px solid rgba(255,255,255,.08);border-radius:16px;box-shadow:0 8px 32px rgba(0,0,0,.5);display:none;flex-direction:column;overflow:hidden;';
      panel.innerHTML = '<div style="padding:16px 18px;border-bottom:1px solid rgba(255,255,255,.08);display:flex;align-items:center;justify-content:space-between;">'
        + '<div><strong style="font-size:15px;color:#d4a843;">Contact Us</strong><p style="margin:2px 0 0;font-size:12px;color:#888;">We usually respond within a few hours</p></div>'
        + '<button id="cg-chat-close" style="background:none;border:none;color:#888;cursor:pointer;font-size:20px;padding:4px;">&times;</button></div>'
        + '<form id="cg-chat-form" style="padding:16px 18px;display:flex;flex-direction:column;gap:10px;">'
        + '<input id="cg-chat-name" placeholder="Your name" style="padding:10px 12px;background:#1a1a1a;color:#fff;border:1px solid rgba(255,255,255,.08);border-radius:8px;font-size:14px;font-family:inherit;outline:none;transition:border-color .2s;" onfocus="this.style.borderColor=\'#d4a843\'" onblur="this.style.borderColor=\'rgba(255,255,255,.08)\'">'
        + '<input id="cg-chat-email" type="email" placeholder="Your email (for reply)" style="padding:10px 12px;background:#1a1a1a;color:#fff;border:1px solid rgba(255,255,255,.08);border-radius:8px;font-size:14px;font-family:inherit;outline:none;transition:border-color .2s;" onfocus="this.style.borderColor=\'#d4a843\'" onblur="this.style.borderColor=\'rgba(255,255,255,.08)\'">'
        + '<textarea id="cg-chat-msg" rows="4" required placeholder="How can we help?" style="padding:10px 12px;background:#1a1a1a;color:#fff;border:1px solid rgba(255,255,255,.08);border-radius:8px;font-size:14px;font-family:inherit;resize:vertical;outline:none;transition:border-color .2s;" onfocus="this.style.borderColor=\'#d4a843\'" onblur="this.style.borderColor=\'rgba(255,255,255,.08)\'"></textarea>'
        + '<button type="submit" style="padding:12px;background:#d4a843;color:#050505;border:none;border-radius:8px;font-size:14px;font-weight:700;cursor:pointer;transition:opacity .2s;" onmouseenter="this.style.opacity=\'0.85\'" onmouseleave="this.style.opacity=\'1\'">Send Message</button>'
        + '</form>';
      document.body.appendChild(panel);
      document.body.appendChild(bubble);

      var open = false;
      bubble.addEventListener('click', function() {
        open = !open;
        panel.style.display = open ? 'flex' : 'none';
      });
      document.getElementById('cg-chat-close').addEventListener('click', function() {
        open = false;
        panel.style.display = 'none';
      });

      document.getElementById('cg-chat-form').addEventListener('submit', function(e) {
        e.preventDefault();
        var btn = this.querySelector('button[type="submit"]');
        btn.disabled = true; btn.textContent = 'Sending...';
        var base = window.CG_API_BASE || '';
        fetch(base + '/api/contact', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            name: document.getElementById('cg-chat-name').value.trim(),
            email: document.getElementById('cg-chat-email').value.trim(),
            message: document.getElementById('cg-chat-msg').value.trim()
          })
        }).then(function(r){ return r.json(); }).then(function(d) {
          if (d.error) throw new Error(d.error);
          panel.querySelector('form').innerHTML = '<div style="text-align:center;padding:32px 0;"><svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#22c55e" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg><p style="margin-top:12px;font-size:15px;font-weight:600;color:#fff;">Message Sent!</p><p style="color:#888;font-size:13px;">We\'ll get back to you soon.</p></div>';
        }).catch(function(err) {
          btn.disabled = false; btn.textContent = 'Send Message';
          alert('Failed to send: ' + err.message);
        });
      });
    })();

    var sid = sessionStorage.getItem('cg_sid');
    if (!sid) { sid = Math.random().toString(36).slice(2) + Date.now().toString(36); sessionStorage.setItem('cg_sid', sid); }
    var params = new URLSearchParams(location.search);
    var ua = navigator.userAgent;
    var mobile = /Mobi|Android/i.test(ua);
    var tablet = /Tablet|iPad/i.test(ua);
    var dt = tablet ? 'tablet' : mobile ? 'mobile' : 'desktop';
    var br = /Edg\//.test(ua) ? 'Edge' : /OPR\//.test(ua) ? 'Opera' : /Chrome\//.test(ua) ? 'Chrome' : /Safari\//.test(ua) ? 'Safari' : /Firefox\//.test(ua) ? 'Firefox' : 'Other';
    var os = /Windows/.test(ua) ? 'Windows' : /Mac OS/.test(ua) ? 'macOS' : /Android/.test(ua) ? 'Android' : /iPhone|iPad/.test(ua) ? 'iOS' : /Linux/.test(ua) ? 'Linux' : 'Other';
    var startTime = Date.now();
    var pagePath = location.pathname || '/';
    var apiBase = (window.CG_API_BASE || '') + '/api/track';

    // ── Capture Firebase user info when available ──
    var userName = '';
    var userEmail = '';
    try {
      var cgAuth = window.__cgAuth;
      if (cgAuth && cgAuth.onAuthStateChanged && cgAuth.auth) {
        cgAuth.onAuthStateChanged(cgAuth.auth, function(u) {
          if (u) {
            userName = (u.displayName || '').slice(0, 100);
            userEmail = (u.email || '').slice(0, 200);
            // Sync user to backend DB
            try {
              u.getIdToken().then(function(token) {
                fetch((window.CG_API_BASE || '') + '/api/auth/sync', {
                  method: 'POST',
                  headers: { 'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json' },
                  body: '{}'
                }).catch(function(){});
              }).catch(function(){});
            } catch(e) {}
          } else {
            userName = '';
            userEmail = '';
          }
        });
      }
    } catch(e) {}

    function beacon(data) {
      if (userName) data.un = userName;
      if (userEmail) data.ue = userEmail;
      var blob = new Blob([JSON.stringify(data)], { type: 'application/json' });
      if (navigator.sendBeacon) {
        navigator.sendBeacon(apiBase, blob);
      } else {
        fetch(apiBase, { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(data), keepalive: true });
      }
    }

    // Send initial pageview after short delay (filters bots)
    setTimeout(function(){
      beacon({ sid: sid, page: pagePath, ref: document.referrer || '',
        us: params.get('utm_source') || '', um: params.get('utm_medium') || '', uc: params.get('utm_campaign') || '',
        dt: dt, br: br, os: os, sw: screen.width, dur: 0 });
    }, 800);

    // Update duration on page leave (no new row — update existing)
    document.addEventListener('visibilitychange', function() {
      if (document.visibilityState === 'hidden') {
        beacon({ sid: sid, page: pagePath, dur: Date.now() - startTime, update: true, dt: dt, br: br, os: os });
      }
    });

    // ── Event tracking helper (exposed globally) ──
    window.cgTrack = function(event, category, detail, meta) {
      beacon({ sid: sid, page: pagePath, event: event, cat: category || 'interaction',
               detail: detail || '', meta: meta || {}, dt: dt, br: br, os: os });
    };

    // ── Track outbound link clicks ──
    document.addEventListener('click', function(e) {
      var a = e.target.closest('a[href]');
      if (!a) return;
      var href = a.getAttribute('href') || '';
      if (href.startsWith('http') && !href.includes(location.hostname)) {
        window.cgTrack('outbound_click', 'navigation', href, { text: (a.textContent || '').trim().slice(0, 100) });
      }
    });

    // ── Track add-to-cart clicks ──
    document.addEventListener('click', function(e) {
      var btn = e.target.closest('[data-add-cart], .add-to-cart, .btn-add-cart');
      if (btn) {
        var label = (btn.dataset.tierName || btn.textContent || '').trim().slice(0, 100);
        window.cgTrack('add_to_cart', 'purchase', label);
      }
    });

    // ── Track JS errors ──
    window.addEventListener('error', function(e) {
      window.cgTrack('js_error', 'error', (e.message || 'Unknown error') + ' at ' + (e.filename || '') + ':' + (e.lineno || 0),
        { message: (e.message || '').slice(0, 500), file: (e.filename || '').slice(0, 200), line: e.lineno, col: e.colno });
    });

    // ── Track unhandled promise rejections ──
    window.addEventListener('unhandledrejection', function(e) {
      var msg = e.reason ? (e.reason.message || String(e.reason)) : 'Unhandled rejection';
      window.cgTrack('promise_error', 'error', msg.slice(0, 500));
    });

    // ── Track scroll depth ──
    var maxScroll = 0;
    var scrollReported = {};
    window.addEventListener('scroll', function() {
      var h = document.documentElement.scrollHeight - window.innerHeight;
      if (h <= 0) return;
      var pct = Math.round(window.scrollY / h * 100);
      if (pct > maxScroll) maxScroll = pct;
      [25, 50, 75, 100].forEach(function(t) {
        if (maxScroll >= t && !scrollReported[t]) {
          scrollReported[t] = true;
          window.cgTrack('scroll_depth', 'engagement', t + '% scroll on ' + pagePath, { depth: t });
        }
      });
    }, { passive: true });

  })();
});
