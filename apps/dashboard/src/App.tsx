import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Sidebar from './layout/Sidebar';
import TopBar from './layout/TopBar';
import DashboardPage from './features/analytics/DashboardPage';
import InfraPage from './features/infra/InfraPage';

function App() {
  return (
    <BrowserRouter>
      <div className="flex w-full h-full">
        <Sidebar />
        <div className="flex-1 lg:ml-64 flex flex-col h-screen overflow-hidden">
          <TopBar />
          <main className="flex-1 overflow-y-auto p-6 space-y-6 custom-scrollbar">
            <Routes>
              <Route path="/" element={<DashboardPage />} />
              <Route path="/infra" element={<InfraPage />} />
              {/* Fallback for other routes */}
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </main>
        </div>
      </div>
    </BrowserRouter>
  );
}

export default App;
