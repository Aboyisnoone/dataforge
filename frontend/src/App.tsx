import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { Inbox } from './pages/Inbox';
import { Workspace } from './pages/Workspace';
import { Datasets } from './pages/Datasets';
import { Database, Inbox as InboxIcon } from 'lucide-react';

const Layout = ({ children }: { children: React.ReactNode }) => (
  <div className="min-h-screen bg-gray-50 font-sans text-gray-900 flex">
    <nav className="w-64 bg-white border-r border-gray-200 flex flex-col">
      <div className="p-4 border-b border-gray-200">
        <h1 className="text-xl font-bold text-blue-600 flex items-center gap-2">
          <Database className="w-6 h-6" /> DataForge
        </h1>
      </div>
      <div className="p-4 flex-1">
        <Link to="/" className="flex items-center gap-3 p-2 text-gray-700 hover:bg-gray-100 rounded-lg mb-2">
          <InboxIcon className="w-5 h-5" /> Inbox
        </Link>
        <Link to="/datasets" className="flex items-center gap-3 p-2 text-gray-700 hover:bg-gray-100 rounded-lg">
          <Database className="w-5 h-5" /> Datasets
        </Link>
      </div>
    </nav>
    <main className="flex-1 overflow-auto">
      {children}
    </main>
  </div>
);

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Layout><Inbox /></Layout>} />
        <Route path="/datasets" element={<Layout><Datasets /></Layout>} />
        <Route path="/investigations/:id" element={<Workspace />} />
      </Routes>
    </Router>
  );
}

export default App;
