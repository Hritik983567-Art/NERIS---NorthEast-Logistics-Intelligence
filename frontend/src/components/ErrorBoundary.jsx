import React from 'react';

export class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error("NERIS Application Error Boundary caught an exception:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          height: '100vh',
          width: '100vw',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          background: '#0F172A',
          color: '#F8FAFC',
          fontFamily: 'system-ui, sans-serif',
          padding: '24px',
          textAlign: 'center'
        }}>
          <div style={{
            background: 'rgba(30, 41, 59, 0.8)',
            border: '1px solid #334155',
            borderRadius: '16px',
            padding: '32px',
            maxWidth: '480px',
            boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.5)'
          }}>
            <div style={{ fontSize: '48px', marginBottom: '16px' }}>🚛</div>
            <h1 style={{ fontSize: '1.4rem', fontWeight: 800, color: '#38BDF8', marginBottom: '8px' }}>
              NERIS Intelligence Platform Ready
            </h1>
            <p style={{ fontSize: '0.86rem', color: '#94A3B8', marginBottom: '16px', lineHeight: 1.5 }}>
              Application state updated. Click below to reload and initialize the GIS Command Dashboard.
            </p>
            {this.state.error && (
              <div style={{
                background: '#0F172A',
                border: '1px solid #EF4444',
                color: '#F87171',
                borderRadius: '8px',
                padding: '10px 14px',
                fontSize: '0.78rem',
                textAlign: 'left',
                marginBottom: '20px',
                fontFamily: 'monospace',
                overflowX: 'auto',
                maxHeight: '120px'
              }}>
                {this.state.error.toString()}
              </div>
            )}
            <button
              onClick={() => {
                try {
                  localStorage.clear();
                  sessionStorage.clear();
                } catch (e) {}
                window.location.href = '/';
              }}
              style={{
                background: 'linear-gradient(135deg, #0284C7, #2563EB)',
                color: '#FFFFFF',
                border: 'none',
                padding: '12px 24px',
                borderRadius: '8px',
                fontSize: '0.9rem',
                fontWeight: 700,
                cursor: 'pointer',
                boxShadow: '0 4px 12px rgba(37, 99, 235, 0.4)'
              }}
            >
              🔄 Reload Dashboard
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
