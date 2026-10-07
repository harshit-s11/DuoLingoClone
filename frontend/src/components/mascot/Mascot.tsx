'use client';

import React from 'react';
import { motion } from 'framer-motion';

export type MascotExpression = 'idle' | 'happy' | 'cheering' | 'worried' | 'celebration' | 'thinking';

interface MascotProps {
  expression?: MascotExpression;
  size?: 'sm' | 'md' | 'lg' | 'xl';
  className?: string;
  speechBubble?: string;
}

const sizeMap = {
  sm: { width: 44, height: 44 },
  md: { width: 80, height: 80 },
  lg: { width: 120, height: 120 },
  xl: { width: 180, height: 180 },
};

export const Mascot: React.FC<MascotProps> = ({
  expression = 'idle',
  size = 'md',
  className = '',
  speechBubble,
}) => {
  const { width, height } = sizeMap[size];

  return (
    <div className={`relative inline-flex flex-col items-center select-none ${className}`}>
      {speechBubble && (
        <motion.div
          initial={{ opacity: 0, y: 10, scale: 0.9 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          className="mb-2 px-4 py-2 bg-white border-2 border-duo-gray-200 rounded-2xl shadow-sm text-sm font-extrabold text-duo-gray-700 relative text-center max-w-xs"
        >
          {speechBubble}
          <div className="absolute -bottom-2 left-1/2 -translate-x-1/2 w-3 h-3 bg-white border-b-2 border-r-2 border-duo-gray-200 rotate-45" />
        </motion.div>
      )}

      <motion.svg
        width={width}
        height={height}
        viewBox="0 0 100 100"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        animate={
          expression === 'cheering' || expression === 'celebration'
            ? { y: [0, -6, 0], rotate: [0, -2, 2, 0] }
            : expression === 'worried'
            ? { x: [-2, 2, -2, 0] }
            : { y: [0, -2, 0] }
        }
        transition={{
          repeat: Infinity,
          duration: expression === 'cheering' ? 0.6 : 3,
          ease: 'easeInOut',
        }}
        className="overflow-visible"
      >
        {/* Shadow */}
        <ellipse cx="50" cy="94" rx="36" ry="6" fill="#E5E5E5" />

        {/* Feet */}
        <ellipse cx="38" cy="90" rx="9" ry="5" fill="#FF9600" />
        <ellipse cx="62" cy="90" rx="9" ry="5" fill="#FF9600" />

        {/* Body Main */}
        <rect x="18" y="16" width="64" height="72" rx="32" fill="#58CC02" />
        {/* Bottom darker shade for 3D depth */}
        <path
          d="M 18 64 C 18 80, 82 80, 82 64 C 82 82, 18 82, 18 64 Z"
          fill="#46A302"
        />

        {/* Belly Patch */}
        <ellipse cx="50" cy="62" rx="22" ry="20" fill="#89E219" />

        {/* Left Wing */}
        {expression === 'cheering' || expression === 'celebration' ? (
          <path
            d="M 20 40 C 6 22, 12 10, 24 24"
            fill="#58CC02"
            stroke="#46A302"
            strokeWidth="3"
            strokeLinecap="round"
          />
        ) : expression === 'thinking' ? (
          <path
            d="M 20 54 C 12 50, 24 36, 40 46"
            fill="#58CC02"
            stroke="#46A302"
            strokeWidth="3"
            strokeLinecap="round"
          />
        ) : (
          <path
            d="M 20 42 C 10 50, 12 68, 22 66"
            fill="#58CC02"
            stroke="#46A302"
            strokeWidth="3"
            strokeLinecap="round"
          />
        )}

        {/* Right Wing */}
        {expression === 'cheering' || expression === 'celebration' ? (
          <path
            d="M 80 40 C 94 22, 88 10, 76 24"
            fill="#58CC02"
            stroke="#46A302"
            strokeWidth="3"
            strokeLinecap="round"
          />
        ) : (
          <path
            d="M 80 42 C 90 50, 88 68, 78 66"
            fill="#58CC02"
            stroke="#46A302"
            strokeWidth="3"
            strokeLinecap="round"
          />
        )}

        {/* Eyes Base (white circles) */}
        <circle cx="37" cy="40" r="14" fill="#FFFFFF" stroke="#46A302" strokeWidth="2" />
        <circle cx="63" cy="40" r="14" fill="#FFFFFF" stroke="#46A302" strokeWidth="2" />

        {/* Pupils & Expression */}
        {expression === 'happy' || expression === 'celebration' ? (
          <>
            {/* Happy curved eyes ^ ^ */}
            <path
              d="M 30 42 Q 37 34 44 42"
              fill="none"
              stroke="#4B4B4B"
              strokeWidth="3.5"
              strokeLinecap="round"
            />
            <path
              d="M 56 42 Q 63 34 70 42"
              fill="none"
              stroke="#4B4B4B"
              strokeWidth="3.5"
              strokeLinecap="round"
            />
          </>
        ) : expression === 'worried' ? (
          <>
            {/* Worried pupils looking down/scared */}
            <circle cx="37" cy="43" r="6" fill="#4B4B4B" />
            <circle cx="63" cy="43" r="6" fill="#4B4B4B" />
            <circle cx="39" cy="41" r="2" fill="#FFFFFF" />
            <circle cx="65" cy="41" r="2" fill="#FFFFFF" />
            {/* Sweat drop */}
            <path
              d="M 76 26 C 76 24, 82 30, 80 34 C 78 36, 75 34, 76 26 Z"
              fill="#1CB0F6"
            />
          </>
        ) : (
          <>
            {/* Normal / idle pupils */}
            <circle cx="38" cy="40" r="7" fill="#4B4B4B" />
            <circle cx="62" cy="40" r="7" fill="#4B4B4B" />
            {/* Pupil reflections */}
            <circle cx="40" cy="38" r="2.5" fill="#FFFFFF" />
            <circle cx="64" cy="38" r="2.5" fill="#FFFFFF" />
          </>
        )}

        {/* Beak */}
        <polygon
          points={expression === 'happy' || expression === 'cheering' ? '44,46 56,46 50,56' : '44,48 56,48 50,55'}
          fill="#FF9600"
          stroke="#E08500"
          strokeWidth="1.5"
        />

        {/* Party Hat for Celebration */}
        {expression === 'celebration' && (
          <g>
            <polygon points="50,4 38,20 62,20" fill="#FF4B4B" />
            <circle cx="50" cy="4" r="4" fill="#FFC800" />
            <polygon points="44,12 56,12 50,20" fill="#1CB0F6" />
          </g>
        )}
      </motion.svg>
    </div>
  );
};
