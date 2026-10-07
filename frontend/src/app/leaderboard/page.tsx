'use client';

import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchLeaderboard } from '@/lib/api/client';
import { AppShell } from '@/components/layout/AppShell';
import { Mascot } from '@/components/mascot/Mascot';

export default function LeaderboardPage() {
  const { data: leaderboard, isLoading, isError, error } = useQuery({
    queryKey: ['leaderboard'],
    queryFn: fetchLeaderboard,
  });

  return (
    <AppShell>
      <div className="w-full max-w-xl mx-auto">
        {/* League Header Card */}
        <div className="bg-gradient-to-r from-duo-yellow-dark via-duo-yellow to-duo-orange text-white rounded-3xl p-6 shadow-[0_5px_0_0_#e5a400] mb-8 border-2 border-duo-yellow-dark text-center relative overflow-hidden">
          <div className="flex justify-center mb-3">
            <span className="text-4xl drop-shadow-md">🛡️</span>
          </div>
          <span className="text-xs font-black uppercase tracking-widest text-white/90">
            WEEKLY LEAGUE
          </span>
          <h1 className="text-2xl font-black mt-1">Silver League</h1>
          <p className="text-xs font-bold text-white/95 mt-1">
            Top 10 advance to Gold League next week. Complete lessons to earn XP!
          </p>
        </div>

        {/* Loading state */}
        {isLoading && (
          <div className="py-16 flex flex-col items-center justify-center text-center">
            <Mascot expression="thinking" size="lg" />
            <p className="mt-4 text-base font-black text-duo-gray-300 animate-pulse">
              Calculating league standings...
            </p>
          </div>
        )}

        {/* Error state */}
        {isError && (
          <div className="py-12 text-center bg-duo-red/10 border-2 border-duo-red/30 rounded-3xl p-6">
            <Mascot expression="worried" size="lg" />
            <h3 className="mt-3 text-lg font-black text-duo-red">Failed to load leaderboard</h3>
            <p className="text-xs font-bold text-duo-gray-700 mt-1">
              {error instanceof Error ? error.message : 'Please check your connection.'}
            </p>
          </div>
        )}

        {/* Rankings Table */}
        {leaderboard?.rankings && (
          <div className="space-y-2.5">
            {leaderboard.rankings.map((entry) => {
              const isCurrentUser = entry.is_current_user;
              const isTop3 = entry.rank <= 3;

              return (
                <div
                  key={`${entry.rank}-${entry.username}`}
                  className={`flex items-center justify-between p-4 rounded-2xl border-2 transition-all select-none ${
                    isCurrentUser
                      ? 'bg-duo-green/15 border-duo-green shadow-[0_3px_0_0_#46a302]'
                      : 'bg-white border-duo-gray-200 hover:border-duo-gray-300'
                  }`}
                >
                  <div className="flex items-center gap-4">
                    {/* Rank Badge */}
                    <div
                      className={`w-9 h-9 rounded-full flex items-center justify-center text-sm font-black ${
                        entry.rank === 1
                          ? 'bg-duo-yellow text-white shadow-sm'
                          : entry.rank === 2
                          ? 'bg-[#afafaf] text-white shadow-sm'
                          : entry.rank === 3
                          ? 'bg-duo-orange text-white shadow-sm'
                          : 'bg-duo-gray-100 text-duo-gray-300'
                      }`}
                    >
                      {entry.rank === 1 ? '🥇' : entry.rank === 2 ? '🥈' : entry.rank === 3 ? '🥉' : entry.rank}
                    </div>

                    {/* User Info */}
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-black text-base text-duo-gray-900">
                          {entry.username}
                        </span>
                        {isCurrentUser && (
                          <span className="text-[10px] font-black uppercase tracking-wider bg-duo-green text-white px-2 py-0.5 rounded-full">
                            YOU
                          </span>
                        )}
                      </div>
                      <span className="text-xs font-bold text-duo-gray-300">
                        {isTop3 ? 'Promotion Zone' : 'Safe Zone'}
                      </span>
                    </div>
                  </div>

                  {/* XP Total */}
                  <div className="flex items-center gap-1 font-black text-sm text-duo-gray-700">
                    <span className="text-duo-yellow-dark">⚡</span>
                    <span>{entry.xp_earned} XP</span>
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
