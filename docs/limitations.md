# 📑 Aria & AI Model Capabilities & System Integration (`limitations.md`)

This document outlines **how Aria interacts with Windows, its newly unlocked OS-level capabilities**, and current hardware/security boundaries.

---

## 🚀 How Aria Now Controls Your PC (Unlocked Capabilities)

| # | Feature / Capability | Method & Technology | Status |
|---|---|---|:---:|
| 1 | **Dynamic PowerShell & System Control** | Executes safe PowerShell scripts on the fly for any Windows setting, hardware query, disk cleanup, or registry adjustment. | ✅ **Active** |
| 2 | **Gemini 2.5 Flash Screen Vision** | Takes live screenshots and uses Gemini's spatial vision to read, summarize, and answer questions about what is on your screen. | ✅ **Active** |
| 3 | **Visual UI Grounding & Clicking** | Gemini 2.5 Flash calculates `(x, y)` pixel coordinates of any visible button/menu and moves/clicks your mouse cursor. | ✅ **Active** |
| 4 | **Universal Application Launcher** | Automatically indexes and opens any installed Windows software or game via Start Menu, Desktop, and AppData shortcuts (`0ms`). | ✅ **Active** |
| 5 | **Intelligent Document & PDF Search** | Recursively scans `Desktop`, `Downloads`, `Documents`, and `OneDrive` to find and open files by fuzzy keyword matching. | ✅ **Active** |
| 6 | **In-App WhatsApp Messaging** | Hands-free messaging: opens WhatsApp, focuses contact search via `Ctrl+F`, types and sends the message. | ✅ **Active** |
| 7 | **Continuous Self-Learning Engine** | Dynamically learns rules, corrects mistakes, and saves custom voice shortcuts into `learned_corrections.json`. | ✅ **Active** |
| 8 | **Desktop Wallpaper Changer** | Native Windows `SystemParametersInfoW` API hook to cycle through desktop backgrounds. | ✅ **Active** |

---

## 🔒 Remaining Hard Limits & Security Boundaries

| # | Boundary | Explanation | Can It Be Bypassed? |
|---|---|---|:---:|
| 1 | **Captchas & 2FA Login Screens** | Websites with Cloudflare / Google Captchas or mobile OTP authenticators require manual human completion. | ❌ Hard security barrier |
| 2 | **Full-Duplex Speaker Echo (Barge-in)** | When Aria speaks through speakers, microphone picks up her own audio loop unless headphones or specialized echo-cancellation hardware is used. | ⚠️ Hardware / Headphone dependent |
| 3 | **Silently Reading Encrypted Local WhatsApp Messages** | WhatsApp desktop chats are end-to-end encrypted; Aria can only read incoming messages if WhatsApp Web is open via Chrome automation. | ⚠️ Privacy/Encryption constraint |

---

## 💡 Example Commands You Can Try Now:

- 👁️ **Screen Vision:** *"What is currently on my screen?"* / *"Look at my screen and read this error."*
- 🖱️ **Visual Clicking:** *"Click the blue download button on screen."*
- ⚡ **Dynamic System Commands:** *"powershell: Get-Process | Sort-Object CPU -Descending | Select-Object -First 5"*
- 📁 **File Search:** *"Open a pdf named hands on machine learning"*
- 💬 **WhatsApp Automation:** *"In WhatsApp type hi to Alex"*
- 🎨 **Desktop Wallpaper:** *"Change desktop background"*
- 🧠 **Self-Learning:** *"Whenever I say 'focus mode', open VS Code and Spotify"*
