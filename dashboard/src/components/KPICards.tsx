import { motion } from 'framer-motion';

export interface KPIProps {
  revenue: number;
  activeUsers: number;
  totalOrders: number;
  failedPayments: number;
}

const KPICards: React.FC<KPIProps> = ({ revenue, activeUsers, totalOrders, failedPayments }) => {
  const kpis = [
    {
      title: 'Total Revenue',
      value: `₹${(revenue / 1000).toFixed(1)}k`,
      trend: 'Live',
      trendUp: true,
      subtitle: 'current total'
    },
    {
      title: 'Active Users',
      value: activeUsers.toLocaleString(),
      trend: 'Live',
      trendUp: true,
      subtitle: 'last 5 minutes'
    },
    {
      title: 'Total Orders',
      value: totalOrders.toLocaleString(),
      trend: 'Live',
      trendUp: true,
      subtitle: 'purchases completed'
    },
    {
      title: 'Failed Payments',
      value: failedPayments.toLocaleString(),
      trend: 'Live',
      trendUp: false,
      subtitle: 'payment failed count'
    }
  ];

  return (
    <section className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
      {kpis.map((kpi, idx) => (
        <motion.div 
          key={kpi.title}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: idx * 0.1, duration: 0.5 }}
          className="glass-card glass-edge-top p-6 rounded-2xl flex flex-col justify-between"
        >
          <div>
            <p className="font-label-sm text-label-sm text-on-surface-variant uppercase tracking-wider mb-2">{kpi.title}</p>
            <h3 className="font-headline-lg text-headline-lg text-on-surface">{kpi.value}</h3>
          </div>
          <div className="flex items-center gap-2 mt-4">
            <span className={`${kpi.trendUp ? 'text-emerald-400' : 'text-error'} font-label-md text-label-md flex items-center`}>
              <span className="material-symbols-outlined text-sm mr-1">
                {kpi.trendUp ? 'trending_up' : 'trending_down'}
              </span> 
              {kpi.trend}
            </span>
            <span className="text-on-surface-variant text-xs">{kpi.subtitle}</span>
          </div>
        </motion.div>
      ))}
    </section>
  );
};

export default KPICards;
