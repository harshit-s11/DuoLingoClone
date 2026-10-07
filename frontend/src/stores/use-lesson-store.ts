import { create } from 'zustand';
import type { StartAttemptResponse } from '@/lib/api/client';

type ExerciseItem = StartAttemptResponse['exercises'][number];

export type FeedbackStatus = 'idle' | 'correct' | 'incorrect' | 'out_of_hearts';

interface LessonState {
  attemptId: number | null;
  lessonId: number | null;
  queue: ExerciseItem[];
  requeue: ExerciseItem[];
  currentIndex: number;
  currentExercise: ExerciseItem | null;
  selectedAnswer: unknown;
  feedbackStatus: FeedbackStatus;
  correctAnswerDisplay: unknown;
  explanation: string | null;
  heartsRemaining: number;
  isChecking: boolean;
  totalInitialExercises: number;
  answeredCount: number;

  // Actions
  initLesson: (attempt: StartAttemptResponse) => void;
  setSelectedAnswer: (answer: unknown) => void;
  setChecking: (checking: boolean) => void;
  setFeedback: (
    status: FeedbackStatus,
    correctAnswer: unknown,
    explanation?: string | null,
    hearts?: number
  ) => void;
  advanceToNext: () => boolean; // returns true if more exercises remain, false if completed
  updateHearts: (hearts: number) => void;
  resetLesson: () => void;
}

export const useLessonStore = create<LessonState>((set, get) => ({
  attemptId: null,
  lessonId: null,
  queue: [],
  requeue: [],
  currentIndex: 0,
  currentExercise: null,
  selectedAnswer: null,
  feedbackStatus: 'idle',
  correctAnswerDisplay: null,
  explanation: null,
  heartsRemaining: 5,
  isChecking: false,
  totalInitialExercises: 0,
  answeredCount: 0,

  initLesson: (attempt: StartAttemptResponse) => {
    set({
      attemptId: attempt.attempt_id,
      lessonId: attempt.lesson_id,
      queue: attempt.exercises,
      requeue: [],
      currentIndex: 0,
      currentExercise: attempt.exercises[0] || null,
      selectedAnswer: null,
      feedbackStatus: 'idle',
      correctAnswerDisplay: null,
      explanation: null,
      heartsRemaining: attempt.hearts_remaining,
      isChecking: false,
      totalInitialExercises: attempt.exercises.length,
      answeredCount: 0,
    });
  },

  setSelectedAnswer: (answer: unknown) => {
    set({ selectedAnswer: answer });
  },

  setChecking: (checking: boolean) => {
    set({ isChecking: checking });
  },

  setFeedback: (status, correctAnswer, explanation = null, hearts) => {
    set((state) => ({
      feedbackStatus: status,
      correctAnswerDisplay: correctAnswer,
      explanation,
      heartsRemaining: hearts !== undefined ? hearts : state.heartsRemaining,
      isChecking: false,
    }));
  },

  advanceToNext: () => {
    const { queue, requeue, currentIndex, feedbackStatus, currentExercise } = get();

    // If answer was incorrect and exercise is known, add to requeue list
    const updatedRequeue = [...requeue];
    if (feedbackStatus === 'incorrect' && currentExercise) {
      updatedRequeue.push(currentExercise);
    }

    const nextIndex = currentIndex + 1;
    if (nextIndex < queue.length) {
      set({
        currentIndex: nextIndex,
        currentExercise: queue[nextIndex],
        selectedAnswer: null,
        feedbackStatus: 'idle',
        correctAnswerDisplay: null,
        explanation: null,
        requeue: updatedRequeue,
        answeredCount: get().answeredCount + (feedbackStatus === 'correct' ? 1 : 0),
      });
      return true;
    } else if (updatedRequeue.length > 0) {
      // Replay missed exercises
      const newQueue = updatedRequeue;
      set({
        queue: newQueue,
        requeue: [],
        currentIndex: 0,
        currentExercise: newQueue[0],
        selectedAnswer: null,
        feedbackStatus: 'idle',
        correctAnswerDisplay: null,
        explanation: null,
        answeredCount: get().answeredCount + (feedbackStatus === 'correct' ? 1 : 0),
      });
      return true;
    } else {
      // Finished all exercises
      set({
        currentExercise: null,
        feedbackStatus: 'idle',
        answeredCount: get().totalInitialExercises,
      });
      return false;
    }
  },

  updateHearts: (hearts: number) => {
    set({ heartsRemaining: hearts });
  },

  resetLesson: () => {
    set({
      attemptId: null,
      lessonId: null,
      queue: [],
      requeue: [],
      currentIndex: 0,
      currentExercise: null,
      selectedAnswer: null,
      feedbackStatus: 'idle',
      correctAnswerDisplay: null,
      explanation: null,
      heartsRemaining: 5,
      isChecking: false,
      totalInitialExercises: 0,
      answeredCount: 0,
    });
  },
}));
