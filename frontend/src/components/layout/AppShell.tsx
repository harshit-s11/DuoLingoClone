'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { fetchMe } from '@/lib/api/client';
import { HeartRefillModal } from '../common/HeartRefillModal';
import { Mascot } from '../mascot/Mascot';

interface AppShellProps {
  children: React.ReactNode;
}

const navItems = [
  { href: '/learn', label: 'Learn', icon: '🏠' },
  { href: '/leaderboard', label: 'Leaderboard', icon: '🏆' },
  { href: '/achievements', label: 'Quests', icon: '🎯' },
  { href: '/profile', label: 'Profile', icon: '👤' },
  { href: '/settings', label: 'Settings', icon: '⚙️' },
];

export const AppShell: React.FC<AppShellProps> = ({ children }) => {
  const pathname = usePathname();
  const [isHeartModalOpen, setIsHeartModalOpen] = useState(false);

  const { data: user } = useQuery({
    queryKey: ['me'],
    queryFn: fetchMe,
    refetchInterval: 30000,
  });

  return (
    <div className="min-h-screen bg-white text-duo-gray-700 flex flex-col md:flex-row">
      {/* ================= Left Sidebar (Desktop) ================= */}
      <aside className="hidden md:flex flex-col w-64 lg:w-72 border-r-2 border-duo-gray-200 p-4 fixed h-screen z-30 bg-white select-none">
        {/* Brand */}
        <Link href="/learn" className="flex items-center gap-3 px-3 py-4 mb-6 group">
          <div className="w-10 h-10 bg-duo-green rounded-2xl flex items-center justify-center text-white text-xl font-black shadow-[0_3px_0_0_#46a302] group-hover:scale-105 transition-transform">
            LQ
          </div>
          <span className="text-2xl font-black tracking-tight text-duo-green">
            linguaquest
          </span>
        </Link>

        {/* Navigation Items */}
        <nav className="flex-1 space-y-2">
          {navItems.map((item) => {
            const isActive = pathname === item.href || (item.href === '/learn' && pathname.startsWith('/lesson'));
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-4 px-4 py-3.5 rounded-2xl font-black text-sm uppercase tracking-wider transition-all border-2 ${
                  isActive
                    ? 'bg-duo-blue/10 border-duo-blue text-duo-blue shadow-[0_2px_0_0_#1899d6]'
                    : 'border-transparent text-duo-gray-700 hover:bg-duo-gray-100 hover:text-duo-gray-900'
                }`}
              >
                <span className="text-2xl">{item.icon}</span>
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>

        {/* Bottom Mascot advice */}
        <div className="bg-duo-gray-100/80 border border-duo-gray-200 rounded-2xl p-4 text-xs font-bold text-duo-gray-700 mb-2">
          <div className="flex items-center gap-2 mb-1 text-duo-green font-black">
            <span>🦉</span>
            <span>DAILY TIP</span>
          </div>
          Practice 5 minutes every day to keep your Spanish memory sharp!
        </div>
      </aside>

      {/* ================= Main Content Container ================= */}
      <div className="flex-1 md:ml-64 lg:ml-72 flex flex-col min-h-screen">
        {/* Mobile Top Header */}
        <header className="md:hidden sticky top-0 z-20 bg-white/95 backdrop-blur-md border-b-2 border-duo-gray-200 px-4 py-3 flex items-center justify-between">
          <Link href="/learn" className="flex items-center gap-2">
            <span className="text-2xl">🇪🇸</span>
          </Link>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-1 font-black text-sm text-duo-orange">
              <span>🔥</span>
              <span>{user?.streak_current ?? 0}</span>
            </div>
            <div className="flex items-center gap-1 font-black text-sm text-duo-blue">
              <span>💎</span>
              <span>{user?.gems ?? 0}</span>
            </div>
            <button
              onClick={() => setIsHeartModalOpen(true)}
              className="flex items-center gap-1 font-black text-sm text-duo-red hover:opacity-80 active:scale-95 transition-transform"
            >
              <span>❤️</span>
              <span>{user?.hearts ?? 5}</span>
            </button>
          </div>
        </header>

        {/* Children Grid with Optional Right Rail on Large Screens */}
        <div className="flex-1 flex justify-center w-full max-w-7xl mx-auto">
          {/* Main Content Area */}
          <main className="flex-1 w-full max-w-2xl px-4 py-6 md:py-8 pb-24 md:pb-8">
            {children}
          </main>

          {/* Right Rail (Desktop) */}
          <aside className="hidden lg:block w-80 lg:w-88 p-6 space-y-6 select-none border-l-2 border-duo-gray-100">
            {/* Top Stats Bar */}
            <div className="flex items-center justify-between bg-white border-2 border-duo-gray-200 rounded-2xl p-3 shadow-sm">
              {/* Language */}
              <div className="flex items-center gap-2 px-2 py-1 rounded-xl hover:bg-duo-gray-100 cursor-pointer">
                <span className="text-2xl">🇪🇸</span>
              </div>

              {/* Streak */}
              <div
                title="Current Streak"
                className="flex items-center gap-1 font-black text-sm text-duo-orange px-2 py-1 rounded-xl hover:bg-duo-gray-100 cursor-default"
              >
                <span>🔥</span>
                <span>{user?.streak_current ?? 0}</span>
              </div>

              {/* Gems */}
              <div
                title="Gems Balance"
                className="flex items-center gap-1 font-black text-sm text-duo-blue px-2 py-1 rounded-xl hover:bg-duo-gray-100 cursor-default"
              >
                <span>💎</span>
                <span>{user?.gems ?? 0}</span>
              </div>

              {/* Hearts */}
              <button
                onClick={() => setIsHeartModalOpen(true)}
                title="Hearts (Click to refill)"
                className="flex items-center gap-1 font-black text-sm text-duo-red px-2 py-1 rounded-xl hover:bg-duo-red/10 cursor-pointer transition-colors"
              >
                <span>❤️</span>
                <span>{user?.hearts ?? 5}</span>
              </button>
            </div>

            {/* Motivation Mascot Box */}
            <div className="bg-gradient-to-br from-duo-green/10 to-duo-blue/10 border-2 border-duo-green/30 rounded-3xl p-5 relative overflow-hidden">
              <div className="flex items-start gap-4">
                <Mascot expression="happy" size="md" />
                <div>
                  <h3 className="font-black text-base text-duo-gray-900 leading-tight mb-1">
                    Supercharge your learning!
                  </h3>
                  <p className="text-xs font-bold text-duo-gray-700">
                    Complete your daily lesson to maintain your {user?.streak_current ?? 0}-day streak!
                  </p>
                </div>
              </div>
            </div>

            {/* Quick Links Card */}
            <div className="border-2 border-duo-gray-200 rounded-3xl p-5">
              <h4 className="font-black text-xs uppercase tracking-wider text-duo-gray-300 mb-3">
                Quick Navigation
              </h4>
              <div className="space-y-2">
                <Link
                  href="/leaderboard"
                  className="flex items-center justify-between p-2.5 rounded-2xl hover:bg-duo-gray-100 transition-colors font-black text-sm text-duo-gray-700"
                >
                  <div className="flex items-center gap-3">
                    <span className="text-xl">🏆</span>
                    <span>View Leaderboard</span>
                  </div>
                  <span className="text-xs text-duo-gray-300 font-extrabold">→</span>
                </Link>
                <Link
                  href="/achievements"
                  className="flex items-center justify-between p-2.5 rounded-2xl hover:bg-duo-gray-100 transition-colors font-black text-sm text-duo-gray-700"
                >
                  <div className="flex items-center gap-3">
                    <span className="text-xl">🎯</span>
                    <span>Quests & Badges</span>
                  </div>
                  <span className="text-xs text-duo-gray-300 font-extrabold">→</span>
                </Link>
                <Link
                  href="/settings"
                  className="flex items-center justify-between p-2.5 rounded-2xl hover:bg-duo-gray-100 transition-colors font-black text-sm text-duo-gray-700"
                >
                  <div className="flex items-center gap-3">
                    <span className="text-xl">⚙️</span>
                    <span>Demo Controls</span>
                  </div>
                  <span className="text-xs text-duo-gray-300 font-extrabold">→</span>
                </Link>
              </div>
            </div>
          </aside>
        </div>

        {/* Mobile Bottom Navigation Bar */}
        <nav className="md:hidden fixed bottom-0 left-0 right-0 z-30 bg-white border-t-2 border-duo-gray-200 flex justify-around py-2.5 px-1 shadow-lg">
          {navItems.map((item) => {
            const isActive = pathname === item.href || (item.href === '/learn' && pathname.startsWith('/lesson'));
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex flex-col items-center justify-center py-1 px-3 rounded-2xl transition-all ${
                  isActive ? 'text-duo-blue font-black' : 'text-duo-gray-300 hover:text-duo-gray-700'
                }`}
              >
                <span className="text-2xl">{item.icon}</span>
                <span className="text-[10px] font-extrabold uppercase tracking-tight mt-0.5">
                  {item.label}
                </span>
              </Link>
            );
          })}
        </nav>
      </div>

      {/* Heart Refill Modal */}
      <HeartRefillModal
        isOpen={isHeartModalOpen}
        onClose={() => setIsHeartModalOpen(false)}
        user={user}
      />
    </div>
  );
};
