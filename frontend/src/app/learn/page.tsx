'use client';

import React from 'react';
import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { fetchCoursePath } from '@/lib/api/client';
import { AppShell } from '@/components/layout/AppShell';
import { Mascot } from '@/components/mascot/Mascot';

// Horizontal offsets for wavy zigzag path effect
const X_OFFSETS = [0, -45, -70, -40, 0, 40, 70, 45];

export default function LearnPage() {
  const { data: coursePath, isLoading, isError, error } = useQuery({
    queryKey: ['course-path', 1],
    queryFn: () => fetchCoursePath(1),
  });

  // Find the very first unlocked, uncompleted lesson to place the "START" badge
  let firstActiveLessonId: number | null = null;
  if (coursePath?.units) {
    for (const unit of coursePath.units) {
      for (const skill of unit.skills) {
        for (const lesson of skill.lessons) {
          if (!lesson.is_completed && !lesson.is_locked && firstActiveLessonId === null) {
            firstActiveLessonId = lesson.id;
            break;
          }
        }
        if (firstActiveLessonId !== null) break;
      }
      if (firstActiveLessonId !== null) break;
    }
  }

  return (
    <AppShell>
      <div className="flex flex-col items-center w-full max-w-xl mx-auto">
        {/* Loading State */}
        {isLoading && (
          <div className="py-20 flex flex-col items-center justify-center text-center">
            <Mascot expression="thinking" size="lg" />
            <p className="mt-4 text-base font-black text-duo-gray-300 animate-pulse">
              Loading your Spanish journey...
            </p>
          </div>
        )}

        {/* Error State */}
        {isError && (
          <div className="py-16 text-center max-w-md bg-duo-red/10 border-2 border-duo-red/30 rounded-3xl p-6">
            <Mascot expression="worried" size="lg" />
            <h3 className="mt-3 text-lg font-black text-duo-red">Failed to load course path</h3>
            <p className="text-xs font-bold text-duo-gray-700 mt-1">
              {error instanceof Error ? error.message : 'Please check your connection and try again.'}
            </p>
          </div>
        )}

        {/* Course Units and Wavy Path */}
        {coursePath?.units && (
          <div className="w-full space-y-12">
            {coursePath.units.map((unit) => {
              // Flatten lessons for path node sequencing within this unit
              const allUnitLessons = unit.skills.flatMap((s) =>
                s.lessons.map((l) => ({ ...l, skillName: s.name, skillIcon: s.icon_name }))
              );

              return (
                <section key={unit.id} className="w-full">
                  {/* Unit Banner */}
                  <div className="sticky top-16 md:top-4 z-10 bg-duo-green text-white rounded-3xl p-5 shadow-[0_5px_0_0_#46a302] mb-8 border-2 border-duo-green-dark">
                    <div className="flex items-center justify-between">
                      <div>
                        <span className="text-xs font-black uppercase tracking-wider text-duo-green-light">
                          Unit {unit.unit_order}
                        </span>
                        <h2 className="text-xl font-black leading-tight mt-0.5">
                          {unit.title}
                        </h2>
                        <p className="text-xs font-bold text-white/90 mt-1">
                          {unit.description}
                        </p>
                      </div>
                      <div className="hidden sm:block text-3xl p-2 bg-white/10 rounded-2xl">
                        🗺️
                      </div>
                    </div>
                  </div>

                  {/* Wavy Lesson Nodes */}
                  <div className="relative flex flex-col items-center py-4 space-y-7">
                    {allUnitLessons.map((lesson, idx) => {
                      const offsetIndex = idx % X_OFFSETS.length;
                      const xOffset = X_OFFSETS[offsetIndex];
                      const isStartLesson = lesson.id === firstActiveLessonId;
                      const isCompleted = lesson.is_completed;
                      const isLocked = lesson.is_locked;

                      return (
                        <div
                          key={lesson.id}
                          className="relative flex flex-col items-center"
                          style={{
                            transform: `translateX(${xOffset}px)`,
                          }}
                        >
                          {/* Floating START Prompt Bubble */}
                          {isStartLesson && (
                            <motion.div
                              initial={{ y: 0 }}
                              animate={{ y: [-4, 4, -4] }}
                              transition={{ repeat: Infinity, duration: 1.5, ease: 'easeInOut' }}
                              className="absolute -top-11 z-20 flex flex-col items-center pointer-events-none select-none"
                            >
                              <div className="px-3.5 py-1.5 bg-white border-2 border-duo-gray-200 rounded-2xl shadow-md text-xs font-black uppercase tracking-wider text-duo-green flex items-center gap-1.5">
                                <span>START</span>
                                <span className="text-[10px]">▶</span>
                              </div>
                              <div className="w-2.5 h-2.5 bg-white border-r-2 border-b-2 border-duo-gray-200 rotate-45 -mt-1.5" />
                            </motion.div>
                          )}

                          {/* Interactive Circular Node */}
                          {isLocked ? (
                            <div
                              title={`${lesson.title} (Locked)`}
                              className="w-16 h-16 sm:w-20 sm:h-20 rounded-full bg-duo-gray-200 border-4 border-duo-gray-300 shadow-[0_4px_0_0_#afafaf] flex items-center justify-center text-duo-gray-300 cursor-not-allowed select-none"
                            >
                              <span className="text-2xl opacity-60">🔒</span>
                            </div>
                          ) : (
                            <Link
                              href={`/lesson/${lesson.id}`}
                              className="group block relative"
                              title={`${lesson.title} - ${isCompleted ? 'Completed (Practice)' : 'Ready to Start'}`}
                            >
                              <div
                                className={`w-16 h-16 sm:w-20 sm:h-20 rounded-full border-4 flex flex-col items-center justify-center transition-transform active:translate-y-1 select-none ${
                                  isCompleted
                                    ? 'bg-duo-yellow border-duo-yellow-dark text-white shadow-[0_5px_0_0_#e5a400] hover:brightness-105'
                                    : 'bg-duo-green border-duo-green-dark text-white shadow-[0_5px_0_0_#46a302] hover:brightness-105 animate-pulse'
                                }`}
                              >
                                {isCompleted ? (
                                  <span className="text-2xl drop-shadow-sm">👑</span>
                                ) : (
                                  <span className="text-2xl drop-shadow-sm">⭐</span>
                                )}
                              </div>
                            </Link>
                          )}

                          {/* Lesson Title Caption */}
                          <div className="mt-2 text-center max-w-[120px]">
                            <span className="text-[11px] font-black text-duo-gray-700 block leading-tight">
                              {lesson.title}
                            </span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </section>
              );
            })}
          </div>
        )}
      </div>
    </AppShell>
  );
}
