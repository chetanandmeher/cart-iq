import { motion, AnimatePresence } from 'framer-motion';

// Using a type definition for the feed event
export interface FeedEvent {
  id: string;
  type: 'purchase' | 'cart' | 'error';
  title: string;
  subtitle: string;
  time: string;
}

interface LiveFeedProps {
  events: FeedEvent[];
}

const LiveFeed: React.FC<LiveFeedProps> = ({ events }) => {
  return (
    <div className="glass-card glass-edge-top p-6 rounded-2xl h-[400px] flex flex-col">
      <div className="flex items-center justify-between mb-6">
        <h4 className="font-headline-md text-headline-md text-on-surface">Live Events</h4>
        <span className="text-[10px] uppercase bg-surface-container-highest px-2 py-0.5 rounded text-on-surface-variant font-bold tracking-widest">Real-time</span>
      </div>
      <div className="flex-1 overflow-y-auto space-y-4 pr-2 custom-scrollbar">
        <AnimatePresence>
          {events.map((event) => {
            let bgClass = '';
            let iconColor = '';
            let iconName = '';
            let borderClass = '';

            if (event.type === 'purchase') {
              bgClass = 'bg-emerald-500/5';
              borderClass = 'border-emerald-500/10';
              iconColor = 'text-emerald-400 bg-emerald-500/20';
              iconName = 'shopping_bag';
            } else if (event.type === 'cart') {
              bgClass = 'bg-primary/5';
              borderClass = 'border-primary/10';
              iconColor = 'text-primary bg-primary/20';
              iconName = 'add_shopping_cart';
            } else {
              bgClass = 'bg-error/5';
              borderClass = 'border-error/10';
              iconColor = 'text-error bg-error/20';
              iconName = 'gpp_maybe';
            }

            return (
              <motion.div 
                key={event.id}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, scale: 0.9 }}
                className={`flex gap-4 p-3 rounded-xl border ${bgClass} ${borderClass}`}
              >
                <div className={`h-10 w-10 shrink-0 rounded-full flex items-center justify-center ${iconColor}`}>
                  <span className="material-symbols-outlined">{iconName}</span>
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-semibold text-on-surface truncate">{event.title}</p>
                  <p className="text-xs text-on-surface-variant">{event.subtitle} • {event.time}</p>
                </div>
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>
    </div>
  );
};

export default LiveFeed;
