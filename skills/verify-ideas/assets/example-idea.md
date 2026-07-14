---
id: completed-work-is-durable
blocking: true
---

# Customers never lose completed work

When a customer finishes editing and sees “Saved,” their work must survive refreshing the page, signing out and back in, deploying a new version, and temporary network failure.

This matters because “Saved” is a promise, not an indication that saving has started.

The idea is false if the customer sees “Saved” but later receives an older version or no version of their work.
