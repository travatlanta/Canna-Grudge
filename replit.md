# CannaGrudge

## Overview
CannaGrudge is a website for a cannabis boxing/entertainment event on April 25, 2026 in Litchfield Park, AZ. It features event information, ticket purchasing with Square payments, user authentication via Firebase, and a user dashboard.

## Project Architecture
- **Type**: Flask web app serving static HTML/CSS/JS with backend API
- **Backend**: Python Flask (server.py) with Square Payments API endpoint
- **Authentication**: Firebase Auth (Google, Facebook, Apple sign-in)
- **Payments**: Square Web Payments SDK (frontend) + Square Payments API (backend)
- **Port**: 5000 (Flask serves both static files and API)
- **Theme**: Premium dark theme with charcoal/gold palette, modern typography, glassmorphism

## Key Files
- `server.py` - Flask server: static file serving + `/api/create-payment` + `/api/square-config`
- `theme.css` - Complete design system: colors, typography, components, layouts, animations
- `app.js` - Dynamic navbar, mobile hamburger menu, cart system (localStorage), scroll animations
- `firebase-config.js` - Firebase project configuration and auth providers
- `index.html` - Home page: hero section, countdown timer, features, ticket preview, footer
- `event.html` - Event details: tile grid with popups, schedule, FAQ accordion, CTA
- `tickets.html` - Ticket selection: 3 tiers (GA $45, VIP $120, Ringside $250) with quantity controls
- `checkout.html` - Payment: Square card form, order summary, payment processing
- `confirmation.html` - Order confirmation with details from localStorage
- `login.html` - Firebase auth: Google, Facebook, Apple sign-in buttons
- `dashboard.html` - User dashboard: profile card, tickets, order history
- `settings.html` - User preferences (legacy)
- `admin.html` / `analytics.html` / `scanner.html` - Admin tools (legacy)

## Design System (theme.css)
- **Colors**: Charcoal base (#0a0a0a), gold primary (#d4a843), green accent (#22c55e), red (#ef4444)
- **Typography**: Outfit (display/headings, weight 800-900) + Inter (body text)
- **Components**: Cards, buttons (primary/outline/ghost), inputs, badges, accordions
- **Layout**: Fixed top navbar (72px), container (1200px max), responsive grid
- **Navigation**: Dynamic navbar built by app.js, hamburger menu on mobile, cart drawer
- **Cart**: localStorage-based with drawer slide-out, badge counter
- **Animations**: [data-animate] elements with IntersectionObserver, CSS transitions
- **Utility classes**: .text-gradient, .text-gold, .glass, .section-label, .section-title

## Square Payment Flow
1. User selects tickets on tickets.html → adds to localStorage cart
2. Cart drawer shows items with quantity controls
3. Checkout page loads Square Web Payments SDK, renders card form
4. On submit: tokenize card → POST /api/create-payment → confirmation page
5. Secrets: SQUARE_APPLICATION_ID, SQUARE_ACCESS_TOKEN, SQUARE_LOCATION_ID

## Recent Changes
- 2026-02-17: Complete redesign - New theme.css with Outfit+Inter fonts, charcoal/gold palette. New app.js with dynamic top navbar, mobile hamburger, cart drawer. Rebuilt all pages: index, event, tickets, checkout, confirmation, login, dashboard. Added Flask backend with Square payment API. Cart system uses localStorage.
- 2026-02-17: Initial Replit setup.

## User Preferences
- Premium fight-night visual aesthetic
- Dark theme with gold accents
- Clean, modern, high-end design
- Streamlined ticket purchasing flow
