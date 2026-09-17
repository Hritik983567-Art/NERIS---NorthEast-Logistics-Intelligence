import React, { useState, useRef } from 'react';
import { useApp } from '../context/AppContext';
import {
  AlertTriangle,
  Wifi,
  WifiOff,
  RefreshCw,
  CheckCircle2,
  Database,
  Camera,
  FileText,
  UploadCloud,
  AlertCircle,
  ShieldCheck,
  Trash2
} from 'lucide-react';

export const FieldReporter = () => {
  const {
    t,
    isOnline,
    addIncidentReport,
    offlineQueue,
    syncOfflineQueue,
    removeOfflineQueueItem,
    nerStates
  } = useApp();

  const [title, setTitle] = useState('');
  const [type, setType] = useState('LANDSLIDE');
  const [severity, setSeverity] = useState('HIGH');
  const [state, setState] = useState('assam');
  const [locationName, setLocationName] = useState('');
  const [lat, setLat] = useState('26.1433');
  const [lng, setLng] = useState('91.7898');
  const [reporter, setReporter] = useState('Inspector R. Gogoi (BRO Division)');
  const [description, setDescription] = useState('');

  const [photoPreview, setPhotoPreview] = useState("https://images.unsplash.com/photo-1544620347-c4fd4a3d5957?auto=format&fit=crop&w=600&q=80");
  const [photoFile, setPhotoFile] = useState(null);
  const [fileError, setFileError] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitFeedback, setSubmitFeedback] = useState(null);

  const fileInputRef = useRef(null);

  const handlePhotoClick = () => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Enforce 10MB file size limit
    const MAX_SIZE = 10 * 1024 * 1024;
    if (file.size > MAX_SIZE) {
      setFileError("File size exceeds 10MB limit. Please select an image under 10MB.");
      return;
    }

    const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp'];
    if (!allowedTypes.includes(file.type.toLowerCase())) {
      setFileError("Unsupported file type. Please upload JPG, PNG, or WEBP.");
      return;
    }

    setFileError(null);
    setPhotoFile(file);
    setPhotoPreview(URL.createObjectURL(file));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!title || !locationName) {
      alert("Please fill in the incident title and location name.");
      return;
    }

    setIsSubmitting(true);
    setSubmitFeedback(null);

    const report = {
      title,
      type,
      severity,
      state,
      locationName,
      lat,
      lng,
      reporter,
      description: description || "No additional comments provided.",
      photoUrl: photoPreview,
      photoFile: photoFile
    };

    try {
      const res = await addIncidentReport(report);
      setSubmitFeedback(res);

      if (res && res.status !== 'FAILED') {
        setTitle('');
        setLocationName('');
        setDescription('');
        setPhotoFile(null);
      }
    } catch (err) {
      setSubmitFeedback({
        status: 'FAILED',
        error: err.message || 'Error submitting field report to central server.'
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="planner-grid" style={{ gridTemplateColumns: '1fr 340px' }}>
      {/* Left Form Panel */}
      <div className="glass-panel" style={{ padding: '20px', height: '100%', display: 'flex', flexDirection: 'column', overflowY: 'auto' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexShrink: 0, flexWrap: 'wrap', gap: '8px' }}>
          <div>
            <h2 className="section-title">
              <AlertTriangle size={20} color="#F59E0B" />
              {t.submitReport}
            </h2>
            <p style={{ fontSize: '0.78rem', color: 'var(--color-muted)' }}>
              {t.reporterSub || "Geo-tagged field inputs for landslide, flood, and road damage updates"}
            </p>
          </div>

          <div className={`status-badge ${isOnline ? 'online' : 'offline'}`}>
            {isOnline ? <Wifi size={14} /> : <WifiOff size={14} />}
            {isOnline ? (t.onlineUpload || "Online Upload") : (t.offlineLocalQueue || "Offline Local Queue")}
          </div>
        </div>

        {submitFeedback && (
          <div
            style={{
              padding: '12px 16px',
              borderRadius: '8px',
              marginBottom: '14px',
              background: submitFeedback.status === 'FAILED'
                ? 'rgba(239, 68, 68, 0.15)'
                : submitFeedback.status === 'synced'
                ? 'rgba(16, 185, 129, 0.15)'
                : 'rgba(245, 158, 11, 0.15)',
              border: submitFeedback.status === 'FAILED'
                ? '1px solid #EF4444'
                : submitFeedback.status === 'synced'
                ? '1px solid #10B981'
                : '1px solid #F59E0B',
              color: submitFeedback.status === 'FAILED'
                ? '#FCA5A5'
                : submitFeedback.status === 'synced'
                ? '#34D399'
                : '#FBBF24',
              display: 'flex',
              flexDirection: 'column',
              gap: '6px',
              flexShrink: 0
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              {submitFeedback.status === 'FAILED' ? (
                <AlertCircle size={20} color="#EF4444" />
              ) : (
                <CheckCircle2 size={20} />
              )}
              <strong style={{ fontSize: '0.88rem' }}>
                {submitFeedback.status === 'synced'
                  ? (t.fieldReportUploaded || 'Field Report Synced to Cloud Server!')
                  : submitFeedback.status === 'submitted'
                  ? 'Field Report Submitted!'
                  : submitFeedback.status === 'FAILED'
                  ? 'Report Submission Failed'
                  : (t.savedToOfflineQueue || 'Saved to Local Offline Queue!')}
              </strong>
            </div>

            {submitFeedback.status === 'FAILED' ? (
              <p style={{ fontSize: '0.78rem', margin: 0, color: '#EF4444' }}>
                {submitFeedback.error || 'Server error occurred during transmission.'}
              </p>
            ) : (
              <div style={{ fontSize: '0.75rem', display: 'flex', gap: '12px', flexWrap: 'wrap', marginTop: '4px' }}>
                <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', background: 'rgba(255,255,255,0.08)', padding: '2px 8px', borderRadius: '4px' }}>
                  <Database size={12} />
                  Cloud Sync Status: <strong>{submitFeedback.dynamodb_confirmed ? 'SYNCED' : 'PENDING'}</strong>
                </span>

                <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', background: 'rgba(255,255,255,0.08)', padding: '2px 8px', borderRadius: '4px' }}>
                  <UploadCloud size={12} />
                  Evidence Media: <strong>{submitFeedback.s3_confirmed ? 'UPLOADED' : (photoFile ? 'PENDING' : 'NO EVIDENCE')}</strong>
                </span>
              </div>
            )}
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '10px' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px' }}>
            <div className="form-group">
              <label htmlFor="report-title" className="form-label">{t.incidentHeadline || "Incident Headline / Title *"}</label>
              <input
                id="report-title"
                type="text"
                className="form-input"
                placeholder={t.placeholderHeadline || "e.g. Landslide on NH-27 KM 184"}
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="hazard-type" className="form-label">{t.hazardCategory || "Hazard Category"}</label>
              <select
                id="hazard-type"
                className="form-input"
                value={type}
                onChange={(e) => setType(e.target.value)}
              >
                <option value="LANDSLIDE">🌋 {t.landslideRisk || "Landslide / Rockfall"}</option>
                <option value="FLOOD">🌊 {t.floodAlert || "Flash Flood / River Inundation"}</option>
                <option value="ROAD_BLOCKAGE">🛣 {t.roadDamage || "Road Blockage / Subsidence"}</option>
                <option value="BRIDGE_DAMAGE">🌉 {t.roadDamage || "Bridge Damage / Washout"}</option>
                <option value="ACCIDENT">🚗 {t.caution || "Traffic / Vehicle Accident"}</option>
                <option value="WEATHER">⛈️ {t.caution || "Severe Weather / Storm"}</option>
                <option value="OTHER">⚠️ {t.caution || "Other Emergency / Obstruction"}</option>
              </select>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '12px' }}>
            <div className="form-group">
              <label htmlFor="severity-scale" className="form-label">{t.severityScale || "Severity Scale"}</label>
              <select
                id="severity-scale"
                className="form-input"
                value={severity}
                onChange={(e) => setSeverity(e.target.value)}
              >
                <option value="CRITICAL">🔴 {t.blocked || "Critical (Total Blockade)"}</option>
                <option value="HIGH">🟠 {t.caution || "High (Single Lane / Heavy Risk)"}</option>
                <option value="MEDIUM">🟡 {t.clear || "Medium (Slow Moving)"}</option>
                <option value="LOW">🟢 Low / Minor Impact</option>
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="state-select-report" className="form-label">{t.selectState}</label>
              <select
                id="state-select-report"
                className="form-input"
                value={state}
                onChange={(e) => setState(e.target.value)}
              >
                {nerStates.filter(s => s.id !== 'all').map((s) => (
                  <option key={s.id} value={s.id}>
                    {(t.stateNames && t.stateNames[s.id]) || s.name}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="location-name" className="form-label">{t.locationLandmark || "Location / Landmark *"}</label>
              <input
                id="location-name"
                type="text"
                className="form-input"
                placeholder={t.placeholderLocation || "e.g. Sonapur Tunnel Section"}
                value={locationName}
                onChange={(e) => setLocationName(e.target.value)}
                required
              />
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '12px' }}>
            <div className="form-group">
              <label htmlFor="geo-lat" className="form-label">{t.geoLat || "Geo-Latitude (GPS)"}</label>
              <input
                id="geo-lat"
                type="text"
                className="form-input"
                value={lat}
                onChange={(e) => setLat(e.target.value)}
              />
            </div>
            <div className="form-group">
              <label htmlFor="geo-lng" className="form-label">{t.geoLng || "Geo-Longitude (GPS)"}</label>
              <input
                id="geo-lng"
                type="text"
                className="form-input"
                value={lng}
                onChange={(e) => setLng(e.target.value)}
              />
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="reporter-details" className="form-label">{t.reporterDetails || "Reporter Details (Officer / Agency)"}</label>
            <input
              id="reporter-details"
              type="text"
              className="form-input"
              value={reporter}
              onChange={(e) => setReporter(e.target.value)}
            />
          </div>

          <div className="form-group">
            <label htmlFor="incident-desc" className="form-label">{t.detailedDesc || "Detailed Description & Clearance Notes"}</label>
            <textarea
              id="incident-desc"
              className="form-input"
              rows={2}
              placeholder={t.placeholderDesc || "Describe debris volume, deployed BRO machinery, estimated clearance time..."}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </div>

          <div className="form-group">
            <label className="form-label">{t.photoEvidence || "Photo Evidence (JPG, PNG, WEBP, max 10MB)"}</label>
            
            <input
              type="file"
              ref={fileInputRef}
              accept="image/jpeg,image/jpg,image/png,image/webp"
              onChange={handleFileChange}
              style={{ display: 'none' }}
            />

            <div style={{ display: 'flex', gap: '14px', alignItems: 'center', flexWrap: 'wrap' }}>
              <img
                src={photoPreview}
                alt="Incident Preview"
                style={{ width: '90px', height: '55px', borderRadius: '8px', objectFit: 'cover', border: '1px solid var(--color-border)' }}
              />
              <button
                type="button"
                onClick={handlePhotoClick}
                style={{
                  minHeight: '44px',
                  padding: '8px 14px',
                  borderRadius: '6px',
                  background: photoFile ? 'rgba(16, 185, 129, 0.15)' : 'var(--color-surface)',
                  border: photoFile ? '1px solid #10B981' : '1px solid var(--color-border)',
                  color: photoFile ? '#34D399' : 'var(--color-text)',
                  fontSize: '0.78rem',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px'
                }}
              >
                <Camera size={16} />
                {photoFile ? `Selected: ${photoFile.name.substring(0, 20)}...` : (t.capturePhoto || "Attach Photo Evidence")}
              </button>

              {photoFile && (
                <span style={{ fontSize: '0.72rem', color: '#10B981', display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <ShieldCheck size={14} /> Ready for Upload ({(photoFile.size / (1024 * 1024)).toFixed(2)} MB)
                </span>
              )}
            </div>

            {fileError && (
              <div style={{ color: '#EF4444', fontSize: '0.75rem', marginTop: '4px' }}>
                ⚠️ {fileError}
              </div>
            )}
          </div>

          <button
            type="submit"
            className="btn-primary"
            disabled={isSubmitting}
            style={{ marginTop: 'auto', minHeight: '44px', opacity: isSubmitting ? 0.7 : 1 }}
          >
            {isSubmitting ? <RefreshCw className="animate-spin" size={16} /> : <FileText size={16} />}
            {isSubmitting
              ? "Uploading Evidence & Saving Report..."
              : isOnline
              ? (t.submitReportBtn || "Submit Live Geo-Tagged Report")
              : (t.saveOfflineBtn || "Save to Offline Queue (No Network)")}
          </button>
        </form>
      </div>

      {/* Right Sidebar: IndexedDB Offline Queue */}
      <div className="sidebar-panel">
        <div className="glass-panel" style={{ padding: '16px', height: '100%', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px', flexShrink: 0 }}>
            <h3 className="section-title" style={{ fontSize: '0.92rem' }}>
              <Database size={16} color="#F59E0B" />
              Offline Incident Queue
            </h3>
            <span className="pill caution">
              {offlineQueue.filter(i => i.status !== 'SYNCED').length} Pending
            </span>
          </div>

          <p style={{ fontSize: '0.74rem', color: 'var(--color-muted)', marginBottom: '12px', flexShrink: 0 }}>
            Local persistent queue for offline zero-connectivity zones. Automatically synchronizes when network connection is restored.
          </p>

          <button
            onClick={() => syncOfflineQueue(true)}
            disabled={offlineQueue.filter(i => i.status !== 'SYNCED').length === 0 || !isOnline}
            className="btn-primary"
            style={{
              background: isOnline ? 'linear-gradient(135deg, #059669 0%, #10B981 100%)' : '#334155',
              boxShadow: 'none',
              opacity: offlineQueue.filter(i => i.status !== 'SYNCED').length === 0 ? 0.6 : 1,
              flexShrink: 0,
              minHeight: '44px'
            }}
          >
            <RefreshCw size={15} />
            {t.syncNow || "Force Sync Now"}
          </button>

          <div style={{ marginTop: '12px', display: 'flex', flexDirection: 'column', gap: '10px', flex: 1, overflowY: 'auto' }}>
            {offlineQueue.length > 0 ? (
              offlineQueue.map((item, idx) => {
                const statusStr = item.status || 'PENDING SYNC';
                const isSynced = statusStr === 'SYNCED';
                const isSyncing = statusStr === 'SYNCING';
                const isFailed = statusStr === 'FAILED';
                const payload = item.payload || item;

                return (
                  <div
                    key={item.localQueueId || idx}
                    className="item-card"
                    style={{
                      borderLeft: `4px solid ${isSynced ? '#10B981' : isSyncing ? '#3B82F6' : isFailed ? '#EF4444' : '#F59E0B'}`,
                      background: 'var(--color-surface)',
                      padding: '10px 12px',
                      borderRadius: '8px',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '4px'
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '6px' }}>
                      <div style={{ fontWeight: 700, fontSize: '0.82rem', color: 'var(--color-text)' }}>
                        {payload.title || item.title}
                      </div>

                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                        {/* Status Badge */}
                        <span
                          style={{
                            fontSize: '0.65rem',
                            fontWeight: 800,
                            padding: '2px 6px',
                            borderRadius: '4px',
                            background: isSynced
                              ? 'rgba(16, 185, 129, 0.15)'
                              : isSyncing
                              ? 'rgba(59, 130, 246, 0.15)'
                              : isFailed
                              ? 'rgba(239, 68, 68, 0.15)'
                              : 'rgba(245, 158, 11, 0.15)',
                            color: isSynced ? '#10B981' : isSyncing ? '#3B82F6' : isFailed ? '#EF4444' : '#D97706',
                            border: `1px solid ${isSynced ? '#10B981' : isSyncing ? '#3B82F6' : isFailed ? '#EF4444' : '#F59E0B'}`,
                            whiteSpace: 'nowrap'
                          }}
                        >
                          {statusStr}
                        </span>

                        <button
                          onClick={() => removeOfflineQueueItem(item.localQueueId)}
                          title="Remove from offline queue"
                          style={{
                            background: 'transparent',
                            border: 'none',
                            color: '#94A3B8',
                            cursor: 'pointer',
                            padding: '2px',
                            display: 'flex',
                            alignItems: 'center',
                            borderRadius: '4px'
                          }}
                          onMouseEnter={(e) => e.currentTarget.style.color = '#EF4444'}
                          onMouseLeave={(e) => e.currentTarget.style.color = '#94A3B8'}
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </div>

                    <div style={{ fontSize: '0.72rem', color: 'var(--color-muted)' }}>
                      📍 {payload.locationName || payload.location_name || 'NER Corridor'}
                    </div>

                    <div style={{ fontSize: '0.66rem', color: 'var(--color-muted)', display: 'flex', justifyContent: 'space-between', marginTop: '2px' }}>
                      <span>Key: <code>{(item.clientIncidentId || payload.id || '').substring(0, 14)}...</code></span>
                      <span>Retries: {item.attemptCount || 0}</span>
                    </div>

                    {isFailed && item.error && (
                      <div style={{ fontSize: '0.68rem', color: '#EF4444', marginTop: '2px' }}>
                        ⚠️ Error: {item.error}
                      </div>
                    )}
                  </div>
                );
              })
            ) : (
              <div style={{ padding: '16px', textAlign: 'center', color: 'var(--color-muted)', fontSize: '0.76rem', background: 'var(--color-surface)', borderRadius: '8px', border: '1px solid var(--color-border)' }}>
                No pending offline reports.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

