# Chapter 1 Session Reference — Incident Management

Generated: 2026-07-08 for Den Sanchez (IT/SRE professional, 24yr Japan resident)

## Content Structure Used

### Section 1: Professional Keigo Specs (IT-focused)
- 3-Step Incident Report Structure table (Impact / Action / ETA) with Kenjougo forms
- Key Keigo Verbs table: 報告する, 調査する, 対応する, 確認する in Kenjougo + Sonkeigo
- Short-to-fluid transition: bridge phrase `詳細をご報告いたします` + full database failover narrative

### Section 2: Real-World SRE Dialogue
- 8 lines covering: database failover status, disk I/O latency, auto-failover, service impact, root cause assessment (firmware bug), follow-up tracking
- Format: `<div class="dialogue-line">` with `.speaker`, `.jp`, `.romaji-line`, `.en` children

### Section 3: Tech Email Reading
- Full maintenance notice email from Satō-san at Infra Management Team
- Core router firmware update, 1AM-5AM window, VPN + monitoring impact
- Format: `<div class="email-box">` with `.subject`, `.jp`, `.romaji-line`, `.en` children

## Toggle Implementation Details

**Status dots:** 3 live indicator dots in the header showing which tracks are active:
```html
<div class="status-bar">
  <span><span class="status-dot on" id="dot-jp"></span> Japanese</span>
  <span><span class="status-dot on" id="dot-romaji"></span> Romaji</span>
  <span><span class="status-dot on" id="dot-en"></span> English</span>
</div>
```

**jp-only mode interaction:** When Japanese Only is toggled ON, romaji and english buttons lose `.active` visually and their dots switch to grey. The *state* of romaji/english is preserved underneath — when jp-only is toggled OFF, the previous visibility states restore.

## GitHub Deployment
- Repo: `https://github.com/decniner/sensei-pogi-textbook`
- HTMLPreview URL: `https://htmlpreview.github.io/?https://github.com/decniner/sensei-pogi-textbook/blob/main/chapter1_incident_management.html`
- Git auth: Windows Credential Manager (manager-core) — set remote URL without embedding token
