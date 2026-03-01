import { BrowserRouter, Routes, Route } from "react-router-dom";
import NavBar from "./components/NavBar";
import SearchPage from "./pages/SearchPage";
import ThemesPage from "./pages/ThemesPage";
import RiskPage from "./pages/RiskPage";
import IngestPage from "./pages/IngestPage";

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-lloyds-seashell">
        <NavBar />
        <Routes>
          <Route path="/" element={<SearchPage />} />
          <Route path="/themes" element={<ThemesPage />} />
          <Route path="/risk" element={<RiskPage />} />
          <Route path="/ingest" element={<IngestPage />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}
