import { useState, useEffect } from 'react';
import LogTerminal from './LogTerminal';

interface KafkaTopic {
  topic: string;
  partitions: number;
  message_count: number;
}

interface InfraData {
  redis: {
    used_memory_human: string;
    connected_clients: number;
    total_commands_processed: number;
    keyspace_hits: number;
    keyspace_misses: number;
    hit_ratio: number;
    total_keys: number;
  };
  kafka: {
    bootstrap_servers: string;
    topics: KafkaTopic[];
    consumer_group: string;
  };
}

const InfraPage = () => {
  const [data, setData] = useState<InfraData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchInfraData = async () => {
    try {
      const response = await fetch('http://localhost:8002/api/v1/analytics/infra');
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      const result = await response.json();
      setData(result);
      setError(null);
    } catch (err) {
      console.error('Failed to fetch infra data', err);
      setError('Connection to Infra API lost. Retrying...');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInfraData();
    const interval = setInterval(fetchInfraData, 10000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center min-h-[400px]">
        <div className="flex flex-col items-center gap-4 text-on-surface-variant">
          <span className="material-symbols-outlined animate-spin text-4xl text-primary">progress_activity</span>
          <p className="font-label-md">Connecting to Infrastructure Stream...</p>
        </div>
      </div>
    );
  }

  const hitPercentage = data?.redis.hit_ratio || 0;
  const missPercentage = 100 - hitPercentage;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="font-headline-md text-headline-md text-on-surface">Infrastructure Monitor</h1>
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-tertiary-container/10 border border-tertiary/20">
          <div className="w-2 h-2 rounded-full bg-tertiary pulse-emerald"></div>
          <span className="text-xs font-label-md text-tertiary uppercase tracking-wider">Live System Feed</span>
        </div>
      </div>

      {error && (
        <div className="bg-error-container/20 text-on-error-container p-4 rounded-xl border border-error/50 flex items-center justify-between">
          <span className="font-label-md">{error}</span>
          <span className="material-symbols-outlined animate-spin text-sm">refresh</span>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Redis Panel */}
        <div className="glass-card rounded-2xl p-6 space-y-6">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-primary/10">
              <span className="material-symbols-outlined text-primary">database</span>
            </div>
            <div>
              <h2 className="font-headline-sm text-lg text-on-surface font-semibold">Redis Instance</h2>
              <p className="text-xs text-on-surface-variant">In-memory caching layer</p>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div className="bg-surface-container-low/50 p-4 rounded-xl border border-white/5">
              <p className="text-[10px] uppercase tracking-wider text-on-surface-variant mb-1">Memory</p>
              <p className="text-xl font-bold text-primary">{data?.redis.used_memory_human}</p>
            </div>
            <div className="bg-surface-container-low/50 p-4 rounded-xl border border-white/5">
              <p className="text-[10px] uppercase tracking-wider text-on-surface-variant mb-1">Clients</p>
              <p className="text-xl font-bold text-primary">{data?.redis.connected_clients}</p>
            </div>
            <div className="bg-surface-container-low/50 p-4 rounded-xl border border-white/5">
              <p className="text-[10px] uppercase tracking-wider text-on-surface-variant mb-1">Commands</p>
              <p className="text-xl font-bold text-primary">{(data?.redis.total_commands_processed || 0).toLocaleString()}</p>
            </div>
          </div>

          <div className="space-y-3">
            <div className="flex items-center justify-between text-xs">
              <span className="text-on-surface-variant font-medium">Keyspace Performance</span>
              <span className="text-primary font-bold">{hitPercentage}% Hit Ratio</span>
            </div>
            <div className="h-2 w-full bg-surface-container-highest rounded-full overflow-hidden flex">
              <div 
                className="h-full bg-primary transition-all duration-1000 ease-in-out" 
                style={{ width: `${hitPercentage}%` }}
              ></div>
              <div 
                className="h-full bg-error/40 transition-all duration-1000 ease-in-out" 
                style={{ width: `${missPercentage}%` }}
              ></div>
            </div>
            <div className="flex items-center justify-between text-[10px] text-on-surface-variant uppercase tracking-widest px-1">
              <div className="flex items-center gap-1.5">
                <div className="w-1.5 h-1.5 rounded-full bg-primary"></div>
                Hits: {data?.redis.keyspace_hits.toLocaleString()}
              </div>
              <div className="flex items-center gap-1.5">
                <div className="w-1.5 h-1.5 rounded-full bg-error/60"></div>
                Misses: {data?.redis.keyspace_misses.toLocaleString()}
              </div>
            </div>
          </div>
        </div>

        {/* Kafka Panel */}
        <div className="glass-card rounded-2xl p-6 space-y-6">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-secondary/10">
              <span className="material-symbols-outlined text-secondary">dynamic_feed</span>
            </div>
            <div>
              <h2 className="font-headline-sm text-lg text-on-surface font-semibold">Kafka Cluster</h2>
              <p className="text-xs text-on-surface-variant">Event streaming backbone</p>
            </div>
          </div>

          <div className="space-y-4">
            <div className="bg-surface-container-low/50 p-4 rounded-xl border border-white/5 space-y-2">
              <div>
                <p className="text-[10px] uppercase tracking-wider text-on-surface-variant mb-0.5">Bootstrap Servers</p>
                <code className="text-xs text-secondary font-mono bg-secondary/5 px-2 py-0.5 rounded border border-secondary/10 block w-fit">
                  {data?.kafka.bootstrap_servers}
                </code>
              </div>
              <div>
                <p className="text-[10px] uppercase tracking-wider text-on-surface-variant mb-0.5">Consumer Group</p>
                <p className="text-sm font-medium text-on-surface">{data?.kafka.consumer_group}</p>
              </div>
            </div>

            <div className="space-y-2">
              <p className="text-[10px] uppercase tracking-wider text-on-surface-variant px-1 font-semibold">Active Topics</p>
              <div className="space-y-2 max-h-[140px] overflow-y-auto custom-scrollbar pr-1">
                {data?.kafka.topics.map((topic) => (
                  <div key={topic.topic} className="flex items-center justify-between p-3 rounded-xl bg-surface-container-low/30 border border-white/5 hover:bg-surface-container-low/50 transition-colors">
                    <div className="flex items-center gap-2">
                      <span className="material-symbols-outlined text-sm text-on-surface-variant">topic</span>
                      <span className="text-sm font-medium text-on-surface">{topic.topic}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] text-on-surface-variant px-2 py-0.5 rounded-full bg-white/5">
                        {topic.partitions} Partitions
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Log Terminal Section */}
      <LogTerminal />
    </div>
  );
};

export default InfraPage;
