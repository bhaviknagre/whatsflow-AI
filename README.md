# WhatsFlow AI

**A CRM for businesses that talk to customers on WhatsApp.**

## What is this, really?

Say your business gets customer messages on WhatsApp — someone asking about
pricing, someone placing an order, someone just saying hi. Right now, those
messages probably live inside the WhatsApp app on one person's phone,
scattered across chats, with no record of who these customers are or what
was said last time.

WhatsFlow AI turns that into an actual system:

- Every customer who messages you is **automatically saved as a contact** —
  no manual data entry.
- Every conversation shows up in one shared **Inbox**, so replying isn't
  tied to a single phone.
- You can send the same WhatsApp message to hundreds of contacts at once
  with a **Campaign** — think "we're open this weekend, 20% off" sent to
  your whole customer list, not typed out one by one.

## How it works, step by step

1. **A customer messages your WhatsApp number.**
   WhatsFlow AI is notified instantly — WhatsApp reports it directly, in
   real time, so nothing needs refreshing.

2. **That customer becomes a saved Contact automatically.**
   Their phone number and name (if WhatsApp shares it) get stored the
   moment they first message you.

3. **The conversation appears in your Inbox.**
   You reply from there, and the customer just sees a normal WhatsApp
   message on their end — they never know it went through WhatsFlow AI.

4. **To reach many people at once, you create a Campaign.**
   Pick a pre-approved WhatsApp message template, choose which contacts
   should get it, and send. WhatsFlow AI delivers it to everyone and
   tracks who received it, who read it, and who it failed for.

## The pieces, in plain English

| What you see | What it actually does |
| --- | --- |
| **Inbox** | The shared chat window for every WhatsApp conversation your business has. |
| **Contacts** | Your customer list — built automatically as people message you, or added by hand. |
| **Campaigns** | Bulk WhatsApp messages sent to a chosen list of contacts, using a template Meta has approved in advance. |
| **Settings → WhatsApp** | Where you connect your business's WhatsApp number so WhatsFlow AI can send and receive on your behalf. |

## Who's actually sending the messages?

WhatsFlow AI talks to WhatsApp through **Meta's official WhatsApp Business
Platform** — the same system large companies use for customer messaging.
It's not a workaround or an unofficial trick; every message goes through
Meta's real, approved channel, which is why templates need Meta's approval
before a Campaign can use them.

## What it's built with, for anyone technical

Next.js on the frontend, FastAPI (Python) on the backend, PostgreSQL for
data, Redis for real-time updates, and Docker to run the whole thing
consistently anywhere. None of that is required knowledge to use the
product — it's here for whoever's curious.
