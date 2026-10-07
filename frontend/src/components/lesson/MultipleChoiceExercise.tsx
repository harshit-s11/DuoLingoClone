'use client';

import React from 'react';

interface MultipleChoiceExerciseProps {
  payload: {
    prompt: string;
    options: string[];
  };
  selectedAnswer: string | null;
  onSelect: (option: string) => void;
  disabled?: boolean;
}

export const MultipleChoiceExercise: React.FC<MultipleChoiceExerciseProps> = ({
  payload,
  selectedAnswer,
  onSelect,
  disabled = false,
}) => {
  return (
    <div className="w-full max-w-xl mx-auto flex flex-col items-center">
      <h2 className="text-xl sm:text-2xl font-black text-duo-gray-900 text-center mb-8">
        {payload.prompt}
      </h2>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5 w-full">
        {payload.options.map((option, idx) => {
          const isSelected = selectedAnswer === option;
          return (
            <button
              key={`${option}-${idx}`}
              type="button"
              disabled={disabled}
              onClick={() => onSelect(option)}
              className={`p-4 rounded-2xl border-2 text-left font-black transition-all flex items-center justify-between text-base select-none ${
                isSelected
                  ? 'bg-duo-blue/15 border-duo-blue text-duo-blue shadow-[0_4px_0_0_#1899d6] translate-y-[-2px]'
                  : 'bg-white border-duo-gray-200 text-duo-gray-700 shadow-[0_4px_0_0_#e5e5e5] hover:bg-duo-gray-100 hover:border-duo-gray-300'
              } ${disabled ? 'cursor-not-allowed opacity-80' : 'cursor-pointer active:translate-y-1 active:shadow-none'}`}
            >
              <div className="flex items-center gap-3">
                <span
                  className={`w-7 h-7 rounded-lg border-2 flex items-center justify-center text-xs font-black ${
                    isSelected
                      ? 'border-duo-blue bg-duo-blue text-white'
                      : 'border-duo-gray-200 text-duo-gray-300'
                  }`}
                >
                  {idx + 1}
                </span>
                <span>{option}</span>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
};
