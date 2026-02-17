# CannaGrudge

## Overview
CannaGrudge is a static website for a cannabis boxing/entertainment event in Litchfield Park, AZ. It features event information, ticket purchasing, user authentication via Firebase, and an admin dashboard.

## Project Architecture
- **Type**: Static website (HTML, CSS, vanilla JavaScript)
- **Authentication**: Firebase Auth (Google, Facebook, Apple sign-in)
- **Hosting**: Originally GitHub Pages, now served via Python static file server on Replit
- **Port**: 5000 (frontend)

## Key Files
- `index.html` - Home page
- `event.html` - Event details
- `login.html` - Firebase authentication page
- `dashboard.html` - User dashboard (protected)
- `checkout.html` / `confirmation.html` - Ticket purchase flow
- `admin.html` / `analytics.html` / `scanner.html` - Admin tools
- `firebase-config.js` - Firebase project configuration
- `app.js` - Global navigation and auth guard logic
- `theme.css` - Global styles
- `server.py` - Python static file server for development

## Recent Changes
- 2026-02-17: Initial Replit setup. Added `server.py` for static file serving on port 5000 with no-cache headers. Configured deployment as static site.

## User Preferences
- (none recorded yet)
