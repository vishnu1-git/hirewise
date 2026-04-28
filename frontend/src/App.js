import React, { useState } from 'react';
import { Routes, Route, NavLink, useNavigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import Upload from './pages/Upload';
import Dashboard from './pages/Dashboard';
import Interview from './pages/Interview';
import Compare from './pages/Compare';
import Analytics from './pages/Analytics';

export default function App() {
  const [sessionId, setSessionId] = useState(null);
  const [analysisData, setAnalysisData] = useState(null);
  const navigate = useNavigate();

  const onAnalyzed = (data) => {
    setSessionId(data.session_id);
    setAnalysisData(data);
    navigate('/dashboard');
  };

  const navItems = [
    { to: '/', label: 'Upload', icon: '📄' },
    { to: '/dashboard', label: 'Dashboard', icon: '📊' },
    { to: '/interview', label: 'Interview', icon: '🎤' },
    { to: '/compare', label: 'Compare Roles', icon: '⚖️' },
    { to: '/analytics', label: 'Analytics', icon: '📈' },
  ];

  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      {/* Sidebar */}
      <nav style={{
        width: 220,
        background: 'var(--bg2)',
        borderRight: '1px solid var(--border)',
        display: 'flex',
        flexDirection: 'column',
        padding: '24px 0',
        position: 'fixed',
        top: 0, left: 0, bottom: 0,
        zIndex: 100,
      }}>
        {/* Logo */}
        <div style={{ padding: '0 20px 28px' }}>
          <div style={{ fontSize: 22, fontWeight: 800, color: '#a5b4fc' }}>
            🧠 HireWise
          </div>
          <div style={{ fontSize: 11, color: 'var(--text3)', marginTop: 2 }}>
            AI Resume Analyzer
          </div>
        </div>

        {navItems.map(({ to, label, icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            style={({ isActive }) => ({
              display: 'flex',
              alignItems: 'center',
              gap: 10,
              padding: '10px 20px',
              color: isActive ? '#a5b4fc' : 'var(--text2)',
              background: isActive ? 'rgba(99,102,241,0.12)' : 'transparent',
              borderRight: isActive ? '3px solid #6366f1' : '3px solid transparent',
              textDecoration: 'none',
              fontSize: 14,
              fontWeight: isActive ? 600 : 400,
              transition: 'all 0.15s',
            })}
          >
            <span style={{ fontSize: 16 }}>{icon}</span>
            {label}
          </NavLink>
        ))}

        {sessionId && (
          <div style={{
            margin: '24px 16px 0',
            padding: '12px',
            background: 'rgba(99,102,241,0.08)',
            border: '1px solid var(--border)',
            borderRadius: 8,
          }}>
            <div style={{ fontSize: 11, color: 'var(--text3)', marginBottom: 4 }}>Active Session</div>
            <div style={{ fontSize: 11, color: '#a5b4fc', wordBreak: 'break-all' }}>
              {sessionId.slice(0, 16)}...
            </div>
          </div>
        )}

        <div style={{ marginTop: 'auto', padding: '0 20px' }}>
          <div style={{ fontSize: 11, color: 'var(--text3)' }}>
            Built with FastAPI + React + ML
          </div>
        </div>
      </nav>

      {/* Main content */}
      <main style={{ marginLeft: 220, flex: 1, minHeight: '100vh', overflowX: 'hidden' }}>
        <Toaster position="top-right" toastOptions={{
          style: { background: 'var(--bg3)', color: 'var(--text)', border: '1px solid var(--border)' }
        }} />
        <Routes>
          <Route path="/" element={<Upload onAnalyzed={onAnalyzed} />} />
          <Route path="/dashboard" element={<Dashboard sessionId={sessionId} analysisData={analysisData} />} />
          <Route path="/interview" element={<Interview sessionId={sessionId} analysisData={analysisData} />} />
          <Route path="/compare" element={<Compare sessionId={sessionId} />} />
          <Route path="/analytics" element={<Analytics />} />
        </Routes>
      </main>
    </div>
  );
}
