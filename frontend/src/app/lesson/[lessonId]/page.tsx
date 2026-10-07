'use client';

import React, { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { useQueryClient } from '@tanstack/react-query';
import {
  startAttempt,
  checkAnswer,
  completeAttempt,
  abandonAttempt,
  refillHearts,
  type CompleteAttemptResponse,
} from '@/lib/api/client';
import { useLessonStore } from '@/stores/use-lesson-store';
import { Mascot } from '@/components/mascot/Mascot';
import { MultipleChoiceExercise } from '@/components/lesson/MultipleChoiceExercise';
import { TranslateExercise } from '@/components/lesson/TranslateExercise';
import { MatchPairsExercise } from '@/components/lesson/MatchPairsExercise';
import { FillBlankExercise } from '@/components/lesson/FillBlankExercise';
import { TypeAnswerExercise } from '@/components/lesson/TypeAnswerExercise';

export default function LessonPage() {
  const params = useParams();
  const router = useRouter();
  const queryClient = useQueryClient();
  const lessonIdStr = params?.lessonId as string;
  const lessonId = parseInt(lessonIdStr, 10);

  const [isLoading, setIsLoading] = useState(true);
  const [initError, setInitError] = useState<string | null>(null);
  const [showExitConfirm, setShowExitConfirm] = useState(false);
  const [showOutOfHeartsModal, setShowOutOfHeartsModal] = useState(false);
  const [completionResult, setCompletionResult] = useState<CompleteAttemptResponse | null>(null);

  const {
    attemptId,
    currentExercise,
    selectedAnswer,
    feedbackStatus,
    correctAnswerDisplay,
    explanation,
    heartsRemaining,
    isChecking,
    totalInitialExercises,
    answeredCount,
    initLesson,
    setSelectedAnswer,
    setChecking,
    setFeedback,
    advanceToNext,
    updateHearts,
    resetLesson,
  } = useLessonStore();

  // Initialize lesson attempt on mount
  useEffect(() => {
    if (isNaN(lessonId)) {
      setInitError('Invalid lesson ID');
      setIsLoading(false);
      return;
    }

    let isMounted = true;
    setIsLoading(true);
    setInitError(null);

    startAttempt(lessonId)
      .then((attemptData) => {
        if (!isMounted) return;
        initLesson(attemptData);
        setIsLoading(false);
      })
      .catch((err: Error) => {
        if (!isMounted) return;
        setInitError(err.message || 'Failed to start lesson attempt');
        setIsLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [lessonId, initLesson]);

  // Check if answer is provided and valid to enable Check button
  const isAnswerProvided = (): boolean => {
    if (!currentExercise || feedbackStatus !== 'idle') return false;

    switch (currentExercise.type) {
      case 'multiple_choice':
      case 'fill_blank':
        return typeof selectedAnswer === 'string' && selectedAnswer.length > 0;
      case 'type_answer':
        return typeof selectedAnswer === 'string' && selectedAnswer.trim().length > 0;
      case 'translate':
        return Array.isArray(selectedAnswer) && selectedAnswer.length > 0;
      case 'match_pairs': {
        const payload = currentExercise.payload as unknown as { left?: unknown[] };
        const leftCount = Array.isArray(payload?.left) ? payload.left.length : 0;
        const matches = (selectedAnswer as Record<string, string>) || {};
        return Object.keys(matches).length === leftCount && leftCount > 0;
      }
      default:
        return false;
    }
  };

  // Submit Answer
  const handleCheck = async () => {
    if (!attemptId || !currentExercise || !isAnswerProvided() || isChecking) return;

    setChecking(true);
    try {
      const result = await checkAnswer(attemptId, {
        exercise_id: currentExercise.id,
        user_answer: selectedAnswer,
      });

      const nextHearts =
        result.hearts_remaining !== undefined
          ? result.hearts_remaining
          : result.hearts !== null && result.hearts !== undefined
          ? result.hearts
          : heartsRemaining;

      if (result.is_correct) {
        setFeedback('correct', result.correct_answer, result.explanation, nextHearts);
      } else {
        if (result.lesson_failed || nextHearts <= 0) {
          setFeedback('out_of_hearts', result.correct_answer, result.explanation, nextHearts);
          setShowOutOfHeartsModal(true);
        } else {
          setFeedback('incorrect', result.correct_answer, result.explanation, nextHearts);
        }
      }
    } catch (err: unknown) {
      setChecking(false);
      const errMsg = err instanceof Error ? err.message : 'Error evaluating answer';
      alert(errMsg);
    }
  };

  // Continue to next question or complete
  const handleContinue = async () => {
    if (!attemptId) return;

    const hasMore = advanceToNext();
    if (!hasMore) {
      // Completed all questions! Finish attempt
      setIsLoading(true);
      try {
        const comp = await completeAttempt(attemptId);
        setCompletionResult(comp);
        queryClient.invalidateQueries({ queryKey: ['course-path'] });
        queryClient.invalidateQueries({ queryKey: ['me'] });
        queryClient.invalidateQueries({ queryKey: ['profile'] });
        queryClient.invalidateQueries({ queryKey: ['leaderboard'] });
      } catch (err: unknown) {
        const errMsg = err instanceof Error ? err.message : 'Error completing lesson';
        alert(errMsg);
      } finally {
        setIsLoading(false);
      }
    }
  };

  // Abandon attempt and return to learn
  const handleExitLesson = async () => {
    if (attemptId) {
      try {
        await abandonAttempt(attemptId);
      } catch {
        // ignore abandon errors
      }
    }
    resetLesson();
    router.push('/learn');
  };

  // Refill hearts during out-of-hearts crisis
  const handleRefillDuringLesson = async (method: 'gems' | 'practice') => {
    try {
      const res = await refillHearts({ method });
      updateHearts(res.hearts);
      setShowOutOfHeartsModal(false);
      setFeedback('incorrect', correctAnswerDisplay, explanation, res.hearts);
    } catch (err: unknown) {
      const errMsg = err instanceof Error ? err.message : 'Refill failed';
      alert(errMsg);
    }
  };

  // Progress percentage calculation
  const progressPercent = totalInitialExercises > 0
    ? Math.min(100, Math.round((answeredCount / totalInitialExercises) * 100))
    : 0;

  // -------------------------------------------------------------
  // COMPLETION SCREEN
  // -------------------------------------------------------------
  if (completionResult) {
    return (
      <main className="min-h-screen bg-white flex flex-col items-center justify-between p-6 select-none max-w-xl mx-auto">
        <div className="flex-1 flex flex-col items-center justify-center text-center w-full py-8">
          <Mascot expression="celebration" size="xl" />

          <motion.h1
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className="text-3xl font-black text-duo-yellow-dark mt-6 mb-2"
          >
            Lesson Complete!
          </motion.h1>
          <p className="text-sm font-bold text-duo-gray-300 mb-8">
            You completed all exercises and earned new experience!
          </p>

          {/* Stats Badges */}
          <div className="grid grid-cols-3 gap-3 w-full mb-8">
            <div className="bg-duo-yellow/15 border-2 border-duo-yellow rounded-2xl p-4 flex flex-col items-center">
              <span className="text-xs font-black uppercase tracking-wider text-duo-yellow-dark">
                TOTAL XP
              </span>
              <span className="text-2xl font-black text-duo-yellow-dark mt-1">
                +{completionResult.xp_earned}
              </span>
            </div>

            <div className="bg-duo-green/15 border-2 border-duo-green rounded-2xl p-4 flex flex-col items-center">
              <span className="text-xs font-black uppercase tracking-wider text-duo-green-dark">
                ACCURACY
              </span>
              <span className="text-2xl font-black text-duo-green mt-1">
                {Math.round(completionResult.accuracy * 100)}%
              </span>
            </div>

            <div className="bg-duo-blue/15 border-2 border-duo-blue rounded-2xl p-4 flex flex-col items-center">
              <span className="text-xs font-black uppercase tracking-wider text-duo-blue-dark">
                TIME
              </span>
              <span className="text-2xl font-black text-duo-blue mt-1">
                {completionResult.time_spent_seconds ?? 45}s
              </span>
            </div>
          </div>

          {/* Streak Banner */}
          <div className="w-full bg-duo-orange/15 border-2 border-duo-orange rounded-2xl p-4 flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <span className="text-3xl">🔥</span>
              <div className="text-left">
                <span className="text-xs font-black uppercase tracking-wider text-duo-orange">
                  STREAK EXTENDED
                </span>
                <p className="text-sm font-black text-duo-gray-900">
                  {completionResult.streak_current} Day Streak!
                </p>
              </div>
            </div>
            <span className="text-xs font-extrabold bg-duo-orange text-white px-2.5 py-1 rounded-full uppercase">
              ACTIVE
            </span>
          </div>

          {/* Crown Banner if earned */}
          {completionResult.new_crown_earned && (
            <div className="w-full bg-duo-yellow/20 border-2 border-duo-yellow rounded-2xl p-4 flex items-center gap-3">
              <span className="text-3xl">👑</span>
              <div className="text-left">
                <span className="text-xs font-black uppercase tracking-wider text-duo-yellow-dark">
                  NEW CROWN EARNED
                </span>
                <p className="text-sm font-black text-duo-gray-900">
                  Skill mastery increased!
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Continue to Learn Button */}
        <div className="w-full pt-4 border-t-2 border-duo-gray-200">
          <button
            onClick={() => {
              resetLesson();
              router.push('/learn');
            }}
            className="w-full py-4 bg-duo-green hover:bg-duo-green-light active:translate-y-1 text-white font-black rounded-2xl shadow-[0_4px_0_0_#46a302] active:shadow-none uppercase tracking-wider text-base transition-all"
          >
            CONTINUE
          </button>
        </div>
      </main>
    );
  }

  // -------------------------------------------------------------
  // LOADING / INITIAL ERROR SCREEN
  // -------------------------------------------------------------
  if (isLoading && !currentExercise) {
    return (
      <div className="min-h-screen bg-white flex flex-col items-center justify-center p-6 text-center">
        <Mascot expression="thinking" size="xl" />
        <h2 className="text-xl font-black text-duo-gray-700 mt-6 animate-pulse">
          Starting your lesson...
        </h2>
      </div>
    );
  }

  if (initError) {
    return (
      <div className="min-h-screen bg-white flex flex-col items-center justify-center p-6 text-center max-w-md mx-auto">
        <Mascot expression="worried" size="xl" />
        <h2 className="text-2xl font-black text-duo-red mt-6">Unable to load lesson</h2>
        <p className="text-sm font-bold text-duo-gray-300 mt-2 mb-8">{initError}</p>
        <button
          onClick={() => router.push('/learn')}
          className="w-full py-4 bg-duo-blue text-white font-black rounded-2xl shadow-[0_4px_0_0_#1899d6] uppercase tracking-wider text-sm active:translate-y-1"
        >
          BACK TO LEARN
        </button>
      </div>
    );
  }

  // -------------------------------------------------------------
  // ACTIVE LESSON RUNNER
  // -------------------------------------------------------------
  return (
    <div className="min-h-screen bg-white flex flex-col justify-between select-none">
      {/* Top Header: Quit button, Progress bar, Hearts */}
      <header className="w-full max-w-4xl mx-auto px-4 py-4 sm:py-6 flex items-center justify-between gap-4">
        {/* Quit X button */}
        <button
          onClick={() => setShowExitConfirm(true)}
          className="text-duo-gray-300 hover:text-duo-gray-700 font-black text-2xl p-2 transition-colors"
          title="Quit Lesson"
        >
          ✕
        </button>

        {/* Animated Progress Bar */}
        <div className="flex-1 h-4 bg-duo-gray-200 rounded-full overflow-hidden relative">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${progressPercent}%` }}
            transition={{ duration: 0.3, ease: 'easeOut' }}
            className="h-full bg-duo-green rounded-full relative"
          >
            {/* Top highlight shine */}
            <div className="absolute top-0 left-0 right-0 h-1.5 bg-white/30 rounded-full" />
          </motion.div>
        </div>

        {/* Hearts indicator */}
        <div className="flex items-center gap-1.5 font-black text-duo-red text-base">
          <span className="text-xl">❤️</span>
          <span>{heartsRemaining}</span>
        </div>
      </header>

      {/* Main Exercise Area */}
      <main className="flex-1 flex flex-col justify-center w-full max-w-2xl mx-auto px-4 py-6">
        {currentExercise && (
          <div>
            {currentExercise.type === 'multiple_choice' && (
              <MultipleChoiceExercise
                payload={currentExercise.payload as unknown as { prompt: string; options: string[] }}
                selectedAnswer={(selectedAnswer as string) || null}
                onSelect={(val) => setSelectedAnswer(val)}
                disabled={feedbackStatus !== 'idle'}
              />
            )}

            {currentExercise.type === 'translate' && (
              <TranslateExercise
                payload={
                  currentExercise.payload as unknown as {
                    prompt: string;
                    direction?: string;
                    word_bank: string[];
                  }
                }
                selectedTokens={(selectedAnswer as string[]) || []}
                onTokensChange={(tokens) => setSelectedAnswer(tokens)}
                disabled={feedbackStatus !== 'idle'}
              />
            )}

            {currentExercise.type === 'match_pairs' && (
              <MatchPairsExercise
                payload={
                  currentExercise.payload as unknown as {
                    prompt: string;
                    left: { id: string; text: string }[];
                    right: { id: string; text: string }[];
                  }
                }
                matchedPairs={(selectedAnswer as Record<string, string>) || {}}
                onMatchedPairsChange={(pairs) => setSelectedAnswer(pairs)}
                disabled={feedbackStatus !== 'idle'}
              />
            )}

            {currentExercise.type === 'fill_blank' && (
              <FillBlankExercise
                payload={currentExercise.payload as unknown as { prompt: string; options: string[] }}
                selectedAnswer={(selectedAnswer as string) || null}
                onSelect={(val) => setSelectedAnswer(val)}
                disabled={feedbackStatus !== 'idle'}
              />
            )}

            {currentExercise.type === 'type_answer' && (
              <TypeAnswerExercise
                payload={currentExercise.payload as unknown as { prompt: string; placeholder?: string }}
                value={(selectedAnswer as string) || ''}
                onChange={(val) => setSelectedAnswer(val)}
                onSubmit={handleCheck}
                disabled={feedbackStatus !== 'idle'}
              />
            )}
          </div>
        )}
      </main>

      {/* Bottom Sticky Action Bar */}
      <footer
        className={`w-full border-t-2 py-5 px-6 transition-colors ${
          feedbackStatus === 'correct'
            ? 'bg-[#d7ffb8] border-[#a5ed6e]'
            : feedbackStatus === 'incorrect' || feedbackStatus === 'out_of_hearts'
            ? 'bg-[#ffdfe0] border-[#ff999b]'
            : 'bg-white border-duo-gray-200'
        }`}
      >
        <div className="max-w-3xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          {/* Feedback Info */}
          <div className="flex-1">
            {feedbackStatus === 'correct' && (
              <div className="flex items-center gap-3 text-duo-green-dark">
                <div className="w-10 h-10 rounded-full bg-white flex items-center justify-center text-xl font-black shadow-sm">
                  ✓
                </div>
                <div>
                  <h3 className="font-black text-lg leading-tight">Nicely done!</h3>
                  {explanation && (
                    <p className="text-xs font-bold text-duo-gray-700">{explanation}</p>
                  )}
                </div>
              </div>
            )}

            {(feedbackStatus === 'incorrect' || feedbackStatus === 'out_of_hearts') && (
              <div className="flex items-center gap-3 text-duo-red-dark">
                <div className="w-10 h-10 rounded-full bg-white flex items-center justify-center text-xl font-black shadow-sm">
                  ✕
                </div>
                <div>
                  <h3 className="font-black text-base leading-tight">Correct solution:</h3>
                  <p className="text-sm font-black text-duo-red-dark">
                    {typeof correctAnswerDisplay === 'object'
                      ? JSON.stringify(correctAnswerDisplay)
                      : String(correctAnswerDisplay || '')}
                  </p>
                  {explanation && (
                    <p className="text-xs font-bold text-duo-gray-700 mt-0.5">{explanation}</p>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Action Buttons */}
          <div className="w-full sm:w-auto min-w-[160px]">
            {feedbackStatus === 'idle' ? (
              <button
                type="button"
                onClick={handleCheck}
                disabled={!isAnswerProvided() || isChecking}
                className={`w-full py-3.5 px-8 rounded-2xl font-black text-base uppercase tracking-wider transition-all border-2 ${
                  isAnswerProvided() && !isChecking
                    ? 'bg-duo-green text-white border-duo-green-dark shadow-[0_4px_0_0_#46a302] active:translate-y-1 active:shadow-none hover:brightness-105 cursor-pointer'
                    : 'bg-duo-gray-200 text-duo-gray-300 border-duo-gray-200 cursor-not-allowed shadow-none'
                }`}
              >
                {isChecking ? 'Checking...' : 'CHECK'}
              </button>
            ) : feedbackStatus === 'correct' ? (
              <button
                type="button"
                onClick={handleContinue}
                className="w-full py-3.5 px-8 rounded-2xl font-black text-base uppercase tracking-wider bg-duo-green text-white border-2 border-duo-green-dark shadow-[0_4px_0_0_#46a302] active:translate-y-1 active:shadow-none hover:brightness-105 cursor-pointer"
              >
                CONTINUE
              </button>
            ) : (
              <button
                type="button"
                onClick={feedbackStatus === 'out_of_hearts' ? () => setShowOutOfHeartsModal(true) : handleContinue}
                className="w-full py-3.5 px-8 rounded-2xl font-black text-base uppercase tracking-wider bg-duo-red text-white border-2 border-duo-red-dark shadow-[0_4px_0_0_#ea2b2b] active:translate-y-1 active:shadow-none hover:brightness-105 cursor-pointer"
              >
                CONTINUE
              </button>
            )}
          </div>
        </div>
      </footer>

      {/* Confirmation Modal when quitting */}
      {showExitConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
          <div className="bg-white rounded-3xl p-6 max-w-sm w-full text-center border-2 border-duo-gray-200">
            <Mascot expression="worried" size="lg" />
            <h3 className="text-xl font-black text-duo-gray-900 mt-4 mb-2">Leave lesson?</h3>
            <p className="text-xs font-bold text-duo-gray-300 mb-6">
              All progress from this practice session will be lost!
            </p>
            <div className="space-y-3">
              <button
                onClick={() => setShowExitConfirm(false)}
                className="w-full py-3 bg-duo-blue text-white font-black rounded-2xl border-2 border-duo-blue-dark shadow-[0_4px_0_0_#1899d6] active:translate-y-1 uppercase tracking-wider text-sm"
              >
                KEEP LEARNING
              </button>
              <button
                onClick={handleExitLesson}
                className="w-full py-3 bg-white text-duo-red font-black rounded-2xl border-2 border-duo-gray-200 hover:bg-duo-gray-100 uppercase tracking-wider text-sm"
              >
                END SESSION
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Out of Hearts Modal */}
      {showOutOfHeartsModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
          <div className="bg-white rounded-3xl p-6 max-w-md w-full text-center border-2 border-duo-gray-200">
            <Mascot expression="worried" size="lg" />
            <h3 className="text-2xl font-black text-duo-gray-900 mt-4 mb-1">Out of Hearts!</h3>
            <p className="text-xs font-bold text-duo-gray-300 mb-6">
              Refill your hearts now to keep going, or take a practice session.
            </p>

            <div className="space-y-3 mb-6">
              <button
                onClick={() => handleRefillDuringLesson('gems')}
                className="w-full py-3.5 px-4 bg-duo-blue text-white font-black rounded-2xl border-2 border-duo-blue-dark shadow-[0_4px_0_0_#1899d6] flex items-center justify-between text-sm active:translate-y-1"
              >
                <span>❤️ REFILL WITH GEMS</span>
                <span className="text-xs bg-black/10 px-2 py-0.5 rounded-lg">💎 350</span>
              </button>

              <button
                onClick={() => handleRefillDuringLesson('practice')}
                className="w-full py-3.5 px-4 bg-duo-green text-white font-black rounded-2xl border-2 border-duo-green-dark shadow-[0_4px_0_0_#46a302] flex items-center justify-between text-sm active:translate-y-1"
              >
                <span>💪 PRACTICE (+1 ❤️)</span>
                <span className="text-xs bg-black/10 px-2 py-0.5 rounded-lg">FREE</span>
              </button>
            </div>

            <button
              onClick={handleExitLesson}
              className="text-xs font-black uppercase text-duo-gray-300 hover:text-duo-gray-700 tracking-wider"
            >
              QUIT LESSON FOR NOW
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
