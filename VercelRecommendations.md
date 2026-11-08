# Vercel Recommendations

## Build Multiple Deployments Simultaneously (Never wait for a queued build)
Enables on‑demand concurrent builds so that multiple deployments can run in parallel without being queued. This reduces waiting time when several branches or PRs are pushed.

**How to enable:**
1. Go to **Settings → Build & Deployment** in the Vercel dashboard.
2. Find the **On‑demand concurrent builds** toggle (the "Never wait for a queued build" recommendation).
3. Switch it **ON** and save.
   - CLI alternative:
     ```bash
     vercel settings set onDemandConcurrency=true
     ```

## Prevent Frontend‑Backend Mismatches (Automatically sync client and server versions)
Activates *Skew Protection*: Vercel will refuse to deploy a frontend that was built against a different backend commit than the one currently deployed, preventing runtime version‑mismatch errors.

**How to enable:**
1. In the Vercel dashboard, open **Settings → Advanced**.
2. Locate **Skew Protection** (the "Prevent Frontend‑Backend Mismatches" card).
3. Turn the switch **ON** and save.
   - CLI alternative:
     ```bash
     vercel settings set skewProtection=true
     ```

---
These settings improve deployment speed and reliability for the **Series Tracker** project.

