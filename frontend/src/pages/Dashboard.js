import React, { useState } from 'react';
import { RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import toast from 'react-hot-toast';
import { matchJD } from '../utils/api';

function ScoreRing({ score, label }) {
  const r = 54, circ = 2 * Math.PI * r;
  const dash = (score / 100) * circ;
  const color = score >= 70 ? '#10b981' : score >= 45 ? '#f59e0b' : '#ef4444';
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
      <svg width={140} height={140} viewBox="0 0 140 140">
        <circle cx={70} cy={70} r={r} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth={10} />
        <circle cx={70} cy={70} r={r} fill="none" stroke={color} strokeWidth={10}
          strokeDasharray={`${dash} ${circ}`} strokeLinecap="round"
          transform="rotate(-90 70 70)"
          style={{ animation: 'scoreIn 1s ease both', transition: 'all 0.5s' }}
        />
        <text x={70} y={64} textAnchor="middle" fill={color} fontSize={28} fontWeight={800}>{score?.toFixed(0)}</text>
        <text x={70} y={82} textAnchor="middle" fill="rgba(255,255,255,0.5)" fontSize={12}>/100</text>
      </svg>
      <span className={`badge badge-${label?.toLowerCase()}`} style={{ marginTop: 4 }}>{label}</span>
    </div>
  );
}

function SHAPBar({ explanations }) {
  if (!explanations?.length) return null;
  const data = explanations.slice(0, 8).map(e => ({
    name: e.feature.length > 18 ? e.feature.slice(0, 18) + '…' : e.feature,
    impact: Math.abs(e.impact * 100),
    dir: e.direction,
  }));
  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart data={data} layout="vertical" margin={{ left: 8, right: 16 }}>
        <XAxis type="number" tick={{ fill: 'var(--text3)', fontSize: 11 }} />
        <YAxis dataKey="name" type="category" tick={{ fill: 'var(--text2)', fontSize: 12 }} width={130} />
        <Tooltip formatter={(v) => v.toFixed(2)} contentStyle={{ background: 'var(--bg3)', border: '1px solid var(--border)', borderRadius: 8 }} />
        <Bar dataKey="impact" radius={4}>
          {data.map((d, i) => <Cell key={i} fill={d.dir === 'positive' ? '#10b981' : '#ef4444'} />)}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

export default function Dashboard({ sessionId, analysisData }) {
  const [jdText, setJdText] = useState('');
  const [jobTitle, setJobTitle] = useState('');
  const [matchResult, setMatchResult] = useState(null);
  const [matchLoading, setMatchLoading] = useState(false);

  if (!analysisData) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh', flexDirection: 'column', gap: 16 }}>
        <div style={{ fontSize: 48 }}>📊</div>
        <h2 style={{ color: 'var(--text2)' }}>No resume analyzed yet</h2>
        <a href="/" className="btn btn-primary">Upload a Resume</a>
      </div>
    );
  }

  const { profile, resume_score } = analysisData;

  const radarData = [
    { subject: 'Skills', value: Math.min(profile.skills?.length * 5, 100) },
    { subject: 'Experience', value: Math.min(profile.experience_years * 15, 100) },
    { subject: 'Projects', value: profile.project_complexity_score * 10 },
    { subject: 'Education', value: { PhD: 100, Masters: 80, Bachelors: 60, Diploma: 40 }[profile.education_level] || 20 },
    { subject: 'ML/AI', value: profile.skills?.some(s => ['Machine Learning','Python','TensorFlow','PyTorch'].includes(s)) ? 80 : 20 },
    { subject: 'Cloud', value: profile.skills?.some(s => ['AWS','GCP','Azure','Docker'].includes(s)) ? 80 : 20 },
  ];

  const handleMatch = async () => {
    if (!jdText.trim()) return toast.error('Paste a job description first.');
    setMatchLoading(true);
    try {
      const res = await matchJD(sessionId, jdText, jobTitle);
      setMatchResult(res.data);
      toast.success('Match computed!');
    } catch {
      toast.error('Match failed. Check backend.');
    } finally {
      setMatchLoading(false);
    }
  };

  return (
    <div style={{ padding: '32px', maxWidth: 1200, margin: '0 auto' }}>
      <div className="fade-up">
        <h1 style={{ fontSize: 28, fontWeight: 800, marginBottom: 4 }}>Resume Dashboard</h1>
        <p style={{ color: 'var(--text3)', marginBottom: 32 }}>
          {profile.name ? `Analysis for ${profile.name}` : 'Full AI analysis results'}
        </p>
      </div>

      {/* Top row: Score + Profile + Radar */}
      <div style={{ display: 'grid', gridTemplateColumns: '200px 1fr 280px', gap: 20, marginBottom: 20 }}>
        {/* Score card */}
        <div className="card fade-up" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 12 }}>
          <ScoreRing score={resume_score.score} label={resume_score.label} />
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: 12, color: 'var(--text3)' }}>Confidence</div>
            <div style={{ fontWeight: 700, color: '#a5b4fc' }}>{(resume_score.confidence * 100).toFixed(0)}%</div>
          </div>
        </div>

        {/* Profile info */}
        <div className="card fade-up">
          <h3 style={{ fontSize: 14, color: 'var(--text3)', marginBottom: 16, textTransform: 'uppercase', letterSpacing: '0.08em' }}>Extracted Profile</h3>
          <div className="grid-2" style={{ gap: 12 }}>
            {[
              ['🎓 Education', profile.education_level + (profile.education_field ? ` — ${profile.education_field}` : '')],
              ['💼 Experience', `${profile.experience_years} years`],
              ['🛠 Skills Found', `${profile.skills?.length || 0} skills`],
              ['🚀 Complexity', `${profile.project_complexity_score}/10`],
              ['📧 Email', profile.email || 'Not detected'],
              ['📱 Phone', profile.phone || 'Not detected'],
            ].map(([k, v]) => (
              <div key={k} style={{ padding: '10px 14px', background: 'var(--bg3)', borderRadius: 8 }}>
                <div style={{ fontSize: 12, color: 'var(--text3)', marginBottom: 2 }}>{k}</div>
                <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text)' }}>{v}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Radar */}
        <div className="card fade-up">
          <h3 style={{ fontSize: 14, color: 'var(--text3)', marginBottom: 8, textTransform: 'uppercase', letterSpacing: '0.08em' }}>Profile Radar</h3>
          <ResponsiveContainer width="100%" height={180}>
            <RadarChart data={radarData}>
              <PolarGrid stroke="rgba(255,255,255,0.08)" />
              <PolarAngleAxis dataKey="subject" tick={{ fill: 'var(--text3)', fontSize: 10 }} />
              <PolarRadiusAxis domain={[0, 100]} tick={false} axisLine={false} />
              <Radar dataKey="value" stroke="#6366f1" fill="#6366f1" fillOpacity={0.2} strokeWidth={2} />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Skills */}
      <div className="card fade-up" style={{ marginBottom: 20 }}>
        <h3 style={{ fontSize: 14, color: 'var(--text3)', marginBottom: 16, textTransform: 'uppercase', letterSpacing: '0.08em' }}>
          Detected Skills ({profile.skills?.length || 0})
        </h3>
        <div style={{ display: 'flex', flexWrap: 'wrap' }}>
          {profile.skills?.map(s => <span key={s} className="skill-tag">{s}</span>)}
          {!profile.skills?.length && <span style={{ color: 'var(--text3)' }}>No skills detected. Ensure resume has readable text.</span>}
        </div>
      </div>

      {/* SHAP Explainability + Feedback */}
      <div className="grid-2" style={{ marginBottom: 20 }}>
        <div className="card fade-up">
          <h3 style={{ fontSize: 14, color: 'var(--text3)', marginBottom: 4, textTransform: 'uppercase', letterSpacing: '0.08em' }}>
            SHAP Feature Impact
          </h3>
          <p style={{ fontSize: 12, color: 'var(--text3)', marginBottom: 16 }}>
            Green = boosted your score | Red = dragged it down
          </p>
          <SHAPBar explanations={resume_score.shap_explanations} />
          {!resume_score.shap_explanations?.length && (
            <p style={{ color: 'var(--text3)', fontSize: 13 }}>Train the ML model to see SHAP explanations.</p>
          )}
        </div>

        <div className="card fade-up">
          <h3 style={{ fontSize: 14, color: 'var(--text3)', marginBottom: 16, textTransform: 'uppercase', letterSpacing: '0.08em' }}>
            AI Feedback
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {resume_score.feedback?.map((f, i) => (
              <div key={i} style={{
                padding: '10px 14px',
                background: f.startsWith('✓') ? 'rgba(16,185,129,0.08)' : 'rgba(99,102,241,0.08)',
                border: `1px solid ${f.startsWith('✓') ? 'rgba(16,185,129,0.2)' : 'var(--border)'}`,
                borderRadius: 8,
                fontSize: 13,
                color: f.startsWith('✓') ? '#6ee7b7' : 'var(--text2)',
              }}>
                {f}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* JD Match */}
      <div className="card fade-up" style={{ marginBottom: 20 }}>
        <h3 style={{ fontSize: 16, fontWeight: 700, marginBottom: 4 }}>📎 Job Description Matcher</h3>
        <p style={{ color: 'var(--text3)', fontSize: 13, marginBottom: 16 }}>
          Paste a job description to get semantic + skill-based match score
        </p>
        <input
          placeholder="Job title (optional)"
          value={jobTitle}
          onChange={e => setJobTitle(e.target.value)}
          style={{ width: '100%', marginBottom: 10, padding: '10px 14px', background: 'var(--bg3)', border: '1px solid var(--border)', borderRadius: 8, color: 'var(--text)', fontSize: 14 }}
        />
        <textarea
          rows={6}
          placeholder="Paste the full job description here..."
          value={jdText}
          onChange={e => setJdText(e.target.value)}
          style={{ width: '100%', marginBottom: 14, padding: '12px 14px', background: 'var(--bg3)', border: '1px solid var(--border)', borderRadius: 8, color: 'var(--text)', fontSize: 14, resize: 'vertical' }}
        />
        <button className="btn btn-primary" onClick={handleMatch} disabled={matchLoading}>
          {matchLoading ? '⏳ Matching...' : '🔍 Match Resume to JD'}
        </button>

        {matchResult && (
          <div style={{ marginTop: 20, display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            {/* Score */}
            <div style={{ padding: '16px', background: 'var(--bg3)', borderRadius: 10 }}>
              <div style={{ fontSize: 12, color: 'var(--text3)', marginBottom: 4 }}>Match Score</div>
              <div style={{ fontSize: 36, fontWeight: 800, color: matchResult.match_result.match_score >= 65 ? '#10b981' : matchResult.match_result.match_score >= 45 ? '#f59e0b' : '#ef4444' }}>
                {matchResult.match_result.match_score.toFixed(0)}%
              </div>
              <div style={{ fontSize: 13, color: 'var(--text2)', marginTop: 4 }}>{matchResult.match_result.role_fit_label} fit</div>
            </div>
            <div style={{ padding: '16px', background: 'var(--bg3)', borderRadius: 10, fontSize: 13, color: 'var(--text2)', lineHeight: 1.6 }}>
              <div style={{ fontWeight: 600, color: 'var(--text)', marginBottom: 6 }}>Recommendation</div>
              {matchResult.recommendation}
            </div>
            {/* Skills diff */}
            <div style={{ gridColumn: '1/-1' }}>
              <div style={{ marginBottom: 8, fontSize: 13, fontWeight: 600, color: '#6ee7b7' }}>✓ Matched Skills</div>
              <div style={{ display: 'flex', flexWrap: 'wrap', marginBottom: 12 }}>
                {matchResult.match_result.matched_skills.map(s => <span key={s} className="skill-tag matched">{s}</span>)}
              </div>
              <div style={{ marginBottom: 8, fontSize: 13, fontWeight: 600, color: '#fca5a5' }}>✗ Missing Skills</div>
              <div style={{ display: 'flex', flexWrap: 'wrap' }}>
                {matchResult.match_result.missing_skills.slice(0, 15).map(s => <span key={s} className="skill-tag missing">{s}</span>)}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Projects */}
      {profile.projects?.length > 0 && (
        <div className="card fade-up">
          <h3 style={{ fontSize: 14, color: 'var(--text3)', marginBottom: 16, textTransform: 'uppercase', letterSpacing: '0.08em' }}>
            Detected Projects
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {profile.projects.map((p, i) => (
              <div key={i} style={{ padding: '10px 14px', background: 'var(--bg3)', borderRadius: 8, fontSize: 13, color: 'var(--text2)' }}>
                🔧 {p}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
