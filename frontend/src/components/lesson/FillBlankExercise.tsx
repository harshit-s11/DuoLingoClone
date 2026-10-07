'use client';

import React from 'react';

interface FillBlankExerciseProps {
  payload: {
    prompt: string;
    options: string[];
  };
  selectedAnswer: string | null;
  onSelect: (option: string) => void;
  disabled?: boolean;
}

export const FillBlankExercise: React.FC<FillBlankExerciseProps> = ({
  payload,
  selectedAnswer,
  onSelect,
  disabled = false,
}) => {
  // Split prompt at '___'
  const parts = payload.prompt.split('___');

  return (
    <div className="w-full max-w-xl mx-auto flex flex-col items-center">
      <span className="text-xs font-black uppercase tracking-wider text-duo-gray-300 block mb-4 self-start">
        Fill in the blank
      </span>

      {/* Sentence with blank filled or highlighted */}
      <div className="w-full bg-duo-gray-100/60 p-6 rounded-3xl border border-duo-gray-200 mb-8 text-center text-xl sm:text-2xl font-black text-duo-gray-900 leading-relaxed">
        <span>{parts[0]}</span>
        <span
          className={`inline-block min-w-[100px] mx-2 px-3 py-1 rounded-xl border-b-4 transition-all text-center ${
            selectedAnswer
              ? 'bg-duo-blue/15 border-duo-blue text-duo-blue font-black'
              : 'bg-white border-duo-gray-300 text-transparent'
          }`}
        >
          {selectedAnswer || 'placeholder'}
        </span>
        {parts[1] && <span>{parts[1]}</span>}
      </div>

      {/* Options */}
      <div className="grid grid-cols-2 gap-3.5 w-full">
        {payload.options.map((option, idx) => {
          const isSelected = selectedAnswer === option;
          return (
            <button
              key={`${option}-${idx}`}
              type="button"
              disabled={disabled}
              onClick={() => onSelect(option)}
              className={`p-4 rounded-2xl border-2 text-center font-black transition-all text-base select-none ${
                isSelected
                  ? 'bg-duo-blue/15 border-duo-blue text-duo-blue shadow-[0_4px_0_0_#1899d6] -translate-y-0.5'
                  : 'bg-white border-duo-gray-200 text-duo-gray-700 shadow-[0_4px_0_0_#e5e5e5] hover:bg-duo-gray-100 hover:border-duo-gray-300'
              } ${disabled ? 'cursor-not-allowed opacity-80' : 'cursor-pointer active:translate-y-1 active:shadow-none'}`}
            >
              {option}
            </button>
          );
        })}
      </div>
    </div>
  );
};
