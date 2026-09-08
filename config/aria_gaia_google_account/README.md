# Aria & GAIA Dedicated Google Account Workspace

This directory stores the isolated Google Cloud & OAuth credentials for **Aria & GAIA's personal Google account** (`aviirrll@gmail.com`).

---

## Dual-Account Architecture

### 1. Master System Infrastructure (Personal Account)
* **Location**: `config/client_secret.json` & `config/google_credentials.json`
* **Role**: Primary system databases, core Google Cloud resources, and master services.
* **Access**: Protected.

### 2. Aria & GAIA Sandbox Account (`aviirrll@gmail.com`)
* **Location**: `config/aria_gaia_google_account/`
  * `client_secret.json` — OAuth client credentials from the new `Aria-Gaia` Google Cloud project.
  * `google_credentials.json` — OAuth refresh tokens for Aria's Gmail, Drive, Calendar, and YouTube.
  * `profile_info.json` — Account metadata and status.
* **Role**: Aria's personal playground (Aria's own Drive folders, sending her own emails, uploading to YouTube, personal calendar).
* **Billing**: $0.00 Free Quota (No billing attached).
