'use client';

import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  fetchSettings,
  updateSettings,
  advanceDebugDay,
  resetDemo,
  unlockAll,
} from '@/lib/api/client';
import { useUserStore } from '@/stores/use-user-store';
import { AppShell } from '@/components/layout/AppShell';

const TIMEZONES = [
  'UTC',
  'America/New_York',
  'America/Los_Angeles',
  'America/Chicago',
  'Europe/London',
  'Europe/Madrid',
  'Europe/Paris',
  'Asia/Tokyo',
  'Asia/Kolkata',
  'Australia/Sydney',
];

export default function SettingsPage() {
  const queryClient = useQueryClient();
  const { soundEnabled, toggleSound } = useUserStore();

  const { data: settings, isLoading } = useQuery({
    queryKey: ['settings'],
    queryFn: fetchSettings,
  });

  const [selectedTz, setSelectedTz] = useState('UTC');
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  useEffect(() => {
    if (settings?.timezone) {
      setSelectedTz(settings.timezone);
    }
  }, [settings]);

  const timezoneMutation = useMutation({
    mutationFn: (tz: string) => updateSettings(tz),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings'] });
      setStatusMessage('Timezone updated successfully!');
      setTimeout(() => setStatusMessage(null), 3000);
    },
    onError: (err: Error) => {
      setStatusMessage(`Error: ${err.message}`);
    },
  });

  const advanceDayMutation = useMutation({
    mutationFn: () => advanceDebugDay(1),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['settings'] });
      queryClient.invalidateQueries({ queryKey: ['me'] });
      queryClient.invalidateQueries({ queryKey: ['profile'] });
      queryClient.invalidateQueries({ queryKey: ['leaderboard'] });
      setStatusMessage(`Advanced day! Logical date now: ${data.logical_now}`);
      setTimeout(() => setStatusMessage(null), 4000);
    },
    onError: (err: Error) => {
      setStatusMessage(`Error: ${err.message}`);
    },
  });

  const resetDemoMutation = useMutation({
    mutationFn: () => resetDemo(),
    onSuccess: () => {
      queryClient.invalidateQueries();
      setStatusMessage('Reset demo state to pristine seed data!');
      setTimeout(() => setStatusMessage(null), 4000);
    },
    onError: (err: Error) => {
      setStatusMessage(`Error: ${err.message}`);
    },
  });

  const unlockAllMutation = useMutation({
    mutationFn: () => unlockAll(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['course-path'] });
      setStatusMessage('Unlocked all curriculum lessons!');
      setTimeout(() => setStatusMessage(null), 4000);
    },
    onError: (err: Error) => {
      setStatusMessage(`Error: ${err.message}`);
    },
  });

  return (
    <AppShell>
      <div className="w-full max-w-xl mx-auto space-y-8 select-none">
        <div>
          <h1 className="text-2xl font-black text-duo-gray-900">Settings</h1>
          <p className="text-xs font-bold text-duo-gray-300 mt-0.5">
            Preferences, account, and demo testing tools
          </p>
        </div>

        {statusMessage && (
          <div className="p-4 bg-duo-blue/15 border-2 border-duo-blue rounded-2xl text-xs font-black text-duo-blue flex items-center justify-between">
            <span>{statusMessage}</span>
            <button onClick={() => setStatusMessage(null)}>✕</button>
          </div>
        )}

        {/* General Preferences */}
        <section className="bg-white border-2 border-duo-gray-200 rounded-3xl p-6 shadow-sm space-y-6">
          <h2 className="text-base font-black text-duo-gray-900 uppercase tracking-wider text-xs">
            Preferences
          </h2>

          {/* Timezone */}
          <div>
            <label className="text-sm font-black text-duo-gray-700 block mb-2">
              Timezone
            </label>
            <div className="flex gap-3">
              <select
                disabled={isLoading}
                value={selectedTz}
                onChange={(e) => setSelectedTz(e.target.value)}
                className="flex-1 p-3.5 bg-duo-gray-100/50 border-2 border-duo-gray-200 rounded-2xl text-sm font-bold text-duo-gray-900 outline-none focus:border-duo-blue"
              >
                {TIMEZONES.map((tz) => (
                  <option key={tz} value={tz}>
                    {tz}
                  </option>
                ))}
              </select>
              <button
                disabled={timezoneMutation.isPending}
                onClick={() => timezoneMutation.mutate(selectedTz)}
                className="px-5 py-3.5 bg-duo-blue text-white font-black text-xs uppercase tracking-wider rounded-2xl border-2 border-duo-blue-dark shadow-[0_3px_0_0_#1899d6] active:translate-y-1 active:shadow-none transition-all"
              >
                {timezoneMutation.isPending ? 'Saving...' : 'SAVE'}
              </button>
            </div>
            {settings && (
              <p className="text-[11px] font-bold text-duo-gray-300 mt-1.5">
                Current date offset: {settings.date_offset_days} day(s)
              </p>
            )}
          </div>

          {/* Sound Effects */}
          <div className="flex items-center justify-between pt-4 border-t border-duo-gray-200">
            <div>
              <span className="text-sm font-black text-duo-gray-900 block">Sound Effects</span>
              <span className="text-xs font-bold text-duo-gray-300">Play feedback audio during lessons</span>
            </div>
            <button
              onClick={toggleSound}
              className={`px-4 py-2 rounded-xl font-black text-xs uppercase tracking-wider border-2 transition-all ${
                soundEnabled
                  ? 'bg-duo-green text-white border-duo-green-dark shadow-[0_2px_0_0_#46a302]'
                  : 'bg-duo-gray-100 text-duo-gray-300 border-duo-gray-200'
              }`}
            >
              {soundEnabled ? 'ON 🔊' : 'MUTED 🔇'}
            </button>
          </div>
        </section>

        {/* Demo & Verification Actions */}
        <section className="bg-white border-2 border-duo-gray-200 rounded-3xl p-6 shadow-sm space-y-4">
          <div className="flex items-center gap-2">
            <span className="text-lg">🛠️</span>
            <h2 className="text-xs font-black uppercase tracking-wider text-duo-gray-300">
              Demo & Debugging Controls
            </h2>
          </div>
          <p className="text-xs font-bold text-duo-gray-700">
            Tools provided for assignment grading to test time progression, streak maintenance, and lesson states.
          </p>

          <div className="space-y-3 pt-2">
            {/* Advance Day */}
            <button
              onClick={() => advanceDayMutation.mutate()}
              disabled={advanceDayMutation.isPending}
              className="w-full py-3.5 px-4 bg-duo-orange text-white font-black rounded-2xl border-2 border-duo-orange-dark shadow-[0_3px_0_0_#e08500] active:translate-y-1 active:shadow-none flex items-center justify-between text-xs uppercase tracking-wider transition-all"
            >
              <span>ADVANCE LOGICAL DAY (+1 DAY)</span>
              <span>📅 +1D</span>
            </button>

            {/* Unlock All */}
            <button
              onClick={() => unlockAllMutation.mutate()}
              disabled={unlockAllMutation.isPending}
              className="w-full py-3.5 px-4 bg-duo-blue text-white font-black rounded-2xl border-2 border-duo-blue-dark shadow-[0_3px_0_0_#1899d6] active:translate-y-1 active:shadow-none flex items-center justify-between text-xs uppercase tracking-wider transition-all"
            >
              <span>UNLOCK ALL LESSONS (EVALUATION MODE)</span>
              <span>🔓 ALL</span>
            </button>

            {/* Reset Demo */}
            <button
              onClick={() => resetDemoMutation.mutate()}
              disabled={resetDemoMutation.isPending}
              className="w-full py-3.5 px-4 bg-white text-duo-red font-black rounded-2xl border-2 border-duo-gray-200 hover:bg-duo-red/5 active:translate-y-1 flex items-center justify-between text-xs uppercase tracking-wider transition-all"
            >
              <span>RESET DEMO DATA TO PRISTINE SEED</span>
              <span>🔄 RESET</span>
            </button>
          </div>
        </section>
      </div>
    </AppShell>
  );
}
