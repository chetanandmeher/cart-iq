import { useState, useEffect } from 'react';

const SimulatorControl = () => {
  const [isRunning, setIsRunning] = useState(false);
  const [eps, setEps] = useState(0);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const response = await fetch('http://localhost:8002/api/v1/analytics/simulator/status');
        if (response.ok) {
          const data = await response.json();
          setIsRunning(data.is_running);
          setEps(data.eps || 0);
        }
      } catch (err) {
        // Silent error to avoid console noise during polling
      }
    };

    fetchStatus();
    const interval = setInterval(fetchStatus, 2000);
    return () => clearInterval(interval);
  }, []);

  const handleToggle = async () => {
    const endpoint = isRunning ? 'stop' : 'start';
    try {
      const response = await fetch(`http://localhost:8002/api/v1/analytics/simulator/${endpoint}`, {
        method: 'POST',
      });
      if (response.ok) {
        setIsRunning(!isRunning);
      }
    } catch (err) {
      console.error(`Failed to ${endpoint} simulator:`, err);
    }
  };

  return (
    <div className="flex items-center gap-4 bg-surface-container/40 backdrop-blur-md px-4 py-1.5 rounded-full border border-white/10 shadow-lg shadow-black/20 group hover:border-primary/30 transition-all duration-300">
      <div className="flex items-center gap-2 pr-3 border-r border-white/5">
        <span className={`flex h-2 w-2 rounded-full ${isRunning ? 'bg-emerald-500 pulse-emerald' : 'bg-slate-600'}`}></span>
        <span className={`text-[11px] font-bold uppercase tracking-widest ${isRunning ? 'text-emerald-400' : 'text-slate-500'}`}>
          {isRunning ? 'Simulator Live' : 'Simulator Offline'}
        </span>
      </div>

      {isRunning && (
        <div className="flex items-center gap-2 animate-in fade-in slide-in-from-left-2 duration-500">
          <div className="flex flex-col leading-none">
            <span className="text-[9px] text-on-surface-variant uppercase font-bold opacity-50 tracking-tighter">Throughput</span>
            <div className="flex items-baseline gap-1">
              <span className="text-sm font-mono font-black text-primary">{eps.toFixed(1)}</span>
              <span className="text-[10px] text-primary/70 font-medium">EPS</span>
            </div>
          </div>
        </div>
      )}

      <button
        onClick={handleToggle}
        title={isRunning ? "Stop Simulator" : "Start Simulator"}
        className={`flex items-center justify-center w-8 h-8 rounded-full transition-all duration-500 relative overflow-hidden ${isRunning
            ? 'bg-error/10 text-error hover:bg-error hover:text-on-error shadow-lg shadow-error/20'
            : 'bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500 hover:text-on-tertiary shadow-lg shadow-emerald-500/10'
          }`}
      >
        <span className="material-symbols-outlined text-xl z-10">
          {isRunning ? 'stop' : 'play_arrow'}
        </span>
        <span className={`absolute inset-0 opacity-0 group-hover:opacity-20 transition-opacity duration-300 ${isRunning ? 'bg-white' : 'bg-white'}`}></span>
      </button>
    </div>
  );
};

export default SimulatorControl;
