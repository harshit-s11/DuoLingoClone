'use client';

import React, { useState } from 'react';

interface MatchPairsExerciseProps {
  payload: {
    prompt: string;
    left: { id: string; text: string }[];
    right: { id: string; text: string }[];
  };
  matchedPairs: Record<string, string>;
  onMatchedPairsChange: (pairs: Record<string, string>) => void;
  disabled?: boolean;
}

export const MatchPairsExercise: React.FC<MatchPairsExerciseProps> = ({
  payload,
  matchedPairs,
  onMatchedPairsChange,
  disabled = false,
}) => {
  const [selectedLeftId, setSelectedLeftId] = useState<string | null>(null);
  const [selectedRightId, setSelectedRightId] = useState<string | null>(null);

  const handleLeftClick = (id: string) => {
    if (disabled) return;
    // If clicking already selected left, deselect
    if (selectedLeftId === id) {
      setSelectedLeftId(null);
      return;
    }
    // If a right item was previously selected, make the match
    if (selectedRightId) {
      const next = { ...matchedPairs, [id]: selectedRightId };
      onMatchedPairsChange(next);
      setSelectedLeftId(null);
      setSelectedRightId(null);
    } else {
      setSelectedLeftId(id);
    }
  };

  const handleRightClick = (id: string) => {
    if (disabled) return;
    // If clicking already selected right, deselect
    if (selectedRightId === id) {
      setSelectedRightId(null);
      return;
    }
    // If a left item was previously selected, make the match
    if (selectedLeftId) {
      const next = { ...matchedPairs, [selectedLeftId]: id };
      onMatchedPairsChange(next);
      setSelectedLeftId(null);
      setSelectedRightId(null);
    } else {
      setSelectedRightId(id);
    }
  };

  const handleUnpair = (leftId: string) => {
    if (disabled) return;
    const next = { ...matchedPairs };
    delete next[leftId];
    onMatchedPairsChange(next);
  };

  return (
    <div className="w-full max-w-xl mx-auto flex flex-col items-center">
      <h2 className="text-xl sm:text-2xl font-black text-duo-gray-900 text-center mb-8">
        {payload.prompt || 'Tap the matching pairs'}
      </h2>

      <div className="grid grid-cols-2 gap-4 w-full">
        {/* Left Column */}
        <div className="space-y-3">
          {payload.left.map((item) => {
            const isMatched = !!matchedPairs[item.id];
            const isSelected = selectedLeftId === item.id;

            return (
              <button
                key={item.id}
                type="button"
                disabled={disabled}
                onClick={() => {
                  if (isMatched) {
                    handleUnpair(item.id);
                  } else {
                    handleLeftClick(item.id);
                  }
                }}
                className={`w-full p-4 rounded-2xl border-2 font-black text-center text-sm sm:text-base transition-all select-none ${
                  isMatched
                    ? 'bg-duo-green/10 border-duo-green text-duo-green shadow-none opacity-80'
                    : isSelected
                    ? 'bg-duo-blue/15 border-duo-blue text-duo-blue shadow-[0_4px_0_0_#1899d6] -translate-y-0.5'
                    : 'bg-white border-duo-gray-200 text-duo-gray-700 shadow-[0_4px_0_0_#e5e5e5] hover:bg-duo-gray-100 hover:border-duo-gray-300'
                } ${disabled ? 'cursor-not-allowed' : 'cursor-pointer active:translate-y-1 active:shadow-none'}`}
              >
                <div className="flex items-center justify-between px-2">
                  <span>{item.text}</span>
                  {isMatched && <span className="text-xs">✓</span>}
                </div>
              </button>
            );
          })}
        </div>

        {/* Right Column */}
        <div className="space-y-3">
          {payload.right.map((item) => {
            const matchedLeftKey = Object.keys(matchedPairs).find(
              (k) => matchedPairs[k] === item.id
            );
            const isMatched = !!matchedLeftKey;
            const isSelected = selectedRightId === item.id;

            return (
              <button
                key={item.id}
                type="button"
                disabled={disabled}
                onClick={() => {
                  if (isMatched && matchedLeftKey) {
                    handleUnpair(matchedLeftKey);
                  } else {
                    handleRightClick(item.id);
                  }
                }}
                className={`w-full p-4 rounded-2xl border-2 font-black text-center text-sm sm:text-base transition-all select-none ${
                  isMatched
                    ? 'bg-duo-green/10 border-duo-green text-duo-green shadow-none opacity-80'
                    : isSelected
                    ? 'bg-duo-blue/15 border-duo-blue text-duo-blue shadow-[0_4px_0_0_#1899d6] -translate-y-0.5'
                    : 'bg-white border-duo-gray-200 text-duo-gray-700 shadow-[0_4px_0_0_#e5e5e5] hover:bg-duo-gray-100 hover:border-duo-gray-300'
                } ${disabled ? 'cursor-not-allowed' : 'cursor-pointer active:translate-y-1 active:shadow-none'}`}
              >
                <div className="flex items-center justify-between px-2">
                  <span>{item.text}</span>
                  {isMatched && <span className="text-xs">✓</span>}
                </div>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
};
