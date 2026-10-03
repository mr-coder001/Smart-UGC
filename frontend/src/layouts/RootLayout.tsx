import React from "react";
import { Link, NavLink, Outlet } from "react-router-dom";
import {
  Image,
  UploadCloud,
  ShieldCheck,
  BarChart3,
  Sparkles,
  Layers,
} from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { apiService } from "../services/api";

export const RootLayout: React.FC = () => {
  const { data: health } = useQuery({
    queryKey: ["health"],
    queryFn: () => apiService.getHealth(),
    refetchInterval: 30000,
  });

  return (
    <div className="min-h-screen flex flex-col bg-slate-950 text-slate-100 selection:bg-indigo-500 selection:text-white">
      {/* Top Navigation */}
      <header className="sticky top-0 z-50 glass-panel border-b border-slate-800/80">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-8">
            <Link to="/" className="flex items-center space-x-3 group">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-cyan-400 flex items-center justify-center shadow-lg shadow-indigo-500/20 group-hover:scale-105 transition-transform duration-200">
                <Sparkles className="w-5 h-5 text-white" />
              </div>
              <div>
                <span className="font-bold text-lg tracking-tight bg-gradient-to-r from-white via-slate-100 to-slate-400 bg-clip-text text-transparent">
                  Claudinary
                </span>
                <span className="text-[10px] block font-mono text-cyan-400 uppercase tracking-widest -mt-1">
                  AI Media Platform
                </span>
              </div>
            </Link>

            <nav className="hidden md:flex items-center space-x-1">
              <NavLink
                to="/"
                className={({ isActive }) =>
                  `px-3 py-2 rounded-lg text-sm font-medium transition-colors flex items-center space-x-2 ${
                    isActive
                      ? "bg-slate-800 text-indigo-400"
                      : "text-slate-400 hover:text-slate-200 hover:bg-slate-900"
                  }`
                }
              >
                <Image className="w-4 h-4" />
                <span>Gallery</span>
              </NavLink>

              <NavLink
                to="/upload"
                className={({ isActive }) =>
                  `px-3 py-2 rounded-lg text-sm font-medium transition-colors flex items-center space-x-2 ${
                    isActive
                      ? "bg-slate-800 text-indigo-400"
                      : "text-slate-400 hover:text-slate-200 hover:bg-slate-900"
                  }`
                }
              >
                <UploadCloud className="w-4 h-4" />
                <span>Upload</span>
              </NavLink>

              <NavLink
                to="/admin/moderation"
                className={({ isActive }) =>
                  `px-3 py-2 rounded-lg text-sm font-medium transition-colors flex items-center space-x-2 ${
                    isActive
                      ? "bg-slate-800 text-indigo-400"
                      : "text-slate-400 hover:text-slate-200 hover:bg-slate-900"
                  }`
                }
              >
                <ShieldCheck className="w-4 h-4" />
                <span>Moderation</span>
              </NavLink>

              <NavLink
                to="/admin/stats"
                className={({ isActive }) =>
                  `px-3 py-2 rounded-lg text-sm font-medium transition-colors flex items-center space-x-2 ${
                    isActive
                      ? "bg-slate-800 text-indigo-400"
                      : "text-slate-400 hover:text-slate-200 hover:bg-slate-900"
                  }`
                }
              >
                <BarChart3 className="w-4 h-4" />
                <span>Metrics</span>
              </NavLink>
            </nav>
          </div>

          <div className="flex items-center space-x-4">
            {/* System Status Pill */}
            <div className="flex items-center space-x-2 px-3 py-1 rounded-full bg-slate-900 border border-slate-800 text-xs">
              <span
                className={`w-2 h-2 rounded-full ${
                  health?.status === "ok" ? "bg-emerald-400 animate-pulse" : "bg-amber-400"
                }`}
              />
              <span className="text-slate-300 font-mono">
                {health?.status === "ok" ? "API Online" : "Connecting..."}
              </span>
            </div>

            <Link
              to="/upload"
              className="hidden sm:inline-flex items-center space-x-2 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium transition shadow-lg shadow-indigo-600/25"
            >
              <UploadCloud className="w-4 h-4" />
              <span>New Asset</span>
            </Link>
          </div>
        </div>
      </header>

      {/* Main Content Body */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Outlet />
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-900 bg-slate-950/60 py-6 text-center text-xs text-slate-500">
        <p>Claudinary AI-Powered Asset Management Platform • Designed for Public Production</p>
      </footer>
    </div>
  );
};
