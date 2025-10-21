/* CannaGrudge minimal app scaffolding (client-side only)
   - Handles mobile nav, sticky CTA behavior, mock auth modals, and ticket preview routing.
   - Replace stubs with real auth/payment later.
*/
(() => {
  const qs = s => document.querySelector(s);
  const qsa = s => Array.from(document.querySelectorAll(s));

  // Sticky CTA visibility on scroll stop
  let scrollTimer;
  const sticky = qs(".sticky-cta");
  if (sticky) {
    document.addEventListener("scroll", () => {
      sticky.style.opacity = "0.92";
      clearTimeout(scrollTimer);
      scrollTimer = setTimeout(() => sticky.style.opacity = "1", 160);
    }, { passive: true });
  }

  // Mobile nav active state
  const path = location.pathname.split("/").pop() || "index.html";
  qsa("[data-nav]").forEach(el => {
    if (el.dataset.nav === path) el.classList.add("is-active");
  });

  // Mock login flow (replace with real auth)
  function openModal(id){ const modal = qs(id); if(modal){ modal.showModal(); } }
  function closeModals(){ qsa("dialog").forEach(d => d.close()); }

  qsa("[data-open-login]").forEach(btn => {
    btn.addEventListener("click", () => openModal("#loginModal"));
  });
  qsa("[data-close-modal]").forEach(btn => btn.addEventListener("click", closeModals));

  // Mock checkout -> confirmation flow
  qsa("[data-checkout]").forEach(btn => {
    btn.addEventListener("click", () => {
      // In real app, redirect to Stripe then back to /confirmation.html
      location.href = "checkout.html";
    });
  });

  if (path === "checkout.html") {
    const form = qs("#checkoutForm");
    if (form) {
      form.addEventListener("submit", e => {
        e.preventDefault();
        // Simulate success
        const purchaser = new FormData(form).get("fullName") || "Guest";
        const email = new FormData(form).get("email") || "guest@example.com";
        sessionStorage.setItem("cg_order", JSON.stringify({
          name: purchaser, email, event:"CannaGrudge", date:"Nov 22, 2025", venue:"Phoenix, AZ"
        }));
        location.href = "confirmation.html";
      });
    }
  }

  if (path === "confirmation.html") {
    const data = JSON.parse(sessionStorage.getItem("cg_order") || "{}");
    if (data.name) {
      qs("[data-name]").textContent = data.name;
      qs("[data-email]").textContent = data.email;
    }
  }

  // Generate a mock QR payload for the ticket preview
  if (path === "dashboard.html") {
    const canvas = qs("#qr");
    if (canvas) {
      const payload = {
        ticket_id: "CG25-PHX-" + Math.random().toString(36).slice(2,7).toUpperCase(),
        event_id: "cannagrudge-2025",
        issued_at: Date.now()
      };
      qs("[data-ticket-id]").textContent = payload.ticket_id;
      // Simple placeholder QR: render payload text; replace with real QR lib later
      const ctx = canvas.getContext("2d");
      canvas.width = 240; canvas.height = 240;
      ctx.fillStyle = "#000"; ctx.fillRect(0,0,240,240);
      ctx.fillStyle = "#fff";
      ctx.font = "12px monospace";
      const lines = JSON.stringify(payload, null, 2).split("\n");
      lines.forEach((line,i)=> ctx.fillText(line, 8, 20 + i*16));
    }
  }

})();