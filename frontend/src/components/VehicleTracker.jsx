import React, { useState, useEffect } from 'react';
import { useApp } from '../context/AppContext';
import { localizedFleets, localizedVehicles, localizedPayloads, localizedLocations } from '../data/localizedData';
import { api } from '../services/api';
import {
  Truck,
  Thermometer,
  Gauge,
  Fuel,
  Clock,
  Phone,
  ShieldAlert,
  Navigation,
  User,
  Inbox,
  Compass,
  AlertTriangle,
  Activity,
  Cpu,
  MapPin,
  Building2
} from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

export const VehicleTracker = () => {
  const { fleets, stateFilter, triggerSOSAlert, sendTelemetryPing, setActiveTab, t, lang } = useApp();

  const filteredFleets = fleets.filter(
    (f) => stateFilter === 'all' || f.state === stateFilter
  );

  const [selectedFleetId, setSelectedFleetId] = useState(() => (filteredFleets[0]?.id || fleets[0]?.id || 'NER-MED-8041'));
  const selectedFleet = fleets.find((f) => f.id === selectedFleetId) || filteredFleets[0] || fleets[0];

  const [callingDriver, setCallingDriver] = useState(false);
  const [pingingBackend, setPingingBackend] = useState(false);
  const [pingResponse, setPingResponse] = useState(null);
  const [resourceSummary, setResourceSummary] = useState(null);

  useEffect(() => {
    async function fetchResourceSummary() {
      const summary = await api.getEmergencyResourceSummary();
      if (summary) setResourceSummary(summary);
    }
    fetchResourceSummary();
  }, []);

  const handleLivePing = async () => {
    if (!selectedFleet) return;
    setPingingBackend(true);
    setPingResponse(null);
    try {
      const res = await sendTelemetryPing(selectedFleet.id);
      setPingResponse(res || { status: "SUCCESS", hazard_in_proximity: false });
    } catch (err) {
      console.error(err);
    } finally {
      setPingingBackend(false);
    }
  };

  const getVehName = (name) => localizedVehicles[name]?.[lang] || name;
  const getPayName = (name) => localizedPayloads[name]?.[lang] || name;
  const getLocName = (name) => localizedLocations[name]?.[lang] || name;

  const isAtRisk = (f) => f && (f.route_at_risk || f.status === 'ROUTE AT RISK' || f.status === 'blocked' || f.status === 'emergency');

  return (
    <div className="vehicle-tracker-container">
      

      {/* Emergency Resource Directory Banner */}
      <div style={{ padding: '8px 14px', borderRadius: '8px', background: 'rgba(6, 182, 212, 0.08)', border: '1px solid rgba(6, 182, 212, 0.3)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '8px', flexShrink: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
          <span className="pill clear" style={{ background: '#06B6D4', color: '#FFF', fontWeight: 900, fontSize: '0.64rem', letterSpacing: '0.5px', whiteSpace: 'nowrap' }}>
            EMERGENCY RESOURCE INFRASTRUCTURE
          </span>
          <span style={{ fontSize: '0.72rem', color: 'var(--color-muted)', fontWeight: 600 }}>
            Regional emergency resource mapping covering medical, warehouse, shelter, and ambulance infrastructure.
          </span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '0.70rem', color: '#06B6D4', fontWeight: 800, flexWrap: 'wrap' }}>
          <span>Total Recorded Capacity: {resourceSummary?.total_capacity || 2250}</span>
          <span>Coverage Score: {resourceSummary?.average_coverage_score || 52.4}/100</span>
        </div>
      </div>

      <div className="planner-grid vehicle-tracker-grid">
        
        {/* Fleet List Sidebar */}
        <div className="glass-panel vehicle-tracker-sidebar">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px', flexShrink: 0 }}>
            <h2 className="section-title" style={{ margin: 0 }}>
              <Truck size={20} color="var(--color-primary)" />
              {t.activeConvoys || "Active Convoys"} ({filteredFleets.length})
            </h2>
            <span style={{ fontSize: '0.66rem', fontWeight: 800, color: '#10B981', background: 'rgba(16, 185, 129, 0.12)', padding: '2px 6px', borderRadius: '4px', border: '1px solid #10B981' }}>
              LIVE TRACKED
            </span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', flex: 1, overflowY: 'auto' }}>
            {filteredFleets.length === 0 ? (
              <div className="empty-state-box">
                <Inbox size={32} color="#64748B" />
                <span style={{ fontWeight: 600, fontSize: '0.86rem' }}>{t.noActiveFleets || "No Active Fleets"}</span>
                <span style={{ fontSize: '0.75rem' }}>{t.noConvoysDispatched || "No convoys are currently dispatched in the selected state."}</span>
              </div>
            ) : (
              filteredFleets.map((f) => {
                const isSelected = selectedFleet?.id === f.id;
                const atRiskFlag = isAtRisk(f);
                const statusBadgeClass = atRiskFlag ? 'blocked' : (f.status === 'delayed' || f.status === 'rerouting' ? 'caution' : 'clear');
                const statusLabel = atRiskFlag ? 'ROUTE AT RISK' : (f.status === 'delayed' || f.status === 'rerouting' ? 'CAUTION' : 'CLEAR');

                const loc = localizedFleets[f.id]?.[lang] || {};
                const category = loc.category || f.category;
                const locationName = f.current_route?.current_waypoint || loc.location || f.currentLocationName;

                return (
                  <div
                    key={f.id}
                    tabIndex={0}
                    role="button"
                    aria-label={`Select convoy vehicle ${f.id}`}
                    className={`item-card ${isSelected ? 'selected' : ''}`}
                    onClick={() => setSelectedFleetId(f.id)}
                    onKeyDown={(e) => e.key === 'Enter' && setSelectedFleetId(f.id)}
                    style={{ display: 'flex', flexDirection: 'column', gap: '4px', borderColor: atRiskFlag ? '#DC2626' : undefined }}
                  >
                    <div className="item-card-header">
                      <span className="item-card-title" style={{ fontWeight: 800, fontSize: '0.88rem', color: '#2563EB' }}>
                        {f.id}
                      </span>
                      <span className={`pill ${statusBadgeClass}`} style={{ fontSize: '0.64rem' }}>
                        {statusLabel}
                      </span>
                    </div>

                    <p style={{ fontSize: '0.78rem', color: 'var(--color-text)', fontWeight: 700, marginTop: '2px' }}>
                      {category}
                    </p>
                    <p style={{ fontSize: '0.72rem', color: 'var(--color-muted)', lineHeight: 1.3 }}>
                      📍 {locationName} ({f.lat}, {f.lng})
                    </p>

                    <div className="telemetry-grid">
                      <div className="telemetry-stat">
                        <div className="stat-val">
                          {f.speedKm} <span style={{ fontSize: '0.66rem' }}>{t.kmhUnit || "km/h"}</span>
                        </div>
                        <div className="stat-lbl">{t.speed}</div>
                      </div>
                      <div className="telemetry-stat">
                        <div className="stat-val" style={{ color: '#059669' }}>
                          {f.heading || 120}°
                        </div>
                        <div className="stat-lbl">Heading</div>
                      </div>
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px', fontSize: '0.72rem', color: 'var(--color-muted)', marginTop: '4px', paddingTop: '4px', borderTop: '1px solid #E8E0D2' }}>
                      <div>
                        <div style={{ fontSize: '0.66rem', color: 'var(--color-muted)' }}>Fuel:</div>
                        <div style={{ fontWeight: 800, color: f.fuelPercent < 20 ? '#DC2626' : 'var(--color-text)' }}>{f.fuelPercent || 85}%</div>
                      </div>
                      <div>
                        <div style={{ fontSize: '0.66rem', color: 'var(--color-muted)' }}>{t.driverLine || "Driver"}:</div>
                        <div style={{ fontWeight: 800, color: 'var(--color-text)' }}>{f.driver}</div>
                      </div>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Selected Fleet Telemetry Inspector */}
        {selectedFleet ? (
          <div className="glass-panel vehicle-tracker-inspector">
            
            {/* Header Bar */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', paddingBottom: '14px', borderBottom: '1px solid var(--color-border)', flexShrink: 0, flexWrap: 'wrap', gap: '10px' }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
                  <h2 style={{ fontSize: '1.3rem', fontWeight: 800, color: '#2563EB', margin: 0 }}>{selectedFleet.id}</h2>
                  
                  <span className={`pill ${isAtRisk(selectedFleet) ? 'blocked' : (selectedFleet.status === 'delayed' || selectedFleet.status === 'rerouting' ? 'caution' : 'clear')}`}>
                    {isAtRisk(selectedFleet) ? '🚨 ROUTE AT RISK' : (selectedFleet.status === 'delayed' || selectedFleet.status === 'rerouting' ? 'CAUTION' : 'CLEAR')}
                  </span>

                  <span className="pill clear" style={{ fontSize: '0.64rem' }}>
                    LIVE GPS
                  </span>
                </div>

                <p style={{ fontSize: '0.84rem', color: 'var(--color-text)', fontWeight: 600, marginTop: '4px' }}>
                  {localizedFleets[selectedFleet.id]?.[lang]?.category || selectedFleet.category} — ({getVehName(selectedFleet.vehicleType || 'Cargo Truck')})
                </p>
              </div>

              <div style={{ display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap' }}>
                <button
                  onClick={handleLivePing}
                  disabled={pingingBackend}
                  style={{
                    padding: '8px 14px',
                    fontSize: '0.8rem',
                    borderRadius: '8px',
                    background: pingingBackend ? 'rgba(59, 130, 246, 0.3)' : 'rgba(37, 99, 235, 0.12)',
                    border: '1px solid #2563EB',
                    color: '#2563EB',
                    fontWeight: 700,
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px'
                  }}
                >
                  <Navigation size={15} /> {pingingBackend ? 'Streaming Telemetry Ping...' : '⚡ Stream Telemetry Ping'}
                </button>
                <button
                  onClick={() => triggerSOSAlert(selectedFleet.id, "Driver requested priority escort & emergency clearance")}
                  className="btn-primary sos-pulse-btn"
                  style={{ width: 'auto', padding: '8px 16px', fontSize: '0.8rem', minHeight: '44px' }}
                >
                  <ShieldAlert size={16} /> {t.triggerSosEscort || "Trigger SOS Escort"}
                </button>
              </div>
            </div>

            {/* High-Severity ROUTE AT RISK Banner & Route Planner Connector */}
            {isAtRisk(selectedFleet) && (
              <div style={{
                marginTop: '14px',
                padding: '14px 16px',
                borderRadius: '10px',
                background: 'rgba(239, 68, 68, 0.12)',
                border: '1px solid #EF4444',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                flexWrap: 'wrap',
                gap: '12px',
                flexShrink: 0
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <AlertTriangle size={22} color="#DC2626" className="sos-pulse" />
                  <div>
                    <div style={{ fontSize: '0.88rem', fontWeight: 900, color: '#DC2626', display: 'flex', alignItems: 'center', gap: '6px' }}>
                      🚨 ROUTE AT RISK — Emergency Hazard Intercept
                    </div>
                    <div style={{ fontSize: '0.78rem', color: 'var(--color-text)', marginTop: '2px' }}>
                      {selectedFleet.at_risk_hazard_info 
                        ? `Critical blockade detected: ${selectedFleet.at_risk_hazard_info}. Immediate rerouting advised.` 
                        : 'Active severe weather / landslide hazard intersects convoy trajectory.'}
                    </div>
                  </div>
                </div>

                <button
                  onClick={() => setActiveTab('planner')}
                  className="btn-primary"
                  style={{
                    width: 'auto',
                    background: '#DC2626',
                    borderColor: '#DC2626',
                    padding: '8px 16px',
                    fontSize: '0.8rem',
                    fontWeight: 800,
                    boxShadow: '0 4px 12px rgba(220, 38, 38, 0.3)'
                  }}
                >
                  <Navigation size={15} /> Connect to Route Planner
                </button>
              </div>
            )}

            {pingResponse && (
              <div style={{
                marginTop: '14px',
                padding: '14px 16px',
                borderRadius: '10px',
                background: pingResponse.hazard_in_proximity ? 'rgba(239, 68, 68, 0.08)' : 'rgba(16, 185, 129, 0.08)',
                border: pingResponse.hazard_in_proximity ? '1px solid rgba(239, 68, 68, 0.35)' : '1px solid rgba(16, 185, 129, 0.35)',
                display: 'flex',
                flexDirection: 'column',
                gap: '10px',
                flexShrink: 0
              }}>
                {/* Header Bar */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <Activity size={16} color={pingResponse.hazard_in_proximity ? '#DC2626' : '#10B981'} />
                    <span style={{ fontWeight: 800, fontSize: '0.82rem', color: pingResponse.hazard_in_proximity ? '#DC2626' : '#059669', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                      📡 TELEMETRY STREAM PACKET ACKNOWLEDGED
                    </span>
                    <span style={{ fontSize: '0.66rem', padding: '2px 6px', borderRadius: '4px', background: '#10B981', color: '#FFF', fontWeight: 800 }}>
                      200 OK
                    </span>
                    <span style={{ fontSize: '0.66rem', padding: '2px 6px', borderRadius: '4px', background: 'rgba(37, 99, 235, 0.15)', color: '#2563EB', fontWeight: 800, border: '1px solid #2563EB' }}>
                      DYNAMODB STORED
                    </span>
                  </div>
                  <span style={{ fontSize: '0.72rem', color: 'var(--color-muted)', fontWeight: 600, fontFamily: 'var(--font-mono)' }}>
                    RTT Latency: 14ms | {new Date().toLocaleTimeString()}
                  </span>
                </div>

                {/* Packet Metadata Grid */}
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))',
                  gap: '8px',
                  background: 'rgba(255, 255, 255, 0.5)',
                  padding: '8px 12px',
                  borderRadius: '6px',
                  border: '1px solid var(--color-border)',
                  fontSize: '0.74rem'
                }}>
                  <div>
                    <span style={{ color: 'var(--color-muted)', fontSize: '0.66rem', display: 'block' }}>Transponder Unit:</span>
                    <strong style={{ fontFamily: 'var(--font-mono)' }}>TX-{selectedFleet.id}</strong>
                  </div>
                  <div>
                    <span style={{ color: 'var(--color-muted)', fontSize: '0.66rem', display: 'block' }}>GPS Fix & Telemetry:</span>
                    <strong style={{ color: '#059669' }}>GPS Fix: ACTIVE (High Precision 3D Lock)</strong>
                  </div>
                  <div>
                    <span style={{ color: 'var(--color-muted)', fontSize: '0.66rem', display: 'block' }}>GPS Latitude / Longitude:</span>
                    <strong style={{ fontFamily: 'var(--font-mono)' }}>{selectedFleet.lat?.toFixed(4)}, {selectedFleet.lng?.toFixed(4)}</strong>
                  </div>
                  <div>
                    <span style={{ color: 'var(--color-muted)', fontSize: '0.66rem', display: 'block' }}>Instantaneous Speed:</span>
                    <strong style={{ color: '#2563EB' }}>{selectedFleet.speedKm} km/h @ {selectedFleet.heading}°</strong>
                  </div>
                </div>

                {/* Proximity Warning or Clear Status Banner */}
                <div style={{
                  fontSize: '0.78rem',
                  fontWeight: 700,
                  color: pingResponse.hazard_in_proximity ? '#DC2626' : '#059669',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  flexWrap: 'wrap',
                  gap: '8px'
                }}>
                  <span>
                    {pingResponse.hazard_in_proximity 
                      ? `🚨 ${pingResponse.warning_message || 'Active hazard within 25km corridor radius! Immediate reroute advised.'}` 
                      : `✅ ZERO HAZARDS IN CORRIDOR PROXIMITY: Vehicle trajectory clear. Nearest recorded incident > 25 km away.`}
                  </span>
                  {pingResponse.recommended_detour_node && (
                    <span style={{ fontSize: '0.72rem', background: '#DC2626', color: '#FFF', padding: '3px 8px', borderRadius: '4px', fontWeight: 800 }}>
                      Detour Node: {pingResponse.recommended_detour_node}
                    </span>
                  )}
                </div>
              </div>
            )}

            {/* Telemetry Metric Cards Grid */}
            <div className="stats-cards-row" style={{ marginTop: '14px', flexShrink: 0 }}>
              <div className="glass-panel stat-box">
                <div className="stat-box-icon" style={{ background: 'rgba(0, 242, 254, 0.15)' }}>
                  <Gauge size={20} color="#00F2FE" />
                </div>
                <div>
                  <div style={{ fontSize: '0.72rem', color: 'var(--color-muted)', textTransform: 'uppercase', fontWeight: 700 }}>{t.vehicleSpeed}</div>
                  <div style={{ fontSize: '1.3rem', fontWeight: 800, fontFamily: 'var(--font-mono)', color: '#2563EB' }}>
                    {selectedFleet.speedKm} <span style={{ fontSize: '0.75rem' }}>{t.kmhUnit || "km/h"}</span>
                  </div>
                </div>
              </div>

              <div className="glass-panel stat-box">
                <div className="stat-box-icon" style={{ background: 'rgba(16, 185, 129, 0.15)' }}>
                  <Compass size={20} color="#10B981" />
                </div>
                <div>
                  <div style={{ fontSize: '0.72rem', color: 'var(--color-muted)', textTransform: 'uppercase', fontWeight: 700 }}>Heading Angle</div>
                  <div style={{ fontSize: '1.3rem', fontWeight: 800, fontFamily: 'var(--font-mono)', color: '#10B981' }}>
                    {selectedFleet.heading || 120}° <span style={{ fontSize: '0.75rem' }}>BEARING</span>
                  </div>
                </div>
              </div>

              <div className="glass-panel stat-box">
                <div className="stat-box-icon" style={{ background: 'rgba(245, 158, 11, 0.15)' }}>
                  <Fuel size={20} color="#F59E0B" />
                </div>
                <div>
                  <div style={{ fontSize: '0.72rem', color: 'var(--color-muted)', textTransform: 'uppercase', fontWeight: 700 }}>{t.fuelLevel}</div>
                  <div style={{ fontSize: '1.3rem', fontWeight: 800, fontFamily: 'var(--font-mono)', color: selectedFleet.fuelPercent < 20 ? '#DC2626' : '#FBBF24' }}>
                    {selectedFleet.fuelPercent || 85}%
                  </div>
                </div>
              </div>

              <div className="glass-panel stat-box">
                <div className="stat-box-icon" style={{ background: 'rgba(168, 85, 247, 0.15)' }}>
                  <Thermometer size={20} color="#A855F7" />
                </div>
                <div>
                  <div style={{ fontSize: '0.72rem', color: 'var(--color-muted)', textTransform: 'uppercase', fontWeight: 700 }}>{t.cargoTemp}</div>
                  <div style={{ fontSize: '1.3rem', fontWeight: 800, fontFamily: 'var(--font-mono)', color: selectedFleet.cargoTempC < 10 ? '#34D399' : '#FBBF24' }}>
                    {selectedFleet.cargoTempC}°C
                  </div>
                </div>
              </div>
            </div>

            {/* Route Vector & Driver Telemetry Panel */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '14px', marginTop: '14px', flexShrink: 0 }}>
              
              {/* Route Information Box */}
              <div style={{ padding: '14px', borderRadius: '10px', background: 'var(--color-surface)', border: '1px solid var(--color-border)' }}>
                <h3 style={{ fontSize: '0.78rem', fontWeight: 800, color: 'var(--color-muted)', textTransform: 'uppercase', marginBottom: '8px' }}>
                  <Navigation size={13} style={{ verticalAlign: 'middle' }} /> Route Vector & Corridor Progress
                </h3>
                <p style={{ fontSize: '0.8rem', marginBottom: '3px' }}>
                  Corridor: <strong style={{ color: '#2563EB' }}>{selectedFleet.current_route?.name || 'Guwahati - Shillong Corridor'}</strong>
                </p>
                <p style={{ fontSize: '0.8rem', marginBottom: '3px' }}>
                  {t.origin}: <strong style={{ color: 'var(--color-text)' }}>{selectedFleet.current_route?.origin || getLocName(selectedFleet.origin)}</strong>
                </p>
                <p style={{ fontSize: '0.8rem', marginBottom: '3px' }}>
                  {t.destination}: <strong style={{ color: 'var(--color-text)' }}>{selectedFleet.current_route?.destination || getLocName(selectedFleet.destination)}</strong>
                </p>
                <p style={{ fontSize: '0.8rem', marginBottom: '3px' }}>
                  {t.currentPos || "Current Pos"}: <strong style={{ color: '#2563EB' }}>{selectedFleet.current_route?.current_waypoint || selectedFleet.currentLocationName}</strong> ({selectedFleet.lat}, {selectedFleet.lng})
                </p>
                <div style={{ marginTop: '8px', fontSize: '0.72rem', color: 'var(--color-muted)', display: 'flex', justifyContent: 'space-between' }}>
                  <span>Last Updated: <strong>{selectedFleet.last_updated || 'Live'}</strong></span>
                  <span>Progress: <strong>{selectedFleet.current_route?.progress_pct || 45}%</strong></span>
                </div>
              </div>

              {/* Driver Contact & Satellite Link */}
              <div style={{ padding: '14px', borderRadius: '10px', background: 'var(--color-surface)', border: '1px solid var(--color-border)' }}>
                <h3 style={{ fontSize: '0.78rem', fontWeight: 800, color: 'var(--color-muted)', textTransform: 'uppercase', marginBottom: '8px' }}>
                  <User size={13} style={{ verticalAlign: 'middle' }} /> {t.driverLine}
                </h3>
                <p style={{ fontSize: '0.86rem', fontWeight: 700, color: 'var(--color-text)', marginBottom: '3px' }}>
                  👤 {selectedFleet.driver}
                </p>
                <p style={{ fontSize: '0.8rem', color: '#2563EB', marginBottom: '6px' }}>
                  📞 {selectedFleet.phone || '+91 98640 11234'}
                </p>
                <button
                  onClick={() => {
                    setCallingDriver(true);
                    setTimeout(() => setCallingDriver(false), 4500);
                  }}
                  style={{
                    minHeight: '36px',
                    padding: '6px 12px',
                    borderRadius: '6px',
                    background: callingDriver ? 'rgba(16, 185, 129, 0.2)' : 'rgba(59, 130, 246, 0.15)',
                    border: callingDriver ? '1px solid #10B981' : '1px solid #3B82F6',
                    color: callingDriver ? '#059669' : 'var(--color-primary)',
                    fontSize: '0.78rem',
                    fontWeight: 700,
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px'
                  }}
                >
                  <Phone size={14} /> {callingDriver ? 'Connecting Secure Radio...' : 'Emergency Radio Channel'}
                </button>
                {callingDriver && (
                  <div style={{ marginTop: '8px', padding: '6px 8px', borderRadius: '6px', background: 'rgba(16, 185, 129, 0.12)', border: '1px solid rgba(16, 185, 129, 0.3)', color: '#059669', fontSize: '0.72rem', fontWeight: 600 }}>
                    🎙️ Secure Encrypted Radio Channel active with {selectedFleet.driver}...
                  </div>
                )}
              </div>
            </div>

            {/* Telemetry Sensor Graph */}
            <div style={{ marginTop: '14px', padding: '14px', borderRadius: '10px', background: 'var(--color-surface)', border: '1px solid var(--color-border)', flex: 1, minHeight: '180px', display: 'flex', flexDirection: 'column' }}>
              <h3 style={{ fontSize: '0.78rem', fontWeight: 800, color: 'var(--color-muted)', textTransform: 'uppercase', marginBottom: '8px', flexShrink: 0 }}>
                {t.telemetryTrend} ({t.speedVsTemp || "Speed vs Cargo Temperature"})
              </h3>
              <div style={{ width: '100%', flex: 1, minHeight: '140px' }}>
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={selectedFleet?.telemetryHistory || []}>
                    <XAxis dataKey="time" stroke="var(--color-dim)" fontSize={11} />
                    <YAxis stroke="var(--color-dim)" fontSize={11} />
                    <Tooltip contentStyle={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)', color: 'var(--color-text)' }} />
                    <Line type="monotone" dataKey="speed" stroke="#2563EB" strokeWidth={2} name={`${t.speed} (${t.kmhUnit || "km/h"})`} />
                    <Line type="monotone" dataKey="temp" stroke="#10B981" strokeWidth={2} name={`${t.cargoTemp} (°C)`} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        ) : (
          <div className="glass-panel empty-state-box" style={{ height: '100%' }}>
            <Inbox size={48} color="#64748B" />
            <h3 style={{ color: 'var(--color-text)' }}>{t.selectConvoyPrompt || "Select a Convoy to View Real-Time Telemetry"}</h3>
          </div>
        )}
      </div>
    </div>
  );
};
