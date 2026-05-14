
const TopBar = () => {
  return (
    <header className="flex justify-between items-center px-6 py-4 w-full h-16 z-30 bg-surface/80 backdrop-blur-xl border-b border-white/10 shadow-sm shadow-primary/10 relative lg:static">
      <div className="flex items-center gap-4">
        {/* Placeholder for CartIQ Logo */}
        <div className="font-bold text-lg text-primary tracking-wide">
          CartIQ
        </div>
        <div className="flex items-center gap-2 bg-surface-container px-3 py-1 rounded-full border border-white/5">
          <span className="flex h-2 w-2 rounded-full bg-emerald-500 pulse-emerald"></span>
          <span className="font-label-md text-label-md text-emerald-400">Live</span>
        </div>
      </div>
      <div className="flex items-center gap-6">
        <div className="relative group hidden sm:block">
          <input 
            className="bg-surface-container border border-outline-variant/30 rounded-full py-1.5 pl-10 pr-4 focus:ring-2 focus:ring-primary/50 focus:border-primary transition-all text-sm outline-none w-64 text-on-surface" 
            placeholder="Global search..." 
            type="text"
          />
          <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant text-lg">search</span>
        </div>
        <div className="flex items-center gap-4">
          <button className="p-2 hover:bg-surface-variant/50 rounded-full transition-colors text-on-surface-variant">
            <span className="material-symbols-outlined">dark_mode</span>
          </button>
          <button className="p-2 hover:bg-surface-variant/50 rounded-full transition-colors text-on-surface-variant">
            <span className="material-symbols-outlined">sensors</span>
          </button>
          <div className="h-8 w-8 rounded-full overflow-hidden border border-primary/30 bg-surface-variant">
            <div className="h-full w-full flex items-center justify-center text-primary">
              <span className="material-symbols-outlined text-sm">person</span>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};

export default TopBar;
