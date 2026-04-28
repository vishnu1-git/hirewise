import React, { useEffect, useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from 'recharts';
import { getModelMetrics, getSessionStats } from '../utils/api';

const LABEL_COLORS = { Strong: '#10b981', Average: '#f59e0b', Weak: '#ef4444' };

function MetricCard({ label, value, suffix = '', color = '#a5b4fc' }) {
  return (
    <div className="card" style={{ textAlign: 'center', padding: '20px 16px' }}>
      <div style={{ fontSize: 12, color: 'var(--text3)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 8 }}>{label}</div>
      <div style={{ fontSize: 32, fontWeight: 800, color }}>{value !== null ? `${value}${suffix}` : '—'}</div>
    </div>
  );
}

export default function Analytics() {
  const [metrics, setMetrics] = useState(null);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([getModelMetrics(), getSessionStats()])
      .then(([m, s]) => { setMetrics(m.data); setStats(s.data); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh' }}>
      <div style={{ fontSize: 24, color: 'var(--text3)' }}>Loading analytics...</div>
    </div>
  );

  const featureData = metrics?.feature_importances
    ? Object.entries(metrics.feature_importances)
        .sort(([, a], [, b]) => b - a)
        .map(([name, val]) => ({ name: name.replace(/_/g, ' '), value: +(val * 100).toFixed(1) }))
    : [];

  const pieData = stats?.score_distribution
    ? Object.entries(stats.score_distribution).map(([name, value]) => ({ name, value }))
    : [];

  const cvData = metrics?.cv_scores?.map((v, i) => ({ fold: `Fold ${i + 1}`, score: +(v * 100).toFixed(1) })) || [];

  return (
    <div style={{ maxWidth: 1100, margin: '0 auto', padding: '32px' }}>
      <div className="fade-up" style={{ marginBottom: 32 }}>
        <h1 style={{ fontSize: 28, fontWeight: 800, marginBottom: 8 }}>📈 Analytics</h1>
        <p style={{ color: 'var(--text3)' }}>ML model performance metrics and platform usage stats</p>
      </div>

      {metrics?.message && (
        <div className="card fade-up" style={{ marginBottom: 24, borderColor: 'rgba(245,158,11,0.3)', background: 'rgba(245,158,11,0.05)', padding: '16px 20px' }}>
          <span style={{ color: '#fbbf24', fontSize: 14 }}>⚠️ {metrics.message}</span>
        </div>
      )}

      {/* ML Model Metrics */}
      <h2 style={{ fontSize: 16, color: 'var(--text3)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 16 }}>
        ML Model — {metrics?.model_name || 'Not trained'}
      </h2>
      <div className="grid-3" style={{ marginBottom: 24 }}>
        <MetricCard label="Accuracy" value={metrics?.accuracy != null ? (metrics.accuracy * 100).toFixed(1) : null} suffix="%" color="#10b981" />
        <MetricCard label="F1 Score" value={metrics?.f1_score != null ? (metrics.f1_score * 100).toFixed(1) : null} suffix="%" color="#6366f1" />
        <MetricCard label="Precision" value={metrics?.precision != null ? (metrics.precision * 100).toFixed(1) : null} suffix="%" color="#f59e0b" />
        <MetricCard label="Recall" value={metrics?.recall != null ? (metrics.recall * 100).toFixed(1) : null} suffix="%" color="#a855f7" />
        <MetricCard label="CV Mean" value={metrics?.cv_mean != null ? (metrics.cv_mean * 100).toFixed(1) : null} suffix="%" color="#22d3ee" />
        <MetricCard label="Training Samples" value={metrics?.training_samples ?? null} color="#fb7185" />
      </div>

      <div className="grid-2" style={{ marginBottom: 24 }}>
        {/* Feature importance */}
        {featureData.length > 0 && (
          <div className="card fade-up">
            <h3 style={{ fontSize: 14, color: 'var(--text3)', marginBottom: 16, textTransform: 'uppercase' }}>Feature Importance (%)</h3>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={featureData} layout="vertical">
                <XAxis type="number" tick={{ fill: 'var(--text3)', fontSize: 11 }} />
                <YAxis dataKey="name" type="category" tick={{ fill: 'var(--text2)', fontSize: 11 }} width={140} />
                <Tooltip formatter={v => v + '%'} contentStyle={{ background: 'var(--bg3)', border: '1px solid var(--border)', borderRadius: 8 }} />
                <Bar dataKey="value" fill="#6366f1" radius={4} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* CV scores */}
        {cvData.length > 0 && (
          <div className="card fade-up">
            <h3 style={{ fontSize: 14, color: 'var(--text3)', marginBottom: 16, textTransform: 'uppercase' }}>5-Fold Cross-Validation F1</h3>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={cvData}>
                <XAxis dataKey="fold" tick={{ fill: 'var(--text2)', fontSize: 12 }} />
                <YAxis domain={[80, 100]} tick={{ fill: 'var(--text3)', fontSize: 11 }} />
                <Tooltip formatter={v => v + '%'} contentStyle={{ background: 'var(--bg3)', border: '1px solid var(--border)', borderRadius: 8 }} />
                <Bar dataKey="score" fill="#10b981" radius={4} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {/* Platform Stats */}
      {stats && (
        <>
          <h2 style={{ fontSize: 16, color: 'var(--text3)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 16 }}>
            Platform Usage
          </h2>
          <div className="grid-2">
            <div className="card fade-up">
              <h3 style={{ fontSize: 14, color: 'var(--text3)', marginBottom: 16, textTransform: 'uppercase' }}>Score Distribution</h3>
              <ResponsiveContainer width="100%" height={200}>
                <PieChart>
                  <Pie data={pieData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={70} label={({ name, value }) => `${name}: ${value}`}>
                    {pieData.map((e, i) => <Cell key={i} fill={LABEL_COLORS[e.name] || '#6366f1'} />)}
                  </Pie>
                  <Legend wrapperStyle={{ fontSize: 12, color: 'var(--text2)' }} />
                  <Tooltip contentStyle={{ background: 'var(--bg3)', border: '1px solid var(--border)', borderRadius: 8 }} />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="card fade-up" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', gap: 16 }}>
              {[
                { label: 'Total Resumes Analyzed', value: stats.total_sessions, color: '#a5b4fc' },
                { label: 'Average Score', value: `${stats.average_score}/100`, color: '#fbbf24' },
                { label: 'Strong Resumes', value: stats.score_distribution?.Strong || 0, color: '#6ee7b7' },
              ].map(({ label, value, color }) => (
                <div key={label} style={{ padding: '14px 20px', background: 'var(--bg3)', borderRadius: 10 }}>
                  <div style={{ fontSize: 12, color: 'var(--text3)', marginBottom: 4 }}>{label}</div>
                  <div style={{ fontSize: 28, fontWeight: 800, color }}>{value}</div>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
