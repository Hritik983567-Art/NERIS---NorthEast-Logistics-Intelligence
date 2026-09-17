import React, { useState } from 'react';
import { useApp } from '../context/AppContext';
import {
  Radio,
  ShieldCheck,
  Lock,
  User,
  MapPin,
  Sparkles,
  ArrowRight,
  ShieldAlert,
  Globe,
  KeyRound,
  Compass,
  Phone,
  CheckCircle2,
  Car,
  Moon,
  Sun
} from 'lucide-react';

export const LoginPage = () => {
  const { login, loginAsPublic, nerStates, lang, setLang, t, theme, toggleTheme } = useApp();

  // Mode: 'public' or 'official'
  const [authMode, setAuthMode] = useState('public');

  // Public Citizen / Tourist Form State
  const [publicName, setPublicName] = useState('Ananya Sharma');
  const [publicPhone, setPublicPhone] = useState('+91 98765 43210');
  const [publicRole, setPublicRole] = useState('Tourist / Traveler');
  const [publicDestination, setPublicDestination] = useState('Arunachal Pradesh (Tawang & Sela Pass)');

  // Official Officer Form State
  const [officerId, setOfficerId] = useState('NER-CMD-8041');
  const [password, setPassword] = useState('••••••••');
  const [officerRole, setOfficerRole] = useState('Disaster Logistics Commander');
  const [hub, setHub] = useState('Guwahati Central Depot (Assam)');
  const [isAuthenticating, setIsAuthenticating] = useState(false);
  const [authError, setAuthError] = useState(null);

  const handleOfficerSubmit = async (e) => {
    e.preventDefault();
    setIsAuthenticating(true);
    setAuthError(null);
    try {
      await login(officerId, password, officerRole, hub);
    } catch (err) {
      console.warn("Auth error:", err);
      setAuthError(err.message || 'Authentication Failed: Invalid Cognito Credentials.');
    } finally {
      setIsAuthenticating(false);
    }
  };

  const handlePublicSubmit = (e) => {
    e.preventDefault();
    setIsAuthenticating(true);
    setTimeout(() => {
      loginAsPublic(publicName, publicPhone, publicRole, publicDestination);
      setIsAuthenticating(false);
    }, 500);
  };

  const handleQuickPublicFill = (name, phone, role, dest) => {
    setAuthMode('public');
    setPublicName(name);
    setPublicPhone(phone);
    setPublicRole(role);
    setPublicDestination(dest);
  };

  const handleQuickOfficerFill = (presetId, presetRole, presetHub) => {
    setAuthMode('official');
    setOfficerId(presetId);
    setOfficerRole(presetRole);
    setHub(presetHub);
    setPassword('••••••••');
  };

  return (
    <div className="login-wrapper">
      {/* Top Bar / Lang Switcher */}
      <div className="login-top-bar">
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Globe size={14} color="var(--color-muted)" />
          <select
            className="custom-select"
            value={lang}
            onChange={(e) => setLang(e.target.value)}
            style={{ height: '30px', fontSize: '0.74rem' }}
          >
            <option value="en">English (EN)</option>
            <option value="as">অসমীয়া (AS)</option>
            <option value="bn">বাংলা (BN)</option>
            <option value="hi">हिन्दी (HI)</option>
            <option value="mn">ꯃꯩꯇꯩꯂꯣᓐ (MN)</option>
          </select>

          <button
            type="button"
            onClick={toggleTheme}
            style={{
              background: 'var(--color-surface)',
              border: '1px solid var(--color-border)',
              borderRadius: '6px',
              height: '30px',
              padding: '0 10px',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              cursor: 'pointer',
              color: 'var(--color-text)',
              fontSize: '0.74rem',
              fontWeight: 700
            }}
            title={theme === 'dark' ? "Switch to Light Mode" : "Switch to Dark Mode"}
          >
            {theme === 'dark' ? <Sun size={14} color="#F59E0B" /> : <Moon size={14} color="#6366F1" />}
            <span>{theme === 'dark' ? (t.lightMode || "Light Mode") : (t.darkMode || "Dark Mode")}</span>
          </button>
        </div>

        <div className="pill clear" style={{ fontSize: '0.68rem', padding: '3px 9px' }}>
          <ShieldCheck size={12} /> {t.verifiedSafetyNode || "VERIFIED SAFETY NODE"}
        </div>
      </div>

      <div className="login-card-container">
        {/* Left Hero Panel */}
        <div className="login-hero-panel">
          <div className="login-brand-header">
            <div className="brand-icon" style={{ width: '42px', height: '42px', borderRadius: '12px' }}>
              <Radio size={22} color="#FFFFFF" />
            </div>
            <div>
              <h1 className="login-brand-title">{t.appTitle}</h1>
              <p style={{ fontSize: '0.72rem', color: 'var(--color-muted)', fontWeight: 600, margin: 0 }}>
                {t.subTitle || "North-East Emergency & Travel Safety Platform"}
              </p>
            </div>
          </div>

          <div style={{ marginTop: '24px' }}>
            <h2 style={{ fontSize: '1.2rem', fontWeight: 800, color: 'var(--color-text)', letterSpacing: '-0.3px', lineHeight: 1.3 }}>
              {t.loginHeroHeading}
            </h2>
            <p style={{ fontSize: '0.78rem', color: 'var(--color-muted)', marginTop: '6px', lineHeight: 1.5 }}>
              {t.loginHeroSub}
            </p>
          </div>

          {/* Feature Bullets */}
          <div className="login-features-list">
            <div className="login-feature-item">
              <div className="login-feature-icon">
                <Compass size={16} color="#2563EB" />
              </div>
              <div>
                <strong style={{ fontSize: '0.82rem', color: 'var(--color-text)' }}>{t.touristFeatureTitle}</strong>
                <p style={{ fontSize: '0.74rem', color: 'var(--color-muted)', margin: 0 }}>{t.touristFeatureSub}</p>
              </div>
            </div>

            <div className="login-feature-item">
              <div className="login-feature-icon">
                <Sparkles size={16} color="#D97706" />
              </div>
              <div>
                <strong style={{ fontSize: '0.82rem', color: 'var(--color-text)' }}>{t.landslideFeatureTitle}</strong>
                <p style={{ fontSize: '0.74rem', color: 'var(--color-muted)', margin: 0 }}>{t.landslideFeatureSub}</p>
              </div>
            </div>

            <div className="login-feature-item">
              <div className="login-feature-icon">
                <ShieldAlert size={16} color="#DC2626" />
              </div>
              <div>
                <strong style={{ fontSize: '0.82rem', color: 'var(--color-text)' }}>{t.emergencyFeatureTitle}</strong>
                <p style={{ fontSize: '0.74rem', color: 'var(--color-muted)', margin: 0 }}>{t.emergencyFeatureSub}</p>
              </div>
            </div>
          </div>

          <div className="login-badge-footer">
            <span>{t.footerNote || "GOVT OF INDIA • DISASTER & TRAVEL MANAGEMENT PROTOCOL"}</span>
          </div>
        </div>

        {/* Right Authentication & Sign-In Form */}
        <div className="login-form-panel">
          {/* Main Auth Mode Selector Tabs */}
          <div style={{ display: 'flex', background: 'var(--color-surface)', padding: '4px', borderRadius: '10px', border: '1px solid var(--color-border)', marginBottom: '16px' }}>
            <button
              type="button"
              className={`login-role-tab ${authMode === 'public' ? 'active' : ''}`}
              onClick={() => setAuthMode('public')}
              style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px', fontSize: '0.78rem' }}
            >
              <Compass size={15} /> {t.citizenTab}
            </button>
            <button
              type="button"
              className={`login-role-tab ${authMode === 'official' ? 'active' : ''}`}
              onClick={() => setAuthMode('official')}
              style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px', fontSize: '0.78rem' }}
            >
              <Lock size={15} /> {t.officerTab}
            </button>
          </div>

          {/* Form Mode 1: Public Citizen & Tourist Sign-In */}
          {authMode === 'public' && (
            <div>
              <div style={{ marginBottom: '14px' }}>
                <h3 style={{ fontSize: '1.05rem', fontWeight: 800, color: 'var(--color-text)', margin: 0 }}>
                  {t.citizenTitle}
                </h3>
                <p style={{ fontSize: '0.74rem', color: 'var(--color-muted)', marginTop: '2px' }}>
                  {t.citizenSub}
                </p>
              </div>

              <form onSubmit={handlePublicSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                <div className="form-group">
                  <label htmlFor="public-name" className="form-label" style={{ fontSize: '0.68rem' }}>
                    {t.fullNameLabel}
                  </label>
                  <div style={{ position: 'relative' }}>
                    <User size={15} color="var(--color-muted)" style={{ position: 'absolute', left: '10px', top: '10px' }} />
                    <input
                      id="public-name"
                      type="text"
                      className="form-input"
                      style={{ paddingLeft: '32px', height: '36px' }}
                      value={publicName}
                      onChange={(e) => setPublicName(e.target.value)}
                      placeholder="e.g. Ananya Sharma"
                      required
                    />
                  </div>
                </div>

                <div className="form-group">
                  <label htmlFor="public-phone" className="form-label" style={{ fontSize: '0.68rem' }}>
                    {t.mobileLabel}
                  </label>
                  <div style={{ position: 'relative' }}>
                    <Phone size={15} color="var(--color-muted)" style={{ position: 'absolute', left: '10px', top: '10px' }} />
                    <input
                      id="public-phone"
                      type="tel"
                      className="form-input"
                      style={{ paddingLeft: '32px', height: '36px' }}
                      value={publicPhone}
                      onChange={(e) => setPublicPhone(e.target.value)}
                      placeholder="+91 98765 43210"
                      required
                    />
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                  <div className="form-group">
                    <label htmlFor="public-type" className="form-label" style={{ fontSize: '0.68rem' }}>
                      {t.categoryLabel}
                    </label>
                    <select
                      id="public-type"
                      className="custom-select"
                      style={{ width: '100%', height: '36px' }}
                      value={publicRole}
                      onChange={(e) => setPublicRole(e.target.value)}
                    >
                      <option value="Tourist / Traveler">{t.touristOption || "Tourist / Traveler"}</option>
                      <option value="Local Resident & Commuter">{t.commuterOption || "Local Resident & Commuter"}</option>
                    </select>
                  </div>

                  <div className="form-group">
                    <label htmlFor="public-dest" className="form-label" style={{ fontSize: '0.68rem' }}>
                      {t.destLabel}
                    </label>
                    <select
                      id="public-dest"
                      className="custom-select"
                      style={{ width: '100%', height: '36px' }}
                      value={publicDestination}
                      onChange={(e) => setPublicDestination(e.target.value)}
                    >
                      <option value="Arunachal Pradesh (Tawang & Sela Pass)">Arunachal (Tawang)</option>
                      <option value="Assam (Guwahati & Kaziranga)">Assam (Kaziranga)</option>
                      <option value="Meghalaya (Shillong & Cherrapunji)">Meghalaya (Shillong)</option>
                      <option value="Sikkim (Gangtok & Nathu La)">Sikkim (Gangtok)</option>
                      <option value="Manipur (Imphal & Loktak Lake)">Manipur (Imphal)</option>
                      <option value="Nagaland (Kohima / Dimapur)">Nagaland (Kohima)</option>
                    </select>
                  </div>
                </div>

                <button
                  type="submit"
                  className="btn-primary"
                  disabled={isAuthenticating}
                  style={{ marginTop: '4px', minHeight: '42px', fontSize: '0.82rem', background: 'linear-gradient(135deg, #10B981 0%, #059669 100%)' }}
                >
                  {isAuthenticating ? (
                    <span>{t.registeringPass || "Registering Travel Safety Pass..."}</span>
                  ) : (
                    <>
                      <Compass size={16} />
                      {t.publicSignInBtn}
                      <ArrowRight size={16} />
                    </>
                  )}
                </button>
              </form>

              {/* Quick Preset Sign-In Buttons */}
              <div style={{ marginTop: '12px', paddingTop: '10px', borderTop: '1px solid var(--color-border)' }}>
                <span style={{ fontSize: '0.66rem', fontWeight: 700, color: '#F59E0B', textTransform: 'uppercase' }}>
                  {t.quickFillTitle}
                </span>
                <div style={{ display: 'flex', gap: '6px', marginTop: '6px', flexWrap: 'wrap' }}>
                  <button
                    type="button"
                    onClick={() => handleQuickPublicFill('Ananya Roy', '+91 98100 12345', 'Tourist / Traveler', 'Arunachal Pradesh (Tawang & Sela Pass)')}
                    className="demo-chip-btn"
                  >
                    Ananya (Tourist to Tawang)
                  </button>
                  <button
                    type="button"
                    onClick={() => handleQuickPublicFill('Rahul Sharma', '+91 94350 99887', 'Local Resident & Commuter', 'Meghalaya (Shillong & Cherrapunji)')}
                    className="demo-chip-btn"
                  >
                    Rahul (Commuter in Shillong)
                  </button>
                  <button
                    type="button"
                    onClick={() => handleQuickPublicFill('Priya Das', '+91 98640 55443', 'Tourist / Traveler', 'Assam (Guwahati & Kaziranga)')}
                    className="demo-chip-btn"
                  >
                    Priya (Visitor to Kaziranga)
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Form Mode 2: Official Disaster Officer Clearance */}
          {authMode === 'official' && (
            <div>
              <div style={{ marginBottom: '12px', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                  <h3 style={{ fontSize: '1.05rem', fontWeight: 800, color: 'var(--color-text)', margin: 0 }}>
                    {t.officerTitle}
                  </h3>
                  <p style={{ fontSize: '0.74rem', color: 'var(--color-muted)', marginTop: '2px' }}>
                    {t.officerSub}
                  </p>
                </div>
                <div className="pill clear" style={{ fontSize: '0.64rem', padding: '3px 8px', display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                  <ShieldCheck size={12} color="#10B981" />
                  <span>Encrypted Auth</span>
                </div>
              </div>

              {authError && (
                <div style={{ padding: '10px 14px', borderRadius: '8px', background: 'rgba(239, 68, 68, 0.12)', border: '1px solid #EF4444', color: '#F87171', fontSize: '0.8rem', fontWeight: 600, marginBottom: '14px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <ShieldAlert size={16} color="#EF4444" />
                  <span>{authError}</span>
                </div>
              )}

              {/* Quick Officer Role Selector */}
              <div className="login-role-tabs">
                <button
                  type="button"
                  className={`login-role-tab ${officerRole === 'Disaster Logistics Commander' ? 'active' : ''}`}
                  onClick={() => handleQuickOfficerFill('NER-CMD-8041', 'Disaster Logistics Commander', 'Guwahati Central Depot (Assam)')}
                >
                  {t.commanderRole || "Commander"}
                </button>
                <button
                  type="button"
                  className={`login-role-tab ${officerRole === 'Field Inspector (BRO / PWD)' ? 'active' : ''}`}
                  onClick={() => handleQuickOfficerFill('BRO-FIELD-102', 'Field Inspector (BRO / PWD)', 'Shillong Command Hub (Meghalaya)')}
                >
                  {t.fieldRole || "Field Unit"}
                </button>
                <button
                  type="button"
                  className={`login-role-tab ${officerRole === 'Convoy Fleet Driver' ? 'active' : ''}`}
                  onClick={() => handleQuickOfficerFill('FLEET-MED-9102', 'Convoy Fleet Driver', 'Silchar FCI Hub (Assam)')}
                >
                  {t.driverRole || "Fleet Driver"}
                </button>
              </div>

              <form onSubmit={handleOfficerSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                <div className="form-group">
                  <label htmlFor="officer-id" className="form-label" style={{ fontSize: '0.68rem' }}>
                    {t.officerIdLabel}
                  </label>
                  <div style={{ position: 'relative' }}>
                    <User size={15} color="var(--color-muted)" style={{ position: 'absolute', left: '10px', top: '10px' }} />
                    <input
                      id="officer-id"
                      type="text"
                      className="form-input"
                      style={{ paddingLeft: '32px', height: '36px' }}
                      value={officerId}
                      onChange={(e) => setOfficerId(e.target.value)}
                      placeholder="e.g. NER-CMD-8041"
                      required
                    />
                  </div>
                </div>

                <div className="form-group">
                  <label htmlFor="officer-password" className="form-label" style={{ fontSize: '0.68rem' }}>
                    {t.passcodeLabel}
                  </label>
                  <div style={{ position: 'relative' }}>
                    <KeyRound size={15} color="var(--color-muted)" style={{ position: 'absolute', left: '10px', top: '10px' }} />
                    <input
                      id="officer-password"
                      type="password"
                      className="form-input"
                      style={{ paddingLeft: '32px', height: '36px' }}
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="••••••••"
                      required
                    />
                  </div>
                </div>

                <div className="form-group">
                  <label htmlFor="command-hub" className="form-label" style={{ fontSize: '0.68rem' }}>
                    {t.commandBaseLabel}
                  </label>
                  <div style={{ position: 'relative' }}>
                    <MapPin size={15} color="var(--color-muted)" style={{ position: 'absolute', left: '10px', top: '10px' }} />
                    <select
                      id="command-hub"
                      className="form-input custom-select"
                      style={{ paddingLeft: '32px', width: '100%', height: '36px' }}
                      value={hub}
                      onChange={(e) => setHub(e.target.value)}
                    >
                      <option value="Guwahati Central Depot (Assam)">Guwahati Central Depot (Assam)</option>
                      <option value="Shillong Command Hub (Meghalaya)">Shillong Command Hub (Meghalaya)</option>
                      <option value="Silchar FCI Hub (Assam)">Silchar FCI Hub (Assam)</option>
                      <option value="Dimapur Railhead Yard (Nagaland)">Dimapur Railhead Yard (Nagaland)</option>
                      <option value="Agartala Multi-Modal Hub (Tripura)">Agartala Multi-Modal Hub (Tripura)</option>
                    </select>
                  </div>
                </div>

                <button
                  type="submit"
                  className="btn-primary"
                  disabled={isAuthenticating}
                  style={{ marginTop: '4px', minHeight: '42px', fontSize: '0.82rem' }}
                >
                  {isAuthenticating ? (
                    <span>{t.verifyingClearance || "Verifying Security Clearance..."}</span>
                  ) : (
                    <>
                      <Lock size={16} />
                      {t.authorizeBtn}
                      <ArrowRight size={16} />
                    </>
                  )}
                </button>
              </form>

              {/* Quick Officer Demo Preset Buttons */}
              <div style={{ marginTop: '12px', paddingTop: '10px', borderTop: '1px solid var(--color-border)' }}>
                <span style={{ fontSize: '0.66rem', fontWeight: 700, color: '#F59E0B', textTransform: 'uppercase' }}>
                  {t.quickFillTitle}
                </span>
                <div style={{ display: 'flex', gap: '6px', marginTop: '6px', flexWrap: 'wrap' }}>
                  <button
                    type="button"
                    onClick={() => handleQuickOfficerFill('NER-CMD-8041', 'Disaster Logistics Commander', 'Guwahati Central Depot (Assam)')}
                    className="demo-chip-btn"
                  >
                    Cmdr. Gogoi (Assam)
                  </button>
                  <button
                    type="button"
                    onClick={() => handleQuickOfficerFill('BRO-FIELD-102', 'Field Inspector (BRO / PWD)', 'Shillong Command Hub (Meghalaya)')}
                    className="demo-chip-btn"
                  >
                    Insp. Sharma (BRO)
                  </button>
                  <button
                    type="button"
                    onClick={() => handleQuickOfficerFill('FLEET-MED-9102', 'Convoy Fleet Driver', 'Silchar FCI Hub (Assam)')}
                    className="demo-chip-btn"
                  >
                    Driver Tashi Norbu
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
