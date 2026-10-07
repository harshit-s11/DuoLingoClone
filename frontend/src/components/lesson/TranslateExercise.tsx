'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface TranslateExerciseProps {
  payload: {
    prompt: string;
    direction?: string;
    word_bank: string[];
  };
  selectedTokens: string[];
  onTokensChange: (tokens: string[]) => void;
  disabled?: boolean;
}

export const TranslateExercise: React.FC<TranslateExerciseProps> = ({
  payload,
  onTokensChange,
  disabled = false,
}) => {
  // Track selected indices from the word_bank array to preserve duplicate words and slots
  const [selectedIndices, setSelectedIndices] = useState<number[]>([]);

  // Reset when prompt changes
  useEffect(() => {
    setSelectedIndices([]);
  }, [payload.prompt]);

  const handleSelectWord = (index: number) => {
    if (disabled || selectedIndices.includes(index)) return;
    const next = [...selectedIndices, index];
    setSelectedIndices(next);
    onTokensChange(next.map((i) => payload.word_bank[i]));
  };

  const handleRemoveWord = (placementIndex: number) => {
    if (disabled) return;
    const next = selectedIndices.filter((_, idx) => idx !== placementIndex);
    setSelectedIndices(next);
    onTokensChange(next.map((i) => payload.word_bank[i]));
  };

  return (
    <div className="w-full max-w-xl mx-auto flex flex-col items-center">
      {/* Prompt header with speaker and phrase */}
      <div className="w-full mb-8">
        <span className="text-xs font-black uppercase tracking-wider text-duo-gray-300 block mb-2">
          Translate this sentence
        </span>
        <div className="flex items-center gap-4 bg-duo-gray-100/60 p-4 rounded-2xl border border-duo-gray-200">
          <div className="w-10 h-10 rounded-xl bg-duo-blue flex items-center justify-center text-white text-lg shadow-[0_3px_0_0_#1899d6] flex-shrink-0 cursor-pointer">
            🔊
          </div>
          <span className="text-xl font-black text-duo-gray-900">{payload.prompt}</span>
        </div>
      </div>

      {/* Target Assembly Area */}
      <div className="w-full min-h-[90px] border-b-2 border-t-2 border-duo-gray-200 py-3 mb-8 flex flex-wrap gap-2.5 items-center">
        {selectedIndices.length === 0 ? (
          <span className="text-sm font-bold text-duo-gray-300 italic px-2">
            Tap the words below to construct your answer
          </span>
        ) : (
          <AnimatePresence>
            {selectedIndices.map((wordIdx, placementIdx) => {
              const word = payload.word_bank[wordIdx];
              return (
                <motion.button
                  key={`selected-${wordIdx}-${placementIdx}`}
                  initial={{ scale: 0.8, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  exit={{ scale: 0.8, opacity: 0 }}
                  type="button"
                  disabled={disabled}
                  onClick={() => handleRemoveWord(placementIdx)}
                  className="px-3.5 py-2 bg-white border-2 border-duo-gray-200 text-duo-gray-700 font-extrabold text-sm rounded-xl shadow-[0_3px_0_0_#e5e5e5] hover:border-duo-red hover:text-duo-red transition-all cursor-pointer active:translate-y-0.5 active:shadow-none"
                >
                  {word}
                </motion.button>
              );
            })}
          </AnimatePresence>
        )}
      </div>

      {/* Word Bank Area */}
      <div className="w-full flex flex-wrap gap-2.5 justify-center">
        {payload.word_bank.map((word, idx) => {
          const isPlaced = selectedIndices.includes(idx);
          return (
            <div key={`bank-${word}-${idx}`} className="relative">
              {isPlaced ? (
                <div className="px-3.5 py-2 bg-duo-gray-200/50 border-2 border-transparent text-transparent font-extrabold text-sm rounded-xl select-none">
                  {word}
                </div>
              ) : (
                <button
                  type="button"
                  disabled={disabled}
                  onClick={() => handleSelectWord(idx)}
                  className="px-3.5 py-2 bg-white border-2 border-duo-gray-200 text-duo-gray-700 font-black text-sm rounded-xl shadow-[0_3px_0_0_#e5e5e5] hover:bg-duo-gray-100 hover:border-duo-gray-300 active:translate-y-1 active:shadow-none transition-all cursor-pointer"
                >
                  {word}
                </button>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
