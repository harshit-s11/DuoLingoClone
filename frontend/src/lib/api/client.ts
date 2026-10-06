import type { paths } from './schema';

export type HealthResponse =
  paths['/health']['get']['responses']['200']['content']['application/json'];
export type UserResponse =
  paths['/api/me']['get']['responses']['200']['content']['application/json'];
export type ProfileResponse =
  paths['/api/profile']['get']['responses']['200']['content']['application/json'];
export type SettingsResponse =
  paths['/api/settings']['get']['responses']['200']['content']['application/json'];
export type CourseItem =
  paths['/api/courses']['get']['responses']['200']['content']['application/json'][number];
export type CoursePathResponse =
  paths['/api/courses/{course_id}/path']['get']['responses']['200']['content']['application/json'];
export type LessonMetadataResponse =
  paths['/api/lessons/{lesson_id}']['get']['responses']['200']['content']['application/json'];
export type StartAttemptResponse =
  paths['/api/lessons/{lesson_id}/start']['post']['responses']['201']['content']['application/json'];
export type CheckAnswerRequest =
  paths['/api/attempts/{attempt_id}/check']['post']['requestBody']['content']['application/json'];
export type CheckAnswerResponse =
  paths['/api/attempts/{attempt_id}/check']['post']['responses']['200']['content']['application/json'];
export type CompleteAttemptResponse =
  paths['/api/attempts/{attempt_id}/complete']['post']['responses']['200']['content']['application/json'];
export type AbandonAttemptResponse =
  paths['/api/attempts/{attempt_id}/abandon']['post']['responses']['200']['content']['application/json'];
export type RefillHeartsRequest =
  paths['/api/hearts/refill']['post']['requestBody']['content']['application/json'];
export type RefillHeartsResponse =
  paths['/api/hearts/refill']['post']['responses']['200']['content']['application/json'];
export type LeaderboardResponse =
  paths['/api/leaderboard']['get']['responses']['200']['content']['application/json'];
export type AchievementItem =
  paths['/api/achievements']['get']['responses']['200']['content']['application/json'][number];
export type AdvanceDayRequest =
  paths['/api/debug/advance-day']['post']['requestBody']['content']['application/json'];
export type AdvanceDayResponse =
  paths['/api/debug/advance-day']['post']['responses']['200']['content']['application/json'];

const DEFAULT_USER_ID = 1;

/**
 * Universal fetch wrapper applying X-User-Id header and error handling.
 */
export async function fetchApi<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers || {});
  if (!headers.has('X-User-Id')) {
    headers.set('X-User-Id', String(DEFAULT_USER_ID));
  }
  if (!headers.has('Content-Type') && options.body && typeof options.body === 'string') {
    headers.set('Content-Type', 'application/json');
  }

  const response = await fetch(endpoint, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorDetail = `Request failed with status ${response.status}`;
    try {
      const data = await response.json();
      if (data?.detail) {
        errorDetail = typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail);
      }
    } catch {
      // Fallback to HTTP error
    }
    throw new Error(errorDetail);
  }

  return response.json();
}

/* ==================== Strongly Typed Client Functions ==================== */

export async function fetchHealth(): Promise<HealthResponse> {
  return fetchApi<HealthResponse>('/api/health');
}

export async function fetchMe(): Promise<UserResponse> {
  return fetchApi<UserResponse>('/api/me');
}

export async function fetchProfile(): Promise<ProfileResponse> {
  return fetchApi<ProfileResponse>('/api/profile');
}

export async function fetchSettings(): Promise<SettingsResponse> {
  return fetchApi<SettingsResponse>('/api/settings');
}

export async function updateSettings(timezone: string): Promise<SettingsResponse> {
  return fetchApi<SettingsResponse>('/api/settings', {
    method: 'PATCH',
    body: JSON.stringify({ timezone }),
  });
}

export async function fetchCourses(): Promise<CourseItem[]> {
  return fetchApi<CourseItem[]>('/api/courses');
}

export async function fetchCoursePath(courseId: number): Promise<CoursePathResponse> {
  return fetchApi<CoursePathResponse>(`/api/courses/${courseId}/path`);
}

export async function fetchLessonMetadata(lessonId: number): Promise<LessonMetadataResponse> {
  return fetchApi<LessonMetadataResponse>(`/api/lessons/${lessonId}`);
}

export async function startAttempt(lessonId: number): Promise<StartAttemptResponse> {
  return fetchApi<StartAttemptResponse>(`/api/lessons/${lessonId}/start`, {
    method: 'POST',
  });
}

export async function checkAnswer(
  attemptId: number,
  payload: CheckAnswerRequest
): Promise<CheckAnswerResponse> {
  return fetchApi<CheckAnswerResponse>(`/api/attempts/${attemptId}/check`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function completeAttempt(attemptId: number): Promise<CompleteAttemptResponse> {
  return fetchApi<CompleteAttemptResponse>(`/api/attempts/${attemptId}/complete`, {
    method: 'POST',
    body: JSON.stringify({}),
  });
}

export async function abandonAttempt(attemptId: number): Promise<AbandonAttemptResponse> {
  return fetchApi<AbandonAttemptResponse>(`/api/attempts/${attemptId}/abandon`, {
    method: 'POST',
    body: JSON.stringify({}),
  });
}

export async function refillHearts(payload: RefillHeartsRequest): Promise<RefillHeartsResponse> {
  return fetchApi<RefillHeartsResponse>('/api/hearts/refill', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function fetchLeaderboard(): Promise<LeaderboardResponse> {
  return fetchApi<LeaderboardResponse>('/api/leaderboard');
}

export async function fetchAchievements(): Promise<AchievementItem[]> {
  return fetchApi<AchievementItem[]>('/api/achievements');
}

export async function advanceDebugDay(days: number): Promise<AdvanceDayResponse> {
  return fetchApi<AdvanceDayResponse>('/api/debug/advance-day', {
    method: 'POST',
    body: JSON.stringify({ days }),
  });
}
