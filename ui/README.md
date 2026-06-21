# Rebar — Autonomous Data Migration UI

A complete React + Vite landing page and interactive product demo built for Firebase Hosting.

## What is included

- Modern company-style landing page
- Animated autonomous migration demo
- Before / Understand / Transform / Verify / After workflow
- Five-model benchmark leaderboard with metric tabs
- Base-model vs RL-model comparison
- Held-out training curve
- Claude Opus anomaly / diagnosis section
- Business use cases and technical-details panel
- Fully responsive desktop, tablet, and mobile layouts
- Firebase Hosting configuration

> All benchmark values and training counts are demo placeholders. Replace them with your measured results before presenting.

## Edit the benchmark data

Open `src/main.jsx` and update:

- `MODEL_DATA`
- `TRAINING_POINTS`
- the training summary cards
- the Opus vs Sonnet failure breakdown

The user-facing model labels currently follow the requested naming:

- Claude Opus 4.8
- Claude Sonnet 4.6
- GPT-5.4
- Kimi K2.7 32B Base
- Kimi K2.7 32B + RL

## Run locally

```bash
npm install
npm run dev
```

Vite will print a local URL, usually `http://localhost:5173`.

## Build for production

```bash
npm run build
```

The production site is generated in `dist/`.

## Deploy to Firebase Hosting

1. Create a Firebase project in the Firebase Console.
2. Install the Firebase CLI:

```bash
npm install -g firebase-tools
```

3. Sign in:

```bash
firebase login
```

4. Replace `YOUR_FIREBASE_PROJECT_ID` in `.firebaserc` with your Firebase project ID.
5. Build and deploy:

```bash
npm install
npm run build
firebase deploy --only hosting
```

Firebase will return your live `web.app` and `firebaseapp.com` URLs.

## Optional: initialize Firebase yourself

The repository already contains `firebase.json`, so initialization is not required. To regenerate the config:

```bash
firebase init hosting
```

Use these answers:

- Public directory: `dist`
- Configure as a single-page app: `Yes`
- Set up automatic GitHub builds: your choice
- Overwrite `index.html`: `No`

## Connect real benchmark results later

The current UI reads local JavaScript objects. Replace those objects with a fetch call to your backend, Firestore, or a static JSON file. The migration animation can also be driven by WebSocket or Server-Sent Events using event types such as:

- `migration_started`
- `schema_discovered`
- `mapping_progress`
- `transformation_example`
- `issue_repaired`
- `validation_started`
- `migration_completed`
