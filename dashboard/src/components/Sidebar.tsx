
const Sidebar = () => {
  return (
    <aside className="hidden lg:flex fixed left-0 top-0 h-screen flex-col py-6 z-40 bg-surface-container-low/90 backdrop-blur-xl border-r border-white/5 w-64">
      <div className="px-6 mb-8 flex items-center gap-3">
        <div className="font-headline-md text-headline-md text-primary font-bold">CartIQ</div>
      </div>
      <nav className="flex-1 space-y-1">
        <a className="flex items-center gap-3 bg-primary-container text-on-primary-container rounded-xl px-4 py-3 mx-2 translate-x-1 duration-200" href="#">
          <span className="material-symbols-outlined">dashboard</span>
          <span className="font-label-md text-label-md">Dashboard</span>
        </a>
        <a className="flex items-center gap-3 text-on-surface-variant hover:text-on-surface hover:bg-surface-variant/30 rounded-xl px-4 py-3 mx-2 transition-all" href="#">
          <span className="material-symbols-outlined">analytics</span>
          <span className="font-label-md text-label-md">Analytics</span>
        </a>
        <a className="flex items-center gap-3 text-on-surface-variant hover:text-on-surface hover:bg-surface-variant/30 rounded-xl px-4 py-3 mx-2 transition-all" href="#">
          <span className="material-symbols-outlined">shopping_cart</span>
          <span className="font-label-md text-label-md">Orders</span>
        </a>
        <a className="flex items-center gap-3 text-on-surface-variant hover:text-on-surface hover:bg-surface-variant/30 rounded-xl px-4 py-3 mx-2 transition-all" href="#">
          <span className="material-symbols-outlined">inventory_2</span>
          <span className="font-label-md text-label-md">Products</span>
        </a>
        <a className="flex items-center gap-3 text-on-surface-variant hover:text-on-surface hover:bg-surface-variant/30 rounded-xl px-4 py-3 mx-2 transition-all" href="#">
          <span className="material-symbols-outlined">settings</span>
          <span className="font-label-md text-label-md">Settings</span>
        </a>
      </nav>
      <div className="mt-auto px-4 space-y-1">
        <button className="w-full bg-gradient-to-r from-primary to-secondary text-on-primary py-3 rounded-xl font-label-md text-label-md mb-4 shadow-lg shadow-primary/20">
          Export Report
        </button>
        <a className="flex items-center gap-3 text-on-surface-variant hover:text-on-surface px-4 py-3 transition-all" href="#">
          <span className="material-symbols-outlined">help</span>
          <span className="font-label-md text-label-md">Support</span>
        </a>
        <a className="flex items-center gap-3 text-on-surface-variant hover:text-on-surface px-4 py-3 transition-all" href="#">
          <span className="material-symbols-outlined">person</span>
          <span className="font-label-md text-label-md">Account</span>
        </a>
      </div>
    </aside>
  );
};

export default Sidebar;
