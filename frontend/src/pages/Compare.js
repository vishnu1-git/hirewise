import React, { useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import toast from 'react-hot-toast';
import { compareRoles } from '../utils/api';

const COLORS = ['#10b981', '#6366f1', '#f59e0b', '#ef4444', '#a855f7'];

export default function Compare({ sessionId }) {
  const [roles, setRoles] = useState([
    { title: '', description: '' },
    { title: '', description: '' },
  ]);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  if (!sessionId) return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh', flexDirection: 'column', gap: 16 }}>
      <div style={{ fontSize: 48 }}>⚖️</div>
      <h2 style={{ color: 'var(--text2)' }}>Upload a resume first</h2>
      <a href="/" className="btn btn-primary">Upload Resume</a>
    </div>
  );

  const addRole = () => {
    if (roles.length >= 5) return toast.error('Max 5 roles');
    setRoles(prev => [...prev, { title: '', description: '' }]);
  };

  const updateRole = (i, field, val) => {
    setRoles(prev => prev.map((r, idx) => idx === i ? { ...r, [field]: val } : r));
  };

  const removeRole = (i) => setRoles(prev => prev.filter((_, idx) => idx !== i));

  const handleCompare = async () => {
    const valid = roles.filter(r => r.description.trim().length > 20);
    if (valid.length < 2) return toast.error('Add at least 2 roles with descriptions (20+ chars).');
    setLoading(true);
    try {
      const res = await compareRoles(sessionId, valid.map(r => ({ title: r.title || 'Role', description: r.description })));
      setResult(res.data);
    } catch {
      toast.error('Compare failed. Check backend.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: 900, margin: '0 auto', padding: '32px' }}>
      <div className="fade-up" style={{ marginBottom: 32 }}>
        <h1 style={{ fontSize: 28, fontWeight: 800, marginBottom: 8 }}>⚖️ Compare Roles</h1>
        <p style={{ color: 'var(--text3)' }}>Paste up to 5 job descriptions to find your best match</p>
      </div>

      {/* Role inputs */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 16, marginBottom: 20 }}>
        {roles.map((role, i) => (
          <div key={i} className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
              <span style={{ fontSize: 13, fontWeight: 600, color: '#a5b4fc' }}>Role {i + 1}</span>
              {roles.length > 2 && (
                <button onClick={() => removeRole(i)} style={{ background: 'none', border: 'none', color: 'var(--text3)', cursor: 'pointer', fontSize: 18 }}>✕</button>
              )}
            </div>
            <input
              placeholder="Job title (e.g. ML Engineer)"
              value={role.title}
              onChange={e => updateRole(i, 'title', e.target.value)}
              style={{ width: '100%', marginBottom: 8, padding: '9px 12px', background: 'var(--bg3)', border: '1px solid var(--border)', borderRadius: 8, color: 'var(--text)', fontSize: 13 }}
            />
            <textarea
              rows={5}
              placeholder="Paste job description here…"
              value={role.description}
              onChange={e => updateRole(i, 'description', e.target.value)}
              style={{ width: '100%', padding: '9px 12px', background: 'var(--bg3)', border: '1px solid var(--border)', borderRadius: 8, color: 'var(--text)', fontSize: 13, resize: 'vertical' }}
            />
          </div>
        ))}
      </div>

      <div style={{ display: 'flex', gap: 10, marginBottom: 32 }}>
        <button className="btn btn-outline" onClick={addRole}>+ Add Role</button>
        <button className="btn btn-primary" onClick={handleCompare} disabled={loading} style={{ flex: 1, justifyContent: 'center' }}>
          {loading ? '⏳ Comparing...' : '🔍 Compare All Roles'}
        </button>
      </div>

      {/* Results */}
      {result && (
        <div className="fade-up">
          {/* Best fit banner */}
          <div className="card" style={{ marginBottom: 24, background: 'rgba(16,185,129,0.08)', borderColor: 'rgba(16,185,129,0.3)', textAlign: 'center', padding: '24px' }}>
            <div style={{ fontSize: 12, color: '#6ee7b7', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 8 }}>Best Fit Role</div>
            <div style={{ fontSize: 28, fontWeight: 800, color: '#10b981', marginBottom: 8 }}>🏆 {result.best_fit}</div>
            <p style={{ color: 'var(--text2)', fontSize: 14 }}>{result.analysis_summary}</p>
          </div>

          {/* Bar chart */}
          <div className="card" style={{ marginBottom: 24 }}>
            <h3 style={{ fontSize: 14, color: 'var(--text3)', marginBottom: 16, textTransform: 'uppercase' }}>Match Scores</h3>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={result.rankings.map(r => ({ name: r.job_title.slice(0, 20), score: r.match_score, rank: r.rank }))}>
                <XAxis dataKey="name" tick={{ fill: 'var(--text2)', fontSize: 12 }} />
                <YAxis domain={[0, 100]} tick={{ fill: 'var(--text3)', fontSize: 11 }} />
                <Tooltip formatter={v => v.toFixed(1) + '%'} contentStyle={{ background: 'var(--bg3)', border: '1px solid var(--border)', borderRadius: 8 }} />
                <Bar dataKey="score" radius={6}>
                  {result.rankings.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Rankings */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {result.rankings.map((r, i) => (
              <div key={i} className="card" style={{ borderLeft: `3px solid ${COLORS[i % COLORS.length]}` }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
                  <div>
                    <span style={{ fontSize: 11, color: 'var(--text3)', marginRight: 8 }}>#{r.rank}</span>
                    <span style={{ fontWeight: 700, fontSize: 16 }}>{r.job_title}</span>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontSize: 24, fontWeight: 800, color: COLORS[i % COLORS.length] }}>{r.match_score.toFixed(0)}%</div>
                    <div style={{ fontSize: 11, color: 'var(--text3)' }}>{r.match_result.role_fit_label}</div>
                  </div>
                </div>
                <p style={{ fontSize: 13, color: 'var(--text2)', marginBottom: 10 }}>{r.recommendation}</p>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                  {r.match_result.matched_skills.slice(0, 6).map(s => <span key={s} className="skill-tag matched" style={{ fontSize: 11 }}>{s}</span>)}
                  {r.match_result.missing_skills.slice(0, 4).map(s => <span key={s} className="skill-tag missing" style={{ fontSize: 11 }}>{s}</span>)}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
