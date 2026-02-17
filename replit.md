# CannaGrudge

## Overview
CannaGrudge is a static website for a cannabis boxing/entertainment event on April 25, 2026 in Litchfield Park, AZ. It features event information, ticket purchasing, user authentication via Firebase, and an admin dashboard.

## Project Architecture
- **Type**: Static website (HTML, CSS, vanilla JavaScript)
- **Authentication**: Firebase Auth (Google, Facebook, Apple sign-in)
- **Hosting**: Originally GitHub Pages, now served via Python static file server on Replit
- **Port**: 5000 (frontend)
- **Theme**: Premium dark theme with gold accents, glassmorphism, and scroll animations

## Key Files
- `index.html` - Home page with countdown timer, hero section, feature cards
- `event.html` - Event details with interactive tile grid and popup system
- `login.html` - Firebase authentication page with premium auth buttons
- `dashboard.html` - User dashboard (protected) with profile, tickets, FAQ
- `checkout.html` / `confirmation.html` - Ticket purchase flow (checkout placeholder, confirmation with success UI)
- `settings.html` - User preferences, notifications, privacy settings
- `messages.html` - Message center with inbox/sent/trash tabs
- `profile.html` - User profile page
- `admin.html` / `analytics.html` / `scanner.html` - Admin tools
- `deck.html` - Presentation deck viewer
- `firebase-config.js` - Firebase project configuration
- `app.js` - Global navigation, auth guard, and scroll animation observer
- `theme.css` - Global premium dark theme with gold accents, glassmorphism, animations
- `server.py` - Python static file server for development

## Design System (theme.css)
- **Colors**: Deep dark palette (--cg-ink-925 through --cg-ink-600), gold primary (#f5b81a), scarlet accent (#ef4444)
- **Cards**: Glassmorphism with backdrop-filter blur, gold-tinted borders
- **Buttons**: Gold primary with glow hover, frosted ghost buttons
- **Animations**: fadeInUp, fadeIn, pulseGlow, shimmer, float keyframes
- **Scroll animations**: [data-animate] elements observed by IntersectionObserver in app.js
- **Utility classes**: .text-gradient, .glass, .glow-border, .section-title

## Recent Changes
- 2026-02-17: Full visual revamp - rewrote theme.css with premium fight-night aesthetic (deep darks, gold glow, glassmorphism, animations). Upgraded all HTML pages with new theme. Added live countdown timer to home page. Centralized scroll animation observer in app.js.
- 2026-02-17: Initial Replit setup. Added `server.py` for static file serving on port 5000 with no-cache headers. Configured deployment as static site.

## User Preferences
- User wants a "cool" premium fight-night visual aesthetic
- Dark theme with gold accents preferred
