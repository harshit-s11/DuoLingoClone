'use client';

import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchProfile } from '@/lib/api/client';
import { AppShell } from '@/components/layout/AppShell';
import { Mascot } from '@/components/mascot/Mascot';

export default function ProfilePage() {
  const { data: profile, isLoading, isError, error } = useQuery({
    queryKey: ['profile'],
    queryFn: fetchProfile,
  });

  return (
    <AppShell>
      <div className="w-full max-w-xl mx-auto space-y-8 select-none">
        {/* Profile Card Header */}
        <div className="bg-white border-2 border-duo-gray-200 rounded-3xl p-6 shadow-sm flex flex-col sm:flex-row items-center sm:items-start gap-6 text-center sm:text-left">
          <div className="w-24 h-24 rounded-full bg-duo-green/10 border-2 border-duo-green flex items-center justify-center p-2 flex-shrink-0">
            <Mascot expression="happy" size="md" />
          </div>

          <div className="flex-1">
            <h1 className="text-2xl font-black text-duo-gray-900">
              {profile?.user.username || 'Learner'}
            </h1>
            <p className="text-xs font-bold text-duo-gray-300 mt-0.5">
              Joined {profile?.user.created_at ? new Date(profile.user.created_at).toLocaleDateString() : 'Recently'}
            </p>

            <div className="mt-4 flex flex-wrap gap-2 justify-center sm:justify-start">
              <span className="px-3 py-1 bg-duo-green/15 text-duo-green font-black rounded-xl text-xs flex items-center gap-1.5">
                <span>🇪🇸</span> Spanish Learner
              </span>
              <span className="px-3 py-1 bg-duo-yellow/20 text-duo-yellow-dark font-black rounded-xl text-xs flex items-center gap-1.5">
                <span>🛡️</span> Silver League
              </span>
            </div>
          </div>
        </div>

        {/* Loading */}
        {isLoading && (
          <div className="py-12 flex flex-col items-center justify-center text-center">
            <Mascot expression="thinking" size="lg" />
            <p className="mt-4 text-base font-black text-duo-gray-300 animate-pulse">
              Loading your profile stats...
            </p>
          </div>
        )}

        {/* Error */}
        {isError && (
          <div className="py-8 text-center bg-duo-red/10 border-2 border-duo-red/30 rounded-3xl p-6">
            <Mascot expression="worried" size="md" />
            <h3 className="mt-2 text-base font-black text-duo-red">Could not load profile</h3>
            <p className="text-xs font-bold text-duo-gray-700 mt-1">
              {error instanceof Error ? error.message : 'Please try again later.'}
            </p>
          </div>
        )}

        {/* Statistics Grid */}
        {profile?.user && (
          <section>
            <h2 className="text-lg font-black text-duo-gray-900 mb-3">Statistics</h2>
            <div className="grid grid-cols-2 gap-3.5">
              {/* Streak */}
              <div className="bg-white border-2 border-duo-gray-200 rounded-2xl p-4 flex items-center gap-3.5 shadow-sm">
                <span className="text-3xl">🔥</span>
                <div>
                  <span className="text-xl font-black text-duo-gray-900 block leading-tight">
                    {profile.user.streak_current}
                  </span>
                  <span className="text-xs font-black uppercase tracking-wider text-duo-gray-300">
                    Day streak
                  </span>
                </div>
              </div>

              {/* Total XP */}
              <div className="bg-white border-2 border-duo-gray-200 rounded-2xl p-4 flex items-center gap-3.5 shadow-sm">
                <span className="text-3xl">⚡</span>
                <div>
                  <span className="text-xl font-black text-duo-gray-900 block leading-tight">
                    {profile.user.xp_total}
                  </span>
                  <span className="text-xs font-black uppercase tracking-wider text-duo-gray-300">
                    Total XP
                  </span>
                </div>
              </div>

              {/* Total Crowns */}
              <div className="bg-white border-2 border-duo-gray-200 rounded-2xl p-4 flex items-center gap-3.5 shadow-sm">
                <span className="text-3xl">👑</span>
                <div>
                  <span className="text-xl font-black text-duo-gray-900 block leading-tight">
                    {profile.user.total_crowns}
                  </span>
                  <span className="text-xs font-black uppercase tracking-wider text-duo-gray-300">
                    Crowns earned
                  </span>
                </div>
              </div>

              {/* Quests/Achievements */}
              <div className="bg-white border-2 border-duo-gray-200 rounded-2xl p-4 flex items-center gap-3.5 shadow-sm">
                <span className="text-3xl">🎯</span>
                <div>
                  <span className="text-xl font-black text-duo-gray-900 block leading-tight">
                    {profile.unlocked_achievements_count} / 8
                  </span>
                  <span className="text-xs font-black uppercase tracking-wider text-duo-gray-300">
                    Badges unlocked
                  </span>
                </div>
              </div>
            </div>
          </section>
        )}

        {/* Recent Daily Activity */}
        {profile?.recent_activity && profile.recent_activity.length > 0 && (
          <section>
            <h2 className="text-lg font-black text-duo-gray-900 mb-3">Recent Activity</h2>
            <div className="space-y-2">
              {profile.recent_activity.map((item) => (
                <div
                  key={item.activity_date}
                  className="bg-white border-2 border-duo-gray-200 rounded-2xl p-4 flex items-center justify-between shadow-sm"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-duo-green/15 text-duo-green flex items-center justify-center font-black text-sm">
                      ✓
                    </div>
                    <div>
                      <span className="font-black text-sm text-duo-gray-900 block">
                        {item.activity_date}
                      </span>
                      <span className="text-xs font-bold text-duo-gray-300">
                        {item.lessons_completed} {item.lessons_completed === 1 ? 'lesson' : 'lessons'} finished
                      </span>
                    </div>
                  </div>

                  <span className="text-sm font-black text-duo-yellow-dark">
                    +{item.xp_earned} XP
                  </span>
                </div>
              ))}
            </div>
          </section>
        )}
      </div>
    </AppShell>
  );
}
