import { NavLink } from 'react-router-dom';

const Sidebar = () => {
  const menuItems = [
    { name: 'Dashboard', icon: 'dashboard', path: '/' },
    { name: 'Infra', icon: 'dns', path: '/infra' },
    { name: 'Analytics', icon: 'analytics', path: '/analytics' },
    { name: 'Orders', icon: 'shopping_cart', path: '/orders' },
    { name: 'Products', icon: 'inventory_2', path: '/products' },
    { name: 'Settings', icon: 'settings', path: '/settings' },
  ];

  return (
    <aside className="hidden lg:flex fixed left-0 top-0 h-screen flex-col py-6 z-40 bg-surface-container-low/90 backdrop-blur-xl border-r border-white/5 w-64">
      <div className="px-6 mb-8 flex items-center gap-3">
        <div className="font-headline-md text-headline-md text-primary font-bold tracking-tight">CartIQ</div>
        <div className="text-[10px] bg-primary/10 text-primary px-2 py-0.5 rounded-full border border-primary/20 font-bold">PRO</div>
      </div>
      <nav className="flex-1 space-y-1">
        {menuItems.map((item) => (
          <NavLink
            key={item.name}
            to={item.path}
            className={({ isActive }) =>
              `flex items-center gap-3 rounded-xl px-4 py-3 mx-2 transition-all duration-200 ${
                isActive
                  ? 'bg-primary-container text-on-primary-container translate-x-1 shadow-lg shadow-primary/10'
                  : 'text-on-surface-variant hover:text-on-surface hover:bg-surface-variant/30'
              }`
            }
          >
            <span className="material-symbols-outlined">{item.icon}</span>
            <span className="font-label-md text-label-md font-medium">{item.name}</span>
          </NavLink>
        ))}
      </nav>
      <div className="mt-auto px-4 space-y-1">
        <button className="w-full bg-gradient-to-r from-primary to-secondary text-on-primary py-3 rounded-xl font-label-md text-label-md mb-4 shadow-lg shadow-primary/20 hover:opacity-90 transition-opacity">
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
