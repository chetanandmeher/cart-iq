import { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import KPICards from './KPICards';
import ChartsArea, { type TopProduct, type EventData, type RevenueData } from './ChartsArea';
import LiveFeed, { type FeedEvent } from './LiveFeed';

interface ApiPayload {
  revenue: { total_revenue: number; currency: string };
  top_products: { products: { product_name: string; purchase_count: number }[] };
  event_counts: { product_viewed: number; cart_added: number; cart_removed: number; purchase_completed: number; payment_failed: number; total: number };
  active_users: { active_users: number; window: string };
  recent_events: FeedEvent[];
  revenue_history: RevenueData[];
}

type Period = 'all' | 'today' | 'week' | 'month' | 'year' | 'session';

const API_URL = 'http://localhost:8002';

const PERIODS: { label: string; value: Period; icon: string }[] = [
  { label: 'All Time', value: 'all', icon: 'all_inclusive' },
  { label: 'Today', value: 'today', icon: 'today' },
  { label: 'Week', value: 'week', icon: 'date_range' },
  { label: 'Month', value: 'month', icon: 'calendar_month' },
  { label: 'Year', value: 'year', icon: 'calendar_today' },
  { label: 'Live Session', value: 'session', icon: 'bolt' },
];

// Format seconds → HH:MM:SS
const formatTimer = (secs: number) => {
  const h = Math.floor(secs / 3600).toString().padStart(2, '0');
  const m = Math.floor((secs % 3600) / 60).toString().padStart(2, '0');
  const s = (secs % 60).toString().padStart(2, '0');
  return `${h}:${m}:${s}`;
};

const DashboardPage = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [period, setPeriod] = useState<Period>('all');
  const [resetting, setResetting] = useState(false);
  const [resetMsg, setResetMsg] = useState<string | null>(null);

  // Timer
  const [sessionSecs, setSessionSecs] = useState<number | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // KPI state
  const [revenue, setRevenue] = useState(0);
  const [activeUsers, setActiveUsers] = useState(0);
  const [totalOrders, setTotalOrders] = useState(0);
  const [failedPayments, setFailedPayments] = useState(0);
  const [totalEvents, setTotalEvents] = useState(0);
  const [revenueHistory, setRevenueHistory] = useState<RevenueData[]>([]);
  const [topProducts, setTopProducts] = useState<TopProduct[]>([]);
  const [eventData, setEventData] = useState<EventData[]>([]);
  const [feedEvents, setFeedEvents] = useState<FeedEvent[]>([]);

  const dbBase = useRef<ApiPayload | null>(null);
  const redisSnapshot = useRef<ApiPayload | null>(null);

  // ── helpers ────────────────────────────────────────────────────
  const toIncremental = (history: RevenueData[]): RevenueData[] =>
    history.map((p, i) => ({ name: p.name, revenue: i === 0 ? p.revenue : Math.max(0, p.revenue - history[i - 1].revenue) }));


  const getLiveLabel = (p: Period): string => {
    const now = new Date();
    const pad = (n: number) => n.toString().padStart(2, '0');
    if (p === 'session') {
      // Live session: HH:MM:SS every 5s
      return `${pad(now.getHours())}:${pad(now.getMinutes())}:${pad(now.getSeconds())}`;
    } else if (p === 'today') {
      // Today: show current hour bucket e.g. "14:00"
      return `${pad(now.getHours())}:00`;
    } else if (p === 'week') {
      // Week: show day name + date e.g. "Mon 19"
      const day = now.toLocaleDateString('en-US', { weekday: 'short' });
      const date = pad(now.getDate());
      return `${day} ${date}`;
    } else if (p === 'month' || p === 'year' || p === 'all') {
      // Month/Year/All: show month + year e.g. "Jan 2025"
      return now.toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
    }
    return `${pad(now.getHours())}:${pad(now.getMinutes())}`;
  };

  const applyRedis = (data: ApiPayload) => {
    setRevenue(data.revenue.total_revenue);
    setActiveUsers(data.active_users.active_users);
    setTotalOrders(data.event_counts.purchase_completed);
    setFailedPayments(data.event_counts.payment_failed);
    setTotalEvents(data.event_counts.total);
    // For Live Session: append current revenue as a new live point
    setRevenueHistory(prev => [...prev, { name: getLiveLabel('session'), revenue: data.revenue.total_revenue }].slice(-30));
    setTopProducts(data.top_products.products.map(p => ({ name: p.product_name, sales: p.purchase_count })));
    setEventData([
      { name: 'Page Views', value: data.event_counts.product_viewed, color: '#8ed5ff' },
      { name: 'Cart Additions', value: data.event_counts.cart_added, color: '#bdc2ff' },
      { name: 'Purchases', value: data.event_counts.purchase_completed, color: '#10b981' },
    ]);
    setFeedEvents(data.recent_events || []);
  };

  const applyWithDelta = (redisNow: ApiPayload, currentPeriod: Period) => {
    if (!dbBase.current || !redisSnapshot.current) return;
    const snap = redisSnapshot.current;
    const db = dbBase.current;
    const d = (now: number, s: number) => Math.max(0, now - s);

    const deltaRev = d(redisNow.revenue.total_revenue, snap.revenue.total_revenue);
    const deltaOrders = d(redisNow.event_counts.purchase_completed, snap.event_counts.purchase_completed);
    const deltaFailed = d(redisNow.event_counts.payment_failed, snap.event_counts.payment_failed);
    const deltaTotal = d(redisNow.event_counts.total, snap.event_counts.total);
    const deltaViews = d(redisNow.event_counts.product_viewed, snap.event_counts.product_viewed);
    const deltaCart = d(redisNow.event_counts.cart_added, snap.event_counts.cart_added);

    const totalRevenue = db.revenue.total_revenue + deltaRev;
    const totalOrders = db.event_counts.purchase_completed + deltaOrders;

    setRevenue(totalRevenue);
    setTotalOrders(totalOrders);
    setFailedPayments(db.event_counts.payment_failed + deltaFailed);
    setTotalEvents(db.event_counts.total + deltaTotal);
    setActiveUsers(redisNow.active_users.active_users);
    setEventData([
      { name: 'Page Views', value: db.event_counts.product_viewed + deltaViews, color: '#8ed5ff' },
      { name: 'Cart Additions', value: db.event_counts.cart_added + deltaCart, color: '#bdc2ff' },
      { name: 'Purchases', value: totalOrders, color: '#10b981' },
    ]);

    // Merge live delta into top products so they accumulate too
    const liveProductMap = new Map(redisNow.top_products.products.map(p => [p.product_name, p.purchase_count]));
    const snapProductMap = new Map(snap.top_products.products.map(p => [p.product_name, p.purchase_count]));
    setTopProducts(
      db.top_products.products.map(p => ({
        name: p.product_name,
        sales: p.purchase_count + Math.max(0, (liveProductMap.get(p.product_name) ?? 0) - (snapProductMap.get(p.product_name) ?? 0)),
      }))
    );

    // Accumulate a live data point on the revenue graph for non-session periods
    const liveLabel = getLiveLabel(currentPeriod);
    setRevenueHistory(prev => {
      // Replace the last point if it has the same label (same time bucket), otherwise append
      const last = prev[prev.length - 1];
      if (last && last.name === liveLabel) {
        return [...prev.slice(0, -1), { name: liveLabel, revenue: totalRevenue }];
      }
      return [...prev, { name: liveLabel, revenue: totalRevenue }].slice(-200);
    });

    setFeedEvents(redisNow.recent_events || []);
  };

  // ── session timer ──────────────────────────────────────────────

  const startTimer = (elapsedAtFetch: number) => {
    if (timerRef.current) clearInterval(timerRef.current);
    let secs = elapsedAtFetch;
    setSessionSecs(secs);
    timerRef.current = setInterval(() => {
      secs += 1;
      setSessionSecs(secs);
    }, 1000);
  };

  const stopTimer = () => {
    if (timerRef.current) clearInterval(timerRef.current);
    setSessionSecs(null);
  };

  useEffect(() => {
    // Fetch session info on mount to restore timer if page refreshed
    fetch(`${API_URL}/api/v1/analytics/session`)
      .then(r => r.json())
      .then(d => { if (d.elapsed_seconds !== null) startTimer(d.elapsed_seconds); })
      .catch(() => { });
    return () => { if (timerRef.current) clearInterval(timerRef.current); };
  }, []);

  // ── fetch base when period changes ─────────────────────────────

  const fetchBase = async (p: Period) => {
    setLoading(true);
    try {
      if (p === 'session') {
        // Pure Redis — no DB base, clear history so it builds fresh
        setRevenueHistory([]);
        const redisRes = await fetch(`${API_URL}/api/v1/analytics/dashboard`);
        const redisData: ApiPayload = await redisRes.json();
        dbBase.current = null;
        redisSnapshot.current = null;
        applyRedis(redisData);
      } else {
        const [dbRes, redisRes] = await Promise.all([
          fetch(`${API_URL}/api/v1/analytics/dashboard?period=${p}`),
          fetch(`${API_URL}/api/v1/analytics/dashboard`),
        ]);
        dbBase.current = await dbRes.json();
        redisSnapshot.current = await redisRes.json();
        // Seed graph with full DB history for this period, then append live point immediately
        setRevenueHistory(dbBase.current!.revenue_history || []);
        applyWithDelta(redisSnapshot.current!, p);
      }
    } catch {
      setError('Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchBase(period); }, [period]);

  // ── Redis live polling ─────────────────────────────────────────

  useEffect(() => {
    const poll = async () => {
      try {
        const res = await fetch(`${API_URL}/api/v1/analytics/dashboard`);
        if (!res.ok) throw new Error();
        const data: ApiPayload = await res.json();
        if (period === 'session') {
          applyRedis(data);
        } else {
          applyWithDelta(data, period);
        }
        setError(null);
      } catch {
        setError('Connection to backend lost. Retrying...');
      }
    };
    const id = setInterval(poll, 5000);
    return () => clearInterval(id);
  }, [period]);

  // ── Reset ──────────────────────────────────────────────────────

  const handleReset = async () => {
    if (!confirm('Reset dashboard? This clears all live Redis data. Historical DB data is untouched.')) return;
    setResetting(true);
    try {
      await fetch(`${API_URL}/api/v1/analytics/reset`, { method: 'POST' });
      setResetMsg('Dashboard reset! Accumulating fresh data...');
      setTimeout(() => setResetMsg(null), 4000);
      startTimer(0);
      // Always wipe the graph so it starts fresh from zero
      setRevenueHistory([]);
      dbBase.current = null;
      redisSnapshot.current = null;
      if (period === 'session') {
        // Already on session — fetchBase won't re-trigger, so manually re-fetch Redis
        const redisRes = await fetch(`${API_URL}/api/v1/analytics/dashboard`);
        const redisData: ApiPayload = await redisRes.json();
        applyRedis(redisData);
      } else {
        // Switch to session — fetchBase will fire via useEffect and seed fresh data
        setPeriod('session');
      }
    } catch {
      setError('Reset failed');
    } finally {
      setResetting(false);
    }
  };

  // ── render ─────────────────────────────────────────────────────

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center min-h-[400px]">
        <div className="flex flex-col items-center gap-4 text-on-surface-variant">
          <span className="material-symbols-outlined animate-spin text-4xl text-primary">progress_activity</span>
          <p className="font-label-md">Connecting to Data Stream...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">

      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <h1 className="font-headline-md text-headline-md text-on-surface">Analytics Overview</h1>
        <div className="flex items-center gap-3 flex-wrap">

          {/* Session timer */}
          {sessionSecs !== null && (
            <div className="flex items-center gap-2 bg-surface-container px-3 py-2 rounded-xl border border-emerald-500/30">
              <span className="flex h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></span>
              <span className="material-symbols-outlined text-sm text-emerald-400">timer</span>
              <span className="text-sm font-mono text-emerald-400">{formatTimer(sessionSecs)}</span>
              <span className="text-xs text-on-surface-variant">since reset</span>
            </div>
          )}

          {/* Reset button */}
          <button
            onClick={handleReset}
            disabled={resetting}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-error/10 text-red-400 border border-error/20 hover:bg-error/20 transition-all group disabled:opacity-50"
          >
            <span className={`material-symbols-outlined text-lg ${resetting ? 'animate-spin' : 'group-hover:rotate-180 transition-transform duration-500'}`}>
              refresh
            </span>
            <span className="text-sm font-medium">Reset Dashboard</span>
          </button>

          <Link
            to="/infra"
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-primary/10 text-primary border border-primary/20 hover:bg-primary/20 transition-all group"
          >
            <span className="material-symbols-outlined text-lg group-hover:rotate-12 transition-transform">settings_input_component</span>
            <span className="text-sm font-medium">Infrastructure Stats</span>
            <span className="material-symbols-outlined text-sm">chevron_right</span>
          </Link>
        </div>
      </div>

      {/* Period tabs */}
      <div className="flex items-center gap-2 flex-wrap">
        {PERIODS.map(p => (
          <button
            key={p.value}
            onClick={() => setPeriod(p.value)}
            className={`flex items-center gap-1.5 px-4 py-1.5 rounded-full text-sm font-medium transition-all border ${period === p.value
              ? p.value === 'session'
                ? 'bg-emerald-500 text-white border-emerald-500 shadow-lg shadow-emerald-500/20'
                : 'bg-primary text-white border-primary shadow-lg shadow-primary/20'
              : 'bg-surface-container text-on-surface-variant border-outline-variant/30 hover:border-primary/50'
              }`}
          >
            <span className="material-symbols-outlined text-sm">{p.icon}</span>
            {p.label}
            {p.value === 'session' && period !== 'session' && sessionSecs !== null && (
              <span className="flex h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
            )}
          </button>
        ))}

        {/* Mode badge */}
        <span className="ml-1 text-xs text-on-surface-variant bg-surface-container px-2 py-1 rounded-full border border-outline-variant/20">
          {period === 'session' ? '⚡ Pure Redis · Live' : 'DB base · Redis live'}
        </span>
      </div>

      {/* Live Session banner */}
      {period === 'session' && (
        <div className="flex items-center gap-3 bg-emerald-500/10 border border-emerald-500/20 rounded-xl px-4 py-3">
          <span className="flex h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></span>
          <span className="text-sm text-emerald-400 font-medium">
            Live Session — showing data accumulated since last reset
            {sessionSecs !== null && ` · running for ${formatTimer(sessionSecs)}`}
          </span>
        </div>
      )}

      {/* Reset message */}
      {resetMsg && (
        <div className="bg-emerald-500/10 text-emerald-400 p-4 rounded-xl border border-emerald-500/20 flex items-center gap-3">
          <span className="material-symbols-outlined text-sm">check_circle</span>
          <span className="text-sm">{resetMsg}</span>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="bg-error-container text-on-error-container p-4 rounded-xl border border-error/50 flex items-center justify-between">
          <span className="font-label-md">{error}</span>
          <span className="material-symbols-outlined animate-spin text-sm">refresh</span>
        </div>
      )}

      {/* KPIs */}
      <KPICards
        revenue={revenue}
        activeUsers={activeUsers}
        totalOrders={totalOrders}
        failedPayments={failedPayments}
      />

      {/* Charts + Feed */}
      <div className="grid grid-cols-1 xl:grid-cols-12 gap-6 relative">
        <div className="xl:col-span-8 flex flex-col gap-6">
          <ChartsArea
            revenueData={revenueHistory}
            topProducts={topProducts}
            eventData={eventData}
            totalEvents={totalEvents}
            liveSession={period === 'session'}
            period={period}
          />
        </div>
        <div className="xl:col-span-4 mt-6 xl:mt-0">
          <LiveFeed events={feedEvents} />
        </div>
      </div>

    </div>
  );
};

export default DashboardPage;