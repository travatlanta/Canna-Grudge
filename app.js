/* CannaGrudge app.js — clean version with no CTA movement */

(() => {
  const qs = s => document.querySelector(s);
  const qsa = s => Array.from(document.querySelectorAll(s));

  // Sticky CTA size var so page bottom spacing matches real height
  const cta = qs(".sticky-cta");
  if (cta) {
    const setH = () => {
      const h = cta.getBoundingClientRect().height || 68;
      document.documentElement.style.setProperty("--cta-h", h + "px");
      // Nuke any inline transforms from old scripts
      cta.style.transform = "none";
    };
    setH();
    window.addEventListener("resize", setH);
  }

  // Mobile nav active state
  const path = location.pathname.split("/").pop() || "index.html";
  qsa("[data-nav]").forEach(el => {
    if (el.dataset.nav === path) el.classList.add("is-active");
  });

  // Open mock login modal
  function openModal(id){ const modal = qs(id); if(modal){ modal.showModal(); } }
  function closeModals(){ qsa("dialog").forEach(d => d.close()); }
  qsa("[data-open-login]").forEach(btn => btn.addEventListener("click", () => openModal("#loginModal")));
  qsa("[data-close-modal]").forEach(btn => btn.addEventListener("click", closeModals));

  // Checkout flow (mock)
  qsa("[data-checkout]").forEach(btn => btn.addEventListener("click", () => location.href = "checkout.html"));
  if (path === "checkout.html") {
    const form = qs("#checkoutForm");
    if (form) {
      form.addEventListener("submit", e => {
        e.preventDefault();
        const d = new FormData(form);
        sessionStorage.setItem("cg_order", JSON.stringify({
          name: d.get("fullName") || "Guest",
          email: d.get("email") || "guest@example.com",
          event: "CannaGrudge",
          date: "Nov 22, 2025",
          venue: "Phoenix, AZ"
        }));
        location.href = "confirmation.html";
      });
    }
  }
  if (path === "confirmation.html") {
    const data = JSON.parse(sessionStorage.getItem("cg_order") || "{}");
    if (data.name) { qs("[data-name]").textContent = data.name; qs("[data-email]").textContent = data.email; }
  }

  // Ticket placeholder QR
  if (path === "dashboard.html") {
    const canvas = qs("#qr");
    if (canvas) {
      const payload = {
        ticket_id: "CG25-PHX-" + Math.random().toString(36).slice(2,7).toUpperCase(),
        event_id: "cannagrudge-2025",
        issued_at: Date.now()
      };
      qs("[data-ticket-id]").textContent = payload.ticket_id;
      const ctx = canvas.getContext("2d");
      canvas.width = 240; canvas.height = 240;
      ctx.fillStyle = "#000"; ctx.fillRect(0,0,240,240);
      ctx.fillStyle = "#fff"; ctx.font = "12px monospace";
      JSON.stringify(payload, null, 2).split("\n").forEach((line,i)=> ctx.fillText(line, 8, 20 + i*16));
    }
  }

  // Footer share buttons (big five) using native share when possible, fallback to FB/Twitter
  (() => {
    const links = document.querySelectorAll("[data-share]");
    if (!links.length) return;
    const url = location.origin ? location.href : "https://cannagrudge.example";
    const text = "CannaGrudge — live bouts, music, vendors. Join us!";
    function shareFallback(network){
      const u = encodeURIComponent(url);
      const t = encodeURIComponent(text);
      const map = {
        facebook: `https://www.facebook.com/sharer/sharer.php?u=${u}`,
        twitter: `https://twitter.com/intent/tweet?url=${u}&text=${t}`
      };
      window.open(map[network] || map.facebook, "_blank");
    }
    links.forEach(a => {
      a.addEventListener("click", e => {
        e.preventDefault();
        const n = a.getAttribute("data-share");
        if (navigator.share) {
          navigator.share({ title: "CannaGrudge", text, url }).catch(()=>shareFallback("facebook"));
        } else {
          shareFallback(n);
        }
      });
    });
  })();

})();

// Ensure footer clears CTA dock: set margin dynamically to dock height
(function footerClearance(){
  const dock = document.querySelector(".cta-dock");
  const footer = document.querySelector("footer.footer");
  if (!dock || !footer) return;
  function apply(){
    const h = dock.getBoundingClientRect().height || 92;
    footer.style.marginBottom = (h + 12) + "px";
    document.body.classList.add("with-dock");
  }
  apply();
  window.addEventListener("resize", apply);
})();


// Lower dock below footer when footer is visible (no movement, only z-index swap)
(function(){
  const dock = document.querySelector(".cta-dock");
  const footer = document.querySelector("footer.footer");
  if (!dock || !footer) return;
  const dockObserver = new IntersectionObserver((entries)=>{
    entries.forEach(entry => {
      if (entry.isIntersecting) dock.classList.add("behind");
      else dock.classList.remove("behind");
    });
  }, { root: null, threshold: 0.001 });
  dockObserver.observe(footer);
})();
