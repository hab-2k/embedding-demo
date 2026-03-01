import { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { getHealth } from "../api/client";

const NAV_ITEMS = [
  { path: "/", label: "Search" },
  { path: "/themes", label: "Themes" },
  { path: "/risk", label: "Risk Flags" },
  { path: "/ingest", label: "Ingest" },
];

export default function NavBar() {
  const location = useLocation();
  const [chunksIndexed, setChunksIndexed] = useState<number | null>(null);

  useEffect(() => {
    getHealth()
      .then((h) => setChunksIndexed(h.chunks_indexed))
      .catch(() => setChunksIndexed(null));
  }, [location.pathname]);

  return (
    <nav className="bg-lloyds-green">
      <div className="max-w-7xl mx-auto px-6 flex items-center justify-between h-16">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-white rounded-sm flex items-center justify-center">
            <svg viewBox="0 0 24 24" className="w-5 h-5 text-lloyds-green" fill="currentColor">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z" />
            </svg>
          </div>
          <span className="text-white font-semibold text-lg tracking-tight">
            Transcript Search
          </span>
        </div>

        <div className="flex items-center gap-1">
          {NAV_ITEMS.map((item) => {
            const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-white/20 text-white"
                    : "text-white/75 hover:text-white hover:bg-white/10"
                }`}
              >
                {item.label}
              </Link>
            );
          })}
        </div>

        <div className="text-white/80 text-sm">
          {chunksIndexed !== null ? (
            <span className="bg-white/15 px-3 py-1.5 rounded-full text-xs font-medium">
              {chunksIndexed.toLocaleString()} chunks indexed
            </span>
          ) : (
            <span className="bg-red-500/30 px-3 py-1.5 rounded-full text-xs font-medium">
              Disconnected
            </span>
          )}
        </div>
      </div>
    </nav>
  );
}
