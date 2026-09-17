import React, { useState } from 'react';
import { useApp } from '../context/AppContext';
import {
  Map,
  Navigation,
  Truck,
  AlertTriangle,
  BarChart3,
  Bell,
  Newspaper,
  Wifi,
  WifiOff,
  Globe,
  Radio,
  Menu,
  X,
  ChevronLeft,
  ChevronRight,
  LogOut,
  User,
  Moon,
  Sun
} from 'lucide-react';

export const Navbar = () => {
  const {
    lang,
    setLang,
    t,
    stateFilter,
    setStateFilter,
    activeTab,
    setActiveTab,
    isOnline,
    toggleOnlineStatus,
    offlineQueue,
    broadcastAlerts,
    nerStates,
    user,
    logout,
    theme,
    toggleTheme
  } = useApp();

  const [collapsed, setCollapsed] = useState(false);
  const [mobileDrawerOpen, setMobileDrawerOpen] = useState(false);

  const handleSelectTab = (tabId) => {
    setActiveTab(tabId);
    setMobileDrawerOpen(false);
  };

  return (
    <>
      {/* Mobile Top Header (Visible only on screens < 1024px) */}
      <div className="mobile-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div className="brand-icon">
            <Radio size={18} color="#FFFFFF" />
          </div>
          <h1 className="brand-title" style={{ fontSize: '1rem' }}>{t.appTitle}</h1>
          <span className="pill clear" style={{ fontSize: '0.6rem', padding: '1px 6px', background: 'rgba(16, 185, 129, 0.15)', color: '#059669', border: '1px solid #10B981' }}>🟢 SYSTEM ONLINE</span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <button
            className={`status-badge ${isOnline ? 'online' : 'offline'}`}
            onClick={toggleOnlineStatus}
            style={{ cursor: 'pointer', border: 'none' }}
          >
            <span className={`dot-pulse ${isOnline ? 'online' : 'offline'}`}></span>
            {isOnline ? 'ONLINE' : 'OFFLINE'}
          </button>

          <button
            onClick={toggleTheme}
            style={{
              background: 'transparent',
              border: '1px solid var(--color-border)',
              borderRadius: '6px',
              padding: '5px 9px',
              display: 'flex',
              alignItems: 'center',
              gap: '5px',
              cursor: 'pointer',
              color: 'var(--color-text)',
              fontSize: '0.74rem',
              fontWeight: 700
            }}
            title={theme === 'dark' ? "Switch to Light Mode" : "Switch to Dark Mode"}
          >
            {theme === 'dark' ? <Sun size={15} color="#F59E0B" /> : <Moon size={15} color="#6366F1" />}
          </button>

          <button
            className="mobile-hamburger-btn"
            onClick={() => setMobileDrawerOpen(!mobileDrawerOpen)}
            aria-label="Toggle menu"
          >
            {mobileDrawerOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>
      </div>

      {/* Mobile Drawer Overlay (< 1024px) */}
      {mobileDrawerOpen && (
        <>
          <div className="drawer-backdrop" onClick={() => setMobileDrawerOpen(false)} />
          <div className="mobile-drawer" role="dialog" aria-label="Mobile Navigation Menu">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
              <span style={{ fontWeight: 800, color: '#2563EB', fontSize: '1rem' }}>Navigation Menu</span>
              <button
                onClick={() => setMobileDrawerOpen(false)}
                style={{ background: 'transparent', border: 'none', color: 'var(--color-muted)', cursor: 'pointer', padding: '6px' }}
              >
                <X size={22} />
              </button>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <button className={`sidebar-nav-btn ${activeTab === 'map' ? 'active' : ''}`} onClick={() => handleSelectTab('map')} style={{ width: '100%' }}>
                <Map size={18} /> {t.navMap}
              </button>
              <button className={`sidebar-nav-btn ${activeTab === 'planner' ? 'active' : ''}`} onClick={() => handleSelectTab('planner')} style={{ width: '100%' }}>
                <Navigation size={18} /> {t.navRoutePlanner}
              </button>
              <button className={`sidebar-nav-btn ${activeTab === 'fleet' ? 'active' : ''}`} onClick={() => handleSelectTab('fleet')} style={{ width: '100%' }}>
                <Truck size={18} /> {t.navFleet}
              </button>
              <button className={`sidebar-nav-btn ${activeTab === 'incidents' ? 'active' : ''}`} onClick={() => handleSelectTab('incidents')} style={{ width: '100%' }}>
                <AlertTriangle size={18} /> {t.navIncidents}
              </button>
              <button className={`sidebar-nav-btn ${activeTab === 'analytics' ? 'active' : ''}`} onClick={() => handleSelectTab('analytics')} style={{ width: '100%' }}>
                <BarChart3 size={18} /> {t.navAnalytics}
              </button>
              <button className={`sidebar-nav-btn ${activeTab === 'alerts' ? 'active' : ''}`} onClick={() => handleSelectTab('alerts')} style={{ width: '100%' }}>
                <Bell size={18} /> {t.navAlerts}
              </button>
              <button className={`sidebar-nav-btn ${activeTab === 'news' ? 'active' : ''}`} onClick={() => handleSelectTab('news')} style={{ width: '100%' }}>
                <Newspaper size={18} /> {t.navNews}
              </button>

              {/* Mobile Drawer Dedicated Night Mode Switch Sign */}
              <button
                type="button"
                onClick={toggleTheme}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  width: '100%',
                  padding: '10px 12px',
                  borderRadius: '8px',
                  background: 'var(--color-surface)',
                  border: '1px solid var(--color-border)',
                  color: 'var(--color-text)',
                  fontSize: '0.78rem',
                  fontWeight: 700,
                  cursor: 'pointer',
                  marginTop: '6px'
                }}
                title={theme === 'dark' ? (t.lightMode || "Day Mode") : (t.darkMode || "Night Mode")}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  {theme === 'dark' ? <Moon size={16} color="#FBBF24" /> : <Sun size={16} color="#F59E0B" />}
                  <span>{theme === 'dark' ? (t.darkMode || "Night Mode") : (t.lightMode || "Day Mode")}</span>
                </div>
                <div style={{
                  width: '32px',
                  height: '18px',
                  borderRadius: '10px',
                  background: theme === 'dark' ? '#2563EB' : '#D6CEBE',
                  position: 'relative',
                  transition: 'all 0.2s ease',
                  flexShrink: 0
                }}>
                  <div style={{
                    width: '14px',
                    height: '14px',
                    borderRadius: '50%',
                    background: '#FFFFFF',
                    position: 'absolute',
                    top: '2px',
                    left: theme === 'dark' ? '16px' : '2px',
                    transition: 'all 0.2s ease'
                  }} />
                </div>
              </button>
            </div>

            <div style={{ marginTop: 'auto', display: 'flex', flexDirection: 'column', gap: '12px', paddingTop: '16px', borderTop: '1px solid var(--color-border)' }}>
              <div>
                <label className="form-label">{t.selectState}</label>
                <select className="custom-select" value={stateFilter} onChange={(e) => setStateFilter(e.target.value)} style={{ width: '100%' }}>
                  {nerStates.map((s) => (
                    <option key={s.id} value={s.id}>
                      {(t.stateNames && t.stateNames[s.id]) || s.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="form-label">{t.selectLanguage}</label>
                <select className="custom-select" value={lang} onChange={(e) => setLang(e.target.value)} style={{ width: '100%' }}>
                  <option value="en">English (EN)</option>
                  <option value="as">অসমীয়া (AS)</option>
                  <option value="bn">বাংলা (BN)</option>
                  <option value="hi">हिन्दी (HI)</option>
                  <option value="mn">ꯃꯩꯇꯩꯂꯣᓐ (MN)</option>
                </select>
              </div>
            </div>
          </div>
        </>
      )}

      {/* Desktop & Laptop Left Vertical Sidebar Menu */}
      <aside className={`sidebar-nav ${collapsed ? 'collapsed' : ''}`}>
        {/* Top Brand Header */}
        <div className="sidebar-brand-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', overflow: 'hidden', flex: 1, minWidth: 0 }}>
            <div className="brand-icon">
              <Radio size={18} color="#FFFFFF" />
            </div>
            {!collapsed && (
              <div style={{ overflow: 'hidden', minWidth: 0, flex: 1 }}>
                <h1 className="brand-title" title={t.appTitle}>{t.appTitle}</h1>
                <p style={{ fontSize: '0.64rem', color: 'var(--color-muted)', margin: 0, fontWeight: 600, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                  {t.emergencyTransitSubTitle || "Emergency Transit"}
                </p>
                <div style={{ marginTop: '2px' }}>
                  <span className="pill clear" style={{ fontSize: '0.58rem', padding: '1px 5px', background: 'rgba(16, 185, 129, 0.15)', color: '#059669', border: '1px solid #10B981' }}>🟢 SYSTEM OPERATIONAL</span>
                </div>
              </div>
            )}
          </div>

          <button
            onClick={() => setCollapsed(!collapsed)}
            className="collapse-toggle-btn"
            title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
            aria-label="Toggle sidebar collapse"
          >
            {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
          </button>
        </div>

        {/* Middle Vertical Navigation Links */}
        <nav className="sidebar-nav-list" role="tablist" aria-label="Left Vertical Navigation">
          <button
            role="tab"
            aria-selected={activeTab === 'map'}
            className={`sidebar-nav-btn ${activeTab === 'map' ? 'active' : ''}`}
            onClick={() => handleSelectTab('map')}
            title={t.navMap}
          >
            <Map size={18} />
            {!collapsed && <span>{t.navMap}</span>}
          </button>

          <button
            role="tab"
            aria-selected={activeTab === 'planner'}
            className={`sidebar-nav-btn ${activeTab === 'planner' ? 'active' : ''}`}
            onClick={() => handleSelectTab('planner')}
            title={t.navRoutePlanner}
          >
            <Navigation size={18} />
            {!collapsed && <span>{t.navRoutePlanner}</span>}
          </button>

          <button
            role="tab"
            aria-selected={activeTab === 'fleet'}
            className={`sidebar-nav-btn ${activeTab === 'fleet' ? 'active' : ''}`}
            onClick={() => handleSelectTab('fleet')}
            title={t.navFleet}
          >
            <Truck size={18} />
            {!collapsed && <span>{t.navFleet}</span>}
          </button>

          <button
            role="tab"
            aria-selected={activeTab === 'incidents'}
            className={`sidebar-nav-btn ${activeTab === 'incidents' ? 'active' : ''}`}
            onClick={() => handleSelectTab('incidents')}
            title={t.navIncidents}
          >
            <AlertTriangle size={18} />
            {!collapsed && <span>{t.navIncidents}</span>}
            {offlineQueue.length > 0 && (
              <span className="sidebar-badge warning">
                {offlineQueue.length}
              </span>
            )}
          </button>

          <button
            role="tab"
            aria-selected={activeTab === 'analytics'}
            className={`sidebar-nav-btn ${activeTab === 'analytics' ? 'active' : ''}`}
            onClick={() => handleSelectTab('analytics')}
            title={t.navAnalytics}
          >
            <BarChart3 size={18} />
            {!collapsed && <span>{t.navAnalytics}</span>}
          </button>

          <button
            role="tab"
            aria-selected={activeTab === 'alerts'}
            className={`sidebar-nav-btn ${activeTab === 'alerts' ? 'active' : ''}`}
            onClick={() => handleSelectTab('alerts')}
            title={t.navAlerts}
          >
            <Bell size={18} />
            {!collapsed && <span>{t.navAlerts}</span>}
            <span className="sidebar-badge error">
              {broadcastAlerts.length}
            </span>
          </button>

          <button
            role="tab"
            aria-selected={activeTab === 'news'}
            className={`sidebar-nav-btn ${activeTab === 'news' ? 'active' : ''}`}
            onClick={() => handleSelectTab('news')}
            title={t.navNews}
          >
            <Newspaper size={18} />
            {!collapsed && <span>{t.navNews}</span>}
          </button>
        </nav>

        {/* Bottom Controls Section */}
        <div className="sidebar-footer">
          {!collapsed && (
            <>
              <div className="sidebar-control-group">
                <label className="form-label" style={{ fontSize: '0.68rem' }}>{t.selectState}</label>
                <select
                  className="custom-select"
                  value={stateFilter}
                  onChange={(e) => setStateFilter(e.target.value)}
                  style={{ width: '100%' }}
                >
                  {nerStates.map((s) => (
                    <option key={s.id} value={s.id}>
                      {(t.stateNames && t.stateNames[s.id]) || s.name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="sidebar-control-group">
                <label className="form-label" style={{ fontSize: '0.68rem' }}>{t.selectLanguage}</label>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <Globe size={14} color="#9CA3AF" />
                  <select
                    className="custom-select"
                    value={lang}
                    onChange={(e) => setLang(e.target.value)}
                    style={{ flex: 1 }}
                  >
                    <option value="en">English (EN)</option>
                    <option value="as">অসমীয়া (AS)</option>
                    <option value="bn">বাংলা (BN)</option>
                    <option value="hi">हिन्दी (HI)</option>
                    <option value="mn">ꯃꯩꯇꯩꯂꯣᓐ (MN)</option>
                  </select>
                </div>
              </div>
            </>
          )}

          {/* Dedicated Night Mode Switch Sign Control */}
          <button
            type="button"
            onClick={toggleTheme}
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              width: '100%',
              padding: '8px 10px',
              borderRadius: '8px',
              background: 'var(--color-surface)',
              border: '1px solid var(--color-border)',
              color: 'var(--color-text)',
              fontSize: '0.76rem',
              fontWeight: 700,
              cursor: 'pointer',
              marginTop: '4px'
            }}
            title={theme === 'dark' ? (t.lightMode || "Day Mode") : (t.darkMode || "Night Mode")}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              {theme === 'dark' ? <Moon size={16} color="#FBBF24" /> : <Sun size={16} color="#F59E0B" />}
              {!collapsed && <span>{theme === 'dark' ? (t.darkMode || "Night Mode") : (t.lightMode || "Day Mode")}</span>}
            </div>
            <div style={{
              width: '32px',
              height: '18px',
              borderRadius: '10px',
              background: theme === 'dark' ? '#2563EB' : '#D6CEBE',
              position: 'relative',
              transition: 'all 0.2s ease',
              flexShrink: 0
            }}>
              <div style={{
                width: '14px',
                height: '14px',
                borderRadius: '50%',
                background: '#FFFFFF',
                position: 'absolute',
                top: '2px',
                left: theme === 'dark' ? '16px' : '2px',
                transition: 'all 0.2s ease'
              }} />
            </div>
          </button>

          <button
            className={`status-badge ${isOnline ? 'online' : 'offline'}`}
            onClick={toggleOnlineStatus}
            style={{ width: '100%', justifyContent: 'center', cursor: 'pointer', border: 'none', minHeight: '34px', marginTop: '8px' }}
          >
            <span className={`dot-pulse ${isOnline ? 'online' : 'offline'}`}></span>
            {isOnline ? (collapsed ? 'ON' : 'ONLINE (CLOUD SYNC)') : (collapsed ? 'OFF' : 'OFFLINE (LOCAL QUEUE)')}
          </button>

          {/* User Profile Card & Logout */}
          {user && (
            <div style={{ padding: '8px 10px', borderRadius: '8px', background: 'var(--color-surface)', border: '1px solid var(--color-border)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '6px', overflow: 'hidden' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', overflow: 'hidden', flex: 1, minWidth: 0 }}>
                <div style={{ width: '28px', height: '28px', borderRadius: '50%', background: '#2563EB', color: '#FFF', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.74rem', fontWeight: 800, flexShrink: 0 }}>
                  <User size={15} />
                </div>
                {!collapsed && (
                  <div style={{ overflow: 'hidden', minWidth: 0, flex: 1 }}>
                    <div style={{ fontSize: '0.76rem', fontWeight: 800, color: 'var(--color-text)', whiteSpace: 'nowrap', textOverflow: 'ellipsis', overflow: 'hidden' }} title={user.name}>
                      {user.name}
                    </div>
                    <div style={{ fontSize: '0.64rem', color: 'var(--color-muted)', whiteSpace: 'nowrap', textOverflow: 'ellipsis', overflow: 'hidden' }} title={user.role}>
                      {user.role}
                    </div>
                  </div>
                )}
              </div>

              <button
                onClick={logout}
                title="Logout from system"
                aria-label="Logout"
                style={{ background: 'transparent', border: 'none', color: '#DC2626', cursor: 'pointer', padding: '4px', display: 'flex', alignItems: 'center', flexShrink: 0 }}
              >
                <LogOut size={16} />
              </button>
            </div>
          )}

          {!collapsed && (
            <div style={{ marginTop: '8px', padding: '0 4px', fontSize: '0.58rem', color: 'var(--color-muted)', lineHeight: 1.2, textAlign: 'center' }}>
              NERIS is an independent student project and is not affiliated with the U.S. NERIS framework.
            </div>
          )}
        </div>
      </aside>
    </>
  );
};
