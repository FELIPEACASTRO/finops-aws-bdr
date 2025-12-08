import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Layout } from './components/layout';
import {
  Dashboard,
  Costs,
  Recommendations,
  AIConsultant,
  MultiRegion,
  Analytics,
  Settings,
} from './pages';
import './index.css';

function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/costs" element={<Costs />} />
          <Route path="/recommendations" element={<Recommendations />} />
          <Route path="/ai-consultant" element={<AIConsultant />} />
          <Route path="/multi-region" element={<MultiRegion />} />
          <Route path="/analytics" element={<Analytics />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}

export default App;
