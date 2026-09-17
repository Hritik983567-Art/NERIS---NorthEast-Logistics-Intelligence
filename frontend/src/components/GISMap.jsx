import React, { useState, useEffect, useMemo } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap } from 'react-leaflet';
import L from 'leaflet';
import { useApp } from '../context/AppContext';
import { api } from '../services/api';
import { majorCorridors, hubLocations } from '../data/nerData';
import { localizedCorridors, localizedFleets } from '../data/localizedData';
import {
  Layers,
  AlertTriangle,
  Truck,
  CloudRain,
  Navigation,
  ShieldAlert,
  Inbox,
  HelpCircle,
  Info,
  Sparkles,
  Building2,
  ChevronLeft,
  ChevronRight,
  Sliders,
  X
} from 'lucide-react';
import 'leaflet/dist/leaflet.css';

// Custom SVG Markers
const createSvgIcon = (svgString, color) => {
  if (typeof window === 'undefined' || !L || typeof L.divIcon !== 'function') return null;
  try {
    return L.divIcon({
      html: `<div style="
        background-color: ${color};
        width: 32px;
        height: 32px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 0 12px ${color};
        border: 2px solid white;
      ">${svgString}</div>`,
      className: 'custom-leaflet-marker',
      iconSize: [32, 32],
      iconAnchor: [16, 16],
      popupAnchor: [0, -16]
    });
  } catch (err) {
    return null;
  }
};

function MapViewCenter({ center, zoom }) {
  const map = useMap();
  const lastTargetRef = React.useRef({ lat: null, lng: null, zoom: null });

  useEffect(() => {
    if (!center || !Array.isArray(center) || center.length < 2) return;
    const lat = Number(center[0]);
    const lng = Number(center[1]);
    const z = Number(zoom);

    if (!Number.isFinite(lat) || !Number.isFinite(lng)) return;

    // Only invoke flyTo if latitude, longitude, or zoom level actually changed
    if (
      lastTargetRef.current.lat === lat &&
      lastTargetRef.current.lng === lng &&
      lastTargetRef.current.zoom === z
    ) {
      return;
    }

    lastTargetRef.current = { lat, lng, zoom: z };
    map.flyTo([lat, lng], z, { duration: 0.8, easeLinearity: 0.3 });
  }, [center, zoom, map]);

  return null;
}

export const GISMap = () => {
  const { t, lang, stateFilter, incidents, fleets, nerStates, triggerSOSAlert, theme } = useApp();

  const isDark = theme === 'dark';

  const truckIcon = useMemo(() => createSvgIcon(
    '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2"><rect x="1" y="3" width="15" height="13"></rect><polygon points="16 8 20 8 23 11 23 16 16 16 16 8"></polygon><circle cx="5.5" cy="18.5" r="2.5"></circle><circle cx="18.5" cy="18.5" r="2.5"></circle></svg>',
    '#06B6D4'
  ), []);

  const landslideIcon = useMemo(() => createSvgIcon(
    '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>',
    '#EF4444'
  ), []);

  const floodIcon = useMemo(() => createSvgIcon(
    '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2"><path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z"></path></svg>',
    '#3B82F6'
  ), []);

  const hubIcon = useMemo(() => createSvgIcon(
    '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2"><path d="M3 21h18"></path><path d="M3 10h18"></path><path d="M5 6l7-3 7 3"></path><path d="M4 10v11"></path><path d="M20 10v11"></path></svg>',
    '#8B5CF6'
  ), []);

  const historicalMarkerIcon = useMemo(() => createSvgIcon(
    '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2"><polygon points="12 2 22 12 12 22 2 12 12 2"></polygon></svg>',
    '#A855F7'
  ), []);
  
  // Single, 100% reliable free OpenStreetMap tile provider for both Day & Night modes
  const tileUrl = "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png";
  const tileSubdomains = "abc";
  const tileAttribution = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors';

  const [showIncidents, setShowIncidents] = useState(true);
  const [showFleets, setShowFleets] = useState(true);
  const [showCorridors, setShowCorridors] = useState(true);
  const [showWeatherOverlay, setShowWeatherOverlay] = useState(false);
  const [showHistoricalRainfall, setShowHistoricalRainfall] = useState(false);
  const [showHistoricalLandslidesFloods, setShowHistoricalLandslidesFloods] = useState(false);
  const [showHistoricalRoadRisk, setShowHistoricalRoadRisk] = useState(false);
  const [showHistoricalEmergencyResources, setShowHistoricalEmergencyResources] = useState(false);
  
  const [dockOpen, setDockOpen] = useState(false);
  const [leftCollapsed, setLeftCollapsed] = useState(false);
  const [rightCollapsed, setRightCollapsed] = useState(false);
  const [rainfallRiskIndex, setRainfallRiskIndex] = useState([]);
  const [historicalLandslideFloodRecords, setHistoricalLandslideFloodRecords] = useState([]);
  const [roadRiskIndices, setRoadRiskIndices] = useState([]);
  const [emergencyResourceRecords, setEmergencyResourceRecords] = useState([]);
  const [selectedItem, setSelectedItem] = useState(null);
  const [dockTab, setDockTab] = useState('layers');
  const [backendHubs, setBackendHubs] = useState([]);
  const [dynamicCorridors, setDynamicCorridors] = useState([]);
  const [liveIncidents, setLiveIncidents] = useState([]);
  const [liveWeatherList, setLiveWeatherList] = useState([]);
  const [aiIntelligence, setAiIntelligence] = useState(null);
  const [loadingAi, setLoadingAi] = useState(false);

  useEffect(() => {
    setAiIntelligence(null);
  }, [selectedItem]);

  const handleGenerateAI = async () => {
    if (!selectedItem || selectedItem.type !== 'incident') return;
    setLoadingAi(true);
    setAiIntelligence(null);
    try {
      const res = await api.getIncidentAIIntelligence(selectedItem.data.id, selectedItem.data);
      setAiIntelligence(res);
    } catch (err) {
      setAiIntelligence({
        available: false,
        error_message: err.message || 'Amazon Bedrock connection error.'
      });
    } finally {
      setLoadingAi(false);
    }
  };

  useEffect(() => {
    async function loadNetworkData() {
      const nodes = await api.getNetworkNodes();
      if (nodes && nodes.length > 0) {
        setBackendHubs(nodes);
      }
      const corridors = await api.getNetworkCorridors();
      if (corridors && corridors.length > 0) {
        setDynamicCorridors(corridors);
      }
      const liveIncs = await api.getLiveIncidents();
      if (liveIncs && liveIncs.length > 0) {
        setLiveIncidents(liveIncs);
      }
      const weatherRes = await api.getLiveWeather();
      if (weatherRes && weatherRes.hubs_weather) {
        setLiveWeatherList(weatherRes.hubs_weather);
      }
      const rfRisk = await api.getHistoricalRainfallRiskIndex('SEP');
      if (rfRisk && rfRisk.length > 0) {
        setRainfallRiskIndex(rfRisk);
      }
      const histLF = await api.getHistoricalLandslideFloodRecords();
      if (histLF && Array.isArray(histLF)) {
        setHistoricalLandslideFloodRecords(histLF);
      }
      const roadRisk = await api.getHistoricalRoadRiskIndex();
      if (roadRisk && Array.isArray(roadRisk)) {
        setRoadRiskIndices(roadRisk);
      }
      const resData = await api.getEmergencyResources();
      if (resData && Array.isArray(resData)) {
        setEmergencyResourceRecords(resData);
      }
    }
    loadNetworkData();
  }, []);

  const currentStateObj = nerStates.find((s) => s.id === stateFilter) || nerStates[0];
  
  let rawLat = Number(currentStateObj?.lat);
  let rawLng = Number(currentStateObj?.lng);
  let activeCenter = [
    Number.isFinite(rawLat) ? rawLat : defaultCenter[0],
    Number.isFinite(rawLng) ? rawLng : defaultCenter[1]
  ];
  let activeZoom = currentStateObj?.zoom || 7;

  if (selectedItem && selectedItem.data) {
    if (selectedItem.type === 'corridor' && selectedItem.data.coordinates?.length) {
      const firstCoord = selectedItem.data.coordinates[0];
      if (Array.isArray(firstCoord) && Number.isFinite(Number(firstCoord[0])) && Number.isFinite(Number(firstCoord[1]))) {
        activeCenter = [Number(firstCoord[0]), Number(firstCoord[1])];
        activeZoom = 8;
      }
    } else {
      const itemLat = Number(selectedItem.data.lat ?? selectedItem.data.latitude);
      const itemLng = Number(selectedItem.data.lng ?? selectedItem.data.longitude);
      if (Number.isFinite(itemLat) && Number.isFinite(itemLng)) {
        activeCenter = [itemLat, itemLng];
        activeZoom = 10;
      }
    }
  }

  if (
    !Array.isArray(activeCenter) ||
    activeCenter.length < 2 ||
    !Number.isFinite(Number(activeCenter[0])) ||
    !Number.isFinite(Number(activeCenter[1]))
  ) {
    activeCenter = defaultCenter;
  }

  const filteredIncidents = incidents.filter(
    (inc) => stateFilter === 'all' || inc.state === stateFilter
  );

  const filteredFleets = fleets.filter(
    (f) => stateFilter === 'all' || f.state === stateFilter
  );

  const filteredCorridors = majorCorridors.filter(
    (c) => stateFilter === 'all' || c.state === stateFilter
  );

  const getCorridorColor = (status) => {
    switch (status) {
      case 'clear': return '#10B981';
      case 'caution': return '#F59E0B';
      case 'blocked': return '#EF4444';
      default: return '#3B82F6';
    }
  };

  return (
    <div className="gis-layout" style={{ gridTemplateColumns: `${leftCollapsed ? '44px' : '285px'} 1fr ${rightCollapsed ? '44px' : '290px'}`, transition: 'grid-template-columns 0.25s cubic-bezier(0.4, 0, 0.2, 1)' }}>
      {/* Left Control Panel: Corridor Accessibility & Hazards */}
      {leftCollapsed ? (
        <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '12px 6px', height: '100%', gap: '16px' }}>
          <button
            onClick={() => setLeftCollapsed(false)}
            title="Expand Hazards & Corridors Sidebar"
            style={{ background: '#2563EB', color: '#FFF', border: 'none', borderRadius: '8px', padding: '8px', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 2px 8px rgba(37,99,235,0.4)' }}
          >
            <ChevronRight size={18} />
          </button>
          <div style={{ writingMode: 'vertical-rl', textTransform: 'uppercase', letterSpacing: '1px', fontSize: '0.72rem', fontWeight: 800, color: 'var(--color-muted)', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <AlertTriangle size={14} color="#EF4444" />
            <span>Hazards & Corridors ({filteredIncidents.length})</span>
          </div>
        </div>
      ) : (
        <div className="sidebar-panel">
          <div className="glass-panel" style={{ padding: '12px 14px', flex: '0 0 auto', maxHeight: '42%', display: 'flex', flexDirection: 'column' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
              <h2 className="section-title" style={{ fontSize: '0.92rem', flexShrink: 0, margin: 0 }}>
                <Layers size={17} color="#3B82F6" />
                {t.accessibilityStatus}
              </h2>
              <button
                onClick={() => setLeftCollapsed(true)}
                title="Collapse Panel"
                style={{ background: 'transparent', border: 'none', cursor: 'pointer', color: 'var(--color-muted)', padding: '2px', borderRadius: '4px' }}
              >
                <ChevronLeft size={18} />
              </button>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', overflowY: 'auto', flex: 1, paddingRight: '2px' }}>
              {filteredCorridors.map((c) => {
                const statusText = c.status === 'blocked' ? (t.pillBlocked || 'BLOCKED') : c.status === 'caution' ? (t.pillCaution || 'CAUTION') : (t.pillClear || 'CLEAR');
                const loc = localizedCorridors[c.id]?.[lang] || {};
                const name = loc.name || c.name;
                const route = loc.route || c.route;
                const activeAlert = loc.alert || c.activeAlert;

                return (
                  <div
                    key={c.id}
                    tabIndex={0}
                    role="button"
                    aria-label={`Select corridor ${name}, status ${c.status}`}
                    className={`item-card ${selectedItem?.data?.id === c.id ? 'selected' : ''}`}
                    onClick={() => setSelectedItem({ type: 'corridor', data: c })}
                    onKeyDown={(e) => e.key === 'Enter' && setSelectedItem({ type: 'corridor', data: c })}
                    style={{ padding: '8px 10px' }}
                  >
                    <div className="item-card-header">
                      <span className="item-card-title" style={{ fontWeight: 800, fontSize: '0.82rem', color: '#2563EB' }}>{name}</span>
                      <span className={`pill ${c.status}`}>{statusText}</span>
                    </div>
                    <p style={{ fontSize: '0.72rem', color: 'var(--color-muted)', marginTop: '2px', lineHeight: 1.3 }}>
                      {route}
                    </p>
                    {activeAlert && (
                      <p style={{ fontSize: '0.7rem', color: '#D97706', marginTop: '2px', display: 'flex', alignItems: 'center', gap: '4px', fontWeight: 600 }}>
                        <AlertTriangle size={11} /> {activeAlert}
                      </p>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Active Hazards Panel */}
          <div className="glass-panel" style={{ padding: '12px 14px', flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', minHeight: 0 }}>
            <h2 className="section-title" style={{ fontSize: '0.92rem', flexShrink: 0, marginBottom: '8px' }}>
              <AlertTriangle size={17} color="#EF4444" />
              {t.activeHazards} ({filteredIncidents.length})
            </h2>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', flex: 1, overflowY: 'auto', paddingRight: '2px' }}>
              {filteredIncidents.length === 0 ? (
                <div className="empty-state-box">
                  <Inbox size={24} color="#64748B" />
                  <span style={{ fontWeight: 600, fontSize: '0.8rem' }}>No Active Hazards</span>
                  <span style={{ fontSize: '0.7rem' }}>Selected region is clear.</span>
                </div>
              ) : (
                filteredIncidents.map((inc) => {
                  const incStatusText = inc.severity?.toLowerCase() === 'critical' ? (t.pillBlocked || 'BLOCKED') : (t.pillCaution || 'CAUTION');
                  const isLiveIncident = Boolean(inc.is_live || inc.dynamodb_confirmed || inc.status === 'SYNCED' || inc.status === 'SUBMITTED');

                  return (
                    <div
                      key={inc.id}
                      tabIndex={0}
                      role="button"
                      aria-label={`Select hazard ${inc.title}`}
                      className={`item-card ${selectedItem?.data?.id === inc.id ? 'selected' : ''}`}
                      onClick={() => setSelectedItem({ type: 'incident', data: inc })}
                      onKeyDown={(e) => e.key === 'Enter' && setSelectedItem({ type: 'incident', data: inc })}
                      style={{ padding: '8px 10px' }}
                    >
                      <div className="item-card-header">
                        <span className="item-card-title" style={{ fontWeight: 800, fontSize: '0.82rem', color: 'var(--color-text)' }}>{inc.title}</span>
                        <span className={`pill ${inc.severity?.toLowerCase() === 'critical' ? 'blocked' : 'caution'}`}>
                          {incStatusText}
                        </span>
                      </div>

                      <div style={{ display: 'flex', gap: '4px', alignItems: 'center', marginTop: '3px', flexWrap: 'wrap' }}>
                        <span className={`pill ${isLiveIncident ? 'blocked' : 'clear'}`} style={{ fontSize: '0.6rem', padding: '1px 5px', fontWeight: 800 }}>
                          {isLiveIncident ? '🔴 VERIFIED INCIDENT' : 'REPORTED HAZARD'}
                        </span>
                        {inc.type && (
                          <span className="pill clear" style={{ fontSize: '0.6rem', padding: '1px 5px' }}>
                            {inc.type}
                          </span>
                        )}
                      </div>

                      <p style={{ fontSize: '0.72rem', color: 'var(--color-muted)', marginTop: '3px' }}>
                        📍 {inc.locationName || inc.location_name}
                      </p>
                    </div>
                  );
                })
              )}
            </div>
          </div>
        </div>
      )}

      {/* Main Map Container Box */}
      <div className="map-container-box" style={{ position: 'relative' }}>
        {/* Compact Non-Intrusive Active Overlays Indicator Bar (Bottom Left) */}
        {(showHistoricalRainfall || showHistoricalLandslidesFloods || showHistoricalRoadRisk || showHistoricalEmergencyResources) && (
          <div style={{
            position: 'absolute',
            bottom: '12px',
            left: '12px',
            zIndex: 400,
            display: 'flex',
            flexWrap: 'wrap',
            gap: '6px',
            alignItems: 'center',
            maxWidth: 'calc(100% - 240px)',
            pointerEvents: 'none'
          }}>
            {showHistoricalRainfall && (
              <div style={{
                background: 'rgba(15, 23, 42, 0.92)',
                backdropFilter: 'blur(8px)',
                color: '#F87171',
                padding: '4px 10px',
                borderRadius: '12px',
                fontSize: '0.68rem',
                fontWeight: 700,
                display: 'flex',
                alignItems: 'center',
                gap: '5px',
                border: '1px solid rgba(239, 68, 68, 0.4)',
                boxShadow: '0 4px 12px rgba(0,0,0,0.3)'
              }}>
                <CloudRain size={12} />
                <span>Rainfall Baseline (1901–2017)</span>
              </div>
            )}
            {showHistoricalLandslidesFloods && (
              <div style={{
                background: 'rgba(15, 23, 42, 0.92)',
                backdropFilter: 'blur(8px)',
                color: '#C084FC',
                padding: '4px 10px',
                borderRadius: '12px',
                fontSize: '0.68rem',
                fontWeight: 700,
                display: 'flex',
                alignItems: 'center',
                gap: '5px',
                border: '1px solid rgba(168, 85, 247, 0.4)',
                boxShadow: '0 4px 12px rgba(0,0,0,0.3)'
              }}>
                <AlertTriangle size={12} />
                <span>Flood & Landslide Risk</span>
              </div>
            )}
            {showHistoricalRoadRisk && (
              <div style={{
                background: 'rgba(15, 23, 42, 0.92)',
                backdropFilter: 'blur(8px)',
                color: '#A78BFA',
                padding: '4px 10px',
                borderRadius: '12px',
                fontSize: '0.68rem',
                fontWeight: 700,
                display: 'flex',
                alignItems: 'center',
                gap: '5px',
                border: '1px solid rgba(124, 58, 237, 0.4)',
                boxShadow: '0 4px 12px rgba(0,0,0,0.3)'
              }}>
                <ShieldAlert size={12} />
                <span>Road Risk Blackspots</span>
              </div>
            )}
            {showHistoricalEmergencyResources && (
              <div style={{
                background: 'rgba(15, 23, 42, 0.92)',
                backdropFilter: 'blur(8px)',
                color: '#38BDF8',
                padding: '4px 10px',
                borderRadius: '12px',
                fontSize: '0.68rem',
                fontWeight: 700,
                display: 'flex',
                alignItems: 'center',
                gap: '5px',
                border: '1px solid rgba(6, 182, 212, 0.4)',
                boxShadow: '0 4px 12px rgba(0,0,0,0.3)'
              }}>
                <Building2 size={12} />
                <span>Emergency Resource Depots</span>
              </div>
            )}
          </div>
        )}
        <MapContainer
          center={activeCenter}
          zoom={activeZoom}
          scrollWheelZoom={true}
          style={{ width: '100%', height: '100%' }}
        >
          <MapViewCenter center={activeCenter} zoom={activeZoom} />
          
          <TileLayer
            key="osm-unified-tiles"
            attribution={tileAttribution}
            url={tileUrl}
            subdomains={tileSubdomains}
            maxZoom={19}
          />

          {showCorridors && filteredCorridors.map((c) => (
            <Polyline
              key={c.id}
              positions={c.coordinates}
              pathOptions={{
                color: getCorridorColor(c.status),
                weight: c.status === 'blocked' ? 5 : 4,
                dashArray: c.status === 'blocked' ? '8, 8' : undefined,
                opacity: 0.85
              }}
              eventHandlers={{
                click: () => setSelectedItem({ type: 'corridor', data: c })
              }}
            >
              <Popup>
                <div style={{ padding: '4px', color: '#F8FAFC' }}>
                  <strong style={{ fontSize: '0.9rem', color: '#38BDF8' }}>{c.name}</strong>
                  <p style={{ fontSize: '0.8rem', margin: '4px 0', color: 'var(--color-muted)' }}>{c.route}</p>
                  <p style={{ fontSize: '0.78rem', color: '#FBBF24', fontWeight: 600 }}>{c.activeAlert}</p>
                </div>
              </Popup>
            </Polyline>
          ))}

          {showIncidents && filteredIncidents
            .filter((inc) => {
              const lat = Number(inc?.lat ?? inc?.latitude);
              const lng = Number(inc?.lng ?? inc?.longitude);
              return Number.isFinite(lat) && Number.isFinite(lng);
            })
            .map((inc, idx) => {
              const lat = Number(inc.lat ?? inc.latitude);
              const lng = Number(inc.lng ?? inc.longitude);
              const isLive = Boolean(inc.is_live || inc.dynamodb_confirmed || inc.status === 'SYNCED' || inc.status === 'SUBMITTED');
              const photoSrc = inc.evidence_url || inc.photoUrl;

              return (
                <Marker
                  key={inc.id || `inc-marker-${idx}`}
                  position={[lat, lng]}
                  icon={String(inc.type || '').toLowerCase() === 'flood' ? floodIcon : landslideIcon}
                  eventHandlers={{
                    click: () => setSelectedItem({ type: 'incident', data: inc })
                  }}
                >
                  <Popup>
                    <div style={{ color: '#F8FAFC', maxWidth: '240px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                        <strong style={{ color: '#FF66B2', fontSize: '0.9rem' }}>{inc.title}</strong>
                      </div>

                      <div style={{ marginBottom: '6px' }}>
                        <span className={`pill ${isLive ? 'blocked' : 'clear'}`} style={{ fontSize: '0.6rem', padding: '1px 5px' }}>
                          {isLive ? '🔴 VERIFIED INCIDENT' : 'REPORTED HAZARD'}
                        </span>
                      </div>

                      <p style={{ fontSize: '0.78rem', color: '#E2E8F0', margin: '4px 0' }}>{inc.description}</p>
                      
                      <div style={{ fontSize: '0.72rem', color: '#94A3B8', marginTop: '4px', borderTop: '1px solid rgba(255,255,255,0.1)', paddingTop: '4px' }}>
                        <div>Type: <strong style={{ color: '#FFF' }}>{inc.type || 'HAZARD'}</strong> • Severity: <strong style={{ color: '#EF4444' }}>{inc.severity}</strong></div>
                        <div>GPS: <code>{lat.toFixed(4)}, {lng.toFixed(4)}</code></div>
                        <div>Reporter: {inc.reporter || 'Field Unit'}</div>
                        <div>Status: <strong style={{ color: '#34D399' }}>{inc.status || 'ACTIVE'}</strong></div>
                        {inc.timestamp && <div>Time: {new Date(inc.timestamp).toLocaleTimeString()}</div>}
                      </div>

                      {photoSrc && (
                        <div style={{ marginTop: '6px' }}>
                          <img
                            src={photoSrc}
                            alt="Evidence"
                            style={{ width: '100%', height: '80px', objectFit: 'cover', borderRadius: '4px', border: '1px solid rgba(255,255,255,0.2)' }}
                          />
                        </div>
                      )}
                    </div>
                  </Popup>
                </Marker>
              );
            })}

          {showHistoricalLandslidesFloods && historicalLandslideFloodRecords
            .filter((ev) => {
              const lat = Number(ev?.lat ?? ev?.latitude);
              const lng = Number(ev?.lng ?? ev?.longitude);
              return Number.isFinite(lat) && Number.isFinite(lng);
            })
            .map((ev, idx) => {
              const lat = Number(ev.lat ?? ev.latitude);
              const lng = Number(ev.lng ?? ev.longitude);

              return (
                <Marker
                  key={ev.id || `hist-marker-${idx}`}
                  position={[lat, lng]}
                  icon={historicalMarkerIcon}
                >
                  <Popup>
                    <div style={{ color: '#F8FAFC', maxWidth: '250px' }}>
                      <strong style={{ color: '#C084FC', fontSize: '0.88rem' }}>📜 {ev.event_name || ev.title}</strong>
                      <div style={{ marginTop: '4px' }}>
                        <span className="pill clear" style={{ fontSize: '0.6rem', padding: '1px 5px', background: 'rgba(168, 85, 247, 0.2)', color: '#C084FC', border: '1px solid #A855F7' }}>
                          HISTORICAL HAZARD RECORD
                        </span>
                      </div>
                      <p style={{ fontSize: '0.74rem', color: '#E2E8F0', margin: '4px 0' }}>{ev.description}</p>
                      <div style={{ fontSize: '0.72rem', color: '#94A3B8', marginTop: '4px', borderTop: '1px solid rgba(255,255,255,0.1)', paddingTop: '4px' }}>
                        <div>Type: <strong style={{ color: '#FFF' }}>{ev.event_type}</strong> • State: <strong style={{ color: '#A855F7' }}>{ev.state}</strong></div>
                        <div>Year / Period: {ev.year || ev.event_date || '2000–2023 Catalog'}</div>
                        <div>Source: {ev.dataset_source || 'National Landslide Database'}</div>
                        <div>Status: <strong style={{ color: '#C084FC' }}>HISTORICAL HAZARD RECORD</strong></div>
                      </div>
                    </div>
                  </Popup>
                </Marker>
              );
            })}

          {showHistoricalRainfall && rainfallRiskIndex.map((rf, idx) => {
            const centroids = {
              "ASSAM & MEGHALAYA": [26.2006, 92.9376],
              "ARUNACHAL PRADESH": [28.2180, 94.7278],
              "NAGA MANI MIZO TRIPURA": [24.6637, 93.9063],
              "SUB HIMALAYAN WEST BENGAL & SIKKIM": [27.5330, 88.5122]
            };
            const pos = centroids[rf.subdivision] || [26.0, 92.0];
            return (
              <Marker
                key={`rf-sub-${idx}`}
                position={pos}
                icon={createSvgIcon(
                  '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2"><path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z"></path></svg>',
                  rf.risk_level === 'CRITICAL' ? '#DC2626' : rf.risk_level === 'HIGH' ? '#EA580C' : rf.risk_level === 'MODERATE' ? '#D97706' : '#2563EB'
                )}
                eventHandlers={{
                  click: () => setSelectedItem({ type: 'historical_rainfall', data: rf })
                }}
              >
                <Popup>
                  <div style={{ color: '#F8FAFC', maxWidth: '260px' }}>
                    <strong style={{ color: '#38BDF8', fontSize: '0.9rem' }}>🌧️ {rf.subdivision}</strong>
                    <div style={{ marginTop: '4px' }}>
                      <span className="pill blocked" style={{ fontSize: '0.62rem', padding: '1px 6px', background: 'rgba(220, 38, 38, 0.2)', color: '#F87171', border: '1px solid #F87171' }}>
                        IMD RAINFALL BASELINE
                      </span>
                    </div>
                    <div style={{ fontSize: '0.78rem', color: '#E2E8F0', marginTop: '6px' }}>
                      <div>Month Baseline: <strong>{rf.month}</strong></div>
                      <div>Average Rainfall: <strong>{rf.mean_rainfall_mm} mm</strong></div>
                      <div>Historical Risk Score: <strong style={{ color: rf.risk_level === 'CRITICAL' ? '#EF4444' : '#F59E0B' }}>{rf.risk_score} ({rf.risk_level})</strong></div>
                    </div>
                    <div style={{ fontSize: '0.7rem', color: '#94A3B8', marginTop: '6px', borderTop: '1px solid rgba(255,255,255,0.1)', paddingTop: '4px' }}>
                      Source: IMD / Government of India Meteorological Archive
                    </div>
                  </div>
                </Popup>
              </Marker>
            );
          })}

          {showHistoricalRoadRisk && roadRiskIndices.map((rd, idx) => {
            const stateCentroids = {
              "Assam": [26.2006, 92.9376],
              "Meghalaya": [25.5788, 91.8933],
              "Arunachal Pradesh": [28.2180, 94.7278],
              "Nagaland": [26.1584, 94.5624],
              "Manipur": [24.6637, 93.9063],
              "Mizoram": [23.1645, 92.9376],
              "Tripura": [23.8315, 91.2868],
              "Sikkim": [27.5330, 88.5122]
            };
            const pos = stateCentroids[rd.state] || [26.0, 92.0];
            return (
              <Marker
                key={`rd-risk-${idx}`}
                position={pos}
                icon={createSvgIcon(
                  '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>',
                  rd.risk_level === 'CRITICAL' ? '#DC2626' : rd.risk_level === 'HIGH' ? '#EA580C' : rd.risk_level === 'MODERATE' ? '#D97706' : '#2563EB'
                )}
                eventHandlers={{
                  click: () => setSelectedItem({ type: 'road_risk', data: rd })
                }}
              >
                <Popup>
                  <div style={{ color: '#F8FAFC', maxWidth: '270px' }}>
                    <strong style={{ color: '#A78BFA', fontSize: '0.9rem' }}>🚗 {rd.state} Road Risk Baseline</strong>
                    <div style={{ marginTop: '4px' }}>
                      <span className="pill clear" style={{ fontSize: '0.62rem', padding: '1px 6px', background: 'rgba(167, 139, 250, 0.2)', color: '#C4B5FD', border: '1px solid #A78BFA' }}>
                        ROAD ACCIDENT RISK MATRIX
                      </span>
                    </div>
                    <div style={{ fontSize: '0.78rem', color: '#E2E8F0', marginTop: '6px' }}>
                      <div>Historical Risk Rating: <strong style={{ color: rd.risk_level === 'HIGH' || rd.risk_level === 'CRITICAL' ? '#EF4444' : '#F59E0B' }}>{rd.risk_score}/100 ({rd.risk_level})</strong></div>
                      <div>Sampled Incidents: <strong>{rd.total_records} records</strong></div>
                      <div>Top Factors: <strong>{rd.top_risk_factors?.join(', ') || 'N/A'}</strong></div>
                    </div>
                    <div style={{ fontSize: '0.7rem', color: '#94A3B8', marginTop: '6px', borderTop: '1px solid rgba(255,255,255,0.1)', paddingTop: '4px' }}>
                      Source: Road Safety Statistical Analysis
                    </div>
                  </div>
                </Popup>
              </Marker>
            );
          })}

          {showHistoricalEmergencyResources && emergencyResourceRecords
            .filter((r) => {
              const lat = Number(r?.lat ?? r?.latitude);
              const lng = Number(r?.lng ?? r?.longitude);
              return Number.isFinite(lat) && Number.isFinite(lng);
            })
            .map((r, idx) => {
              const lat = Number(r.lat ?? r.latitude);
              const lng = Number(r.lng ?? r.longitude);

              return (
                <Marker
                  key={`res-${r.id || idx}`}
                  position={[lat, lng]}
                  icon={createSvgIcon(
                    '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2"><path d="M3 21h18"></path><path d="M5 21V7l7-4 7 4v14"></path><path d="M9 10h6"></path><path d="M12 7v6"></path></svg>',
                    r.type === 'HOSPITAL' ? '#EF4444' : r.type === 'WAREHOUSE' ? '#F59E0B' : r.type === 'SHELTER' ? '#10B981' : '#06B6D4'
                  )}
                  eventHandlers={{
                    click: () => setSelectedItem({ type: 'emergency_resource', data: r })
                  }}
                >
                  <Popup>
                    <div style={{ color: '#F8FAFC', maxWidth: '270px' }}>
                      <strong style={{ color: '#38BDF8', fontSize: '0.9rem' }}>🏥 {r.name}</strong>
                      <div style={{ marginTop: '4px' }}>
                        <span className="pill clear" style={{ fontSize: '0.62rem', padding: '1px 6px', background: 'rgba(6, 182, 212, 0.2)', color: '#22D3EE', border: '1px solid #06B6D4' }}>
                          EMERGENCY INFRASTRUCTURE DIRECTORY
                        </span>
                      </div>
                      <div style={{ fontSize: '0.78rem', color: '#E2E8F0', marginTop: '6px' }}>
                        <div>Category: <strong>{r.type}</strong> • State: <strong>{r.state}</strong></div>
                        <div>Recorded Capacity: <strong>{r.capacity_bed_or_sqm} ({r.type === 'HOSPITAL' ? 'Beds' : 'Sqm'})</strong></div>
                        <div>Historical Available Snapshot: <strong>{r.historical_available_capacity}</strong></div>
                        <div>District: <strong>{r.district}</strong></div>
                      </div>
                      <div style={{ fontSize: '0.7rem', color: '#94A3B8', marginTop: '6px', borderTop: '1px solid rgba(255,255,255,0.1)', paddingTop: '4px' }}>
                        Source: Regional Infrastructure Directory
                      </div>
                    </div>
                  </Popup>
                </Marker>
              );
            })}

          {showFleets && filteredFleets
            .filter((f) => {
              const lat = Number(f?.lat ?? f?.latitude);
              const lng = Number(f?.lng ?? f?.longitude);
              return Number.isFinite(lat) && Number.isFinite(lng);
            })
            .map((f, idx) => {
              const lat = Number(f.lat ?? f.latitude);
              const lng = Number(f.lng ?? f.longitude);

              return (
                <Marker
                  key={f.id || `fleet-marker-${idx}`}
                  position={[lat, lng]}
                  icon={truckIcon}
                  eventHandlers={{
                    click: () => setSelectedItem({ type: 'fleet', data: f })
                  }}
                >
                  <Popup>
                    <div style={{ color: '#F8FAFC', maxWidth: '240px' }}>
                      <strong style={{ color: '#38BDF8', fontSize: '0.92rem' }}>🚚 {f.id}</strong>
                      <p style={{ fontSize: '0.8rem', fontWeight: 600, color: '#FFF' }}>{f.category}</p>
                      <p style={{ fontSize: '0.76rem', color: '#94A3B8' }}>Payload: {f.payload}</p>
                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4px', marginTop: '6px', background: 'rgba(255,255,255,0.06)', padding: '6px', borderRadius: '6px' }}>
                        <div>Speed: <strong style={{ color: '#00F2FE' }}>{f.speedKm} km/h</strong></div>
                        <div>Temp: <strong style={{ color: f.cargoTempC < 10 ? '#34D399' : '#FBBF24' }}>{f.cargoTempC}°C</strong></div>
                      </div>
                      <p style={{ fontSize: '0.72rem', color: '#94A3B8', marginTop: '4px' }}>ETA: {f.eta}</p>
                      <button
                        onClick={() => triggerSOSAlert(f.id, "Emergency assistance requested from live map popup")}
                        className="sos-pulse-btn"
                        style={{
                          marginTop: '8px',
                          width: '100%',
                          minHeight: '36px',
                          border: 'none',
                          padding: '6px 10px',
                          borderRadius: '6px',
                          fontSize: '0.78rem',
                          fontWeight: 700,
                          cursor: 'pointer'
                        }}
                      >
                        🚨 Trigger SOS Alert
                      </button>
                    </div>
                  </Popup>
                </Marker>
              );
            })}

          {(backendHubs.length > 0 ? backendHubs : hubLocations)
            .filter((hub) => {
              const lat = Number(hub?.lat ?? hub?.latitude);
              const lng = Number(hub?.lng ?? hub?.longitude);
              return Number.isFinite(lat) && Number.isFinite(lng);
            })
            .map((hub, idx) => {
              const lat = Number(hub.lat ?? hub.latitude);
              const lng = Number(hub.lng ?? hub.longitude);

              return (
                <Marker key={hub.id || idx} position={[lat, lng]} icon={hubIcon}>
                  <Popup>
                    <div style={{ color: '#F8FAFC' }}>
                      <strong style={{ color: '#C084FC' }}>🏬 {hub.name || hub.id}</strong>
                      <p style={{ fontSize: '0.75rem', color: '#94A3B8', marginTop: '2px' }}>
                        Regional Supply Node ({hub.state}) {hub.elevation_m ? `• ${hub.elevation_m}m Alt` : ''}
                      </p>
                    </div>
                  </Popup>
                </Marker>
              );
            })}
        </MapContainer>

        {selectedItem && (
          <div className="map-inspector-banner" role="region" aria-label="Map Inspector Panel">
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              {selectedItem.type === 'fleet' && <Truck size={22} color="#00F2FE" />}
              {selectedItem.type === 'incident' && <AlertTriangle size={22} color="#FF2E93" />}
              {selectedItem.type === 'corridor' && <Navigation size={22} color="#10B981" />}
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                  <strong style={{ fontSize: '0.92rem', color: 'var(--color-text)' }}>
                    {selectedItem.type === 'fleet' ? selectedItem.data.id : selectedItem.data.name || selectedItem.data.title}
                  </strong>
                  <span className={`pill ${selectedItem.data.status || selectedItem.data.severity || 'clear'}`}>
                    {selectedItem.type.toUpperCase()} • {selectedItem.data.status || selectedItem.data.severity}
                  </span>

                  {selectedItem.type === 'incident' && (
                    <span className={`pill ${selectedItem.data.source_type === 'historical_dataset' ? 'caution' : (selectedItem.data.is_verified || selectedItem.data.verificationStatus === 'VERIFIED') ? 'blocked' : 'clear'}`} style={{ fontSize: '0.64rem', fontWeight: 800 }}>
                      {selectedItem.data.source_type === 'historical_dataset'
                        ? '📜 HISTORICAL RISK EVENT'
                        : (selectedItem.data.is_verified || selectedItem.data.verificationStatus === 'VERIFIED')
                          ? '🔴 VERIFIED INCIDENT'
                          : '🟡 UNVERIFIED REPORT'}
                    </span>
                  )}
                </div>

                <p style={{ fontSize: '0.78rem', color: 'var(--color-muted)', marginTop: '2px' }}>
                  {selectedItem.data.route || selectedItem.data.locationName || selectedItem.data.location_name || selectedItem.data.currentLocationName || selectedItem.data.description}
                </p>

                {selectedItem.type === 'incident' && (
                  <div style={{ fontSize: '0.72rem', color: 'var(--color-muted)', display: 'flex', gap: '12px', marginTop: '4px', flexWrap: 'wrap' }}>
                    <span>📍 GPS: <code>{selectedItem.data.lat?.toFixed(4)}, {selectedItem.data.lng?.toFixed(4)}</code></span>
                    <span>Officer: <strong>{selectedItem.data.reporter || 'Field Unit'}</strong></span>
                    <span>Status: <strong>{selectedItem.data.status || 'ACTIVE'}</strong></span>
                    {(selectedItem.data.evidence_url || selectedItem.data.photoUrl) && (
                      <span style={{ color: '#10B981', fontWeight: 700 }}>📷 S3 Evidence Attached</span>
                    )}
                  </div>
                )}
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
              {selectedItem.type === 'incident' && (
                <button
                  onClick={handleGenerateAI}
                  disabled={loadingAi}
                  className="btn-primary"
                  style={{
                    background: 'linear-gradient(135deg, #7C3AED 0%, #6366F1 100%)',
                    padding: '6px 14px',
                    fontSize: '0.78rem',
                    width: 'auto',
                    minHeight: '36px',
                    boxShadow: '0 0 10px rgba(124, 58, 237, 0.4)'
                  }}
                >
                  <Sparkles size={14} className={loadingAi ? "animate-spin" : ""} />
                  {loadingAi ? "Synthesizing AI Hazard Analysis..." : "AI Hazard Intelligence"}
                </button>
              )}
              {selectedItem.type === 'fleet' && (
                <button
                  onClick={() => triggerSOSAlert(selectedItem.data.id, "Inspector Escort Dispatched")}
                  className="btn-primary sos-pulse-btn"
                  style={{ padding: '6px 14px', fontSize: '0.78rem', width: 'auto', minHeight: '36px' }}
                >
                  <ShieldAlert size={14} /> SOS Escort
                </button>
              )}
              <button
                onClick={() => setSelectedItem(null)}
                style={{
                  background: 'rgba(255, 255, 255, 0.08)',
                  border: '1px solid var(--color-border)',
                  color: 'var(--color-muted)',
                  borderRadius: '6px',
                  padding: '6px 12px',
                  fontSize: '0.78rem',
                  cursor: 'pointer',
                  minHeight: '36px'
                }}
              >
                Dismiss
              </button>
            </div>

            {/* AI Intelligence Output Block */}
            {selectedItem.type === 'incident' && aiIntelligence && (
              <div style={{
                marginTop: '12px',
                paddingTop: '12px',
                borderTop: '1px solid var(--color-border)',
                gridColumn: '1 / -1',
                width: '100%'
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                  <h5 style={{ margin: 0, color: '#A78BFA', fontSize: '0.82rem', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <Sparkles size={14} /> AI-generated assessment
                    {aiIntelligence.model_used && (
                      <span style={{ fontSize: '0.68rem', padding: '2px 6px', background: 'rgba(167, 139, 250, 0.2)', borderRadius: '4px', color: '#C4B5FD' }}>
                        {aiIntelligence.model_used}
                      </span>
                    )}
                  </h5>
                  {aiIntelligence.latency_ms !== undefined && (
                    <span style={{ fontSize: '0.68rem', color: 'var(--color-muted)' }}>
                      Latency: {aiIntelligence.latency_ms}ms
                    </span>
                  )}
                </div>

                <div style={{
                  padding: '8px 12px',
                  borderRadius: '6px',
                  background: 'rgba(245, 158, 11, 0.15)',
                  border: '1px solid #F59E0B',
                  color: '#FBBF24',
                  fontSize: '0.75rem',
                  fontWeight: 700,
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  marginBottom: '10px'
                }}>
                  <Info size={14} />
                  <span>{aiIntelligence.disclaimer || "⚠️ AI-Assisted Incident Intelligence — Requires Human Field Officer Verification."}</span>
                </div>

                {aiIntelligence.available === false || aiIntelligence.ai_analysis_status === "FAILED" || aiIntelligence.ai_analysis_status === "UNCONFIGURED" ? (
                  <div style={{ padding: '10px 14px', background: 'rgba(245, 158, 11, 0.12)', border: '1px solid #F59E0B', borderRadius: '6px', color: '#FBBF24', fontSize: '0.76rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <Info size={15} color="#F59E0B" />
                    <span>
                      {(aiIntelligence.error_message || "AI Hazard Intelligence is currently updating parameters. Please consult ground field reports.")
                        .replace(/Amazon Bedrock AI service returned an error\.?/gi, "AI Hazard Intelligence is currently updating parameters. Please consult ground field reports.")
                        .replace(/Amazon Bedrock client unavailable:?/gi, "AI Hazard Analysis currently synthesizing parameters.")
                        .replace(/AWS Bedrock/gi, "AI Hazard Engine")
                        .replace(/DynamoDB/gi, "Cloud Storage")}
                    </span>
                  </div>
                ) : (
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '10px', fontSize: '0.76rem', color: 'var(--color-text)' }}>
                    <div style={{ background: 'var(--color-surface)', padding: '10px', borderRadius: '6px', border: '1px solid var(--color-border)' }}>
                      <strong style={{ color: '#A78BFA', fontSize: '0.78rem' }}>Summary:</strong>
                      <p style={{ margin: '4px 0 0 0', color: 'var(--color-text)', lineHeight: 1.4 }}>{aiIntelligence.summary || aiIntelligence.reasoning}</p>
                    </div>

                    <div style={{ background: 'var(--color-surface)', padding: '10px', borderRadius: '6px', border: '1px solid var(--color-border)' }}>
                      <strong style={{ color: '#F87171', fontSize: '0.78rem' }}>Potential Operational Impact / Transport:</strong>
                      <p style={{ margin: '4px 0 0 0', color: 'var(--color-text)', lineHeight: 1.4 }}>{aiIntelligence.potential_operational_impact || aiIntelligence.transportImpact || aiIntelligence.severityAssessment}</p>
                    </div>

                    {(aiIntelligence.verification_questions?.length > 0 || aiIntelligence.riskFactors?.length > 0) && (
                      <div style={{ background: 'var(--color-surface)', padding: '10px', borderRadius: '6px', border: '1px solid var(--color-border)' }}>
                        <strong style={{ color: '#FBBF24', fontSize: '0.78rem' }}>Risk Factors & Ground Verification:</strong>
                        <ul style={{ margin: '4px 0 0 16px', padding: 0, color: 'var(--color-text)', lineHeight: 1.35 }}>
                          {(aiIntelligence.verification_questions || aiIntelligence.riskFactors || []).map((q, idx) => (
                            <li key={idx}>{q}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {(aiIntelligence.suggested_response_actions?.length > 0 || aiIntelligence.recommendedActions?.length > 0) && (
                      <div style={{ background: 'var(--color-surface)', padding: '10px', borderRadius: '6px', border: '1px solid var(--color-border)' }}>
                        <strong style={{ color: '#34D399', fontSize: '0.78rem' }}>Suggested Response Actions:</strong>
                        <ul style={{ margin: '4px 0 0 16px', padding: 0, color: 'var(--color-text)', lineHeight: 1.35 }}>
                          {(aiIntelligence.suggested_response_actions || aiIntelligence.recommendedActions || []).map((act, idx) => (
                            <li key={idx}>{act}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Single Unified Map Control Dock (Top Right) */}
        {!dockOpen ? (
          <button
            onClick={() => setDockOpen(true)}
            className="glass-panel"
            style={{
              position: 'absolute',
              top: '12px',
              right: '12px',
              zIndex: 1000,
              padding: '8px 14px',
              borderRadius: '20px',
              border: '1px solid var(--color-border)',
              background: 'var(--color-surface)',
              color: 'var(--color-text)',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              cursor: 'pointer',
              boxShadow: '0 4px 16px rgba(0,0,0,0.25)',
              fontWeight: 700,
              fontSize: '0.78rem'
            }}
          >
            <Sliders size={15} color="#3B82F6" />
            <span>{t.gisLayerControls || "Map Layers & Legend"}</span>
          </button>
        ) : (
          <div className="glass-panel map-overlay-card" style={{ position: 'absolute', top: '12px', right: '12px', width: '240px', padding: '12px', zIndex: 1000 }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
              <span style={{ fontSize: '0.75rem', fontWeight: 800, textTransform: 'uppercase', color: 'var(--color-text)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Sliders size={14} color="#3B82F6" /> {t.gisLayerControls || "Map Layers"}
              </span>
              <button onClick={() => setDockOpen(false)} style={{ background: 'transparent', border: 'none', cursor: 'pointer', padding: '2px', color: 'var(--color-muted)' }}>
                <X size={16} />
              </button>
            </div>

            {/* Tab Switcher */}
            <div style={{ display: 'flex', gap: '3px', background: 'var(--color-surface)', padding: '3px', borderRadius: '7px', marginBottom: '8px', border: '1px solid var(--color-border)' }}>
              <button
                onClick={() => setDockTab('layers')}
                style={{ flex: 1, padding: '4px 6px', fontSize: '0.7rem', fontWeight: 800, border: 'none', borderRadius: '5px', cursor: 'pointer', background: dockTab === 'layers' ? '#2563EB' : 'transparent', color: dockTab === 'layers' ? '#FFF' : 'var(--color-muted)', transition: 'all 0.15s ease', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '4px' }}
              >
                <Layers size={12} /> {t.gisLayerControls || "Layers"}
              </button>
              <button
                onClick={() => setDockTab('legend')}
                style={{ flex: 1, padding: '4px 6px', fontSize: '0.7rem', fontWeight: 800, border: 'none', borderRadius: '5px', cursor: 'pointer', background: dockTab === 'legend' ? '#2563EB' : 'transparent', color: dockTab === 'legend' ? '#FFF' : 'var(--color-muted)', transition: 'all 0.15s ease', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '4px' }}
              >
                <HelpCircle size={12} /> {t.mapLegendTitle ? "Legend" : "Legend"}
              </button>
            </div>

            {dockTab === 'layers' ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                <div className="overlay-toggle">
                  <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <AlertTriangle size={14} color="#EF4444" /> {t.hazardPins}
                  </span>
                  <label className="switch">
                    <input type="checkbox" checked={showIncidents} onChange={(e) => setShowIncidents(e.target.checked)} />
                    <span className="slider"></span>
                  </label>
                </div>
                <div className="overlay-toggle">
                  <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <Truck size={14} color="#06B6D4" /> {t.convoyFleets}
                  </span>
                  <label className="switch">
                    <input type="checkbox" checked={showFleets} onChange={(e) => setShowFleets(e.target.checked)} />
                    <span className="slider"></span>
                  </label>
                </div>
                <div className="overlay-toggle">
                  <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <Navigation size={14} color="#10B981" /> {t.highways}
                  </span>
                  <label className="switch">
                    <input type="checkbox" checked={showCorridors} onChange={(e) => setShowCorridors(e.target.checked)} />
                    <span className="slider"></span>
                  </label>
                </div>
                <div className="overlay-toggle">
                  <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <CloudRain size={14} color="#3B82F6" /> {t.rainfallOverlay}
                  </span>
                  <label className="switch">
                    <input type="checkbox" checked={showWeatherOverlay} onChange={(e) => setShowWeatherOverlay(e.target.checked)} />
                    <span className="slider"></span>
                  </label>
                </div>
                <div className="overlay-toggle">
                  <span style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.72rem', fontWeight: 600 }}>
                    <CloudRain size={14} color="#A855F7" /> Historical Rainfall (1901–2017)
                  </span>
                  <label className="switch">
                    <input type="checkbox" checked={showHistoricalRainfall} onChange={(e) => setShowHistoricalRainfall(e.target.checked)} />
                    <span className="slider"></span>
                  </label>
                </div>
                <div className="overlay-toggle">
                  <span style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.72rem', fontWeight: 600 }}>
                    <AlertTriangle size={14} color="#C084FC" /> Historical Flood/Landslides
                  </span>
                  <label className="switch">
                    <input type="checkbox" checked={showHistoricalLandslidesFloods} onChange={(e) => setShowHistoricalLandslidesFloods(e.target.checked)} />
                    <span className="slider"></span>
                  </label>
                </div>
                <div className="overlay-toggle">
                  <span style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.72rem', fontWeight: 600 }}>
                    <ShieldAlert size={14} color="#A78BFA" /> Historical Road Risk
                  </span>
                  <label className="switch">
                    <input type="checkbox" checked={showHistoricalRoadRisk} onChange={(e) => setShowHistoricalRoadRisk(e.target.checked)} />
                    <span className="slider"></span>
                  </label>
                </div>
                <div className="overlay-toggle">
                  <span style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.72rem', fontWeight: 600 }}>
                    <Building2 size={14} color="#06B6D4" /> Emergency Depots
                  </span>
                  <label className="switch">
                    <input type="checkbox" checked={showHistoricalEmergencyResources} onChange={(e) => setShowHistoricalEmergencyResources(e.target.checked)} />
                    <span className="slider"></span>
                  </label>
                </div>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '5px', fontSize: '0.7rem', color: 'var(--color-text)', paddingTop: '2px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ width: '9px', height: '9px', borderRadius: '50%', background: '#06B6D4', display: 'inline-block' }}></span>
                  <span>{t.legendFleets || "🚚 Active Convoy"}</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ width: '9px', height: '9px', borderRadius: '50%', background: '#EF4444', display: 'inline-block' }}></span>
                  <span>{t.legendLandslide || "🚨 Landslide Hazard"}</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ width: '9px', height: '9px', borderRadius: '50%', background: '#3B82F6', display: 'inline-block' }}></span>
                  <span>{t.legendFlood || "💧 Flash Flood Alert"}</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ width: '9px', height: '9px', borderRadius: '50%', background: '#8B5CF6', display: 'inline-block' }}></span>
                  <span>{t.legendHub || "🏬 Essential Supply Hub"}</span>
                </div>
                <div style={{ height: '1px', background: '#E6DFD3', margin: '2px 0' }}></div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ width: '16px', height: '3px', background: '#10B981', borderRadius: '2px', display: 'inline-block' }}></span>
                  <span>{t.legendClearRoute || "Clear Highway"}</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ width: '16px', height: '3px', background: '#F59E0B', borderRadius: '2px', display: 'inline-block' }}></span>
                  <span>{t.legendCautionRoute || "Caution Highway"}</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ width: '16px', height: '3px', background: '#EF4444', borderRadius: '2px', display: 'inline-block' }}></span>
                  <span>{t.legendBlockedRoute || "Blocked Highway"}</span>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Right Telemetry & Fleet Sidebar */}
      {rightCollapsed ? (
        <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '12px 6px', height: '100%', gap: '16px' }}>
          <button
            onClick={() => setRightCollapsed(false)}
            title="Expand Convoy Telemetry Sidebar"
            style={{ background: '#2563EB', color: '#FFF', border: 'none', borderRadius: '8px', padding: '8px', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 2px 8px rgba(37,99,235,0.4)' }}
          >
            <ChevronLeft size={18} />
          </button>
          <div style={{ writingMode: 'vertical-rl', textTransform: 'uppercase', letterSpacing: '1px', fontSize: '0.72rem', fontWeight: 800, color: 'var(--color-muted)', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Truck size={14} color="#06B6D4" />
            <span>Active Convoys ({filteredFleets.length})</span>
          </div>
        </div>
      ) : (
        <div className="sidebar-panel">
          <div className="glass-panel" style={{ padding: '14px', height: '100%', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
              <h2 className="section-title" style={{ fontSize: '0.92rem', flexShrink: 0, margin: 0 }}>
                <Truck size={17} color="#06B6D4" />
                {t.activeConvoys || "Active Convoys"} ({filteredFleets.length})
              </h2>
              <button
                onClick={() => setRightCollapsed(true)}
                title="Collapse Sidebar"
                style={{ background: 'transparent', border: 'none', cursor: 'pointer', color: 'var(--color-muted)', padding: '2px', borderRadius: '4px' }}
              >
                <ChevronRight size={18} />
              </button>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', flex: 1, overflowY: 'auto', paddingRight: '2px' }}>
              {filteredFleets.length === 0 ? (
                <div className="empty-state-box">
                  <Inbox size={24} color="#64748B" />
                  <span style={{ fontWeight: 600, fontSize: '0.8rem' }}>No Convoys Active</span>
                </div>
              ) : (
                filteredFleets.map((f) => {
                  const statusText = f.status === 'blocked' || f.status === 'emergency' ? (t.pillBlocked || 'BLOCKED') : f.status === 'delayed' || f.status === 'rerouting' || f.status === 'caution' ? (t.pillCaution || 'CAUTION') : (t.pillClear || 'CLEAR');
                  const loc = localizedFleets[f.id]?.[lang] || {};
                  const category = loc.category || f.category;
                  const locationName = loc.location || f.currentLocationName;

                  return (
                    <div
                      key={f.id}
                      tabIndex={0}
                      role="button"
                      aria-label={`Select vehicle convoy ${f.id}`}
                      className={`item-card ${selectedItem?.data?.id === f.id ? 'selected' : ''}`}
                      onClick={() => setSelectedItem({ type: 'fleet', data: f })}
                      onKeyDown={(e) => e.key === 'Enter' && setSelectedItem({ type: 'fleet', data: f })}
                      style={{ padding: '8px 10px', display: 'flex', flexDirection: 'column', gap: '3px' }}
                    >
                      <div className="item-card-header">
                        <span className="item-card-title" style={{ fontWeight: 800, fontSize: '0.84rem', color: '#2563EB' }}>
                          {f.id}
                        </span>
                        <span className={`pill ${f.status === 'emergency' || f.status === 'blocked' ? 'blocked' : f.status === 'delayed' || f.status === 'rerouting' ? 'caution' : 'clear'}`}>
                          {statusText}
                        </span>
                      </div>

                      <p style={{ fontSize: '0.74rem', color: 'var(--color-text)', fontWeight: 700 }}>
                        {category}
                      </p>
                      <p style={{ fontSize: '0.7rem', color: 'var(--color-muted)' }}>
                        📍 {locationName}
                      </p>
                    </div>
                  );
                })
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
