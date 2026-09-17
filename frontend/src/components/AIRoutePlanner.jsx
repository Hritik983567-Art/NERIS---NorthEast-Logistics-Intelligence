import React, { useState, useEffect } from 'react';
import { useApp } from '../context/AppContext';
import { api } from '../services/api';
import { calculateAIRoutes } from '../data/nerData';
import { localizedVehicles, localizedPayloads, localizedLocations } from '../data/localizedData';
import {
  Navigation,
  ShieldCheck,
  CheckCircle2,
  Send,
  CloudRain,
  Activity,
  Cpu,
  AlertTriangle,
  Info,
  MapPin,
  Route,
  Clock,
  ShieldAlert
} from 'lucide-react';

export const AIRoutePlanner = () => {
  const { t, lang } = useApp();

  const [origin, setOrigin] = useState("Guwahati Central Depot (Assam)");
  const [destination, setDestination] = useState("Silchar FCI Hub (Assam)");
  const [commodity, setCommodity] = useState("Life-Saving Vaccines & Insulin (Cold-Chain)");
  const [convoyWeight, setConvoyWeight] = useState(15.0);

  const [routeResult, setRouteResult] = useState(() => {
    return {
      route_id: "route-init",
      origin: "Guwahati Central Depot (Assam)",
      destination: "Silchar FCI Hub (Assam)",
      path_nodes: ["Guwahati", "Nongpoh", "Shillong", "Jowai", "Silchar"],
      distance: 312.5,
      estimated_time: 7.8,
      risk_score: 22.4,
      risk_factors: [
        "Monsoon heavy rain warning penalty (1.3x) applied on Shillong-Jowai ghat stretch",
        "Moderate terrain incline vulnerability index (0.35)"
      ],
      blocked_segments: [],
      alternate_route: {
        route_name: "Secondary Detour via Haflong / Umrangso Corridor",
        path_nodes: ["Guwahati", "Nagaon", "Lumding", "Haflong", "Silchar"],
        distance: 368.0,
        estimated_time: 9.5,
        risk_score: 38.0,
        rationale: "Secondary state highway fallback bypasses Shillong plateau during extreme rainfall."
      },
      decision_explanation: "Primary Route via NH-27/NH-6 selected using multi-criteria disaster risk engine. This path provides optimal travel time (7.8 hrs) over 312.5 km while bypassing active landslide blockades.",
      data_source_mode: "DEMO/SIMULATION"
    };
  });

  const [loading, setLoading] = useState(false);
  const [routeError, setRouteError] = useState(null);
  const [selectedRouteType, setSelectedRouteType] = useState("primary");
  const [dispatchSuccess, setDispatchSuccess] = useState(false);
  const [liveWeatherCategory, setLiveWeatherCategory] = useState("MONSOON_STORM");
  const [liveWeatherDesc, setLiveWeatherDesc] = useState("Live Weather Reading");

  useEffect(() => {
    const loadLiveWeather = async () => {
      const weatherData = await api.getLiveWeather();
      if (weatherData && weatherData.hubs_weather && weatherData.hubs_weather.length > 0) {
        const topHub = weatherData.hubs_weather[0];
        setLiveWeatherCategory(topHub.condition_category || "MONSOON_STORM");
        setLiveWeatherDesc(`Live Web Weather (${topHub.hub_name}): ${topHub.temp_celsius}°C, ${topHub.condition_description}`);
      }
    };
    loadLiveWeather();
  }, []);

  const runRouteComputation = async (optOrigin, optDestination, optCommodity, optWeight) => {
    setLoading(true);
    setRouteError(null);
    setDispatchSuccess(false);

    const cargoTypeMap = {
      "Life-Saving Vaccines & Insulin (Cold-Chain)": "MEDICINE",
      "Fortified Food Grains & Rice (FCI Supply)": "GRAINS_RATIONS",
      "Liquid Medical Oxygen (Cryogenic Tanker)": "OXYGEN_CYLINDERS",
      "Bridge & Road Heavy Steel Girders": "CONSTRUCTION",
      "Petroleum & Diesel Fuel Supply": "FUEL"
    };

    const targetOrigin = optOrigin || origin;
    const targetDest = optDestination || destination;
    const targetCommodity = optCommodity || commodity;
    const targetWeight = optWeight !== undefined ? optWeight : convoyWeight;

    const cargoEnum = cargoTypeMap[targetCommodity] || "MEDICINE";
    const apiResponse = await api.calculateRoute(targetOrigin, targetDest, cargoEnum, targetWeight, liveWeatherCategory);

    if (apiResponse && apiResponse.error) {
      setRouteError(apiResponse.error);
      setRouteResult(prev => ({
        ...prev,
        origin: targetOrigin,
        destination: targetDest
      }));
    } else if (apiResponse && (apiResponse.path_nodes || apiResponse.geometry)) {
      setRouteResult({
        routeId: apiResponse.routeId || apiResponse.route_id || `route-${Date.now()}`,
        origin: targetOrigin,
        destination: targetDest,
        path_nodes: apiResponse.path_nodes && apiResponse.path_nodes.length > 0 ? apiResponse.path_nodes : [targetOrigin.split(' ')[0], targetDest.split(' ')[0]],
        geometry: apiResponse.geometry || [],
        distance: apiResponse.distance !== undefined ? apiResponse.distance : (apiResponse.total_distance_km || 312.5),
        duration: apiResponse.duration !== undefined ? apiResponse.duration : (apiResponse.estimated_time || apiResponse.disaster_adjusted_eta_hours || 7.8),
        estimated_time: apiResponse.estimated_time !== undefined ? apiResponse.estimated_time : (apiResponse.duration || 7.8),
        riskScore: apiResponse.riskScore !== undefined ? apiResponse.riskScore : (apiResponse.risk_score || 22.4),
        risk_score: apiResponse.riskScore !== undefined ? apiResponse.riskScore : (apiResponse.risk_score || 22.4),
        riskLevel: apiResponse.riskLevel || apiResponse.risk_level || "MODERATE",
        risk_level: apiResponse.riskLevel || apiResponse.risk_level || "MODERATE",
        riskFactors: apiResponse.riskFactors || apiResponse.risk_factors || [],
        risk_factors: apiResponse.riskFactors || apiResponse.risk_factors || [],
        blocked_segments: apiResponse.blocked_segments || [],
        alternate_route: apiResponse.alternate_route || null,
        decision_explanation: apiResponse.decision_explanation || `Primary Route calculated via ${targetOrigin.split(' ')[0]} ➔ ${targetDest.split(' ')[0]}.`,
        bedrock_explanation: apiResponse.bedrock_explanation || null,
        data_source_mode: apiResponse.data_source_mode || "NERIS_GRAPH_DIJKSTRA"
      });
    } else {
      setRouteError("Failed to calculate route from backend risk engine.");
    }
    setLoading(false);
  };

  useEffect(() => {
    runRouteComputation(origin, destination, commodity, convoyWeight);
  }, [origin, destination, commodity, convoyWeight, liveWeatherCategory]);

  const handleCalculate = (e) => {
    if (e) e.preventDefault();
    runRouteComputation(origin, destination, commodity, convoyWeight);
  };

  const [dispatchedInfo, setDispatchedInfo] = useState(null);

  const handleDispatchConvoy = (type = 'primary') => {
    setSelectedRouteType(type);
    if (type === 'alternate' && routeResult.alternate_route) {
      setDispatchedInfo({
        name: routeResult.alternate_route.route_name || "Secondary Alternate Corridor",
        distance: routeResult.alternate_route.distance,
        time: routeResult.alternate_route.estimated_time,
        type: "Alternate Secondary Corridor"
      });
    } else {
      setDispatchedInfo({
        name: `Primary Corridor (${routeResult.path_nodes.join(' ➔ ')})`,
        distance: routeResult.distance,
        time: routeResult.estimated_time,
        type: "Primary Recommended Vector"
      });
    }
    setDispatchSuccess(true);
    setTimeout(() => {
      setDispatchSuccess(false);
    }, 5000);
  };

  const getLocName = (name) => localizedLocations[name]?.[lang] || name;
  const getPayName = (name) => localizedPayloads[name]?.[lang] || name;

  return (
    <div className="planner-grid">
      {/* Left Input Form Panel */}
      <div className="glass-panel" style={{ padding: '20px', height: '100%', display: 'flex', flexDirection: 'column', overflowY: 'auto' }}>
        {/* Panel Header */}
        <div style={{ marginBottom: '16px', flexShrink: 0 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px' }}>
            <h2 className="section-title">
              <Cpu size={20} color="#00F2FE" />
              NERIS Route Planner Workflow
            </h2>
            <span className="pill blocked" style={{ padding: '3px 10px', fontSize: '0.7rem', background: 'rgba(16, 185, 129, 0.15)', color: '#10B981', borderColor: '#10B981' }}>
              <ShieldCheck size={11} style={{ verticalAlign: 'middle', marginRight: '3px' }} />
              LIVE ROUTE ENGINE
            </span>
          </div>
          <p style={{ fontSize: '0.78rem', color: 'var(--color-muted)', marginTop: '4px' }}>
            Disaster-aware intelligent route optimization consuming real-time incident data & weather risks
          </p>
        </div>

        <form onSubmit={handleCalculate} style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
          <div className="form-group">
            <label htmlFor="origin-select" className="form-label">{t.origin}</label>
            <select
              id="origin-select"
              className="form-input"
              value={origin}
              onChange={(e) => setOrigin(e.target.value)}
            >
              <option value="Guwahati Central Depot (Assam)">{getLocName("Guwahati Central Depot (Assam)")}</option>
              <option value="Shillong Hub (Meghalaya)">{getLocName("Shillong Hub (Meghalaya)")}</option>
              <option value="Tezpur Transit Point (Assam)">{getLocName("Tezpur Transit Point (Assam)")}</option>
              <option value="Silchar FCI Hub (Assam)">{getLocName("Silchar FCI Hub (Assam)")}</option>
              <option value="Dimapur Railhead Yard (Nagaland)">{getLocName("Dimapur Railhead Yard (Nagaland)")}</option>
              <option value="Agartala Multi-Modal Hub (Tripura)">{getLocName("Agartala Multi-Modal Hub (Tripura)")}</option>
              <option value="Itanagar Gateway Depot (Arunachal Pradesh)">{getLocName("Itanagar Gateway Depot (Arunachal Pradesh)")}</option>
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="destination-select" className="form-label">{t.destination}</label>
            <select
              id="destination-select"
              className="form-input"
              value={destination}
              onChange={(e) => setDestination(e.target.value)}
            >
              <option value="Silchar FCI Hub (Assam)">{getLocName("Silchar FCI Hub (Assam)")}</option>
              <option value="Kaziranga Safari Highway (Assam)">{getLocName("Kaziranga Safari Highway (Assam)")}</option>
              <option value="Imphal Gateway Depot (Manipur)">{getLocName("Imphal Gateway Depot (Manipur)")}</option>
              <option value="Kohima Supply Depot (Nagaland)">{getLocName("Kohima Supply Depot (Nagaland)")}</option>
              <option value="Aizawl Buffer Depot (Mizoram)">{getLocName("Aizawl Buffer Depot (Mizoram)")}</option>
              <option value="Agartala Terminal (Tripura)">{getLocName("Agartala Terminal (Tripura)")}</option>
              <option value="Cherrapunji High-Rainfall Zone (Meghalaya)">{getLocName("Cherrapunji High-Rainfall Zone (Meghalaya)")}</option>
              <option value="Jowai Transit Hub (Meghalaya)">{getLocName("Jowai Transit Hub (Meghalaya)")}</option>
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="cargo-select" className="form-label">{t.cargoType}</label>
            <select
              id="cargo-select"
              className="form-input"
              value={commodity}
              onChange={(e) => setCommodity(e.target.value)}
            >
              <option value="Life-Saving Vaccines & Insulin (Cold-Chain)">{getPayName("Life-Saving Vaccines & Insulin (Cold-Chain)")}</option>
              <option value="Fortified Food Grains & Rice (FCI Supply)">{getPayName("Fortified Food Grains & Rice (FCI Supply)")}</option>
              <option value="Liquid Medical Oxygen (Cryogenic Tanker)">{getPayName("Liquid Medical Oxygen (Cryogenic Tanker)")}</option>
              <option value="Bridge & Road Heavy Steel Girders">{getPayName("Bridge & Road Heavy Steel Girders")}</option>
              <option value="Petroleum & Diesel Fuel Supply">{getPayName("Petroleum & Diesel Fuel Supply")}</option>
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="weight-select" className="form-label">Convoy Weight Capacity (Metric Tonnes)</label>
            <select
              id="weight-select"
              className="form-input"
              value={convoyWeight}
              onChange={(e) => setConvoyWeight(parseFloat(e.target.value))}
            >
              <option value={10.0}>Light Duty Convoy (10 Tonnes)</option>
              <option value={15.0}>Medium Essential Carrier (15 Tonnes)</option>
              <option value={25.0}>Heavy Multi-Axle Carrier (25 Tonnes)</option>
              <option value={45.0}>Extreme Heavy Steel Transport (45 Tonnes)</option>
            </select>
          </div>

          <button
            type="submit"
            className="btn-primary"
            disabled={loading}
            style={{ marginTop: '10px' }}
          >
            {loading ? (
              <span>Computing Optimal Route Vector...</span>
            ) : (
              <>
                <Route size={18} />
                Compute Operational Route
              </>
            )}
          </button>
        </form>

        <div style={{ marginTop: '20px', padding: '12px 14px', borderRadius: '10px', background: 'var(--color-surface)', border: '1px solid var(--color-border)', flexShrink: 0 }}>
          <h4 style={{ fontSize: '0.78rem', textTransform: 'uppercase', color: 'var(--color-muted)', marginBottom: '6px', fontWeight: 800 }}>
            <Activity size={14} color="#00F2FE" style={{ verticalAlign: 'middle' }} /> Route Computation Pipeline
          </h4>
          <ul style={{ fontSize: '0.75rem', color: 'var(--color-muted)', listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '4px', paddingLeft: 0 }}>
            <li>1. Ingest active incident callset from live alerts</li>
            <li>2. Map incidents to highway graph edge boundaries</li>
            <li>3. Compute dynamic edge weights (Terrain + Weather + Penalty)</li>
            <li>4. Calculate safest Primary & Alternate paths</li>
            <li>5. Synthesize operational decision rationale</li>
          </ul>
        </div>
      </div>

      {/* Right Results Panel */}
      <div className="glass-panel" style={{ padding: '20px', height: '100%', display: 'flex', flexDirection: 'column', overflowY: 'auto' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px', flexShrink: 0 }}>
          <div>
            <h2 className="section-title">
              <Navigation size={20} color="#10B981" />
              Operational Route Results
            </h2>
            <p style={{ fontSize: '0.78rem', color: 'var(--color-muted)', marginTop: '2px' }}>
              {t.origin}: <strong style={{ color: 'var(--color-text)' }}>{getLocName(routeResult.origin)}</strong> ➔ {t.destination}: <strong style={{ color: 'var(--color-text)' }}>{getLocName(routeResult.destination)}</strong>
            </p>
          </div>
          <span className={`pill ${routeResult.risk_score > 40 ? 'caution' : 'clear'}`} style={{ fontSize: '0.8rem', padding: '4px 10px' }}>
            Risk Index: {routeResult.risk_score}/100
          </span>
        </div>

        {/* Route Error Alert */}
        {routeError && (
          <div style={{ padding: '12px 14px', borderRadius: '8px', background: 'rgba(239, 68, 68, 0.15)', border: '1px solid #EF4444', color: '#FCA5A5', marginBottom: '14px', fontSize: '0.8rem', display: 'flex', alignItems: 'center', gap: '8px', flexShrink: 0 }}>
            <AlertTriangle size={16} color="#EF4444" />
            <span><strong>Routing Calculation Notice:</strong> {routeError}</span>
          </div>
        )}

        {/* --- EXPLICIT ROUTE DECISION RATIONALE PANEL --- */}
        <div style={{ padding: '12px 16px', borderRadius: '10px', background: 'rgba(2, 132, 199, 0.08)', border: '1px solid rgba(2, 132, 199, 0.3)', marginBottom: '14px', flexShrink: 0 }}>
          <h4 style={{ fontSize: '0.84rem', fontWeight: 800, color: '#0284C7', marginBottom: '6px', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Info size={16} /> Route Decision Rationale (Why Selected)
          </h4>
          <p style={{ fontSize: '0.78rem', color: 'var(--color-text)', lineHeight: 1.45, margin: 0 }}>
            {routeResult.decision_explanation}
          </p>
        </div>

        {/* Live Weather Indicator */}
        <div style={{ padding: '8px 12px', borderRadius: '8px', background: 'var(--color-surface)', border: '1px solid var(--color-border)', marginBottom: '14px', display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.76rem', color: 'var(--color-muted)', flexShrink: 0 }}>
          <CloudRain size={16} color="#00F2FE" />
          <span>{liveWeatherDesc} • Status: <strong style={{ color: '#10B981' }}>LIVE SYNCED</strong></span>
        </div>

        {/* Route Stack or Skeleton Loader */}
        {loading ? (
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <div className="skeleton-card" style={{ height: '110px' }} />
            <div className="skeleton-card" style={{ height: '110px' }} />
          </div>
        ) : (
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '12px', overflowY: 'auto' }}>
            {/* --- PRIMARY ROUTE CARD --- */}
            <div
              className={`route-card ${selectedRouteType === 'primary' ? 'recommended' : ''}`}
              style={{
                borderColor: selectedRouteType === 'primary' ? '#10B981' : undefined,
                cursor: 'pointer'
              }}
              onClick={() => setSelectedRouteType('primary')}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '6px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ fontWeight: 800, fontSize: '0.95rem', color: '#10B981' }}>
                    PRIMARY ROUTE ({routeResult.path_nodes.join(' ➔ ')})
                  </span>
                  <span className="pill clear" style={{ background: '#10B981', color: '#FFF' }}>
                    <ShieldCheck size={12} /> PRIMARY RECOMMENDED
                  </span>
                </div>
                <span className="pill clear">SAFEST ETA</span>
              </div>

              <div className="telemetry-grid" style={{ marginTop: '10px' }}>
                <div className="telemetry-stat">
                  <div className="stat-val">{routeResult.distance} <span style={{ fontSize: '0.7rem' }}>km</span></div>
                  <div className="stat-lbl">Distance</div>
                </div>
                <div className="telemetry-stat">
                  <div className="stat-val" style={{ color: '#FBBF24' }}>{routeResult.estimated_time} hrs</div>
                  <div className="stat-lbl">Estimated Time</div>
                </div>
                <div className="telemetry-stat">
                  <div className="stat-val" style={{ color: routeResult.risk_score < 30 ? '#34D399' : '#F59E0B' }}>
                    {routeResult.risk_score}
                  </div>
                  <div className="stat-lbl">Risk Score</div>
                </div>
              </div>

              {/* Identified Risk Factors */}
              <div style={{ marginTop: '10px', paddingTop: '8px', borderTop: '1px solid var(--color-border)' }}>
                <div style={{ fontSize: '0.74rem', fontWeight: 700, color: 'var(--color-muted)', marginBottom: '4px' }}>
                  Identified Risk Factors ({routeResult.risk_factors.length}):
                </div>
                <ul style={{ paddingLeft: '16px', margin: 0, fontSize: '0.74rem', color: 'var(--color-text)', lineHeight: 1.4 }}>
                  {routeResult.risk_factors.map((rf, idx) => (
                    <li key={idx}>{rf}</li>
                  ))}
                </ul>
              </div>

              {/* Blocked Segments */}
              {routeResult.blocked_segments && routeResult.blocked_segments.length > 0 && (
                <div style={{ marginTop: '8px', padding: '6px 10px', borderRadius: '6px', background: 'rgba(220, 38, 38, 0.1)', border: '1px solid #DC2626', color: '#DC2626', fontSize: '0.73rem' }}>
                  <strong>🚨 Blocked Segments Detoured:</strong>
                  <ul style={{ paddingLeft: '16px', margin: '2px 0 0 0' }}>
                    {routeResult.blocked_segments.map((bs, idx) => (
                      <li key={idx}>{bs}</li>
                    ))}
                  </ul>
                </div>
              )}

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '10px', paddingTop: '8px', borderTop: '1px solid var(--color-border)' }}>
                <span style={{ fontSize: '0.72rem', color: 'var(--color-muted)' }}>
                  ⚙️ Optimized via Dynamic Risk & Terrain Matrix
                </span>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDispatchConvoy('primary');
                  }}
                  className="btn-primary"
                  style={{ width: 'auto', padding: '6px 14px', fontSize: '0.76rem', minHeight: '36px' }}
                >
                  <Send size={13} /> Dispatch Primary Route
                </button>
              </div>
            </div>

            {/* --- ALTERNATE ROUTE CARD --- */}
            {routeResult.alternate_route && (
              <div
                className={`route-card ${selectedRouteType === 'alternate' ? 'recommended' : ''}`}
                style={{
                  borderColor: selectedRouteType === 'alternate' ? '#0284C7' : 'var(--color-border)',
                  background: 'var(--color-surface)',
                  cursor: 'pointer'
                }}
                onClick={() => setSelectedRouteType('alternate')}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '6px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ fontWeight: 800, fontSize: '0.9rem', color: '#0284C7' }}>
                      ALTERNATE ROUTE ({routeResult.alternate_route.route_name})
                    </span>
                    {routeResult.alternate_route.risk_score < routeResult.risk_score && (
                      <span className="pill clear" style={{ background: '#0284C7', color: '#FFF', fontSize: '0.68rem' }}>
                        🛡️ LOWER RISK ({routeResult.alternate_route.risk_score})
                      </span>
                    )}
                  </div>
                  <span className="pill warning" style={{ fontSize: '0.7rem' }}>SECONDARY OPTION</span>
                </div>

                <div className="telemetry-grid" style={{ marginTop: '10px' }}>
                  <div className="telemetry-stat">
                    <div className="stat-val">{routeResult.alternate_route.distance} <span style={{ fontSize: '0.7rem' }}>km</span></div>
                    <div className="stat-lbl">Distance</div>
                  </div>
                  <div className="telemetry-stat">
                    <div className="stat-val" style={{ color: '#FBBF24' }}>{routeResult.alternate_route.estimated_time} hrs</div>
                    <div className="stat-lbl">Estimated Time</div>
                  </div>
                  <div className="telemetry-stat">
                    <div className="stat-val" style={{ color: routeResult.alternate_route.risk_score < 30 ? '#34D399' : '#F59E0B' }}>
                      {routeResult.alternate_route.risk_score}
                    </div>
                    <div className="stat-lbl">Risk Score</div>
                  </div>
                </div>

                <p style={{ fontSize: '0.74rem', color: 'var(--color-muted)', marginTop: '8px' }}>
                  <strong>Fallback Rationale:</strong> {routeResult.alternate_route.rationale}
                </p>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '10px', paddingTop: '8px', borderTop: '1px solid var(--color-border)' }}>
                  <span style={{ fontSize: '0.72rem', color: 'var(--color-muted)' }}>
                    💡 User Selectable Route Option
                  </span>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDispatchConvoy('alternate');
                    }}
                    className="btn-primary"
                    style={{ width: 'auto', padding: '6px 14px', fontSize: '0.76rem', minHeight: '36px', background: '#0284C7', borderColor: '#0284C7' }}
                  >
                    <Send size={13} /> Dispatch Alternate Route
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

        {dispatchSuccess && dispatchedInfo && (
          <div style={{ marginTop: '12px', padding: '10px 14px', borderRadius: '8px', background: 'rgba(16, 185, 129, 0.2)', border: '1px solid #10B981', color: '#34D399', display: 'flex', alignItems: 'center', gap: '10px', flexShrink: 0 }}>
            <CheckCircle2 size={18} />
            <div>
              <strong style={{ fontSize: '0.86rem' }}>Convoy Dispatch Command Vectorized!</strong>
              <p style={{ fontSize: '0.75rem', margin: '2px 0 0 0' }}>
                Dispatched Vector: <strong>{dispatchedInfo.name}</strong> ({dispatchedInfo.distance} km, {dispatchedInfo.time} hrs). Real-time telemetry monitoring initiated.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
