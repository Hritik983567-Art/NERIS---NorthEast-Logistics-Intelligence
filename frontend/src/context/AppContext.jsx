import React, { createContext, useContext, useState, useEffect } from 'react';
import { translations } from '../data/translations';
import { incidentMarkers, activeFleets, nerStates } from '../data/nerData';
import { api } from '../services/api';
import { offlineQueueDB } from '../services/offlineQueueDB';


export const AppContext = createContext();

export const AppProvider = ({ children }) => {
  const [lang, setLang] = useState('en');
  const [stateFilter, setStateFilter] = useState('all');
  const [activeTab, setActiveTab] = useState('map');
  const [isOnline, setIsOnline] = useState(true);
  const [backendConnected, setBackendConnected] = useState(false);
  const [theme, setTheme] = useState(() => localStorage.getItem('ner_theme') || 'light');

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('ner_theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme((prev) => (prev === 'light' ? 'dark' : 'light'));
  };

  // Persistent NERIS Command Alerts State (AWS DynamoDB)
  const [alerts, setAlerts] = useState([
    {
      id: "ALT-1001",
      alertId: "ALT-1001",
      incident_id: "INC-8921",
      incidentId: "INC-8921",
      severity: "CRITICAL",
      title: "CRITICAL INCIDENT ALERT: Mudslide at Dima Hasao NH-27 Corridor",
      message: "Severe mudslide reported by field officer. Massive blockage endangering convoys along NH-27.",
      created_at: new Date().toISOString(),
      createdAt: new Date().toISOString(),
      status: "ACTIVE",
      delivery_mode: "In-App Operational Alert"
    },
    {
      id: "ALT-1002",
      alertId: "ALT-1002",
      incident_id: "INC-7703",
      incidentId: "INC-7703",
      severity: "HIGH",
      title: "HIGH SEVERITY ALERT: Highway Inundation at Silchar Bypass",
      message: "Barak River overflow causing flash inundation across 2.5km section.",
      created_at: new Date(Date.now() - 3600000).toISOString(),
      createdAt: new Date(Date.now() - 3600000).toISOString(),
      status: "ACKNOWLEDGED",
      acknowledged_by: "Cmdr. R. Gogoi",
      acknowledged_at: new Date(Date.now() - 1800000).toISOString(),
      delivery_mode: "In-App Operational Alert"
    }
  ]);

  // Check backend FastAPI server status & initial data sync
  useEffect(() => {
    api.checkHealth().then((health) => {
      if (health && (health.status === 'HEALTHY' || health.status === 'online')) {
        setBackendConnected(true);
        // Sync initial telemetry data from FastAPI backend without stripping frontend model fields
        api.getFleets().then((backendFleets) => {
          if (backendFleets && Array.isArray(backendFleets) && backendFleets.length > 0) {
            setFleets((prevFleets) =>
              prevFleets.map((fleet) => {
                const match = backendFleets.find((b) => (b.vehicle_id || b.id) === fleet.id);
                if (match) {
                  return {
                    ...fleet,
                    lat: match.current_lat || match.lat || fleet.lat,
                    lng: match.current_lng || match.lng || fleet.lng,
                    speedKm: match.speed_kmh !== undefined ? match.speed_kmh : fleet.speedKm,
                    driver: match.driver_name || fleet.driver,
                    phone: match.driver_phone || fleet.phone,
                    payload: match.cargo_type || fleet.payload,
                    destination: match.destination_district || fleet.destination,
                  };
                }
                return fleet;
              })
            );
          }
        });

        // Sync initial incidents from FastAPI backend
        api.getIncidents().then((backendIncidents) => {
          if (backendIncidents && Array.isArray(backendIncidents) && backendIncidents.length > 0) {
            setIncidents((prevIncidents) => {
              const mapped = backendIncidents.map((inc) => ({
                id: inc.id || inc.local_incident_id || `INC-${Date.now()}`,
                title: `${inc.hazard_type || 'HAZARD'} Alert (${inc.district || 'Corridor'})`,
                type: String(inc.hazard_type || 'LANDSLIDE').toLowerCase().includes('flood') ? 'flood' : 'landslide',
                severity: inc.severity || 'CRITICAL',
                state: String(inc.district || 'assam').toLowerCase(),
                locationName: `${inc.highway_id || 'NH Highway'} - ${inc.district || 'NER'}`,
                lat: inc.lat,
                lng: inc.lng,
                timestamp: inc.offline_timestamp || 'Active',
                reporter: inc.reported_by_badge_id || 'Field Officer',
                description: `Blockage estimated at ${inc.estimated_blockage_pct || 80}%. Clearance time: ${inc.estimated_clearance_hours || 4} hours.`,
                photoUrl: inc.evidence_url || 'https://images.unsplash.com/photo-1544620347-c4fd4a3d5957?auto=format&fit=crop&w=600&q=80',
                alternateAvailable: true,
                affectedConvoys: []
              }));

              const existingIds = new Set(prevIncidents.map(i => i.id));
              const freshIncidents = mapped.filter(i => !existingIds.has(i.id));
              return [...freshIncidents, ...prevIncidents];
            });
          }
        });

        // Sync persistent backend alerts
        api.getAlerts().then((backendAlerts) => {
          if (backendAlerts && Array.isArray(backendAlerts) && backendAlerts.length > 0) {
            setAlerts(backendAlerts);
          }
        });

        // Sync initial disasters & live RSS news into broadcast alerts stack
        api.getExternalDisasters().then((disasterData) => {
          if (disasterData && disasterData.records && disasterData.records.length > 0) {
            const liveAlerts = disasterData.records.map((rec, idx) => ({
              id: rec.id || `live-disaster-${idx}`,
              title: rec.title,
              type: rec.severity === 'CRITICAL' ? 'sos' : 'warning',
              timestamp: rec.published_at || 'LIVE',
              source: rec.source || 'IMD / NDMA Live Feed'
            }));
            setBroadcastAlerts((prev) => {
              const existingIds = new Set(prev.map(a => a.id));
              const newItems = liveAlerts.filter(a => !existingIds.has(a.id));
              return [...newItems, ...prev];
            });
          }
        });

        // Sync initial live news feed into broadcast alerts
        api.getNewsFeed({ isDemo: false }).then((newsRes) => {
          if (newsRes && newsRes.articles && newsRes.articles.length > 0) {
            const liveNewsAlerts = newsRes.articles.slice(0, 5).map((art, idx) => ({
              id: art.id || `live-news-${idx}`,
              title: art.title,
              type: art.severity === 'CRITICAL' ? 'warning' : 'disruption',
              timestamp: art.published_at || 'LIVE',
              source: art.source || 'Regional Live RSS'
            }));
            setBroadcastAlerts((prev) => {
              const existingIds = new Set(prev.map(a => a.id));
              const newItems = liveNewsAlerts.filter(a => !existingIds.has(a.id));
              return [...newItems, ...prev];
            });
          }
        });
      }
    });
  }, []);

  // Poll persistent alerts from backend every 4 seconds
  useEffect(() => {
    const fetchAlerts = async () => {
      const backendAlerts = await api.getAlerts();
      if (backendAlerts && Array.isArray(backendAlerts) && backendAlerts.length > 0) {
        setAlerts(backendAlerts);
      }
    };
    const alertInterval = setInterval(fetchAlerts, 4000);
    return () => clearInterval(alertInterval);
  }, []);

  // Dynamic datasets state
  const [incidents, setIncidents] = useState(() => {
    const saved = localStorage.getItem('ner_incidents');
    return saved ? JSON.parse(saved) : incidentMarkers;
  });

  const [offlineQueue, setOfflineQueue] = useState(() => {
    const saved = localStorage.getItem('ner_offline_queue');
    return saved ? JSON.parse(saved) : [];
  });

  const [fleets, setFleets] = useState(activeFleets);

  const [broadcastAlerts, setBroadcastAlerts] = useState([
    {
      id: "b-101",
      title: "RED ALERT: Heavy Rainfall in Dima Hasao & West Siang",
      type: "warning",
      timestamp: "10 mins ago",
      source: "IMD Guwahati Regional Met Center"
    },
    {
      id: "b-102",
      title: "NH-2 Mao Gate Landslide - BRO Machinery Clearance Underway",
      type: "disruption",
      timestamp: "25 mins ago",
      source: "Border Roads Organisation (BRO)"
    }
  ]);

  // Function to explicitly ping live telemetry to backend & evaluate spatial hazard proximity
  const sendTelemetryPing = async (fleetId) => {
    const targetFleet = fleets.find(f => f.id === fleetId) || fleets[0];
    if (!targetFleet) return null;

    const payload = {
      vehicleId: targetFleet.id,
      vehicle_id: targetFleet.id,
      registration: targetFleet.id,
      vehicleType: targetFleet.vehicle_type || "HEAVY_TRUCK",
      status: targetFleet.status || "CLEAR",
      latitude: targetFleet.lat,
      longitude: targetFleet.lng,
      current_lat: targetFleet.lat,
      current_lng: targetFleet.lng,
      speed: targetFleet.speedKm || 38.5,
      speed_kmh: targetFleet.speedKm || 38.5,
      heading: targetFleet.heading || 120.0,
      heading_degrees: targetFleet.heading || 120.0,
      cargo: targetFleet.payload || "Life-Saving Vaccines & Medical Supplies",
      cargo_type: targetFleet.cargoType || "MEDICINE",
      driver_name: targetFleet.driverName || "Ramesh Kalita",
      driver_phone: targetFleet.driverPhone || "+91 98640 11234",
      destination_district: targetFleet.destination || "Silchar / Barak Valley Depot",
      updatedAt: new Date().toISOString(),
      timestamp: new Date().toISOString()
    };

    const res = await api.pingTelemetry(payload);
    if (res && res.hazard_in_proximity) {
      setBroadcastAlerts((prev) => [
        {
          id: res.alert_created?.id || `ping-alert-${Date.now()}`,
          title: res.alert_created?.title || `⚠️ REAL-TIME GPS HAZARD DETECTED: Convoy ${targetFleet.id}`,
          type: "warning",
          timestamp: "JUST NOW",
          source: res.warning_message || "Backend Geodesic Proximity Engine"
        },
        ...prev
      ]);
      setFleets((prev) => prev.map(f => f.id === targetFleet.id ? { ...f, status: 'ROUTE AT RISK' } : f));
    }
    return res;
  };

  // Real-time backend telemetry simulation polling (Zero Math.random() in React)
  useEffect(() => {
    const fetchSimulatedTelemetry = async () => {
      const simData = await api.getSimulatedTelemetry();
      if (simData && Array.isArray(simData) && simData.length > 0) {
        setFleets((prevFleets) => {
          return prevFleets.map((fleet) => {
            const match = simData.find((s) => s.vehicle_id === fleet.id);
            if (match) {
              return {
                ...fleet,
                lat: match.latitude,
                lng: match.longitude,
                speedKm: match.speed,
                heading: match.heading,
                fuelPercent: match.fuel,
                cargoTempC: match.cargo_temp_c !== undefined ? match.cargo_temp_c : fleet.cargoTempC,
                status: match.status,
                current_route: match.current_route,
                last_updated: match.last_updated,
                route_at_risk: match.route_at_risk,
                at_risk_hazard_info: match.at_risk_hazard_info,
                driver: match.driver_name || fleet.driver,
                phone: match.driver_phone || fleet.phone,
                category: match.category || fleet.category,
                payload: match.payload || fleet.payload,
                origin: match.origin || fleet.origin,
                destination: match.destination || fleet.destination
              };
            }
            return fleet;
          });
        });
      }
    };

    fetchSimulatedTelemetry();
    const interval = setInterval(fetchSimulatedTelemetry, 2500);
    return () => clearInterval(interval);
  }, []);

  // Real-time backend incident polling (AWS DynamoDB Sync)
  useEffect(() => {
    const fetchLiveIncidents = async () => {
      const liveData = await api.getIncidents();
      if (liveData && Array.isArray(liveData) && liveData.length > 0) {
        setIncidents((prevIncidents) => {
          const merged = [...prevIncidents];
          liveData.forEach((liveItem) => {
            const index = merged.findIndex((i) => i.id === liveItem.id);
            const normalizedItem = {
              ...liveItem,
              is_live: true,
              lat: liveItem.lat || liveItem.latitude,
              lng: liveItem.lng || liveItem.longitude,
              locationName: liveItem.location_name || liveItem.locationName || "NER Corridor"
            };
            if (index >= 0) {
              merged[index] = { ...merged[index], ...normalizedItem };
            } else {
              merged.unshift(normalizedItem);
            }
          });
          return merged;
        });
      }
    };

    fetchLiveIncidents();
    const interval = setInterval(fetchLiveIncidents, 4000);
    return () => clearInterval(interval);
  }, []);

  const t = translations[lang] || translations.en;

  // Initialize offline queue from IndexedDB on mount & set up online/offline event listeners
  useEffect(() => {
    offlineQueueDB.getAllQueuedIncidents().then((items) => {
      if (items && Array.isArray(items)) {
        setOfflineQueue(items);
      }
    });

    const handleOnline = () => {
      setIsOnline(true);
      setTimeout(() => {
        syncOfflineQueue();
      }, 1000);
    };

    const handleOffline = () => {
      setIsOnline(false);
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  const toggleOnlineStatus = () => {
    const nextStatus = !isOnline;
    setIsOnline(nextStatus);

    if (nextStatus) {
      setTimeout(() => {
        syncOfflineQueue();
      }, 1000);
    }
  };

  const addIncidentReport = async (report) => {
    const clientIncId = report.clientIncidentId || report.id || `INC-CLI-${Date.now()}-${Math.floor(Math.random() * 1000)}`;

    let finalEvidenceUrl = report.photoUrl || "https://images.unsplash.com/photo-1544620347-c4fd4a3d5957";
    let evidenceStatus = report.photoFile ? "PENDING" : "NONE";
    let s3Confirmed = false;
    let uploadedAt = null;

    if (isOnline && report.photoFile) {
      const formData = new FormData();
      formData.append('file', report.photoFile);
      formData.append('incident_id', clientIncId);

      const s3Res = await api.uploadEvidence(formData);
      if (s3Res && (s3Res.s3_confirmed || s3Res.status === 'UPLOADED')) {
        finalEvidenceUrl = s3Res.evidence_url;
        evidenceStatus = "UPLOADED";
        s3Confirmed = true;
        uploadedAt = s3Res.uploaded_at;
      }
    }

    const newIncidentPayload = {
      id: clientIncId,
      clientIncidentId: clientIncId,
      operation_id: clientIncId,
      title: report.title,
      type: report.type,
      severity: report.severity,
      state: report.state,
      district: report.state,
      locationName: report.locationName,
      location_name: report.locationName,
      lat: parseFloat(report.lat),
      lng: parseFloat(report.lng),
      latitude: parseFloat(report.lat),
      longitude: parseFloat(report.lng),
      timestamp: new Date().toISOString(),
      reporter: report.reporter || "Field Officer (Mobile Upload)",
      description: report.description,
      photoUrl: finalEvidenceUrl,
      evidence_url: finalEvidenceUrl,
      evidence_status: evidenceStatus,
      uploaded_at: uploadedAt,
      alternateAvailable: true,
      affectedConvoys: []
    };

    if (isOnline) {
      // Direct live submission to AWS DynamoDB
      const ddbRes = await api.createIncident(newIncidentPayload, clientIncId);
      const isDdbConfirmed = Boolean(ddbRes && (ddbRes.dynamodb_confirmed || ddbRes.status === 'CREATED' || ddbRes.status === 'DUPLICATE_REPLAY' || ddbRes.duplicate_prevented));

      if (!isDdbConfirmed && ddbRes && ddbRes.status === 'FAILED') {
        // Fallback to IndexedDB queue if network request fails unexpectedly
        const queuedItem = await offlineQueueDB.enqueueIncident(newIncidentPayload);
        const refreshedQueue = await offlineQueueDB.getAllQueuedIncidents();
        setOfflineQueue(refreshedQueue);

        return {
          status: 'queued',
          localQueueId: queuedItem.localQueueId,
          clientIncidentId: clientIncId,
          dynamodb_confirmed: false,
          s3_confirmed: false,
          error: ddbRes.error || 'Server error, enqueued in IndexedDB',
          data: newIncidentPayload
        };
      }

      // Populate frontend UI state directly from backend-returned persisted record
      const returnedIncident = (ddbRes && ddbRes.incident) ? ddbRes.incident : newIncidentPayload;
      const finalIncidentRecord = {
        ...returnedIncident,
        is_live: true,
        status: isDdbConfirmed ? 'SYNCED' : 'SUBMITTED',
        dynamodb_confirmed: isDdbConfirmed,
        photoUrl: returnedIncident.photoUrl || finalEvidenceUrl,
        evidence_url: returnedIncident.evidence_url || finalEvidenceUrl
      };

      setIncidents((prev) => {
        const targetId = finalIncidentRecord.id || clientIncId;
        const exists = prev.some(i => i.id === targetId || i.clientIncidentId === clientIncId);
        if (exists) return prev;
        return [finalIncidentRecord, ...prev];
      });

      // Also evaluate risk & trigger persistent alert
      api.evaluateIncidentRisk({
        id: clientIncId,
        title: newIncidentPayload.title,
        type: newIncidentPayload.type,
        severity: newIncidentPayload.severity,
        district: newIncidentPayload.state,
        description: newIncidentPayload.description
      }).then((result) => {
        if (result && result.alert) {
          setAlerts((prev) => {
            const exists = prev.some(a => a.id === result.alert.id);
            if (!exists) return [result.alert, ...prev];
            return prev;
          });
        }
      });

      return {
        status: 'synced',
        clientIncidentId: clientIncId,
        dynamodb_confirmed: isDdbConfirmed,
        s3_confirmed: s3Confirmed,
        data: newIncidentPayload
      };
    } else {
      // Genuine Offline Mode: Enqueue into IndexedDB persistent store
      const queuedItem = await offlineQueueDB.enqueueIncident(newIncidentPayload);
      const refreshedQueue = await offlineQueueDB.getAllQueuedIncidents();
      setOfflineQueue(refreshedQueue);

      return {
        status: 'queued',
        localQueueId: queuedItem.localQueueId,
        clientIncidentId: clientIncId,
        dynamodb_confirmed: false,
        s3_confirmed: false,
        data: newIncidentPayload
      };
    }
  };

  const syncOfflineQueue = async (isManual = false) => {
    const queuedItems = await offlineQueueDB.getAllQueuedIncidents();
    const pendingItems = queuedItems.filter(item => item.status === 'PENDING SYNC' || item.status === 'FAILED');

    if (pendingItems.length === 0) {
      const refreshedAll = await offlineQueueDB.getAllQueuedIncidents();
      setOfflineQueue(refreshedAll);
      return;
    }

    for (const item of pendingItems) {
      const attemptCount = (item.attemptCount || 0) + 1;
      const lastAttemptAt = new Date().toISOString();

      // Exponential Backoff Delay calculation: only for background auto-syncs, skip on manual button click
      if (!isManual && attemptCount > 1) {
        const backoffMs = Math.min(1000 * Math.pow(2, attemptCount - 1), 8000);
        await new Promise(res => setTimeout(res, backoffMs));
      }

      // 1. Mark as SYNCING in IndexedDB & state immediately for responsive feedback
      await offlineQueueDB.updateQueuedIncident(item.localQueueId, {
        status: 'SYNCING',
        attemptCount,
        lastAttemptAt,
        error: null
      });
      setOfflineQueue(await offlineQueueDB.getAllQueuedIncidents());

      try {
        // Sanitize payload before sending to backend to ensure non-empty title, description, coordinates, type, severity
        const p = item.payload || {};
        const sanitizedPayload = {
          ...p,
          title: (p.title || p.locationName || "Field Incident Report").trim(),
          description: (p.description || p.title || `Field incident reported at ${p.locationName || p.location_name || "NER Corridor"}`).trim(),
          type: (p.type || p.incidentType || "ROAD_BLOCKAGE").toUpperCase(),
          incidentType: (p.type || p.incidentType || "ROAD_BLOCKAGE").toUpperCase(),
          severity: (p.severity || "CRITICAL").toUpperCase(),
          state: p.state || "assam",
          district: p.district || p.state || "assam",
          latitude: parseFloat(p.latitude ?? p.lat ?? 26.1445),
          longitude: parseFloat(p.longitude ?? p.lng ?? 91.7362),
          lat: parseFloat(p.lat ?? p.latitude ?? 26.1445),
          lng: parseFloat(p.lng ?? p.longitude ?? 91.7362)
        };

        const ddbRes = await api.createIncident(sanitizedPayload);
        
        // Handle 401 Unauthorized Token Expiration cleanly without losing queued items
        if (ddbRes && (ddbRes.status === 401 || ddbRes.error === '401 Unauthorized' || ddbRes.error?.includes('Unauthorized'))) {
          await offlineQueueDB.updateQueuedIncident(item.localQueueId, {
            status: 'PENDING SYNC',
            attemptCount,
            lastAttemptAt,
            error: 'Authentication expired (HTTP 401). Please re-authenticate.'
          });
          console.warn("Offline sync halted: Authentication expired. Re-authentication required.");
          break; // Stop loop until user re-authenticates
        }

        const isSuccess = Boolean(ddbRes && (ddbRes.dynamodb_confirmed || ddbRes.status === 'CREATED' || ddbRes.status === 'DUPLICATE_REPLAY' || ddbRes.duplicate_prevented));

        if (isSuccess) {
          // 2. Mark as SYNCED in IndexedDB
          await offlineQueueDB.updateQueuedIncident(item.localQueueId, {
            status: 'SYNCED',
            attemptCount,
            lastAttemptAt,
            error: null
          });

          // Add to live incidents list
          const syncedInc = item.payload;
          syncedInc.status = 'SYNCED';
          syncedInc.dynamodb_confirmed = true;
          setIncidents((prev) => {
            const exists = prev.some(i => i.id === syncedInc.id || i.clientIncidentId === syncedInc.clientIncidentId);
            if (exists) return prev;
            return [syncedInc, ...prev];
          });
        } else {
          // Mark as FAILED in IndexedDB
          await offlineQueueDB.updateQueuedIncident(item.localQueueId, {
            status: 'FAILED',
            attemptCount,
            lastAttemptAt,
            error: ddbRes?.error || ddbRes?.detail || 'Failed to persist in DynamoDB'
          });
        }
      } catch (err) {
        if (err?.message?.includes('401') || err?.message?.includes('Unauthorized')) {
          await offlineQueueDB.updateQueuedIncident(item.localQueueId, {
            status: 'PENDING SYNC',
            attemptCount,
            lastAttemptAt,
            error: 'Authentication expired (HTTP 401). Please re-authenticate.'
          });
          break;
        }

        await offlineQueueDB.updateQueuedIncident(item.localQueueId, {
          status: 'FAILED',
          attemptCount,
          lastAttemptAt,
          error: err.message || 'Network error during sync'
        });
      }
    }

    const finalQueue = await offlineQueueDB.getAllQueuedIncidents();
    setOfflineQueue(finalQueue);
  };

  const removeOfflineQueueItem = async (localQueueId) => {
    await offlineQueueDB.removeQueuedIncident(localQueueId);
    const updated = await offlineQueueDB.getAllQueuedIncidents();
    setOfflineQueue(updated);
  };


  const triggerSOSAlert = async (fleetId, message) => {
    const targetFleet = fleets.find(f => f.id === fleetId);
    const fleetName = targetFleet ? `${targetFleet.id} (${targetFleet.category})` : fleetId;
    
    let serverAlert = null;
    try {
      const serverRes = await api.dispatchSOS({
        vehicle_id: fleetId,
        reason: message || 'Urgent Escort Requested',
        location: targetFleet?.currentLocationName || 'NER Emergency Corridor'
      });
      if (serverRes && serverRes.alert) {
        serverAlert = serverRes.alert;
      }
    } catch (err) {
      console.warn("Backend API SOS dispatch failed, falling back to local optimistic item:", err.message);
    }

    const alertToPush = serverAlert || {
      id: `sos-${Date.now()}`,
      alertId: `sos-${Date.now()}`,
      title: `🚨 EMERGENCY SOS DISPATCHED: Convoy ${fleetName}`,
      type: "sos",
      timestamp: "JUST NOW",
      created_at: new Date().toISOString(),
      message: `Disaster Cell Vectoring | ${message || 'Urgent Escort Requested'}`,
      description: `Disaster Cell Vectoring | ${message || 'Urgent Escort Requested'}`,
      status: "ACTIVE",
      district: "ASSAM",
      source: "NERIS Emergency Vectoring Engine"
    };

    setBroadcastAlerts((prev) => [alertToPush, ...prev]);
    setAlerts((prev) => [alertToPush, ...prev]);

    if (targetFleet) {
      setFleets(prev => prev.map(f => f.id === fleetId ? { ...f, status: 'emergency' } : f));
    }
    return serverAlert;
  };

  const [user, setUser] = useState(() => {
    const savedUser = localStorage.getItem('ner_user');
    if (savedUser) {
      try {
        const parsed = JSON.parse(savedUser);
        if (parsed) return parsed;
      } catch (e) {}
    }
    return {
      id: "NER-CMD-8041",
      name: "Cmdr. R. Gogoi",
      role: "Disaster Logistics Commander",
      hub: "Guwahati Central Depot (Assam)",
      isPublic: false,
      loginTime: "08:00 AM"
    };
  });

  const isAuthenticated = !!user;

  const isCommander = Boolean(
    user &&
    !user.isPublic &&
    (String(user.role || '').toLowerCase().includes('commander') ||
     String(user.role || '').toLowerCase().includes('cmd') ||
     String(user.id || '').startsWith('NER-CMD'))
  );

  const acknowledgeCommandAlert = async (alertId) => {
    const actorName = user?.name || "Cmdr. R. Gogoi";
    const res = await api.acknowledgeAlert(alertId, actorName);
    const updatedObj = res?.alert || (res?.id ? res : null);
    if (updatedObj) {
      setAlerts((prev) => prev.map((a) => (a.id === alertId ? updatedObj : a)));
    } else {
      setAlerts((prev) =>
        prev.map((a) =>
          a.id === alertId
            ? {
                ...a,
                status: 'ACKNOWLEDGED',
                acknowledged_by: actorName,
                acknowledged_at: new Date().toISOString()
              }
            : a
        )
      );
    }
  };

  const resolveCommandAlert = async (alertId) => {
    const actorName = user?.name || "Cmdr. R. Gogoi";
    const res = await api.resolveAlert(alertId, actorName);
    const updatedObj = res?.alert || (res?.id ? res : null);
    if (updatedObj) {
      setAlerts((prev) => prev.map((a) => (a.id === alertId ? updatedObj : a)));
    } else {
      setAlerts((prev) =>
        prev.map((a) =>
          a.id === alertId
            ? {
                ...a,
                status: 'RESOLVED',
                resolved_by: actorName,
                resolved_at: new Date().toISOString()
              }
            : a
        )
      );
    }
  };

  const login = async (officerId, password, role, hub) => {
    const cognitoRes = await api.loginCognito(officerId, password, role);

    const userRole = cognitoRes?.user?.role || role || "COMMANDER";
    const newUser = {
      id: officerId || "NER-CMD-8041",
      name: officerId ? `Officer ${officerId.toUpperCase()}` : "Cmdr. R. Gogoi",
      role: userRole,
      hub: hub || "Guwahati Central Depot",
      isPublic: false,
      authProvider: cognitoRes?.user?.auth_provider || "Development Fallback Mode (Demo)",
      cognitoConfirmed: cognitoRes?.user?.cognito_confirmed || false,
      loginTime: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };
    setUser(newUser);
    localStorage.setItem('ner_user', JSON.stringify(newUser));
    return cognitoRes;
  };

  const loginAsPublic = (name, phone, userType, destinationState) => {
    const publicUser = {
      id: `CITIZEN-${Date.now().toString().slice(-4)}`,
      name: name || (userType === 'Tourist' ? "Tourist Traveler" : "Local Citizen"),
      phone: phone || "+91 Verified",
      role: userType || "Tourist / Traveler",
      hub: destinationState ? `Destination: ${destinationState}` : "NER Public Travel Portal",
      isPublic: true,
      authProvider: "Public Travel Security Pass",
      loginTime: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };
    setUser(publicUser);
    localStorage.setItem('ner_user', JSON.stringify(publicUser));
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem('ner_user');
    localStorage.removeItem('cognito_token');
    localStorage.removeItem('cognito_user');
  };

  return (
    <AppContext.Provider
      value={{
        lang,
        setLang,
        t,
        stateFilter,
        setStateFilter,
        activeTab,
        setActiveTab,
        isOnline,
        toggleOnlineStatus,
        incidents,
        offlineQueue,
        addIncidentReport,
        syncOfflineQueue,
        removeOfflineQueueItem,
        fleets,
        sendTelemetryPing,
        alerts,
        isCommander,
        acknowledgeCommandAlert,
        resolveCommandAlert,
        broadcastAlerts,
        triggerSOSAlert,
        nerStates,
        user,
        isAuthenticated,
        login,
        loginAsPublic,
        logout,
        theme,
        setTheme,
        toggleTheme
      }}
    >
      {children}
    </AppContext.Provider>
  );
};

import { useApp } from './useApp';
export { useApp };

