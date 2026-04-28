import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: `${API_URL}/api`,
  timeout: 60000,
});

// Resume
export const analyzeResume = (file) => {
  const form = new FormData();
  form.append('file', file);
  return api.post('/resume/analyze', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
};

export const getSession = (sessionId) =>
  api.get(`/resume/session/${sessionId}`);

// Match
export const matchJD = (sessionId, jobDescription, jobTitle) =>
  api.post('/match/', { session_id: sessionId, job_description: jobDescription, job_title: jobTitle });

// Interview
export const getQuestions = (sessionId, numQuestions = 5, difficulty = 'medium', focusAreas = null) =>
  api.post('/interview/questions', {
    session_id: sessionId,
    num_questions: numQuestions,
    difficulty,
    focus_areas: focusAreas,
  });

export const evaluateAnswer = (sessionId, questionId, questionText, userAnswer, expectedConcepts) =>
  api.post('/interview/evaluate', {
    session_id: sessionId,
    question_id: questionId,
    question_text: questionText,
    user_answer: userAnswer,
    expected_concepts: expectedConcepts,
  });

export const getInterviewHistory = (sessionId) =>
  api.get(`/interview/history/${sessionId}`);

// Compare
export const compareRoles = (sessionId, jobDescriptions) =>
  api.post('/compare/', { session_id: sessionId, job_descriptions: jobDescriptions });

// Analytics
export const getModelMetrics = () => api.get('/analytics/model-metrics');
export const getSessionStats = () => api.get('/analytics/sessions/stats');

export default api;
