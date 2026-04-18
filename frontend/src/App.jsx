import React from 'react';
import { useState, useEffect } from 'react';
import { Moon, Sun, Monitor, ShoppingBag, LayoutDashboard, Menu, X } from 'lucide-react';
import CustomerPortal from './components/CustomerPortal';
import InternalDashboard from './components/InternalDashboard';

export default function App() {
  const [role, setRole] = useState('customer'); // 'customer' | 'internal'
  const [darkMode, setDarkMode] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  // Dark mode sync
  useEffect(() => {
    const stored = localStorage.getItem('darkMode');
    if (stored === 'true' || (!stored && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
      setDarkMode(true);
      document.documentElement.classList.add('dark');
    }
  }, []);

  const toggleDarkMode = () => {
    setDarkMode((prev) => {
      const next = !prev;
      localStorage.setItem('darkMode', String(next));
      document.documentElement.classList.toggle('dark', next);
      return next;
    });
  };

  return (
    <div className="min-h-screen transition-colors duration-200">
      {/* ── Top Navigation ── */}
      <nav className="sticky top-0 z-50 bg-white/90 dark:bg-gray-900/90 backdrop-blur-md
                      border-b border-gray-200 dark:border-gray-700 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 h-16 flex items-center gap-4">

          {/* Logo */}
          <div className="flex items-center gap-2 font-bold text-lg text-blue-600 dark:text-blue-400">
            <span className="text-2xl">🤖</span>
            <span>ABSA Portal</span>
          </div>

          {/* Spacer */}
          <div className="flex-1" />

          {/* Desktop Role Switcher */}
          <div className="hidden md:flex items-center bg-gray-100 dark:bg-gray-800 rounded-xl p-1 gap-1">
            <button
              onClick={() => setRole('customer')}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all
                ${role === 'customer'
                  ? 'bg-white dark:bg-gray-700 text-blue-600 dark:text-blue-400 shadow-sm'
                  : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
                }`}
            >
              <ShoppingBag size={16} />
              Customer View
            </button>
            <button
              onClick={() => setRole('internal')}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all
                ${role === 'internal'
                  ? 'bg-white dark:bg-gray-700 text-blue-600 dark:text-blue-400 shadow-sm'
                  : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
                }`}
            >
              <LayoutDashboard size={16} />
              Internal Dashboard
            </button>
          </div>

          {/* Dark Mode Toggle */}
          <button
            onClick={toggleDarkMode}
            className="p-2 rounded-xl bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700
                       text-gray-600 dark:text-gray-400 transition-colors"
            title={darkMode ? 'Switch to Light' : 'Switch to Dark'}
          >
            {darkMode ? <Sun size={18} /> : <Moon size={18} />}
          </button>

          {/* Mobile menu toggle */}
          <button
            className="md:hidden p-2 rounded-xl bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400"
            onClick={() => setMobileOpen((prev) => !prev)}
          >
            {mobileOpen ? <X size={18} /> : <Menu size={18} />}
          </button>
        </div>

        {/* Mobile Role Switcher */}
        {mobileOpen && (
          <div className="md:hidden px-4 pb-4 flex flex-col gap-2">
            <button
              onClick={() => { setRole('customer'); setMobileOpen(false); }}
              className={`flex items-center gap-2 px-4 py-3 rounded-xl text-sm font-medium transition-all
                ${role === 'customer'
                  ? 'bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300'
                  : 'text-gray-500 dark:text-gray-400'
                }`}
            >
              <ShoppingBag size={16} />
              Customer View
            </button>
            <button
              onClick={() => { setRole('internal'); setMobileOpen(false); }}
              className={`flex items-center gap-2 px-4 py-3 rounded-xl text-sm font-medium transition-all
                ${role === 'internal'
                  ? 'bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300'
                  : 'text-gray-500 dark:text-gray-400'
                }`}
            >
              <LayoutDashboard size={16} />
              Internal Dashboard
            </button>
          </div>
        )}
      </nav>

      {/* ── Page Content ── */}
      <main>
        {role === 'customer' ? <CustomerPortal /> : <InternalDashboard />}
      </main>
    </div>
  );
}
