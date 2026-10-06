'use client';

import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { useUserStore } from '@/stores/use-user-store';
import { fetchHealth } from '@/lib/api/client';

export default function HomePage() {
  const { userId, soundEnabled, toggleSound } = useUserStore();

  const { data: health, isLoading, isError, error } = useQuery({
    queryKey: ['health'],
    queryFn: fetchHealth,
  });

  return (
    <main className="min-h-screen bg-slate-50 flex flex-col items-center justify-center p-6 text-duo-gray-700">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="w-full max-w-lg bg-white border-2 border-duo-gray-200 rounded-3xl p-8 shadow-sm"
      >
        <div className="flex items-center gap-3 mb-6">
          <div className="w-12 h-12 bg-duo-green rounded-2xl flex items-center justify-center text-white text-2xl font-black shadow-[0_4px_0_0_#46a302]">
            D
          </div>
          <div>
            <h1 className="text-2xl font-black tracking-tight text-duo-gray-900">Duolingo Clone</h1>
            <p className="text-sm font-bold text-duo-gray-300">Phase 0 Scaffold & Contracts</p>
          </div>
        </div>

        {/* Backend health status pill */}
        <div className="bg-duo-gray-100 rounded-2xl p-4 mb-6 border border-duo-gray-200">
          <div className="text-xs font-extrabold uppercase tracking-wider text-duo-gray-300 mb-2">
            Backend Health Status
          </div>
          {isLoading && (
            <div className="text-sm font-bold text-duo-blue flex items-center gap-2">
              <span className="animate-spin">⏳</span> Connecting to /api/health...
            </div>
          )}
          {isError && (
            <div className="text-sm font-bold text-duo-red">
              Error connecting: {error instanceof Error ? error.message : 'Unknown error'}
            </div>
          )}
          {health && (
            <div className="space-y-1 text-sm font-bold">
              <div className="flex justify-between">
                <span className="text-duo-gray-700">API Status:</span>
                <span className="text-duo-green uppercase font-black">{health.status}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-duo-gray-700">Database:</span>
                <span className="text-duo-blue font-black">{health.database}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-duo-gray-700">Version:</span>
                <span className="text-duo-gray-700">{health.version}</span>
              </div>
            </div>
          )}
        </div>

        {/* Zustand client state demo */}
        <div className="flex items-center justify-between py-3 border-y border-duo-gray-200 mb-6">
          <span className="text-sm font-bold text-duo-gray-700">User Session (X-User-Id):</span>
          <span className="px-3 py-1 bg-duo-green/10 text-duo-green font-extrabold rounded-full text-xs">
            User #{userId}
          </span>
        </div>

        {/* 3D Tactile Buttons */}
        <div className="space-y-3">
          <button
            onClick={toggleSound}
            className="w-full py-3 px-4 bg-duo-green hover:bg-duo-green-light active:translate-y-1 text-white font-extrabold rounded-2xl shadow-[0_4px_0_0_#46a302] active:shadow-none transition-all uppercase tracking-wide text-sm"
          >
            Sound Effects: {soundEnabled ? 'Enabled 🔊' : 'Muted 🔇'}
          </button>
        </div>

        <div className="mt-8 pt-4 border-t border-duo-gray-200 text-center">
          <p className="text-xs font-bold text-duo-gray-300">
            Phase 0 Gate Complete: Monorepo &middot; Next.js &middot; FastAPI &middot; SQLite
          </p>
        </div>
      </motion.div>
    </main>
  );
}
