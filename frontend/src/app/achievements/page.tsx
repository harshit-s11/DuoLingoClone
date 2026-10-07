'use client';

import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchAchievements } from '@/lib/api/client';
import { AppShell } from '@/components/layout/AppShell';
import { Mascot } from '@/components/mascot/Mascot';

export default function AchievementsPage() {
  const { data: achievements, isLoading, isError, error } = useQuery({
    queryKey: ['achievements'],
    queryFn: fetchAchievements,
  });

  return (
    <AppShell>
      <div className="w-full max-w-xl mx-auto space-y-6 select-none">
        <div>
          <h1 className="text-2xl font-black text-duo-gray-900">Achievements</h1>
          <p className="text-xs font-bold text-duo-gray-300 mt-0.5">
            Complete milestones, earn XP, and unlock special badges!
          </p>
        </div>

        {/* Loading */}
        {isLoading && (
          <div className="py-16 flex flex-col items-center justify-center text-center">
            <Mascot expression="thinking" size="lg" />
            <p className="mt-4 text-base font-black text-duo-gray-300 animate-pulse">
              Checking your achievements...
            </p>
          </div>
        )}

        {/* Error */}
        {isError && (
          <div className="py-8 text-center bg-duo-red/10 border-2 border-duo-red/30 rounded-3xl p-6">
            <Mascot expression="worried" size="md" />
            <h3 className="mt-2 text-base font-black text-duo-red">Could not load achievements</h3>
            <p className="text-xs font-bold text-duo-gray-700 mt-1">
              {error instanceof Error ? error.message : 'Please try again later.'}
            </p>
          </div>
        )}

        {/* Achievement List */}
        {achievements && (
          <div className="grid grid-cols-1 gap-3.5">
            {achievements.map((item) => {
              const percent = Math.min(
                100,
                Math.round((item.current_value / (item.target_value || 1)) * 100)
              );

              return (
                <div
                  key={item.id}
                  className={`p-4 rounded-2xl border-2 flex items-center gap-4 transition-all ${
                    item.is_unlocked
                      ? 'bg-white border-duo-yellow/60 shadow-[0_3px_0_0_#e5a400]'
                      : 'bg-duo-gray-100/40 border-duo-gray-200 opacity-80'
                  }`}
                >
                  {/* Badge Icon */}
                  <div
                    className={`w-14 h-14 rounded-2xl border-2 flex items-center justify-center text-2xl flex-shrink-0 ${
                      item.is_unlocked
                        ? 'bg-duo-yellow/20 border-duo-yellow text-duo-yellow-dark shadow-sm'
                        : 'bg-duo-gray-200/60 border-duo-gray-300 text-duo-gray-300 grayscale'
                    }`}
                  >
                    <span>{item.badge_icon || '🏅'}</span>
                  </div>

                  {/* Details */}
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-1">
                      <h3
                        className={`font-black text-base leading-tight ${
                          item.is_unlocked ? 'text-duo-gray-900' : 'text-duo-gray-700'
                        }`}
                      >
                        {item.title}
                      </h3>
                      {item.is_unlocked ? (
                        <span className="text-[10px] font-black uppercase tracking-wider bg-duo-yellow/20 text-duo-yellow-dark px-2 py-0.5 rounded-full">
                          UNLOCKED
                        </span>
                      ) : (
                        <span className="text-xs font-black text-duo-gray-300">
                          {item.current_value} / {item.target_value}
                        </span>
                      )}
                    </div>

                    <p className="text-xs font-bold text-duo-gray-300 mb-2.5">
                      {item.description}
                    </p>

                    {/* Progress Bar */}
                    <div className="w-full h-3 bg-duo-gray-200 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all ${
                          item.is_unlocked ? 'bg-duo-yellow' : 'bg-duo-blue'
                        }`}
                        style={{ width: `${percent}%` }}
                      />
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </AppShell>
  );
}
