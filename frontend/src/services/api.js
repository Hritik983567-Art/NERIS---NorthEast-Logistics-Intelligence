const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || '/api/v1').replace(/\/$/, '');
const IS_PROD_MODE = import.meta.env.PROD || import.meta.env.MODE === 'production';

if (IS_PROD_MODE) {
  console.info(`[NERIS PRODUCTION FRONTEND] Operating in PRODUCTION mode using API Base URL: ${API_BASE_URL}`);
} else {
  console.info(`[NERIS DEVELOPMENT FRONTEND] Operating in DEVELOPMENT mode using API Base URL: ${API_BASE_URL}`);
}


const getAuthHeaders = (extraHeaders = {}) => {
  const token = localStorage.getItem('cognito_token');
  const headers = { ...extraHeaders };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
};

export const api = {
  // Amazon Cognito Login & Session
  loginCognito: async (username, password, role = 'COMMANDER') => {
    try {
      const res = await fetch(`${API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password, role })
      });
      const data = await res.json();
      if (!res.ok) {
        return { status: 'FAILED', error: data.detail || 'Authentication failed' };
      }
      if (data.access_token) {
        localStorage.setItem('cognito_token', data.access_token);
        if (data.user) {
          localStorage.setItem('cognito_user', JSON.stringify(data.user));
        }
      }
      return data;
    } catch (err) {
      return { status: 'FAILED', error: err.message };
    }
  },

  getMe: async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/auth/me`, {
        headers: getAuthHeaders()
      });
      if (!res.ok) return null;
      return await res.json();
    } catch (err) {
      return null;
    }
  },

  checkHealth: async () => {
    try {
      const res = await fetch('/api/health');
      if (!res.ok) {
        const fallback = await fetch('/health');
        if (!fallback.ok) throw new Error('Health check failed');
        return await fallback.json();
      }
      return await res.json();
    } catch (err) {
      return { status: 'offline', error: err.message };
    }
  },

  // Tab 1: GIS Network Hubs & Edges
  getNetworkNodes: async (state = null) => {
    try {
      const url = state ? `${API_BASE_URL}/network/nodes?state=${encodeURIComponent(state)}` : `${API_BASE_URL}/network/nodes`;
      const res = await fetch(url);
      if (!res.ok) throw new Error('Failed to fetch network nodes');
      return await res.json();
    } catch (err) {
      console.warn('Backend network nodes unavailable, using local map hubs:', err.message);
      return null;
    }
  },

  getNetworkEdges: async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/network/edges`);
      if (!res.ok) throw new Error('Failed to fetch network edges');
      return await res.json();
    } catch (err) {
      console.warn('Backend network edges unavailable:', err.message);
      return null;
    }
  },

  getNetworkCorridors: async (state = null) => {
    try {
      const url = state ? `${API_BASE_URL}/network/corridors?state=${encodeURIComponent(state)}` : `${API_BASE_URL}/network/corridors`;
      const res = await fetch(url);
      if (!res.ok) throw new Error('Failed to fetch network corridors');
      return await res.json();
    } catch (err) {
      console.warn('Backend dynamic network corridors unavailable:', err.message);
      return null;
    }
  },


  getNetworkOverview: async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/network/overview`);
      if (!res.ok) throw new Error('Failed to fetch network overview');
      return await res.json();
    } catch (err) {
      console.warn('Backend network overview unavailable:', err.message);
      return null;
    }
  },

  // Fleets Telemetry & Simulation
  getFleets: async (state = null) => {
    try {
      const url = state ? `${API_BASE_URL}/telemetry/active-fleet?state=${encodeURIComponent(state)}` : `${API_BASE_URL}/telemetry/active-fleet`;
      const res = await fetch(url);
      if (!res.ok) throw new Error('Failed to fetch active fleet');
      return await res.json();
    } catch (err) {
      console.warn('Backend API unavailable, using local mock state:', err.message);
      return null;
    }
  },

  getSimulatedTelemetry: async (state = null) => {
    try {
      const url = state ? `${API_BASE_URL}/telemetry/simulation?state=${encodeURIComponent(state)}` : `${API_BASE_URL}/telemetry/simulation`;
      const res = await fetch(url);
      if (!res.ok) throw new Error('Failed to fetch simulated telemetry');
      return await res.json();
    } catch (err) {
      console.warn('Backend simulation unavailable:', err.message);
      return null;
    }
  },

  // Telemetry Ping & Fleet Tracking
  pingTelemetry: async (telemetryPayload) => {
    try {
      const res = await fetch(`${API_BASE_URL}/fleet/telemetry`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(telemetryPayload)
      });
      if (!res.ok) throw new Error('Telemetry ping failed');
      return await res.json();
    } catch (err) {
      return null;
    }
  },

  getFleetVehicles: async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/fleet`);
      if (!res.ok) throw new Error('Failed to fetch active fleet');
      return await res.json();
    } catch (err) {
      return null;
    }
  },

  getFleetVehicleById: async (vehicleId) => {
    try {
      const res = await fetch(`${API_BASE_URL}/fleet/${encodeURIComponent(vehicleId)}`);
      if (!res.ok) throw new Error('Failed to fetch vehicle state');
      return await res.json();
    } catch (err) {
      return null;
    }
  },

  // Live Incidents (AWS DynamoDB)
  getIncidents: async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/incidents`);
      if (!res.ok) throw new Error('Failed to fetch live incidents');
      return await res.json();
    } catch (err) {
      console.warn('Backend API unavailable for live incidents:', err.message);
      return null;
    }
  },

  createIncident: async (incidentPayload, idempotencyKey = null) => {
    try {
      const extraHeaders = { 'Content-Type': 'application/json' };
      if (idempotencyKey) {
        extraHeaders['Idempotency-Key'] = idempotencyKey;
      }
      const res = await fetch(`${API_BASE_URL}/incidents`, {
        method: 'POST',
        headers: getAuthHeaders(extraHeaders),
        body: JSON.stringify(incidentPayload)
      });
      const data = await res.json();
      if (!res.ok) {
        return { status: 'FAILED', error: data.detail || 'Failed to save incident report.', dynamodb_confirmed: false };
      }
      return data;
    } catch (err) {
      console.warn('Backend API error creating incident:', err.message);
      return { status: 'FAILED', error: err.message, dynamodb_confirmed: false };
    }
  },

  // Upload Evidence Photo to Storage
  uploadEvidence: async (formData) => {
    try {
      const res = await fetch(`${API_BASE_URL}/incidents/upload-evidence`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: formData
      });
      const data = await res.json();
      if (!res.ok) {
        return { status: 'FAILED', error: data.detail || 'Evidence photo upload failed.', s3_confirmed: false };
      }
      return data;
    } catch (err) {
      console.warn('Backend evidence upload failed:', err.message);
      return { status: 'FAILED', error: err.message, s3_confirmed: false };
    }
  },

  // AI Incident Intelligence
  getIncidentAIIntelligence: async (incidentId, payload = null) => {
    try {
      const res = await fetch(`${API_BASE_URL}/incidents/${encodeURIComponent(incidentId)}/ai-intelligence`, {
        method: 'POST',
        headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
        body: JSON.stringify(payload || {})
      });
      if (!res.ok) {
        return { available: false, error_message: 'AI Hazard Intelligence is currently updating parameters. Please consult field reports.' };
      }
      return await res.json();
    } catch (err) {
      return { available: false, error_message: 'AI Hazard Intelligence is currently updating parameters.' };
    }
  },

  // Batch Offline Sync
  syncBatchIncidents: async (batchData) => {
    try {
      const res = await fetch(`${API_BASE_URL}/incidents/batch-sync`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(batchData)
      });
      if (!res.ok) throw new Error('Batch sync failed');
      return await res.json();
    } catch (err) {
      return null;
    }
  },

  // Dashboard State Readiness
  getStateReadiness: async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/dashboard/state-readiness`);
      if (!res.ok) throw new Error('Failed to fetch state readiness');
      return await res.json();
    } catch (err) {
      return null;
    }
  },

  // AI Terrain & Disaster-Aware Route Computation
  calculateRoute: async (originNode, destinationNode, cargoType = 'MEDICINE', weightTons = 12.0, weather = 'MONSOON_STORM', vehicleType = 'HEAVY_CONVOY') => {
    try {
      const res = await fetch(`${API_BASE_URL}/routes/compute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          origin: originNode,
          destination: destinationNode,
          origin_node: originNode,
          destination_node: destinationNode,
          vehicleType: vehicleType,
          cargoType: cargoType,
          cargo_type: cargoType,
          convoy_weight_tons: weightTons,
          weather_condition: weather
        })
      });
      if (!res.ok) {
        const errData = await res.json().catch(() => ({ detail: 'Failed to compute route' }));
        throw new Error(errData.detail || 'Failed to compute route');
      }
      return await res.json();
    } catch (err) {
      console.warn('Backend route computation error:', err.message);
      return { error: err.message };
    }
  },

  // Real-Time Web Intelligence & Weather
  getLiveNews: async (state = null, refresh = false) => {
    try {
      let url = `${API_BASE_URL}/external/news?refresh=${refresh}`;
      if (state && state !== 'all') {
        url += `&state=${encodeURIComponent(state)}`;
      }
      const res = await fetch(url);
      if (!res.ok) throw new Error('Failed to fetch external news');
      return await res.json();
    } catch (err) {
      console.warn('External news feed unavailable:', err.message);
      return { is_available: false, records: [], error_message: err.message };
    }
  },

  getLiveWeather: async (refresh = false) => {
    try {
      const res = await fetch(`${API_BASE_URL}/external/weather?refresh=${refresh}`);
      if (!res.ok) throw new Error('Failed to fetch external weather');
      return await res.json();
    } catch (err) {
      console.warn('External weather feed unavailable:', err.message);
      return { is_available: false, records: [], error_message: err.message };
    }
  },

  getLiveIncidents: async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/external/disasters`);
      if (!res.ok) throw new Error('Failed to fetch external disaster alerts');
      return await res.json();
    } catch (err) {
      console.warn('External disaster alerts unavailable:', err.message);
      return { is_available: false, records: [], error_message: err.message };
    }
  },

  // Central External Provider Adapters Gateway
  getExternalNews: async (state = null, refresh = false) => {
    try {
      let url = `${API_BASE_URL}/external/news?refresh=${refresh}`;
      if (state && state !== 'all') url += `&state=${encodeURIComponent(state)}`;
      const res = await fetch(url);
      if (!res.ok) throw new Error('Failed to fetch external news');
      return await res.json();
    } catch (err) {
      return { is_available: false, records: [], error_message: err.message };
    }
  },

  getExternalWeather: async (state = null, refresh = false) => {
    try {
      let url = `${API_BASE_URL}/external/weather?refresh=${refresh}`;
      if (state && state !== 'all') url += `&state=${encodeURIComponent(state)}`;
      const res = await fetch(url);
      if (!res.ok) throw new Error('Failed to fetch external weather');
      return await res.json();
    } catch (err) {
      return { is_available: false, records: [], error_message: err.message };
    }
  },

  getExternalDisasters: async (state = null, refresh = false) => {
    try {
      let url = `${API_BASE_URL}/external/disasters?refresh=${refresh}`;
      if (state && state !== 'all') url += `&state=${encodeURIComponent(state)}`;
      const res = await fetch(url);
      if (!res.ok) throw new Error('Failed to fetch external disasters');
      return await res.json();
    } catch (err) {
      return { is_available: false, records: [], error_message: err.message };
    }
  },

  getExternalGovtNotices: async (state = null, refresh = false) => {
    try {
      let url = `${API_BASE_URL}/external/govt-notices?refresh=${refresh}`;
      if (state && state !== 'all') url += `&state=${encodeURIComponent(state)}`;
      const res = await fetch(url);
      if (!res.ok) throw new Error('Failed to fetch external govt notices');
      return await res.json();
    } catch (err) {
      return { is_available: false, records: [], error_message: err.message };
    }
  },

  getExternalRoadConditions: async (state = null, refresh = false) => {
    try {
      let url = `${API_BASE_URL}/external/road-conditions?refresh=${refresh}`;
      if (state && state !== 'all') url += `&state=${encodeURIComponent(state)}`;
      const res = await fetch(url);
      if (!res.ok) throw new Error('Failed to fetch external road conditions');
      return await res.json();
    } catch (err) {
      return { is_available: false, records: [], error_message: err.message };
    }
  },

  getExternalAllRecords: async (state = null, refresh = false) => {
    try {
      let url = `${API_BASE_URL}/external/all-records?refresh=${refresh}`;
      if (state && state !== 'all') url += `&state=${encodeURIComponent(state)}`;
      const res = await fetch(url);
      if (!res.ok) throw new Error('Failed to fetch external records');
      return await res.json();
    } catch (err) {
      return { is_available: false, records: [], error_message: err.message };
    }
  },

  // Dedicated NERIS News Feed API Endpoints
  getNewsFeed: async ({ category = null, location = null, severity = null, language = null, q = '', sortBy = 'relevance', isDemo = false, refresh = false } = {}) => {
    try {
      const params = new URLSearchParams();
      if (category && category !== 'all' && category !== 'ALL') params.append('category', category);
      if (location && location !== 'all' && location !== 'ALL' && location !== 'ALL NER') params.append('location', location);
      if (severity && severity !== 'all' && severity !== 'ALL') params.append('severity', severity);
      if (language && language !== 'all' && language !== 'ALL') params.append('language', language);
      if (q && q.trim() !== '') params.append('q', q.trim());
      if (sortBy) params.append('sort_by', sortBy);
      if (isDemo) params.append('is_demo', 'true');
      if (refresh) params.append('refresh', 'true');

      const url = `${API_BASE_URL}/news?${params.toString()}`;
      const res = await fetch(url);
      if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
      return await res.json();
    } catch (err) {
      console.warn('Failed to fetch NERIS news feed backend API:', err.message);
      return { status: 'ERROR', is_live_available: false, is_cached: false, articles: [], error: err.message };
    }
  },

  getNewsArticleById: async (id) => {
    try {
      const res = await fetch(`${API_BASE_URL}/news/${encodeURIComponent(id)}`);
      if (!res.ok) throw new Error(`Failed to fetch article ${id}`);
      return await res.json();
    } catch (err) {
      console.warn('Failed to fetch article by ID:', err.message);
      return null;
    }
  },

  getNewsCategories: async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/news/categories`);
      if (!res.ok) throw new Error('Failed to fetch categories');
      return await res.json();
    } catch (err) {
      return { categories: [] };
    }
  },

  getNewsLocations: async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/news/locations`);
      if (!res.ok) throw new Error('Failed to fetch locations');
      return await res.json();
    } catch (err) {
      return { locations: [] };
    }
  },

  getArticleAISummary: async (id) => {
    try {
      const res = await fetch(`${API_BASE_URL}/news/${encodeURIComponent(id)}/ai-summary`, { method: 'POST' });
      if (!res.ok) throw new Error('AI summary generation failed');
      return await res.json();
    } catch (err) {
      console.warn('AI summary service error:', err.message);
      return { article_id: id, ai_summary: 'AI summary currently unavailable.', disclaimer: 'AI-generated summary — verify with original source.' };
    }
  },

  convertToUnverifiedReport: async (id) => {
    try {
      const res = await fetch(`${API_BASE_URL}/news/${encodeURIComponent(id)}/convert-to-unverified-report`, { method: 'POST' });
      if (!res.ok) throw new Error('Failed to convert article to unverified report');
      return await res.json();
    } catch (err) {
      console.warn('Operational report conversion error:', err.message);
      return null;
    }
  },

  // Dedicated Persistent Alerts & Risk Evaluation Workflow
  getAlerts: async (status = null) => {
    try {
      const url = status ? `${API_BASE_URL}/alerts?status=${encodeURIComponent(status)}` : `${API_BASE_URL}/alerts`;
      const res = await fetch(url);
      if (res.status === 401) {
        localStorage.removeItem('cognito_token');
        localStorage.removeItem('cognito_user');
      }
      if (!res.ok) throw new Error('Failed to fetch alerts');
      return await res.json();
    } catch (err) {
      console.warn('Backend alerts endpoint unavailable:', err.message);
      return null;
    }
  },

  createAlert: async (alertPayload) => {
    try {
      const res = await fetch(`${API_BASE_URL}/alerts`, {
        method: 'POST',
        headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
        body: JSON.stringify(alertPayload)
      });
      if (res.status === 401) {
        localStorage.removeItem('cognito_token');
        localStorage.removeItem('cognito_user');
      }
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Failed to create alert');
      return data;
    } catch (err) {
      console.warn('Backend alert creation error:', err.message);
      return null;
    }
  },

  dispatchSOS: async ({ vehicle_id, reason, location = "NER Emergency Transit Corridor" }) => {
    try {
      const res = await fetch(`${API_BASE_URL}/alerts/sos-dispatch`, {
        method: 'POST',
        headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
        body: JSON.stringify({ vehicle_id, reason, location })
      });
      if (res.status === 401) {
        localStorage.removeItem('cognito_token');
        localStorage.removeItem('cognito_user');
      }
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Emergency SOS dispatch failed');
      return data;
    } catch (err) {
      console.warn('Backend API SOS dispatch error:', err.message);
      throw err;
    }
  },


  updateAlertStatus: async (alertId, newStatus, commanderId = 'Commander', notes = null) => {
    try {
      const res = await fetch(`${API_BASE_URL}/alerts/${encodeURIComponent(alertId)}`, {
        method: 'PATCH',
        headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
        body: JSON.stringify({ status: newStatus, commander_id: commanderId, notes })
      });
      if (res.status === 401) {
        localStorage.removeItem('cognito_token');
        localStorage.removeItem('cognito_user');
      }
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Failed to update alert status');
      return data;
    } catch (err) {
      console.warn('Backend alert status update error:', err.message);
      return null;
    }
  },

  evaluateIncidentRisk: async (incidentData) => {
    try {
      const res = await fetch(`${API_BASE_URL}/alerts/evaluate-incident`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(incidentData)
      });
      if (!res.ok) throw new Error('Incident risk evaluation failed');
      return await res.json();
    } catch (err) {
      console.warn('Backend risk evaluation error:', err.message);
      return null;
    }
  },

  acknowledgeAlert: async (alertId, acknowledgedBy = 'Commander') => {
    try {
      const res = await fetch(`${API_BASE_URL}/alerts/${encodeURIComponent(alertId)}/acknowledge`, {
        method: 'PATCH',
        headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
        body: JSON.stringify({ action_by: acknowledgedBy })
      });
      if (res.status === 401) {
        localStorage.removeItem('cognito_token');
        localStorage.removeItem('cognito_user');
      }
      if (!res.ok) throw new Error('Failed to acknowledge alert');
      return await res.json();
    } catch (err) {
      console.warn('Alert acknowledge error:', err.message);
      return null;
    }
  },

  resolveAlert: async (alertId, resolvedBy = 'Commander') => {
    try {
      const res = await fetch(`${API_BASE_URL}/alerts/${encodeURIComponent(alertId)}/resolve`, {
        method: 'PATCH',
        headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
        body: JSON.stringify({ action_by: resolvedBy })
      });
      if (res.status === 401) {
        localStorage.removeItem('cognito_token');
        localStorage.removeItem('cognito_user');
      }
      if (!res.ok) throw new Error('Failed to resolve alert');
      return await res.json();
    } catch (err) {
      console.warn('Alert resolve error:', err.message);
      return null;
    }
  },

  // Historical Rainfall Dataset (1901-2017 IMD Baseline - NOT LIVE WEATHER)
  getHistoricalRainfallMetadata: async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/rainfall/metadata`);
      if (!res.ok) throw new Error('Failed to fetch rainfall metadata');
      return await res.json();
    } catch (err) {
      console.warn('Historical rainfall metadata fetch error:', err.message);
      return null;
    }
  },

  getHistoricalRainfallAnalytics: async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/rainfall/analytics`);
      if (!res.ok) throw new Error('Failed to fetch historical rainfall analytics');
      return await res.json();
    } catch (err) {
      console.warn('Historical rainfall analytics fetch error:', err.message);
      return null;
    }
  },

  getHistoricalRainfallSummary: async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/rainfall/summary`);
      if (!res.ok) throw new Error('Failed to fetch historical rainfall summary');
      return await res.json();
    } catch (err) {
      console.warn('Historical rainfall summary fetch error:', err.message);
      return null;
    }
  },

  getHistoricalRainfallTrends: async (startYear = null, endYear = null) => {
    try {
      const params = new URLSearchParams();
      if (startYear) params.append('start_year', startYear);
      if (endYear) params.append('end_year', endYear);
      const url = `${API_BASE_URL}/rainfall/trends${params.toString() ? '?' + params.toString() : ''}`;
      const res = await fetch(url);
      if (!res.ok) throw new Error('Failed to fetch historical rainfall trends');
      return await res.json();
    } catch (err) {
      console.warn('Historical rainfall trends fetch error:', err.message);
      return null;
    }
  },

  getHistoricalRainfallByRegion: async (region) => {
    try {
      const res = await fetch(`${API_BASE_URL}/rainfall/${encodeURIComponent(region)}`);
      if (!res.ok) throw new Error(`Failed to fetch rainfall data for region ${region}`);
      return await res.json();
    } catch (err) {
      console.warn('Historical rainfall by region fetch error:', err.message);
      return null;
    }
  },

  getHistoricalRainfallRiskIndex: async (month = 'SEP') => {
    try {
      const res = await fetch(`${API_BASE_URL}/rainfall/risk-index?month=${encodeURIComponent(month)}`);
      if (!res.ok) throw new Error('Failed to fetch historical rainfall risk index');
      return await res.json();
    } catch (err) {
      console.warn('Historical rainfall risk index fetch error:', err.message);
      return null;
    }
  },

  // Historical Landslide and Flood Dataset (Kaggle/NASA Historical Dataset - NOT LIVE VERIFIED INCIDENTS)
  getEnvironmentalRiskSummary: async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/environmental-risk/summary`);
      if (!res.ok) throw new Error('Failed to fetch environmental risk summary');
      return await res.json();
    } catch (err) {
      console.warn('Environmental risk summary fetch error:', err.message);
      return null;
    }
  },

  getEnvironmentalRiskIndex: async (state = null) => {
    try {
      const url = state ? `${API_BASE_URL}/environmental-risk/index?state=${encodeURIComponent(state)}` : `${API_BASE_URL}/environmental-risk/index`;
      const res = await fetch(url);
      if (!res.ok) throw new Error('Failed to fetch environmental risk index');
      return await res.json();
    } catch (err) {
      console.warn('Environmental risk index fetch error:', err.message);
      return null;
    }
  },

  getEnvironmentalRiskRegionDetail: async (state) => {
    try {
      const res = await fetch(`${API_BASE_URL}/environmental-risk/region/${encodeURIComponent(state)}`);
      if (!res.ok) throw new Error(`Failed to fetch environmental risk region detail for ${state}`);
      return await res.json();
    } catch (err) {
      console.warn('Environmental risk region detail fetch error:', err.message);
      return null;
    }
  },

  getEnvironmentalRiskTrends: async (startYear = null, endYear = null) => {
    try {
      const params = new URLSearchParams();
      if (startYear) params.append('start_year', startYear);
      if (endYear) params.append('end_year', endYear);
      const url = `${API_BASE_URL}/environmental-risk/trends${params.toString() ? '?' + params.toString() : ''}`;
      const res = await fetch(url);
      if (!res.ok) throw new Error('Failed to fetch environmental risk trends');
      return await res.json();
    } catch (err) {
      console.warn('Environmental risk trends fetch error:', err.message);
      return null;
    }
  },

  getEnvironmentalRiskRecords: async (eventType = null, state = null) => {
    try {
      let url = `${API_BASE_URL}/environmental-risk/records`;
      const params = new URLSearchParams();
      if (eventType) params.append('event_type', eventType);
      if (state) params.append('state', state);
      if (params.toString()) url += `?${params.toString()}`;
      const res = await fetch(url);
      if (!res.ok) throw new Error('Failed to fetch environmental risk records');
      return await res.json();
    } catch (err) {
      console.warn('Environmental risk records fetch error:', err.message);
      return null;
    }
  },

  getEnvironmentalRiskMetadata: async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/environmental-risk/metadata`);
      if (!res.ok) throw new Error('Failed to fetch environmental risk metadata');
      return await res.json();
    } catch (err) {
      console.warn('Environmental risk metadata fetch error:', err.message);
      return null;
    }
  },

  getHistoricalLandslideFloodMetadata: async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/historical-events/metadata`);
      if (!res.ok) throw new Error('Failed to fetch historical landslide/flood metadata');
      return await res.json();
    } catch (err) {
      console.warn('Historical landslide/flood metadata fetch error:', err.message);
      return null;
    }
  },

  getHistoricalLandslideFloodAnalytics: async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/historical-events/analytics`);
      if (!res.ok) throw new Error('Failed to fetch historical landslide/flood analytics');
      return await res.json();
    } catch (err) {
      console.warn('Historical landslide/flood analytics fetch error:', err.message);
      return null;
    }
  },

  getHistoricalLandslideFloodRecords: async (eventType = null, state = null) => {
    try {
      let url = `${API_BASE_URL}/historical-events/records`;
      const params = new URLSearchParams();
      if (eventType) params.append('event_type', eventType);
      if (state) params.append('state', state);
      if (params.toString()) url += `?${params.toString()}`;
      const res = await fetch(url);
      if (!res.ok) throw new Error('Failed to fetch historical landslide/flood records');
      return await res.json();
    } catch (err) {
      console.warn('Historical landslide/flood records fetch error:', err.message);
      return null;
    }
  },

  // Historical Road Accident Risk Dataset (Kaggle Indian Road Accident Dataset 2022-2025 - NOT LIVE INCIDENTS)
  getHistoricalRoadRiskMetadata: async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/road-risk/metadata`);
      if (!res.ok) throw new Error('Failed to fetch road risk metadata');
      return await res.json();
    } catch (err) {
      console.warn('Historical road risk metadata fetch error:', err.message);
      return null;
    }
  },

  getHistoricalRoadRiskAnalytics: async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/road-risk/analytics`);
      if (!res.ok) throw new Error('Failed to fetch historical road risk analytics');
      return await res.json();
    } catch (err) {
      console.warn('Historical road risk analytics fetch error:', err.message);
      return null;
    }
  },

  getHistoricalRoadRiskSummary: async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/road-risk/summary`);
      if (!res.ok) throw new Error('Failed to fetch historical road risk summary');
      return await res.json();
    } catch (err) {
      console.warn('Historical road risk summary fetch error:', err.message);
      return null;
    }
  },

  getHistoricalRoadRiskTrends: async (startYear = null, endYear = null) => {
    try {
      const params = new URLSearchParams();
      if (startYear) params.append('start_year', startYear);
      if (endYear) params.append('end_year', endYear);
      const url = `${API_BASE_URL}/road-risk/trends${params.toString() ? '?' + params.toString() : ''}`;
      const res = await fetch(url);
      if (!res.ok) throw new Error('Failed to fetch historical road risk trends');
      return await res.json();
    } catch (err) {
      console.warn('Historical road risk trends fetch error:', err.message);
      return null;
    }
  },

  getHistoricalRoadRiskByRegion: async (region) => {
    try {
      const res = await fetch(`${API_BASE_URL}/road-risk/${encodeURIComponent(region)}`);
      if (!res.ok) throw new Error(`Failed to fetch road risk data for region ${region}`);
      return await res.json();
    } catch (err) {
      console.warn('Historical road risk by region fetch error:', err.message);
      return null;
    }
  },

  getHistoricalRoadRiskIndex: async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/road-risk/risk-index`);
      if (!res.ok) throw new Error('Failed to fetch historical road risk index');
      return await res.json();
    } catch (err) {
      console.warn('Historical road risk index fetch error:', err.message);
      return null;
    }
  },

  // Dataset 4: Historical Emergency Resource Allocation Intelligence
  getEmergencyResourceSummary: async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/emergency-resources/summary`);
      if (!res.ok) throw new Error('Failed to fetch emergency resource summary');
      return await res.json();
    } catch (err) {
      console.warn('Emergency resource summary fetch error:', err.message);
      return null;
    }
  },

  getEmergencyResources: async (type = null, state = null) => {
    try {
      let url = `${API_BASE_URL}/emergency-resources/resources`;
      const params = new URLSearchParams();
      if (type) params.append('type', type);
      if (state) params.append('state', state);
      if (params.toString()) url += `?${params.toString()}`;
      const res = await fetch(url);
      if (!res.ok) throw new Error('Failed to fetch emergency resources');
      return await res.json();
    } catch (err) {
      console.warn('Emergency resources fetch error:', err.message);
      return null;
    }
  },

  getEmergencyResourceById: async (id) => {
    try {
      const res = await fetch(`${API_BASE_URL}/emergency-resources/${encodeURIComponent(id)}`);
      if (!res.ok) throw new Error(`Failed to fetch emergency resource ${id}`);
      return await res.json();
    } catch (err) {
      console.warn('Emergency resource by ID fetch error:', err.message);
      return null;
    }
  },

  getEmergencyResourcesByRegion: async (state) => {
    try {
      const res = await fetch(`${API_BASE_URL}/emergency-resources/region/${encodeURIComponent(state)}`);
      if (!res.ok) throw new Error(`Failed to fetch emergency resources for region ${state}`);
      return await res.json();
    } catch (err) {
      console.warn('Emergency resources by region fetch error:', err.message);
      return null;
    }
  },

  getEmergencyResourceTypes: async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/emergency-resources/types`);
      if (!res.ok) throw new Error('Failed to fetch emergency resource types');
      return await res.json();
    } catch (err) {
      console.warn('Emergency resource types fetch error:', err.message);
      return null;
    }
  },

  getEmergencyResourceCoverage: async (state = null) => {
    try {
      const url = state ? `${API_BASE_URL}/emergency-resources/coverage?state=${encodeURIComponent(state)}` : `${API_BASE_URL}/emergency-resources/coverage`;
      const res = await fetch(url);
      if (!res.ok) throw new Error('Failed to fetch emergency resource coverage');
      return await res.json();
    } catch (err) {
      console.warn('Emergency resource coverage fetch error:', err.message);
      return null;
    }
  },

  getEmergencyResourceAnalytics: async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/emergency-resources/analytics`);
      if (!res.ok) throw new Error('Failed to fetch emergency resource analytics');
      return await res.json();
    } catch (err) {
      console.warn('Emergency resource analytics fetch error:', err.message);
      return null;
    }
  },

  getEmergencyResourceTrends: async (startYear = null, endYear = null) => {
    try {
      const params = new URLSearchParams();
      if (startYear) params.append('start_year', startYear);
      if (endYear) params.append('end_year', endYear);
      const url = `${API_BASE_URL}/emergency-resources/trends${params.toString() ? '?' + params.toString() : ''}`;
      const res = await fetch(url);
      if (!res.ok) throw new Error('Failed to fetch emergency resource trends');
      return await res.json();
    } catch (err) {
      console.warn('Emergency resource trends fetch error:', err.message);
      return null;
    }
  },

  getEmergencyResourceMetadata: async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/emergency-resources/metadata`);
      if (!res.ok) throw new Error('Failed to fetch emergency resource metadata');
      return await res.json();
    } catch (err) {
      console.warn('Emergency resource metadata fetch error:', err.message);
      return null;
    }
  }
};
