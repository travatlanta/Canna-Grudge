DEFAULT_TEMPLATES = [
    {
        "slug": "purchase_confirmation",
        "name": "Purchase Confirmation",
        "subject": "Your CannaGrudge Tickets Are Confirmed! 🥊",
        "description": "Sent to customers after a successful ticket purchase with order details and event information.",
        "html_body": """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Your CannaGrudge Tickets Are Confirmed!</title>
</head>
<body style="margin:0;padding:0;background-color:#0a0a0a;font-family:'Inter',Arial,Helvetica,sans-serif;color:#ffffff;-webkit-font-smoothing:antialiased;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color:#0a0a0a;">
<tr>
<td align="center" style="padding:20px 10px;">
<table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0" style="max-width:600px;width:100%;background-color:#111111;border:1px solid rgba(255,255,255,0.06);border-radius:12px;overflow:hidden;">
<tr>
<td align="center" style="padding:40px 40px 30px 40px;border-bottom:2px solid #d4a843;">
<table role="presentation" cellpadding="0" cellspacing="0" border="0">
<tr>
<td align="center">
<h1 style="margin:0;font-family:'Outfit',Arial,Helvetica,sans-serif;font-size:32px;font-weight:900;color:#d4a843;letter-spacing:-0.02em;">CannaGrudge</h1>
<p style="margin:8px 0 0 0;font-size:12px;font-weight:700;letter-spacing:0.12em;text-transform:uppercase;color:#a1a1aa;">Fight Night 2026</p>
</td>
</tr>
</table>
</td>
</tr>
<tr>
<td style="padding:40px;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
<tr>
<td>
<p style="margin:0 0 8px 0;font-size:14px;color:#a1a1aa;">Order Confirmed</p>
<h2 style="margin:0 0 24px 0;font-family:'Outfit',Arial,Helvetica,sans-serif;font-size:28px;font-weight:800;color:#ffffff;line-height:1.1;">Your Tickets Are Locked In! 🥊</h2>
<p style="margin:0 0 32px 0;font-size:16px;line-height:1.6;color:#a1a1aa;">Hey {{buyer_name}}, your order has been confirmed and your spot at the biggest fight night of the year is secured.</p>
</td>
</tr>
</table>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color:#1a1a1a;border:1px solid rgba(255,255,255,0.06);border-radius:8px;overflow:hidden;margin-bottom:24px;">
<tr>
<td style="padding:20px 20px 12px 20px;">
<p style="margin:0;font-family:'Outfit',Arial,Helvetica,sans-serif;font-size:14px;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;color:#d4a843;">Order Summary</p>
<p style="margin:4px 0 0 0;font-size:13px;color:#71717a;">Order #{{order_id}}</p>
</td>
</tr>
<tr>
<td style="padding:0 20px;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
<tr>
<td style="padding:8px 0;font-size:13px;font-weight:600;color:#71717a;border-bottom:1px solid rgba(255,255,255,0.06);">Item</td>
<td align="right" style="padding:8px 0;font-size:13px;font-weight:600;color:#71717a;border-bottom:1px solid rgba(255,255,255,0.06);">Amount</td>
</tr>
{{order_items}}
</table>
</td>
</tr>
<tr>
<td style="padding:16px 20px;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
<tr>
<td style="padding:4px 0;font-size:14px;color:#a1a1aa;">Subtotal</td>
<td align="right" style="padding:4px 0;font-size:14px;color:#ffffff;">{{subtotal}}</td>
</tr>
<tr>
<td style="padding:4px 0;font-size:14px;color:#a1a1aa;">Discount</td>
<td align="right" style="padding:4px 0;font-size:14px;color:#22c55e;">-{{discount}}</td>
</tr>
<tr>
<td style="padding:12px 0 4px 0;font-family:'Outfit',Arial,Helvetica,sans-serif;font-size:18px;font-weight:800;color:#ffffff;border-top:1px solid rgba(255,255,255,0.06);">Total</td>
<td align="right" style="padding:12px 0 4px 0;font-family:'Outfit',Arial,Helvetica,sans-serif;font-size:18px;font-weight:800;color:#d4a843;border-top:1px solid rgba(255,255,255,0.06);">{{total}}</td>
</tr>
</table>
</td>
</tr>
</table>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color:#1a1a1a;border:1px solid rgba(255,255,255,0.06);border-radius:8px;overflow:hidden;margin-bottom:24px;">
<tr>
<td style="padding:20px;">
<p style="margin:0 0 12px 0;font-family:'Outfit',Arial,Helvetica,sans-serif;font-size:14px;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;color:#d4a843;">Payment Info</p>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
<tr>
<td style="padding:4px 0;font-size:14px;color:#a1a1aa;">Payment ID</td>
<td align="right" style="padding:4px 0;font-size:14px;color:#ffffff;font-family:monospace;">{{payment_id}}</td>
</tr>
<tr>
<td style="padding:4px 0;font-size:14px;color:#a1a1aa;">Status</td>
<td align="right" style="padding:4px 0;font-size:14px;color:#22c55e;font-weight:600;">Paid</td>
</tr>
</table>
</td>
</tr>
</table>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
<tr>
<td align="center" style="padding:0 0 24px 0;">
<a href="{{receipt_url}}" style="display:inline-block;padding:14px 32px;background-color:#d4a843;color:#050505;font-family:'Outfit',Arial,Helvetica,sans-serif;font-size:14px;font-weight:700;text-decoration:none;border-radius:8px;">View Receipt</a>
</td>
</tr>
</table>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color:#1a1a1a;border:1px solid rgba(255,255,255,0.06);border-radius:8px;overflow:hidden;margin-bottom:24px;">
<tr>
<td style="padding:24px;">
<p style="margin:0 0 16px 0;font-family:'Outfit',Arial,Helvetica,sans-serif;font-size:14px;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;color:#d4a843;">Event Details</p>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
<tr>
<td style="padding:6px 0;font-size:14px;color:#a1a1aa;width:80px;">Date</td>
<td style="padding:6px 0;font-size:14px;color:#ffffff;font-weight:600;">April 25, 2026</td>
</tr>
<tr>
<td style="padding:6px 0;font-size:14px;color:#a1a1aa;width:80px;">Venue</td>
<td style="padding:6px 0;font-size:14px;color:#ffffff;font-weight:600;">Dunn's Arena</td>
</tr>
<tr>
<td style="padding:6px 0;font-size:14px;color:#a1a1aa;width:80px;">Location</td>
<td style="padding:6px 0;font-size:14px;color:#ffffff;font-weight:600;">Litchfield Park, AZ</td>
</tr>
</table>
</td>
</tr>
</table>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color:rgba(212,168,67,0.1);border:1px solid rgba(212,168,67,0.2);border-radius:8px;overflow:hidden;">
<tr>
<td style="padding:16px 20px;">
<p style="margin:0;font-size:14px;color:#d4a843;font-weight:600;">&#9888; Please bring a valid photo ID to the event for entry.</p>
</td>
</tr>
</table>
</td>
</tr>
<tr>
<td style="padding:30px 40px;border-top:1px solid rgba(255,255,255,0.06);text-align:center;">
<p style="margin:0 0 4px 0;font-family:'Outfit',Arial,Helvetica,sans-serif;font-size:14px;font-weight:700;color:#d4a843;">CannaGrudge</p>
<p style="margin:0 0 4px 0;font-size:12px;color:#71717a;">April 25, 2026 &bull; Dunn's Arena &bull; Litchfield Park, AZ</p>
<p style="margin:0;font-size:12px;color:#71717a;">&copy; 2026 CannaGrudge. All rights reserved.</p>
</td>
</tr>
</table>
</td>
</tr>
</table>
</body>
</html>"""
    },
    {
        "slug": "welcome_email",
        "name": "Welcome Email",
        "subject": "Welcome to CannaGrudge 🥊",
        "description": "Sent to new users when they create an account.",
        "html_body": """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Welcome to CannaGrudge</title>
</head>
<body style="margin:0;padding:0;background-color:#0a0a0a;font-family:'Inter',Arial,Helvetica,sans-serif;color:#ffffff;-webkit-font-smoothing:antialiased;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color:#0a0a0a;">
<tr>
<td align="center" style="padding:20px 10px;">
<table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0" style="max-width:600px;width:100%;background-color:#111111;border:1px solid rgba(255,255,255,0.06);border-radius:12px;overflow:hidden;">
<tr>
<td align="center" style="padding:40px 40px 30px 40px;border-bottom:2px solid #d4a843;">
<table role="presentation" cellpadding="0" cellspacing="0" border="0">
<tr>
<td align="center">
<h1 style="margin:0;font-family:'Outfit',Arial,Helvetica,sans-serif;font-size:32px;font-weight:900;color:#d4a843;letter-spacing:-0.02em;">CannaGrudge</h1>
<p style="margin:8px 0 0 0;font-size:12px;font-weight:700;letter-spacing:0.12em;text-transform:uppercase;color:#a1a1aa;">Fight Night 2026</p>
</td>
</tr>
</table>
</td>
</tr>
<tr>
<td style="padding:40px;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
<tr>
<td>
<h2 style="margin:0 0 24px 0;font-family:'Outfit',Arial,Helvetica,sans-serif;font-size:28px;font-weight:800;color:#ffffff;line-height:1.1;">Welcome to the Ring, {{user_name}}! 🥊</h2>
<p style="margin:0 0 24px 0;font-size:16px;line-height:1.6;color:#a1a1aa;">Your account has been created and you're now part of the CannaGrudge community. Get ready for the most electrifying fight night of 2026.</p>
<p style="margin:0 0 8px 0;font-size:13px;color:#71717a;">Your account email:</p>
<p style="margin:0 0 32px 0;font-size:15px;color:#ffffff;font-weight:600;">{{user_email}}</p>
</td>
</tr>
</table>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color:#1a1a1a;border:1px solid rgba(255,255,255,0.06);border-radius:8px;overflow:hidden;margin-bottom:24px;">
<tr>
<td style="padding:24px;">
<p style="margin:0 0 16px 0;font-family:'Outfit',Arial,Helvetica,sans-serif;font-size:14px;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;color:#d4a843;">What You Can Do</p>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
<tr>
<td style="padding:10px 0;border-bottom:1px solid rgba(255,255,255,0.06);">
<table role="presentation" cellpadding="0" cellspacing="0" border="0">
<tr>
<td style="padding-right:12px;font-size:20px;vertical-align:top;">&#127915;</td>
<td>
<p style="margin:0;font-size:15px;font-weight:600;color:#ffffff;">Buy Tickets</p>
<p style="margin:4px 0 0 0;font-size:13px;color:#a1a1aa;">Secure your spot at CannaGrudge with GA, VIP, and premium options.</p>
</td>
</tr>
</table>
</td>
</tr>
<tr>
<td style="padding:10px 0;">
<table role="presentation" cellpadding="0" cellspacing="0" border="0">
<tr>
<td style="padding-right:12px;font-size:20px;vertical-align:top;">&#128230;</td>
<td>
<p style="margin:0;font-size:15px;font-weight:600;color:#ffffff;">Track Your Orders</p>
<p style="margin:4px 0 0 0;font-size:13px;color:#a1a1aa;">View order history, receipts, and ticket status from your dashboard.</p>
</td>
</tr>
</table>
</td>
</tr>
</table>
</td>
</tr>
</table>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color:rgba(212,168,67,0.1);border:1px solid rgba(212,168,67,0.2);border-radius:8px;overflow:hidden;margin-bottom:24px;">
<tr>
<td style="padding:20px;">
<p style="margin:0 0 4px 0;font-family:'Outfit',Arial,Helvetica,sans-serif;font-size:14px;font-weight:700;color:#d4a843;">Save the Date</p>
<p style="margin:0;font-size:15px;color:#ffffff;font-weight:600;">April 25, 2026 &bull; Dunn's Arena &bull; Litchfield Park, AZ</p>
</td>
</tr>
</table>
</td>
</tr>
<tr>
<td style="padding:30px 40px;border-top:1px solid rgba(255,255,255,0.06);text-align:center;">
<p style="margin:0 0 4px 0;font-family:'Outfit',Arial,Helvetica,sans-serif;font-size:14px;font-weight:700;color:#d4a843;">CannaGrudge</p>
<p style="margin:0 0 4px 0;font-size:12px;color:#71717a;">April 25, 2026 &bull; Dunn's Arena &bull; Litchfield Park, AZ</p>
<p style="margin:0;font-size:12px;color:#71717a;">&copy; 2026 CannaGrudge. All rights reserved.</p>
</td>
</tr>
</table>
</td>
</tr>
</table>
</body>
</html>"""
    },
    {
        "slug": "order_status_update",
        "name": "Order Status Update",
        "subject": "CannaGrudge Order #{{order_id}} Update",
        "description": "Sent when an admin updates the status of a customer order.",
        "html_body": """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Order Status Update</title>
</head>
<body style="margin:0;padding:0;background-color:#0a0a0a;font-family:'Inter',Arial,Helvetica,sans-serif;color:#ffffff;-webkit-font-smoothing:antialiased;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color:#0a0a0a;">
<tr>
<td align="center" style="padding:20px 10px;">
<table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0" style="max-width:600px;width:100%;background-color:#111111;border:1px solid rgba(255,255,255,0.06);border-radius:12px;overflow:hidden;">
<tr>
<td align="center" style="padding:40px 40px 30px 40px;border-bottom:2px solid #d4a843;">
<table role="presentation" cellpadding="0" cellspacing="0" border="0">
<tr>
<td align="center">
<h1 style="margin:0;font-family:'Outfit',Arial,Helvetica,sans-serif;font-size:32px;font-weight:900;color:#d4a843;letter-spacing:-0.02em;">CannaGrudge</h1>
<p style="margin:8px 0 0 0;font-size:12px;font-weight:700;letter-spacing:0.12em;text-transform:uppercase;color:#a1a1aa;">Fight Night 2026</p>
</td>
</tr>
</table>
</td>
</tr>
<tr>
<td style="padding:40px;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
<tr>
<td>
<p style="margin:0 0 8px 0;font-size:14px;color:#a1a1aa;">Order Update</p>
<h2 style="margin:0 0 24px 0;font-family:'Outfit',Arial,Helvetica,sans-serif;font-size:28px;font-weight:800;color:#ffffff;line-height:1.1;">Order #{{order_id}} Status Changed</h2>
<p style="margin:0 0 32px 0;font-size:16px;line-height:1.6;color:#a1a1aa;">Hey {{buyer_name}}, there's an update on your CannaGrudge order.</p>
</td>
</tr>
</table>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color:#1a1a1a;border:1px solid rgba(255,255,255,0.06);border-radius:8px;overflow:hidden;margin-bottom:24px;">
<tr>
<td style="padding:24px;text-align:center;">
<p style="margin:0 0 8px 0;font-size:13px;font-weight:600;letter-spacing:0.08em;text-transform:uppercase;color:#71717a;">Current Status</p>
<p style="margin:0;font-family:'Outfit',Arial,Helvetica,sans-serif;font-size:24px;font-weight:800;color:#d4a843;">{{status}}</p>
</td>
</tr>
</table>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color:#1a1a1a;border:1px solid rgba(255,255,255,0.06);border-radius:8px;overflow:hidden;margin-bottom:24px;">
<tr>
<td style="padding:20px 20px 12px 20px;">
<p style="margin:0;font-family:'Outfit',Arial,Helvetica,sans-serif;font-size:14px;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;color:#d4a843;">Order Items</p>
</td>
</tr>
<tr>
<td style="padding:0 20px 20px 20px;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
<tr>
<td style="padding:8px 0;font-size:13px;font-weight:600;color:#71717a;border-bottom:1px solid rgba(255,255,255,0.06);">Item</td>
<td align="right" style="padding:8px 0;font-size:13px;font-weight:600;color:#71717a;border-bottom:1px solid rgba(255,255,255,0.06);">Amount</td>
</tr>
{{order_items}}
</table>
</td>
</tr>
</table>
<p style="margin:0;font-size:14px;line-height:1.6;color:#a1a1aa;">If you have any questions about this update, please reply to this email.</p>
</td>
</tr>
<tr>
<td style="padding:30px 40px;border-top:1px solid rgba(255,255,255,0.06);text-align:center;">
<p style="margin:0 0 4px 0;font-family:'Outfit',Arial,Helvetica,sans-serif;font-size:14px;font-weight:700;color:#d4a843;">CannaGrudge</p>
<p style="margin:0 0 4px 0;font-size:12px;color:#71717a;">April 25, 2026 &bull; Dunn's Arena &bull; Litchfield Park, AZ</p>
<p style="margin:0;font-size:12px;color:#71717a;">&copy; 2026 CannaGrudge. All rights reserved.</p>
</td>
</tr>
</table>
</td>
</tr>
</table>
</body>
</html>"""
    },
    {
        "slug": "invoice_notification",
        "name": "Invoice Notification",
        "subject": "Invoice from CannaGrudge",
        "description": "Sent when an invoice is created or sent to a recipient.",
        "html_body": """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Invoice from CannaGrudge</title>
</head>
<body style="margin:0;padding:0;background-color:#0a0a0a;font-family:'Inter',Arial,Helvetica,sans-serif;color:#ffffff;-webkit-font-smoothing:antialiased;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color:#0a0a0a;">
<tr>
<td align="center" style="padding:20px 10px;">
<table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0" style="max-width:600px;width:100%;background-color:#111111;border:1px solid rgba(255,255,255,0.06);border-radius:12px;overflow:hidden;">
<tr>
<td align="center" style="padding:40px 40px 30px 40px;border-bottom:2px solid #d4a843;">
<table role="presentation" cellpadding="0" cellspacing="0" border="0">
<tr>
<td align="center">
<h1 style="margin:0;font-family:'Outfit',Arial,Helvetica,sans-serif;font-size:32px;font-weight:900;color:#d4a843;letter-spacing:-0.02em;">CannaGrudge</h1>
<p style="margin:8px 0 0 0;font-size:12px;font-weight:700;letter-spacing:0.12em;text-transform:uppercase;color:#a1a1aa;">Fight Night 2026</p>
</td>
</tr>
</table>
</td>
</tr>
<tr>
<td style="padding:40px;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
<tr>
<td>
<p style="margin:0 0 8px 0;font-size:14px;color:#a1a1aa;">Invoice</p>
<h2 style="margin:0 0 24px 0;font-family:'Outfit',Arial,Helvetica,sans-serif;font-size:28px;font-weight:800;color:#ffffff;line-height:1.1;">You Have a New Invoice</h2>
<p style="margin:0 0 32px 0;font-size:16px;line-height:1.6;color:#a1a1aa;">Hey {{recipient_name}}, an invoice has been issued to you from CannaGrudge.</p>
</td>
</tr>
</table>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color:#1a1a1a;border:1px solid rgba(255,255,255,0.06);border-radius:8px;overflow:hidden;margin-bottom:24px;">
<tr>
<td style="padding:24px;">
<p style="margin:0 0 16px 0;font-family:'Outfit',Arial,Helvetica,sans-serif;font-size:14px;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;color:#d4a843;">Invoice Details</p>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
<tr>
<td style="padding:8px 0;font-size:14px;color:#a1a1aa;border-bottom:1px solid rgba(255,255,255,0.06);">Amount</td>
<td align="right" style="padding:8px 0;font-family:'Outfit',Arial,Helvetica,sans-serif;font-size:20px;font-weight:800;color:#d4a843;border-bottom:1px solid rgba(255,255,255,0.06);">{{amount}}</td>
</tr>
<tr>
<td style="padding:8px 0;font-size:14px;color:#a1a1aa;border-bottom:1px solid rgba(255,255,255,0.06);">Description</td>
<td align="right" style="padding:8px 0;font-size:14px;color:#ffffff;font-weight:600;border-bottom:1px solid rgba(255,255,255,0.06);">{{description}}</td>
</tr>
<tr>
<td style="padding:8px 0;font-size:14px;color:#a1a1aa;">Due Date</td>
<td align="right" style="padding:8px 0;font-size:14px;color:#ffffff;font-weight:600;">{{due_date}}</td>
</tr>
</table>
</td>
</tr>
</table>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
<tr>
<td align="center" style="padding:0 0 24px 0;">
<a href="{{invoice_url}}" style="display:inline-block;padding:14px 32px;background-color:#d4a843;color:#050505;font-family:'Outfit',Arial,Helvetica,sans-serif;font-size:14px;font-weight:700;text-decoration:none;border-radius:8px;">View Invoice</a>
</td>
</tr>
</table>
<p style="margin:0;font-size:14px;line-height:1.6;color:#a1a1aa;">If you have any questions about this invoice, please reply to this email.</p>
</td>
</tr>
<tr>
<td style="padding:30px 40px;border-top:1px solid rgba(255,255,255,0.06);text-align:center;">
<p style="margin:0 0 4px 0;font-family:'Outfit',Arial,Helvetica,sans-serif;font-size:14px;font-weight:700;color:#d4a843;">CannaGrudge</p>
<p style="margin:0 0 4px 0;font-size:12px;color:#71717a;">April 25, 2026 &bull; Dunn's Arena &bull; Litchfield Park, AZ</p>
<p style="margin:0;font-size:12px;color:#71717a;">&copy; 2026 CannaGrudge. All rights reserved.</p>
</td>
</tr>
</table>
</td>
</tr>
</table>
</body>
</html>"""
    }
]
