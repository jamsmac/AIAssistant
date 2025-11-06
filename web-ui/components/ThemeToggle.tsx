'use client';

import { Moon, Sun } from 'lucide-react';
import { useContext } from 'react';
import { useTheme } from './ThemeProvider';

export default function ThemeToggle() {
  // Safely handle case where ThemeProvider is not available (e.g., during SSR or in error pages)
  try {
    const { theme, toggleTheme } = useTheme();

    return (
      <button
        onClick={toggleTheme}
        className="p-2 rounded-lg bg-white/5 hover:bg-white/10 dark:bg-white/5 dark:hover:bg-white/10 backdrop-blur-md border border-white/10 transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-gray-950"
        aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
        title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
      >
        {theme === 'dark' ? (
          <Sun className="w-5 h-5 text-yellow-400 transition-transform duration-200 hover:rotate-12" />
        ) : (
          <Moon className="w-5 h-5 text-blue-400 transition-transform duration-200 hover:-rotate-12" />
        )}
      </button>
    );
  } catch (error) {
    // Fallback: render nothing if theme context is not available
    return null;
  }
}
