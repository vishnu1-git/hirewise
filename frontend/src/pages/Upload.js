import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import toast from 'react-hot-toast';
import { analyzeResume } from '../utils/api';

export default function Upload({ onAnalyzed }) {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState('');

  const onDrop = useCallback((accepted) => {
    if (accepted[0]) setFile(accepted[0]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'], 'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'], 'text/plain': ['.txt'] },
    maxFiles: 1,
  });

  const handleAnalyze = async () => {
    if (!file) return toast.error('Please upload a resume first.');
    setLoading(true);
    try {
      setProgress('Extracting text from resume...');
      await new Promise(r => setTimeout(r, 600));
      setProgress('Running NLP skill extraction...');
      await new Promise(r => setTimeout(r, 600));
      setProgress('Scoring with ML model...');
      const res = await analyzeResume(file);
      setProgress('Done!');
      toast.success('Resume analyzed successfully!');
      onAnalyzed(res.data);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Analysis failed. Check backend is running.');
    } finally {
      setLoading(false);
      setProgress('');
    }
  };

  return (
    <div style={{ maxWidth: 760, margin: '0 auto', padding: '48px 32px' }}>
      {/* Hero */}
      <div style={{ textAlign: 'center', marginBottom: 48 }} className="fade-up">
        <div style={{ fontSize: 48, marginBottom: 16 }}>🧠</div>
        <h1 style={{ fontSize: 36, fontWeight: 800, background: 'linear-gradient(135deg,#a5b4fc,#818cf8)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', marginBottom: 12 }}>
          HireWise AI
        </h1>
        <p style={{ fontSize: 16, color: 'var(--text2)', maxWidth: 480, margin: '0 auto' }}>
          Upload your resume and get an AI-powered analysis — skill extraction, ML scoring, semantic matching, mock interview, and SHAP explainability.
        </p>
      </div>

      {/* Feature pills */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, justifyContent: 'center', marginBottom: 40 }}>
        {['🔬 NLP Skill Extraction','🤖 ML Resume Scoring','📊 SHAP Explainability','💬 AI Mock Interview','🎤 Voice Mode','⚖️ Multi-Role Compare'].map(f => (
          <span key={f} style={{ padding: '5px 14px', background: 'rgba(99,102,241,0.1)', border: '1px solid var(--border)', borderRadius: 20, fontSize: 13, color: '#a5b4fc' }}>{f}</span>
        ))}
      </div>

      {/* Dropzone */}
      <div
        {...getRootProps()}
        className="card"
        style={{
          border: `2px dashed ${isDragActive ? '#6366f1' : 'var(--border)'}`,
          background: isDragActive ? 'rgba(99,102,241,0.06)' : 'var(--card)',
          cursor: 'pointer',
          textAlign: 'center',
          padding: '48px 32px',
          transition: 'all 0.2s',
          marginBottom: 24,
        }}
      >
        <input {...getInputProps()} />
        {file ? (
          <div>
            <div style={{ fontSize: 40, marginBottom: 12 }}>📄</div>
            <div style={{ fontWeight: 600, color: '#a5b4fc', marginBottom: 4 }}>{file.name}</div>
            <div style={{ fontSize: 13, color: 'var(--text3)' }}>{(file.size / 1024).toFixed(1)} KB — Click or drag to replace</div>
          </div>
        ) : (
          <div>
            <div style={{ fontSize: 48, marginBottom: 16 }}>📂</div>
            <div style={{ fontWeight: 600, fontSize: 16, marginBottom: 8 }}>
              {isDragActive ? 'Drop it here!' : 'Drag & drop your resume'}
            </div>
            <div style={{ color: 'var(--text3)', fontSize: 14 }}>PDF, DOCX, or TXT — up to 10MB</div>
          </div>
        )}
      </div>

      {/* Progress */}
      {loading && (
        <div className="card fade-up" style={{ marginBottom: 24, padding: '16px 24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <div style={{ width: 18, height: 18, border: '2px solid var(--primary)', borderTopColor: 'transparent', borderRadius: '50%', animation: 'spin 0.8s linear infinite' }} />
            <span style={{ color: 'var(--text2)', fontSize: 14 }}>{progress}</span>
          </div>
        </div>
      )}

      <button
        className="btn btn-primary"
        onClick={handleAnalyze}
        disabled={!file || loading}
        style={{ width: '100%', justifyContent: 'center', padding: '14px', fontSize: 16 }}
      >
        {loading ? 'Analyzing...' : '🚀 Analyze Resume'}
      </button>

      {/* How it works */}
      <div style={{ marginTop: 48 }}>
        <h3 style={{ fontSize: 14, color: 'var(--text3)', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 20 }}>How it works</h3>
        <div className="grid-3">
          {[
            { icon: '📤', step: '1', title: 'Upload', desc: 'Drop your PDF/DOCX resume' },
            { icon: '🤖', step: '2', title: 'Analyze', desc: 'ML model scores & NLP extracts skills' },
            { icon: '🎯', step: '3', title: 'Improve', desc: 'Get SHAP feedback & practice interviews' },
          ].map(({ icon, step, title, desc }) => (
            <div key={step} className="card" style={{ textAlign: 'center', padding: '20px 16px' }}>
              <div style={{ fontSize: 28, marginBottom: 8 }}>{icon}</div>
              <div style={{ fontSize: 11, color: '#6366f1', fontWeight: 700, marginBottom: 4 }}>STEP {step}</div>
              <div style={{ fontWeight: 600, marginBottom: 6 }}>{title}</div>
              <div style={{ fontSize: 13, color: 'var(--text3)' }}>{desc}</div>
            </div>
          ))}
        </div>
      </div>

      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}
