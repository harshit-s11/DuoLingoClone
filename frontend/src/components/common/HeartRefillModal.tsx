'use client';

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { refillHearts, type UserResponse } from '@/lib/api/client';
import { Mascot } from '../mascot/Mascot';

interface HeartRefillModalProps {
  isOpen: boolean;
  onClose: () => void;
  user?: UserResponse;
}

export const HeartRefillModal: React.FC<HeartRefillModalProps> = ({
  isOpen,
  onClose,
  user,
}) => {
  const queryClient = useQueryClient();
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const refillMutation = useMutation({
    mutationFn: (method: 'gems' | 'practice') => refillHearts({ method }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['me'] });
      queryClient.invalidateQueries({ queryKey: ['profile'] });
      setErrorMessage(null);
      onClose();
    },
    onError: (err: Error) => {
      setErrorMessage(err.message || 'Failed to refill hearts');
    },
  });

  if (!isOpen) return null;

  const currentHearts = user?.hearts ?? 5;
  const currentGems = user?.gems ?? 0;

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
        <motion.div
          initial={{ opacity: 0, scale: 0.9, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.9, y: 20 }}
          className="relative w-full max-w-md bg-white rounded-3xl p-6 shadow-2xl border-2 border-duo-gray-200 text-center"
        >
          {/* Close button */}
          <button
            onClick={onClose}
            className="absolute top-4 right-4 text-duo-gray-300 hover:text-duo-gray-700 text-2xl font-black p-1 transition-colors"
          >
            ✕
          </button>

          {/* Header mascot */}
          <div className="mb-4 flex justify-center">
            <Mascot expression={currentHearts === 0 ? 'worried' : 'idle'} size="lg" />
          </div>

          <h2 className="text-2xl font-black text-duo-gray-900 mb-1">Hearts</h2>
          <p className="text-sm font-bold text-duo-gray-300 mb-6">
            Hearts keep you going during lessons! When you run out, take a breather or refill.
          </p>

          {/* Current Hearts Status */}
          <div className="flex items-center justify-center gap-2 mb-6">
            {[1, 2, 3, 4, 5].map((idx) => (
              <span
                key={idx}
                className={`text-3xl transition-transform ${
                  idx <= currentHearts
                    ? 'text-duo-red scale-110 drop-shadow-sm'
                    : 'text-duo-gray-200 scale-95 opacity-50'
                }`}
              >
                ❤️
              </span>
            ))}
          </div>

          {errorMessage && (
            <div className="mb-4 p-3 bg-duo-red/10 border border-duo-red/30 rounded-2xl text-xs font-bold text-duo-red">
              {errorMessage}
            </div>
          )}

          {/* Options */}
          <div className="space-y-3 mb-6">
            {/* Refill with gems */}
            <button
              onClick={() => refillMutation.mutate('gems')}
              disabled={refillMutation.isPending || currentHearts >= 5 || currentGems < 350}
              className={`w-full py-3.5 px-4 rounded-2xl font-black text-sm flex items-center justify-between transition-all border-2 ${
                currentHearts >= 5
                  ? 'bg-duo-gray-100 text-duo-gray-300 border-duo-gray-200 cursor-not-allowed'
                  : currentGems < 350
                  ? 'bg-duo-gray-100 text-duo-gray-300 border-duo-gray-200 cursor-not-allowed'
                  : 'bg-duo-blue text-white border-duo-blue-dark shadow-[0_4px_0_0_#1899d6] active:translate-y-1 active:shadow-none hover:brightness-105'
              }`}
            >
              <div className="flex items-center gap-2">
                <span className="text-xl">❤️</span>
                <span className="uppercase tracking-wide">Refill Hearts</span>
              </div>
              <div className="flex items-center gap-1 font-extrabold text-xs bg-black/10 px-2.5 py-1 rounded-xl">
                <span>💎 350</span>
              </div>
            </button>

            {/* Practice to gain heart */}
            <button
              onClick={() => refillMutation.mutate('practice')}
              disabled={refillMutation.isPending || currentHearts >= 5}
              className={`w-full py-3.5 px-4 rounded-2xl font-black text-sm flex items-center justify-between transition-all border-2 ${
                currentHearts >= 5
                  ? 'bg-duo-gray-100 text-duo-gray-300 border-duo-gray-200 cursor-not-allowed'
                  : 'bg-duo-green text-white border-duo-green-dark shadow-[0_4px_0_0_#46a302] active:translate-y-1 active:shadow-none hover:brightness-105'
              }`}
            >
              <div className="flex items-center gap-2">
                <span className="text-xl">💪</span>
                <span className="uppercase tracking-wide">Practice Session</span>
              </div>
              <span className="text-xs font-black uppercase tracking-wider bg-black/10 px-2.5 py-1 rounded-xl">
                FREE (+1 ❤️)
              </span>
            </button>
          </div>

          <div className="text-xs font-bold text-duo-gray-300">
            Current balance: <span className="text-duo-blue font-black">💎 {currentGems} gems</span>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
};
