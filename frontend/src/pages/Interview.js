import React, { useState, useRef } from 'react';
import toast from 'react-hot-toast';
import { getQuestions, evaluateAnswer } from '../utils/api';

const GRADE_COLORS = { Excellent: '#10b981', Good: '#6366f1', Average: '#f59e0b', Poor: '#ef4444' };

export default function Interview({ sessionId, analysisData }) {
  const [step, setStep] = useState('setup'); // setup | questions | result
  const [difficulty, setDifficulty] = useState('medium');
  const [numQ, setNumQ] = useState(5);
  const [questions, setQuestions] = useState([]);
  const [currentQ, setCurrentQ] = useState(0);
  const [answers, setAnswers] = useState({});
  const [evaluations, setEvaluations] = useState({});
  const [loading, setLoading] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const recognitionRef = useRef(null);

  if (!sessionId) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh', flexDirection: 'column', gap: 16 }}>
        <div style={{ fontSize: 48 }}>🎤</div>
        <h2 style={{ color: 'var(--text2)' }}>Upload a resume first</h2>
        <a href="/" className="btn btn-primary">Upload Resume</a>
      </div>
    );
  }

  const startInterview = async () => {
    setLoading(true);
    try {
      const res = await getQuestions(sessionId, numQ, difficulty);
      setQuestions(res.data.questions);
      setCurrentQ(0);
      setAnswers({});
      setEvaluations({});
      setStep('questions');
    } catch {
      toast.error('Failed to generate questions. Check backend.');
    } finally {
      setLoading(false);
    }
  };

  const startVoice = () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) return toast.error('Voice not supported in this browser. Use Chrome.');
    const rec = new SpeechRecognition();
    rec.continuous = true;
    rec.interimResults = true;
    rec.lang = 'en-US';
    rec.onresult = (e) => {
      const t = Array.from(e.results).map(r => r[0].transcript).join(' ');
      setTranscript(t);
    };
    rec.onerror = () => setIsListening(false);
    rec.onend = () => setIsListening(false);
    recognitionRef.current = rec;
    rec.start();
    setIsListening(true);
    toast.success('Listening… speak your answer!');
  };

  const stopVoice = () => {
    recognitionRef.current?.stop();
    setIsListening(false);
    const q = questions[currentQ];
    setAnswers(prev => ({ ...prev, [q.id]: (prev[q.id] || '') + ' ' + transcript }));
    setTranscript('');
  };

  const submitAnswer = async () => {
    const q = questions[currentQ];
    const ans = (answers[q.id] || '').trim();
    if (!ans) return toast.error('Please write or speak an answer.');
    setLoading(true);
    try {
      const res = await evaluateAnswer(sessionId, q.id, q.question, ans, q.expected_concepts);
      setEvaluations(prev => ({ ...prev, [q.id]: res.data }));
      if (currentQ < questions.length - 1) {
        setCurrentQ(prev => prev + 1);
        setTranscript('');
      } else {
        setStep('result');
      }
    } catch {
      toast.error('Evaluation failed.');
    } finally {
      setLoading(false);
    }
  };

  // Setup screen
  if (step === 'setup') return (
    <div style={{ maxWidth: 600, margin: '0 auto', padding: '48px 32px' }}>
      <h1 style={{ fontSize: 28, fontWeight: 800, marginBottom: 8 }}>🎤 Mock Interview</h1>
      <p style={{ color: 'var(--text3)', marginBottom: 32 }}>AI generates questions tailored to your resume. Answer by typing or voice.</p>

      <div className="card" style={{ marginBottom: 20 }}>
        <h3 style={{ fontSize: 14, color: 'var(--text3)', marginBottom: 16, textTransform: 'uppercase' }}>Settings</h3>
        <div style={{ marginBottom: 16 }}>
          <label style={{ fontSize: 13, color: 'var(--text2)', display: 'block', marginBottom: 8 }}>Number of questions</label>
          <div style={{ display: 'flex', gap: 8 }}>
            {[3, 5, 8, 10].map(n => (
              <button key={n} onClick={() => setNumQ(n)}
                style={{ flex: 1, padding: '8px', borderRadius: 8, border: '1px solid', borderColor: numQ === n ? '#6366f1' : 'var(--border)', background: numQ === n ? 'rgba(99,102,241,0.15)' : 'transparent', color: numQ === n ? '#a5b4fc' : 'var(--text2)', cursor: 'pointer', fontWeight: numQ === n ? 700 : 400 }}>
                {n}
              </button>
            ))}
          </div>
        </div>
        <div>
          <label style={{ fontSize: 13, color: 'var(--text2)', display: 'block', marginBottom: 8 }}>Difficulty</label>
          <div style={{ display: 'flex', gap: 8 }}>
            {['easy', 'medium', 'hard'].map(d => (
              <button key={d} onClick={() => setDifficulty(d)}
                style={{ flex: 1, padding: '8px', borderRadius: 8, border: '1px solid', textTransform: 'capitalize', borderColor: difficulty === d ? '#6366f1' : 'var(--border)', background: difficulty === d ? 'rgba(99,102,241,0.15)' : 'transparent', color: difficulty === d ? '#a5b4fc' : 'var(--text2)', cursor: 'pointer', fontWeight: difficulty === d ? 700 : 400 }}>
                {d}
              </button>
            ))}
          </div>
        </div>
      </div>

      {analysisData?.profile?.skills?.length > 0 && (
        <div className="card" style={{ marginBottom: 24 }}>
          <div style={{ fontSize: 13, color: 'var(--text3)', marginBottom: 8 }}>Questions will focus on:</div>
          <div style={{ display: 'flex', flexWrap: 'wrap' }}>
            {analysisData.profile.skills.slice(0, 8).map(s => <span key={s} className="skill-tag">{s}</span>)}
          </div>
        </div>
      )}

      <button className="btn btn-primary" onClick={startInterview} disabled={loading} style={{ width: '100%', justifyContent: 'center', padding: '14px', fontSize: 16 }}>
        {loading ? '⏳ Generating questions...' : '🚀 Start Interview'}
      </button>
    </div>
  );

  // Question screen
  if (step === 'questions') {
    const q = questions[currentQ];
    const eval_ = evaluations[q.id];
    const progress = ((currentQ) / questions.length) * 100;

    return (
      <div style={{ maxWidth: 700, margin: '0 auto', padding: '32px' }}>
        {/* Progress */}
        <div style={{ marginBottom: 24 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, color: 'var(--text3)', marginBottom: 8 }}>
            <span>Question {currentQ + 1} of {questions.length}</span>
            <span style={{ color: '#a5b4fc' }}>{q.category} · {q.difficulty}</span>
          </div>
          <div style={{ height: 4, background: 'var(--bg3)', borderRadius: 2 }}>
            <div style={{ height: '100%', width: `${progress}%`, background: 'linear-gradient(90deg, #6366f1, #818cf8)', borderRadius: 2, transition: 'width 0.3s' }} />
          </div>
        </div>

        <div className="card" style={{ marginBottom: 20 }}>
          <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
            <span className="badge" style={{ background: 'rgba(99,102,241,0.15)', color: '#a5b4fc' }}>{q.category}</span>
            <span className="badge" style={{ background: 'rgba(245,158,11,0.15)', color: '#fbbf24' }}>{q.difficulty}</span>
          </div>
          <p style={{ fontSize: 17, fontWeight: 600, lineHeight: 1.5, color: 'var(--text)' }}>{q.question}</p>
          {q.expected_concepts?.length > 0 && (
            <div style={{ marginTop: 12, fontSize: 12, color: 'var(--text3)' }}>
              Hint: cover — {q.expected_concepts.slice(0, 3).join(', ')}
            </div>
          )}
        </div>

        {/* Voice status */}
        {isListening && (
          <div className="card fade-up" style={{ marginBottom: 12, padding: '12px 16px', borderColor: '#ef4444', background: 'rgba(239,68,68,0.05)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <div style={{ width: 10, height: 10, borderRadius: '50%', background: '#ef4444', animation: 'pulse 1s infinite' }} />
              <span style={{ fontSize: 13, color: '#f87171' }}>Listening… {transcript.slice(-80)}</span>
            </div>
          </div>
        )}

        {/* Answer input */}
        <textarea
          rows={6}
          placeholder="Type your answer here, or use voice input below…"
          value={answers[q.id] || ''}
          onChange={e => setAnswers(prev => ({ ...prev, [q.id]: e.target.value }))}
          style={{ width: '100%', marginBottom: 12, padding: '14px', background: 'var(--bg3)', border: '1px solid var(--border)', borderRadius: 8, color: 'var(--text)', fontSize: 14, resize: 'vertical' }}
        />

        <div style={{ display: 'flex', gap: 10 }}>
          <button
            className="btn"
            onClick={isListening ? stopVoice : startVoice}
            style={{ background: isListening ? 'rgba(239,68,68,0.15)' : 'rgba(99,102,241,0.15)', color: isListening ? '#f87171' : '#a5b4fc', border: `1px solid ${isListening ? 'rgba(239,68,68,0.3)' : 'var(--border)'}` }}
          >
            {isListening ? '⏹ Stop Recording' : '🎤 Voice Input'}
          </button>
          <button className="btn btn-primary" onClick={submitAnswer} disabled={loading} style={{ flex: 1, justifyContent: 'center' }}>
            {loading ? '⏳ Evaluating...' : currentQ === questions.length - 1 ? '✅ Submit Final Answer' : '➡ Submit & Next'}
          </button>
        </div>

        {/* Live eval result for previous question */}
        {eval_ && (
          <div className="card fade-up" style={{ marginTop: 20, borderColor: GRADE_COLORS[eval_.grade] + '44' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
              <span style={{ fontWeight: 700, color: GRADE_COLORS[eval_.grade] }}>{eval_.grade} — {eval_.score}/10</span>
              <span style={{ fontSize: 12, color: 'var(--text3)' }}>Similarity: {(eval_.similarity_score * 100).toFixed(0)}%</span>
            </div>
            <p style={{ fontSize: 13, color: 'var(--text2)', marginBottom: 8 }}>{eval_.detailed_feedback}</p>
            {eval_.missing_concepts?.length > 0 && (
              <div style={{ fontSize: 12, color: '#fca5a5' }}>Missing: {eval_.missing_concepts.join(', ')}</div>
            )}
          </div>
        )}

        <style>{`@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.4} }`}</style>
      </div>
    );
  }

  // Results screen
  const scores = Object.values(evaluations).map(e => e.score);
  const avgScore = scores.length ? (scores.reduce((a, b) => a + b, 0) / scores.length).toFixed(1) : 0;
  const overallGrade = avgScore >= 8 ? 'Excellent' : avgScore >= 6.5 ? 'Good' : avgScore >= 5 ? 'Average' : 'Needs Work';

  return (
    <div style={{ maxWidth: 800, margin: '0 auto', padding: '32px' }}>
      <div style={{ textAlign: 'center', marginBottom: 40 }} className="fade-up">
        <div style={{ fontSize: 56, marginBottom: 16 }}>{avgScore >= 7 ? '🎉' : avgScore >= 5 ? '📚' : '💪'}</div>
        <h1 style={{ fontSize: 28, fontWeight: 800, marginBottom: 8 }}>Interview Complete!</h1>
        <div style={{ fontSize: 48, fontWeight: 800, color: GRADE_COLORS[overallGrade] || '#6366f1', marginBottom: 4 }}>{avgScore}/10</div>
        <div style={{ fontSize: 18, color: 'var(--text2)' }}>{overallGrade}</div>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
        {questions.map((q, i) => {
          const ev = evaluations[q.id];
          if (!ev) return null;
          return (
            <div key={q.id} className="card fade-up" style={{ borderLeft: `3px solid ${GRADE_COLORS[ev.grade]}` }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                <span style={{ fontSize: 12, color: 'var(--text3)' }}>Q{i + 1} · {q.category}</span>
                <span style={{ fontWeight: 700, color: GRADE_COLORS[ev.grade] }}>{ev.grade} {ev.score}/10</span>
              </div>
              <p style={{ fontWeight: 600, marginBottom: 8, fontSize: 14 }}>{q.question}</p>
              <p style={{ fontSize: 13, color: 'var(--text2)', marginBottom: 8 }}>{ev.detailed_feedback}</p>
              {ev.strengths?.length > 0 && (
                <div style={{ fontSize: 12, color: '#6ee7b7', marginBottom: 4 }}>✓ {ev.strengths[0]}</div>
              )}
              {ev.improvements?.length > 0 && (
                <div style={{ fontSize: 12, color: '#fca5a5' }}>↑ {ev.improvements[0]}</div>
              )}
            </div>
          );
        })}
      </div>

      <div style={{ display: 'flex', gap: 12, marginTop: 24 }}>
        <button className="btn btn-outline" onClick={() => { setStep('setup'); setEvaluations({}); }}>
          🔄 Try Again
        </button>
        <button className="btn btn-primary" onClick={() => setStep('setup')}>
          ⚙️ New Settings
        </button>
      </div>
    </div>
  );
}
