document.addEventListener('DOMContentLoaded', () => {
  const page = (location.pathname.split('/').pop() || 'index.html').replace('.html', '');

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
      ctaBtn = `<a href="dashboard.html" class="btn btn-primary btn-sm nav-tickets-cta">${first}</a>`;
    } else {
      ctaBtn = `<a href="login.html" class="btn btn-primary btn-sm nav-tickets-cta">Sign In</a>`;
    }

    nav.innerHTML = `
      <div class="nav-inner">
        <a href="index.html" class="nav-brand">
          Canna<span>Grudge</span>
        </a>
        <div class="nav-links">
          <a href="index.html" class="${page === 'index' || page === '' ? 'active' : ''}">Home</a>
          <a href="event.html" class="${page === 'event' ? 'active' : ''}">Event</a>
          <a href="tickets.html" class="${page === 'tickets' ? 'active' : ''}">Tickets</a>
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
      <a href="index.html">Home</a>
      <a href="event.html">Event</a>
      <a href="tickets.html">Tickets</a>
      ${loggedIn ? '<a href="dashboard.html">My Account</a>' : '<a href="login.html">Sign In</a>'}
      <a href="tickets.html" style="color: var(--cg-gold); margin-top: 16px;">Tickets &rarr;</a>
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
      <a href="checkout.html" class="btn btn-primary btn-block">Checkout</a>
    `;
  }

  window.renderCartDrawer = renderCartDrawer;

  updateCartBadge();

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
});
