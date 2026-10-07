'use client';

import React from 'react';
import Link from 'next/link';
import { Mascot } from '@/components/mascot/Mascot';

export default function NotFound() {
  return (
    <div className="min-h-screen bg-white flex flex-col items-center justify-center p-6 text-center select-none max-w-md mx-auto">
      <Mascot expression="worried" size="xl" />

      <h1 className="text-3xl font-black text-duo-gray-900 mt-6 mb-2">
        Page Not Found
      </h1>
      <p className="text-sm font-bold text-duo-gray-300 mb-8">
        Even Duo couldn&apos;t find this page. Let&apos;s get you back on track with your lessons!
      </p>

      <Link
        href="/learn"
        className="w-full py-4 bg-duo-green hover:bg-duo-green-light active:translate-y-1 text-white font-black rounded-2xl shadow-[0_4px_0_0_#46a302] active:shadow-none uppercase tracking-wider text-sm transition-all"
      >
        BACK TO LEARN
      </Link>
    </div>
  );
}
