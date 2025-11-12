'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { useApi } from '@/lib/useApi';
import ThemeToggle from './ThemeToggle';
import CreditBalance from './CreditBalance';
import {
  Home,
  MessageSquare,
  Folder,
  Zap,
  Plug,
  BarChart,
  Bell,
  Settings,
  LogOut,
  Menu,
  X,
  User,
  Key,
  ChevronDown,
  Cpu,
  FileText,
  TrendingUp,
  Coins,
  Mail,
} from 'lucide-react';

interface NavItem {
  href: string;
  label: string;
  icon: React.ElementType;
}

export default function Navigation() {
  const pathname = usePathname();
  const router = useRouter();
  const api = useApi();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);
  const [userEmail, setUserEmail] = useState<string | null>(null);

  // Load user info
  useEffect(() => {
    // Check authentication status
    const checkAuth = async () => {
      const { isAuthenticated, user } = await api.checkAuth();
      if (isAuthenticated && user) {
        setUserEmail(user.email || 'user@example.com');
      } else {
        // Try legacy localStorage token
        const token = localStorage.getItem('token');
        if (token) {
          try {
            const payload = JSON.parse(atob(token.split('.')[1]));
            setUserEmail(payload.email || 'user@example.com');
          } catch {
            setUserEmail('user@example.com');
          }
        }
      }
    };
    checkAuth();
  }, []);

  const navItems: NavItem[] = [
    { href: '/', label: 'Dashboard', icon: Home },
    { href: '/chat', label: 'Chat', icon: MessageSquare },
    { href: '/admin/inbox', label: 'Inbox', icon: Mail },
    { href: '/projects', label: 'Projects', icon: Folder },
    { href: '/agents', label: 'Agents', icon: Cpu },
    { href: '/workflows', label: 'Workflows', icon: Zap },
    { href: '/integrations', label: 'Integrations', icon: Plug },
    { href: '/admin/doc-analyzer', label: 'Doc Analyzer', icon: FileText },
    { href: '/credits', label: 'Credits', icon: Coins },
    { href: '/blog', label: 'Blog', icon: FileText },
    { href: '/admin/blog', label: 'Blog Admin', icon: FileText },
    { href: '/admin/analytics', label: 'Analytics', icon: TrendingUp },
  ];

  const isActive = (href: string) => {
    if (href === '/') return pathname === '/';
    return pathname.startsWith(href);
  };

  const handleLogout = async () => {
    try {
      // Use the new logout method that clears cookies
      await api.logout();
    } catch (error) {
      console.error('Logout error:', error);
      // Fallback to manual redirect
      router.push('/login');
    }
  };

  // Close mobile menu when route changes
  useEffect(() => {
    setIsMobileMenuOpen(false);
  }, [pathname]);

  // Close dropdowns when clicking outside
  useEffect(() => {
    const handleClickOutside = () => {
      setIsUserMenuOpen(false);
    };

    if (isUserMenuOpen) {
      document.addEventListener('click', handleClickOutside);
      return () => document.removeEventListener('click', handleClickOutside);
    }
  }, [isUserMenuOpen]);

  return (
    <>
      {/* Desktop Sidebar */}
      <aside className="hidden md:fixed md:inset-y-0 md:left-0 md:flex md:w-60 md:flex-col">
        <div className="flex min-h-0 flex-1 flex-col bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-800 transition-colors duration-200">
          {/* Logo/Brand */}
          <div className="flex h-16 shrink-0 items-center px-6 border-b border-gray-200 dark:border-gray-800 transition-colors">
            <h1 className="text-xl font-bold bg-gradient-to-r from-blue-500 to-purple-600 bg-clip-text text-transparent">
              Autopilot Core
            </h1>
          </div>

          {/* Navigation Links */}
          <nav className="flex-1 space-y-1 px-3 py-4 overflow-y-auto">
            {navItems.map((item) => {
              const Icon = item.icon;
              const active = isActive(item.href);

              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-white dark:focus:ring-offset-gray-900 ${
                    active
                      ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg shadow-blue-500/20'
                      : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100 dark:text-gray-400 dark:hover:text-white dark:hover:bg-gray-800'
                  }`}
                  aria-current={active ? 'page' : undefined}
                >
                  <Icon className="w-5 h-5 shrink-0" aria-hidden="true" />
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </nav>

          {/* Bottom User Section */}
          <div className="border-t border-gray-200 dark:border-gray-800 p-4 transition-colors space-y-3">
            {/* Credit Balance Widget */}
            <div className="px-1">
              <CreditBalance />
            </div>

            {/* User Info */}
            <div className="flex items-center gap-3 px-3 py-2 text-sm text-gray-600 dark:text-gray-400">
              <User className="w-5 h-5" aria-hidden="true" />
              <span className="truncate">{userEmail || 'Loading...'}</span>
            </div>
          </div>
        </div>
      </aside>

      {/* Top Bar */}
      <header className="fixed top-0 left-0 right-0 z-40 md:left-60">
        <div className="flex h-16 items-center justify-between gap-4 bg-white/80 dark:bg-gray-950/80 backdrop-blur-xl border-b border-gray-200 dark:border-gray-800 px-4 md:px-6 transition-colors duration-200">
          {/* Mobile Menu Button */}
          <button
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            className="md:hidden p-2 rounded-lg text-gray-600 hover:text-gray-900 hover:bg-gray-100 dark:text-gray-400 dark:hover:text-white dark:hover:bg-gray-800 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-white dark:focus:ring-offset-gray-950"
            aria-label="Toggle mobile menu"
            aria-expanded={isMobileMenuOpen}
          >
            <Menu className="w-6 h-6" />
          </button>

          {/* Page Title (Desktop) */}
          <div className="hidden md:block">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white transition-colors">
              {navItems.find((item) => isActive(item.href))?.label || 'Dashboard'}
            </h2>
          </div>

          {/* Logo (Mobile) */}
          <h1 className="md:hidden text-lg font-bold bg-gradient-to-r from-blue-400 to-purple-600 bg-clip-text text-transparent">
            Autopilot
          </h1>

          {/* Right Side Actions */}
          <div className="flex items-center gap-2">
            {/* Theme Toggle */}
            <ThemeToggle />

            {/* Notifications */}
            <button
              className="p-2 rounded-lg text-gray-600 hover:text-gray-900 hover:bg-gray-100 dark:text-gray-400 dark:hover:text-white dark:hover:bg-gray-800 transition-colors relative focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-white dark:focus:ring-offset-gray-950"
              aria-label="Notifications"
            >
              <Bell className="w-5 h-5" />
              <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-blue-500 rounded-full" aria-hidden="true"></span>
            </button>

            {/* Settings */}
            <Link
              href="/settings"
              className="p-2 rounded-lg text-gray-600 hover:text-gray-900 hover:bg-gray-100 dark:text-gray-400 dark:hover:text-white dark:hover:bg-gray-800 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-white dark:focus:ring-offset-gray-950"
              aria-label="Settings"
            >
              <Settings className="w-5 h-5" />
            </Link>

            {/* User Menu */}
            <div className="relative">
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  setIsUserMenuOpen(!isUserMenuOpen);
                }}
                className="flex items-center gap-2 px-3 py-2 rounded-lg text-gray-400 hover:text-white hover:bg-gray-800 transition-colors"
              >
                <div className="w-8 h-8 rounded-full bg-gradient-to-r from-blue-500 to-purple-600 flex items-center justify-center text-white text-sm font-medium">
                  {userEmail?.charAt(0).toUpperCase() || 'U'}
                </div>
                <ChevronDown className="w-4 h-4 hidden md:block" />
              </button>

              {/* Dropdown Menu */}
              {isUserMenuOpen && (
                <div className="absolute right-0 mt-2 w-56 bg-gray-900 border border-gray-800 rounded-lg shadow-xl overflow-hidden">
                  <div className="px-4 py-3 border-b border-gray-800">
                    <p className="text-sm text-gray-400">Signed in as</p>
                    <p className="text-sm font-medium text-white truncate">{userEmail}</p>
                  </div>

                  <div className="py-1">
                    <Link
                      href="/settings/account"
                      className="flex items-center gap-3 px-4 py-2 text-sm text-gray-400 hover:text-white hover:bg-gray-800 transition-colors"
                      onClick={() => setIsUserMenuOpen(false)}
                    >
                      <User className="w-4 h-4" />
                      Account Settings
                    </Link>

                    <Link
                      href="/settings/api-keys"
                      className="flex items-center gap-3 px-4 py-2 text-sm text-gray-400 hover:text-white hover:bg-gray-800 transition-colors"
                      onClick={() => setIsUserMenuOpen(false)}
                    >
                      <Key className="w-4 h-4" />
                      API Keys
                    </Link>
                  </div>

                  <div className="border-t border-gray-800 py-1">
                    <button
                      onClick={handleLogout}
                      className="flex w-full items-center gap-3 px-4 py-2 text-sm text-red-400 hover:text-red-300 hover:bg-gray-800 transition-colors"
                    >
                      <LogOut className="w-4 h-4" />
                      Logout
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Mobile Sidebar */}
      {isMobileMenuOpen && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 bg-black/50 z-50 md:hidden"
            onClick={() => setIsMobileMenuOpen(false)}
          />

          {/* Slide-in Sidebar */}
          <aside className="fixed inset-y-0 left-0 z-50 w-64 bg-gray-900 border-r border-gray-800 md:hidden transform transition-transform">
            {/* Header */}
            <div className="flex h-16 items-center justify-between px-6 border-b border-gray-800">
              <h1 className="text-xl font-bold bg-gradient-to-r from-blue-400 to-purple-600 bg-clip-text text-transparent">
                Autopilot Core
              </h1>
              <button
                onClick={() => setIsMobileMenuOpen(false)}
                className="p-2 rounded-lg text-gray-400 hover:text-white hover:bg-gray-800 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Navigation Links */}
            <nav className="flex-1 space-y-1 px-3 py-4 overflow-y-auto">
              {navItems.map((item) => {
                const Icon = item.icon;
                const active = isActive(item.href);

                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                      active
                        ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg shadow-blue-500/20'
                        : 'text-gray-400 hover:text-white hover:bg-gray-800'
                    }`}
                  >
                    <Icon className="w-5 h-5 shrink-0" />
                    <span>{item.label}</span>
                  </Link>
                );
              })}
            </nav>

            {/* User Section */}
            <div className="border-t border-gray-800 p-4">
              <div className="flex items-center gap-3 px-3 py-2 mb-2 text-sm text-gray-400">
                <User className="w-5 h-5" />
                <span className="truncate">{userEmail || 'Loading...'}</span>
              </div>

              <button
                onClick={handleLogout}
                className="flex w-full items-center gap-3 px-3 py-2 text-sm text-red-400 hover:text-red-300 hover:bg-gray-800 rounded-lg transition-colors"
              >
                <LogOut className="w-4 h-4" />
                Logout
              </button>
            </div>
          </aside>
        </>
      )}

      {/* Content Spacer for Desktop */}
      <div className="hidden md:block md:pl-60">
        <div className="h-16" /> {/* Top bar height spacer */}
      </div>

      {/* Content Spacer for Mobile */}
      <div className="md:hidden">
        <div className="h-16" /> {/* Top bar height spacer */}
      </div>
    </>
  );
}













