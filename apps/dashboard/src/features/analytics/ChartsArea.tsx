import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, PieChart, Pie } from 'recharts';

export interface TopProduct {
  name: string;
  sales: number;
}

export interface EventData {
  name: string;
  value: number;
  color: string;
}

export interface RevenueData {
  name: string;
  revenue: number;
}

export interface ChartsAreaProps {
  liveSession?: boolean;
  period?: string;
  revenueData: RevenueData[];
  topProducts: TopProduct[];
  eventData: EventData[];
  totalEvents: number;
}

const ChartsArea: React.FC<ChartsAreaProps> = ({ revenueData, topProducts, eventData, totalEvents, liveSession = false, period = 'all' }) => {
  const yDomain: [number | string, number | string] = liveSession ? ["auto", "auto"] : [0, "auto"];

  // X-axis tick interval and angle based on period
  const xAxisProps = (() => {
    if (liveSession) return { interval: 2, angle: -45, height: 60 };
    if (period === 'today') return { interval: 1, angle: 0, height: 30 };     // every hour
    if (period === 'week') return { interval: 0, angle: 0, height: 30 };      // every day (7-14 points)
    if (period === 'month') return { interval: 1, angle: -30, height: 50 };   // every 2 months
    if (period === 'year') return { interval: 0, angle: -30, height: 50 };    // every month
    return { interval: 2, angle: -30, height: 50 };                           // all time — every 3 months
  })();
  const maxSales = Math.max(...topProducts.map(p => p.sales), 1);
  const productsWithPercent = topProducts.map(p => ({ ...p, percent: (p.sales / maxSales) * 100 }));

  const formatTotalEvents = (total: number) => {
    if (total >= 1000) return `${(total / 1000).toFixed(1)}k`;
    return total.toString();
  };

  return (
    <>
      {/* Large Wide Card: Revenue Chart */}
      <div className="glass-card glass-edge-top p-6 rounded-2xl h-[400px] flex flex-col">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h4 className="font-headline-md text-headline-md text-on-surface">Revenue Over Time</h4>
            <p className="text-on-surface-variant text-sm">{liveSession ? "Live revenue per interval" : "Historical revenue trend"}</p>
          </div>
        </div>

        <div className="flex-1 w-full min-h-0 relative -ml-4">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={revenueData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="colorRevenue" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#38bdf8" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#38bdf8" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
              <XAxis
                dataKey="name"
                stroke="#87929a"
                fontSize={11}
                tickLine={false}
                axisLine={false}
                interval={xAxisProps.interval}
                angle={xAxisProps.angle}
                textAnchor={xAxisProps.angle !== 0 ? "end" : "middle"}
                height={xAxisProps.height}
              />
              <YAxis stroke="#87929a" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(val) => {
                if (val >= 10000000) return `₹${(val / 10000000).toFixed(1)}Cr`;
                if (val >= 100000) return `₹${(val / 100000).toFixed(1)}L`;
                if (val >= 1000) return `₹${(val / 1000).toFixed(0)}k`;
                return `₹${val}`;
              }} domain={yDomain} />
              <Tooltip
                contentStyle={{ backgroundColor: '#171f33', borderColor: 'rgba(255,255,255,0.1)', borderRadius: '8px', color: '#dae2fd' }}
                itemStyle={{ color: '#38bdf8' }}
                formatter={(val: number) => {
                  if (val >= 10000000) return [`₹${(val / 10000000).toFixed(2)}Cr`, 'Revenue'];
                  if (val >= 100000) return [`₹${(val / 100000).toFixed(2)}L`, 'Revenue'];
                  if (val >= 1000) return [`₹${(val / 1000).toFixed(1)}k`, 'Revenue'];
                  return [`₹${val}`, 'Revenue'];
                }}
              />
              <Area type="monotone" dataKey="revenue" stroke="#38bdf8" strokeWidth={3} fillOpacity={1} fill="url(#colorRevenue)" style={{ filter: 'drop-shadow(0px 0px 8px rgba(56,189,248,0.3))' }} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Bottom Row: Charts */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        {/* Top Selling Products */}
        <div className="glass-card glass-edge-top p-6 rounded-2xl min-h-[300px]">
          <h4 className="font-headline-md text-headline-md text-on-surface mb-6">Top Selling Products</h4>
          <div className="space-y-6">
            {productsWithPercent.map((product) => (
              <div key={product.name} className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-on-surface">{product.name}</span>
                  <span className="text-on-surface-variant">{product.sales} sales</span>
                </div>
                <div className="h-2 w-full bg-surface-container rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-primary to-secondary rounded-full"
                    style={{ width: `${product.percent}%` }}
                  ></div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Event Breakdown */}
        <div className="glass-card glass-edge-top p-6 rounded-2xl min-h-[300px] flex flex-col md:flex-row items-center gap-8">
          <div className="w-48 h-48 relative flex items-center justify-center shrink-0">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={eventData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={80}
                  paddingAngle={5}
                  dataKey="value"
                  stroke="none"
                >
                  {eventData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ backgroundColor: '#171f33', borderColor: 'rgba(255,255,255,0.1)', borderRadius: '8px', color: '#dae2fd' }}
                  itemStyle={{ color: '#dae2fd' }}
                />
              </PieChart>
            </ResponsiveContainer>
            <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
              <span className="text-2xl font-bold">{formatTotalEvents(totalEvents)}</span>
              <span className="text-[10px] text-on-surface-variant uppercase">Events</span>
            </div>
          </div>

          <div className="flex-1 space-y-4 w-full">
            <h4 className="font-headline-md text-headline-md text-on-surface mb-2">Event Breakdown</h4>
            {eventData.map((event) => (
              <div key={event.name} className="flex items-center justify-between p-2 rounded-lg bg-surface-container/50">
                <div className="flex items-center gap-3">
                  <span className="h-3 w-3 rounded-full" style={{ backgroundColor: event.color }}></span>
                  <span className="text-sm">{event.name}</span>
                </div>
                <span className="text-sm font-semibold">{event.value.toLocaleString()}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </>
  );
};

export default ChartsArea;