# CannaGrudge

## Overview
CannaGrudge is a website for a cannabis boxing/entertainment event on April 25, 2026 in Litchfield Park, AZ. It features event information, ticket purchasing with Square payments, user authentication via Firebase, a user dashboard, and a comprehensive admin dashboard for managing tickets, orders, promo codes, sponsors, invoices, and purchase links.

## Project Architecture
- **Type**: Flask web app serving static HTML/CSS/JS with backend API
- **Backend**: Python Flask (server.py) with Square Payments API, Firebase Admin SDK, Resend Email, PostgreSQL
- **Database**: PostgreSQL (Neon-backed via Replit) with psycopg2
- **Authentication**: Firebase Auth (Google, Facebook, Apple sign-in) + Firebase Admin SDK server-side verification
- **Payments**: Square Web Payments SDK (frontend) + Square Payments API (backend), server-side price validation
- **Port**: 5000 (Flask serves both static files and API)
- **Theme**: Premium dark theme with charcoal/gold palette, modern typography, glassmorphism

## Database Schema
- `users` - Firebase UID, email, name, is_admin flag
- `ticket_tiers` - name, price_cents, description, features, capacity, sold, active, sale dates
- `orders` - email, name, total_cents, discount_cents, promo_code, status, square_payment_id, receipt_url
- `order_items` - order_id, ticket_tier_id, tier_name, qty, unit_price_cents
- `promo_codes` - code, discount_type (percent/fixed), discount_amount, max_uses, uses, active, dates
- `sponsor_requests` - company, contact_name, email, phone, message, status, deck_token, deck_token_expires
- `invoices` - recipient info, amount_cents, description, status, due_date, view_token, notes
- `admin_invites` - email, token, expires_at, used_at, created_by
- `purchase_links` - token, email, tier_id, qty, promo_code, expires_at, used_at
- `email_templates` - slug, name, subject, html_body, description, created_at, updated_at

## Key Files
- `server.py` - Flask server: 30+ API routes, Firebase Admin auth, admin middleware, Square payments, Resend emails, DB operations
- `email_templates.py` - Default HTML email template definitions (purchase confirmation, welcome, order status, invoice)
- `theme.css` - Complete design system: colors, typography, components, layouts, animations
- `app.js` - Dynamic navbar, mobile hamburger menu, cart system (localStorage), scroll animations
- `firebase-config.js` - Firebase project configuration and auth providers
- `index.html` - Home page: hero section, countdown timer, features, ticket preview, footer
- `event.html` - Event details: tile grid with popups, schedule, FAQ accordion, CTA
- `tickets.html` - Ticket selection: 3 tiers (GA $45, VIP $120, Ringside $250) with quantity controls
- `checkout.html` - Payment: Square card form, promo code input, order summary, server-side totals
- `confirmation.html` - Order confirmation with details from localStorage
- `login.html` - Firebase auth: Google, Facebook, Apple sign-in buttons
- `dashboard.html` - User dashboard: profile card, tickets, order history
- `admin.html` - Admin dashboard: sidebar nav, 8 tabs (Stats, Tickets, Orders, Promos, Sponsors, Invoices, Purchase Links, Admins)
- `sponsors.html` - Public sponsor request form with benefits info
- `invoice.html` - Public invoice viewer with token-based access
- `deck.html` - Token-gated sponsorship deck viewer with PDF download

## Design System (theme.css)
- **Colors**: Charcoal base (#0a0a0a), gold primary (#d4a843), green accent (#22c55e), red (#ef4444)
- **Typography**: Outfit (display/headings, weight 800-900) + Inter (body text)
- **Components**: Cards, buttons (primary/outline/ghost), inputs, badges, accordions
- **Layout**: Fixed top navbar (72px), container (1200px max), responsive grid
- **Navigation**: Dynamic navbar built by app.js, hamburger menu on mobile, cart drawer
- **Cart**: localStorage-based with drawer slide-out, badge counter
- **Animations**: [data-animate] elements with IntersectionObserver, CSS transitions
- **Utility classes**: .text-gradient, .text-gold, .glass, .section-label, .section-title

## API Routes
### Public
- `GET /api/square-config` - Square app/location IDs
- `GET /api/tickets` - Active ticket tiers
- `POST /api/promos/validate` - Validate promo code
- `POST /api/create-payment` - Process payment (server-side price validation, capacity check)
- `POST /api/sponsors/request` - Submit sponsor request
- `GET /api/sponsors/deck-access?token=` - Verify deck access token
- `GET /api/invoices/<token>` - View invoice by token
- `GET /api/purchase-links/<token>` - Get purchase link details

### Admin (requires Firebase token + is_admin)
- `POST /api/admin/verify` - Check admin status (auto-creates user, accepts invites)
- `GET /api/admin/stats` - Dashboard statistics
- `GET/POST /api/admin/tickets` - List/create ticket tiers
- `PUT/DELETE /api/admin/tickets/<id>` - Update/delete ticket tier
- `GET /api/admin/orders` - List orders with items
- `PUT /api/admin/orders/<id>` - Update order status
- `GET/POST /api/admin/promos` - List/create promo codes
- `PUT/DELETE /api/admin/promos/<id>` - Update/delete promo
- `GET /api/admin/sponsors` - List sponsor requests
- `POST /api/admin/sponsors/<id>/approve` - Approve + generate deck token
- `POST /api/admin/sponsors/<id>/deny` - Deny request
- `GET/POST /api/admin/invoices` - List/create invoices
- `PUT /api/admin/invoices/<id>` - Update invoice
- `POST /api/admin/invoices/<id>/send` - Mark invoice as sent
- `GET /api/admin/admins` - List admins and invites
- `POST /api/admin/admins/invite` - Invite new admin
- `POST /api/admin/admins/<id>/remove` - Remove admin
- `GET/POST /api/admin/purchase-links` - List/create purchase links

## Security
- All admin routes require Firebase ID token + is_admin database check
- Payment totals computed server-side from DB prices (no client price fallback)
- Capacity validation prevents overselling
- Promo code validation and application server-side
- Deck assets protected via Referer check (requires valid token in URL)
- SQL queries use parameterized statements (psycopg2)
- First user to sign in gets auto-admin; subsequent admins added via invite system

## Square Payment Flow
1. User selects tickets on tickets.html → adds to localStorage cart
2. Cart drawer shows items with quantity controls
3. Checkout page loads Square Web Payments SDK, renders card form
4. Optional: Apply promo code (validated via /api/promos/validate)
5. On submit: tokenize card → POST /api/create-payment (sends items + promoCode)
6. Server validates tiers from DB, computes total, applies promo, charges via Square
7. Order saved to DB with line items → confirmation page
8. Secrets: SQUARE_APPLICATION_ID, SQUARE_ACCESS_TOKEN, SQUARE_LOCATION_ID

## Sponsor Flow
1. Prospective sponsor visits sponsors.html, fills request form
2. Request saved to DB with status "pending"
3. Admin reviews in admin dashboard → Approve/Deny
4. On approve: generates time-limited token (7 days), deck URL created
5. Sponsor accesses deck.html?token=xxx → token verified → deck content shown
6. Deck assets (images/PDF) protected from direct access

## Invoice Flow
1. Admin creates invoice in dashboard (recipient, amount, description, due date)
2. System generates view_token for public access
3. Admin sends invoice (updates status to "sent")
4. Recipient views invoice at invoice.html?token=xxx
5. Admin can mark as paid

## Email System
- **Provider**: Resend API (RESEND_API_KEY secret)
- **Templates**: 4 customizable templates stored in DB (purchase_confirmation, welcome_email, order_status_update, invoice_notification)
- **Defaults**: Defined in email_templates.py, seeded on server start
- **Admin UI**: Email Templates tab in admin dashboard with preview, edit, test send, and reset to default
- **Triggers**: Purchase confirmation (after payment), welcome email (first sign-in), invoice notification (admin sends invoice)
- **Template variables**: {{name}}, {{email}}, {{order_id}}, {{total}}, {{items}}, {{invoice_url}}, etc.

## Recent Changes
- 2026-02-17: Event images - Incorporated fight card poster as hero background, event poster in new "Presented by" section on home page, and guidelines image with full rules/weight classes section on event page. All responsive.
- 2026-02-17: Invoice attachments - Added file upload support for sponsorship contracts on invoices. Admin can attach PDF/DOC/IMG files (max 10MB), download/remove attachments. Public invoice view shows download link.
- 2026-02-17: Email system - Added Resend integration with 4 premium dark/gold HTML email templates, admin template editor with preview/test/reset, automated sending on purchase and account creation
- 2026-02-17: Admin dashboard - Built comprehensive admin system with 25+ API routes, 8-tab admin dashboard, Firebase Admin SDK auth, server-side payment validation, promo codes, sponsor management, invoice system, purchase links, admin invite system
- 2026-02-17: Complete redesign - New theme.css with Outfit+Inter fonts, charcoal/gold palette. New app.js with dynamic top navbar, mobile hamburger, cart drawer. Rebuilt all pages. Added Flask backend with Square payment API.
- 2026-02-17: Initial Replit setup.

## User Preferences
- Premium fight-night visual aesthetic
- Dark theme with gold accents
- Clean, modern, high-end design
- Streamlined ticket purchasing flow
