   # CartIQ Frontend - Detailed Architecture & Context

   This document provides a comprehensive breakdown of the CartIQ React Dashboard. It is designed to give an AI (like Claude) full context on the frontend application state so that backend APIs and future UI iterations can be built seamlessly.

   ## 1. Project Specifications
   - **Framework:** React 18 (Vite template `react-ts`)
   - **Language:** TypeScript
   - **Styling:** Tailwind CSS v3 (Customized via `tailwind.config.js` with deep design tokens)
   - **Animations:** Framer Motion (`"framer-motion": "^11.x"`)
   - **Charting:** Recharts (`"recharts": "^2.x"`)
   - **Icons:** Google Material Symbols Outlined (imported via CDN) & Google Fonts (Plus Jakarta Sans, Inter).

   ---

   ## 2. Directory Structure
   ```text
   /dashboard
   ├── /src
   │   ├── /components
   │   │   ├── ChartsArea.tsx     # Recharts (Area, Bar, Pie)
   │   │   ├── KPICards.tsx       # 4 Top-level animated metrics
   │   │   ├── LiveFeed.tsx       # Real-time event ticker
   │   │   ├── Sidebar.tsx        # Left navigation pane
   │   │   └── TopBar.tsx         # Header with branding and 'Live' status
   │   ├── App.tsx                # Main layout coordinator & Data Fetching loop
   │   ├── index.css              # Tailwind base & custom .glass-card utilities
   │   ├── main.tsx               # React DOM rendering
   │   └── vite-env.d.ts
   ├── index.html                 # HTML shell with Google Fonts & "dark" class
   ├── package.json
   ├── tailwind.config.js         # Precision Insight color tokens and typography
   ├── postcss.config.js
   └── tsconfig.json
   ```

   ---

   ## 3. The Design System ("Precision Insight")
   The dashboard enforces a highly specific **Dark Mode Glassmorphism** aesthetic. 
   - **Background:** `#060e20` (Deep Navy/Charcoal).
   - **Surfaces:** Components use `.glass-card`, which combines `bg-slate-800/50`, `backdrop-blur-[12px]`, and `border-white/10`.
   - **Accents:** 
   - Primary (`#8ed5ff` / `#38bdf8`) for active states and primary charts.
   - Emerald (`#10b981`) for positive growth and "Success/Purchase" events.
   - Error (`#ffb4ab` / `#93000a`) for failed payments/errors.
   - **Typography:**
   - Headlines/Metrics: `font-headline-md`, `font-headline-lg` utilizing **Plus Jakarta Sans**.
   - Body/Labels: `font-body-md`, `font-label-md` utilizing **Inter**.

   ---

   ## 4. Component Deep-Dive

   ### `App.tsx` (State & Data Polling)
   This is the heart of the frontend. It manages layout using a 12-column grid and holds the state for the `LiveFeed`.
   - **Current Data Strategy:** Uses `useEffect` with `setInterval` to run `fetchDashboardData()` every 5 seconds.
   - **Backend Target:** It is designed to poll `http://localhost:8002/api/v1/analytics/dashboard` (currently commented out while using mock data).
   - **Layout:**
   ```tsx
   <div className="flex w-full h-full">
      <Sidebar />
      <div className="flex-1 lg:ml-64 flex flex-col h-screen overflow-hidden">
         <TopBar />
         <main>
            <KPICards />
            <div className="grid grid-cols-1 xl:grid-cols-12 gap-6 relative">
               <div className="xl:col-span-8"> <ChartsArea /> </div>
               <div className="xl:col-span-4"> <LiveFeed events={events} /> </div>
            </div>
         </main>
      </div>
   </div>
   ```

   ### `LiveFeed.tsx` (Real-Time List)
   Maps over an array of `FeedEvent` objects and uses `AnimatePresence` to animate new items entering the list.
   **Expected Data Schema (`FeedEvent`):**
   ```typescript
   export interface FeedEvent {
   id: string;
   type: 'purchase' | 'cart' | 'error';
   title: string;       // e.g., "Purchase: ₹12,499"
   subtitle: string;    // e.g., "User #8293"
   time: string;        // e.g., "2m ago" or "Just now"
   }
   ```
   *UI Behavior:*
   - `type === 'purchase'` renders with Emerald green accents.
   - `type === 'cart'` renders with Primary blue accents.
   - `type === 'error'` renders with Red/Error accents.

   ### `ChartsArea.tsx` (Visualizations)
   Currently uses static internal arrays for data (`revenueData`, `topProducts`, `eventData`). 
   **To make this dynamic in the future, it needs this exact data structure from the API:**

   1. **AreaChart (Revenue):**
      `{ name: string, revenue: number }[]`
   2. **Top Products (Custom Progress Bars):**
      `{ name: string, sales: number, percent: number }[]`
   3. **PieChart (Event Breakdown):**
      `{ name: string, value: number, color: string }[]`

   ### `KPICards.tsx`
   Renders 4 metric blocks. Currently static. 
   **Future API requirement to hydrate this component:**
   ```typescript
   interface KPI {
   title: string;      // e.g., "Total Revenue"
   value: string;      // e.g., "₹4.2M"
   trend: string;      // e.g., "+12.5%"
   trendUp: boolean;   // Dictates Emerald vs Red color formatting
   subtitle: string;   // e.g., "vs last month"
   }
   ```

   ---

   ## 5. API Integration Requirements (For the Backend Developer)

   To fully wire this frontend up to the real backend, the FastAPI endpoint `GET /api/v1/analytics/dashboard` must return a JSON payload that maps cleanly to the React state.

   **Ideal JSON Payload from FastAPI:**
   ```json
   {
   "kpis": [
      { "title": "Total Revenue", "value": "₹4.2M", "trend": "+12.5%", "trendUp": true, "subtitle": "vs last month" },
      { "title": "Active Users", "value": "2,840", "trend": "+8.2%", "trendUp": true, "subtitle": "live now" },
      ...
   ],
   "charts": {
      "revenue": [
         { "name": "Jan", "revenue": 4000 },
         { "name": "Feb", "revenue": 3000 }
      ],
      "topProducts": [
         { "name": "iPhone 15 Pro", "sales": 412, "percent": 85 }
      ],
      "eventBreakdown": [
         { "name": "Page Views", "value": 12402, "color": "#8ed5ff" }
      ]
   },
   "liveEvents": [
      { "id": "uuid-1", "type": "purchase", "title": "Purchase: ₹12,499", "subtitle": "User #8293", "time": "Just now" }
   ]
   }
   ```

   ## 6. How to Run
   ```bash
   # From the cart_iq/dashboard directory
   npm install
   npm run dev
   ```
   The application will launch on `http://localhost:5173/`. Ensure the backend is running on port `8002` when real data integration begins.
