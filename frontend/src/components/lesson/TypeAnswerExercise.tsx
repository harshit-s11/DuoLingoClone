'use client';

import React, { useRef, useEffect } from 'react';

interface TypeAnswerExerciseProps {
  payload: {
    prompt: string;
    placeholder?: string;
  };
  value: string;
  onChange: (val: string) => void;
  onSubmit?: () => void;
  disabled?: boolean;
}

export const TypeAnswerExercise: React.FC<TypeAnswerExerciseProps> = ({
  payload,
  value,
  onChange,
  onSubmit,
  disabled = false,
}) => {
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!disabled) {
      inputRef.current?.focus();
    }
  }, [disabled, payload.prompt]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && value.trim() && onSubmit) {
      e.preventDefault();
      onSubmit();
    }
  };

  return (
    <div className="w-full max-w-xl mx-auto flex flex-col items-center">
      <span className="text-xs font-black uppercase tracking-wider text-duo-gray-300 block mb-2 self-start">
        Write this in Spanish
      </span>

      <div className="w-full bg-duo-gray-100/60 p-5 rounded-2xl border border-duo-gray-200 mb-8 flex items-center gap-4">
        <div className="w-10 h-10 rounded-xl bg-duo-blue flex items-center justify-center text-white text-lg shadow-[0_3px_0_0_#1899d6] flex-shrink-0 cursor-pointer">
          🔊
        </div>
        <span className="text-xl font-black text-duo-gray-900">{payload.prompt}</span>
      </div>

      <div className="w-full">
        <input
          ref={inputRef}
          type="text"
          value={value}
          disabled={disabled}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={payload.placeholder || 'Type in Spanish...'}
          className="w-full p-4 text-lg font-bold bg-duo-gray-100/50 border-2 border-duo-gray-200 focus:border-duo-blue focus:bg-white rounded-2xl outline-none transition-all placeholder:text-duo-gray-300 shadow-inner"
        />
      </div>
    </div>
  );
};
