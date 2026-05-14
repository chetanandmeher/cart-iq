import { useState, useEffect, useRef } from 'react';

interface LogLine {
  id: number;
  timestamp: string;
  level: 'INFO' | 'WARNING' | 'ERROR' | 'UNKNOWN';
  message: string;
  raw: string;
}

const LogTerminal = () => {
  const [activeTab, setActiveTab] = useState<'redis' | 'kafka'>('redis');
  const [logs, setLogs] = useState<LogLine[]>([]);
  const scrollRef = useRef<HTMLDivElement>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  const parseLogLine = (raw: string, id: number): LogLine => {
    // Expected format from SSE: "2026-05-14T11:28:27.123Z INFO  some message"
    const parts = raw.split(' ');
    const timestamp = parts[0] || '';
    let level: LogLine['level'] = 'UNKNOWN';
    let message = raw;

    if (raw.includes('INFO')) level = 'INFO';
    else if (raw.includes('WARNING')) level = 'WARNING';
    else if (raw.includes('ERROR')) level = 'ERROR';

    // Simple heuristic to extract message if level is found
    const levelIndex = raw.indexOf(level);
    if (levelIndex !== -1) {
      message = raw.substring(levelIndex + level.length).trim();
    }

    return { id, timestamp, level, message, raw };
  };

  useEffect(() => {
    // Close existing connection if any
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    const url = `http://localhost:8002/api/v1/analytics/logs/${activeTab}`;
    const es = new EventSource(url);
    eventSourceRef.current = es;

    es.onmessage = (event) => {
      const newLine = parseLogLine(event.data, Date.now());
      setLogs((prev) => {
        const updated = [...prev, newLine];
        return updated.slice(-200); // Keep last 200 lines
      });
    };

    es.onerror = (err) => {
      console.error('SSE connection error:', err);
      es.close();
    };

    return () => {
      es.close();
    };
  }, [activeTab]);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs]);

  const clearLogs = () => setLogs([]);

  const getLevelColor = (level: LogLine['level']) => {
    switch (level) {
      case 'INFO': return 'text-emerald-400';
      case 'WARNING': return 'text-yellow-400';
      case 'ERROR': return 'text-error';
      default: return 'text-on-surface';
    }
  };

  return (
    <div className="glass-card rounded-2xl overflow-hidden flex flex-col h-[500px]">
      {/* Terminal Header */}
      <div className="bg-surface-container-highest/50 px-6 py-3 flex items-center justify-between border-b border-white/5">
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-on-surface-variant text-lg">terminal</span>
            <h3 className="font-label-md text-on-surface font-semibold uppercase tracking-wider text-xs">Live Logs</h3>
          </div>
          <div className="flex bg-surface-container-low/80 p-1 rounded-lg border border-white/5">
            <button
              onClick={() => setActiveTab('redis')}
              className={`px-4 py-1.5 rounded-md text-xs font-medium transition-all ${
                activeTab === 'redis'
                  ? 'bg-primary text-on-primary shadow-sm'
                  : 'text-on-surface-variant hover:text-on-surface'
              }`}
            >
              Redis
            </button>
            <button
              onClick={() => setActiveTab('kafka')}
              className={`px-4 py-1.5 rounded-md text-xs font-medium transition-all ${
                activeTab === 'kafka'
                  ? 'bg-secondary text-on-secondary shadow-sm'
                  : 'text-on-surface-variant hover:text-on-surface'
              }`}
            >
              Kafka
            </button>
          </div>
        </div>
        <button
          onClick={clearLogs}
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg hover:bg-surface-variant/50 text-on-surface-variant hover:text-on-surface transition-all text-xs"
        >
          <span className="material-symbols-outlined text-sm">delete_sweep</span>
          <span>Clear Terminal</span>
        </button>
      </div>

      {/* Terminal Body */}
      <div 
        ref={scrollRef}
        className="flex-1 bg-black/90 p-4 font-mono text-sm overflow-y-auto custom-scrollbar selection:bg-primary/30"
      >
        {logs.length === 0 ? (
          <div className="h-full flex items-center justify-center text-on-surface-variant/30 flex-col gap-2">
            <span className="material-symbols-outlined text-4xl animate-pulse">settings_input_component</span>
            <p className="text-xs italic">Waiting for {activeTab} log stream...</p>
          </div>
        ) : (
          <div className="space-y-0.5">
            {logs.map((log) => (
              <div key={log.id} className="flex gap-3 leading-relaxed group">
                <span className="text-on-surface-variant/40 shrink-0 select-none text-[12px]">
                  {log.timestamp.split('T')[1]?.substring(0, 12) || log.timestamp}
                </span>
                <span className={`font-bold shrink-0 min-w-[50px] ${getLevelColor(log.level)} text-[12px]`}>
                  {log.level}
                </span>
                <span className="text-on-surface-variant group-hover:text-on-surface transition-colors break-all">
                  {log.message}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
      
      {/* Terminal Footer */}
      <div className="bg-black/95 px-4 py-2 flex items-center gap-3 border-t border-white/5">
        <div className="flex gap-1.5">
          <div className="w-2.5 h-2.5 rounded-full bg-error/50"></div>
          <div className="w-2.5 h-2.5 rounded-full bg-yellow-500/50"></div>
          <div className="w-2.5 h-2.5 rounded-full bg-emerald-500/50"></div>
        </div>
        <div className="text-[10px] text-on-surface-variant/50 font-mono flex items-center gap-2">
          <span className="text-primary opacity-70">➜</span>
          <span>Streaming {activeTab}_service.log</span>
          <span className="animate-pulse">_</span>
        </div>
        <div className="ml-auto text-[10px] text-on-surface-variant/30 font-mono">
          {logs.length} / 200 lines
        </div>
      </div>
    </div>
  );
};

export default LogTerminal;
