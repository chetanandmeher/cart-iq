import { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import TopBar from './components/TopBar';
import KPICards from './components/KPICards';
import ChartsArea, { type TopProduct, type EventData, type RevenueData } from './components/ChartsArea';
import LiveFeed, { type FeedEvent } from './components/LiveFeed';

interface ApiPayload {
  revenue: { total_revenue: number; currency: string };
  top_products: { products: { product_name: string; purchase_count: number }[] };
  event_counts: { product_viewed: number; cart_added: number; cart_removed: number; purchase_completed: number; payment_failed: number; total: number };
  active_users: { active_users: number; window: string };
  recent_events: FeedEvent[];
  revenue_history: RevenueData[];
}

function App() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [revenue, setRevenue] = useState(0);
  const [activeUsers, setActiveUsers] = useState(0);
  const [totalOrders, setTotalOrders] = useState(0);
  const [failedPayments, setFailedPayments] = useState(0);
  const [totalEvents, setTotalEvents] = useState(0);

  const [revenueHistory, setRevenueHistory] = useState<RevenueData[]>([]);
  const [topProducts, setTopProducts] = useState<TopProduct[]>([]);
  const [eventData, setEventData] = useState<EventData[]>([]);
  
  const [feedEvents, setFeedEvents] = useState<FeedEvent[]>([]);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        const response = await fetch('http://localhost:8002/api/v1/analytics/dashboard');
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data: ApiPayload = await response.json();
        
        // 1. Update KPIs
        setRevenue(data.revenue.total_revenue);
        setActiveUsers(data.active_users.active_users);
        setTotalOrders(data.event_counts.purchase_completed);
        setFailedPayments(data.event_counts.payment_failed);
        setTotalEvents(data.event_counts.total);

        // 2. Update Revenue History (From backend)
        setRevenueHistory(data.revenue_history || []);

        // 3. Update Top Products
        const mappedProducts: TopProduct[] = data.top_products.products.map(p => ({
          name: p.product_name,
          sales: p.purchase_count
        }));
        setTopProducts(mappedProducts);

        // 4. Update Event Pie Chart
        setEventData([
          { name: 'Page Views', value: data.event_counts.product_viewed, color: '#8ed5ff' },
          { name: 'Cart Additions', value: data.event_counts.cart_added, color: '#bdc2ff' },
          { name: 'Purchases', value: data.event_counts.purchase_completed, color: '#10b981' }
        ]);

        // 5. Live Feed Events (From backend)
        setFeedEvents(data.recent_events || []);

        setError(null);
      } catch (err) {
        console.error('Data stream interrupted', err);
        setError('Connection to backend lost. Retrying...');
      } finally {
        setLoading(false);
      }
    };

    // Initial fetch
    fetchDashboardData();
    
    // Poll every 5 seconds
    const intervalId = setInterval(fetchDashboardData, 5000);
    return () => clearInterval(intervalId);
  }, []);

  return (
    <div className="flex w-full h-full">
      <Sidebar />
      <div className="flex-1 lg:ml-64 flex flex-col h-screen overflow-hidden">
        <TopBar />
        <main className="flex-1 overflow-y-auto p-6 space-y-6">
          
          {error && (
            <div className="bg-error-container text-on-error-container p-4 rounded-xl border border-error/50 flex items-center justify-between">
              <span className="font-label-md">{error}</span>
              <span className="material-symbols-outlined animate-spin text-sm">refresh</span>
            </div>
          )}

          {loading ? (
            <div className="flex-1 flex items-center justify-center min-h-[400px]">
              <div className="flex flex-col items-center gap-4 text-on-surface-variant">
                <span className="material-symbols-outlined animate-spin text-4xl text-primary">progress_activity</span>
                <p className="font-label-md">Connecting to Data Stream...</p>
              </div>
            </div>
          ) : (
            <>
              <KPICards 
                revenue={revenue} 
                activeUsers={activeUsers} 
                totalOrders={totalOrders} 
                failedPayments={failedPayments} 
              />
              
              <div className="grid grid-cols-1 xl:grid-cols-12 gap-6 relative">
                <div className="xl:col-span-8 flex flex-col gap-6">
                  <ChartsArea 
                     revenueData={revenueHistory}
                     topProducts={topProducts}
                     eventData={eventData}
                     totalEvents={totalEvents}
                   />
                </div>
                
                <div className="xl:col-span-4 mt-6 xl:mt-0">
                   <LiveFeed events={feedEvents} />
                </div>
              </div>
            </>
          )}

        </main>
      </div>
    </div>
  );
}

export default App;
