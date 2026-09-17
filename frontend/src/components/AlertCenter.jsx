import React, { useState } from 'react';
import { useApp } from '../context/AppContext';
import { localizedFleets } from '../data/localizedData';
import { api } from '../services/api';
import {
  Radio,
  ShieldAlert,
  AlertTriangle,
  CheckCircle2,
  Send,
  Volume2,
  Megaphone,
  Shield,
  ShieldCheck,
  Lock,
  Clock,
  UserCheck
} from 'lucide-react';

const fleetStatements = {
  "NER-MED-8041": {
    badge: "COLD-CHAIN MEDICAL ESCORT",
    badgeColor: "#3B82F6",
    notice: {
      en: "Directly vector military/SDRF escorts, temperature-controlled cold-chain protection, and priority BRO clearing teams for high-priority life-saving medical supplies.",
      as: "জিৱনৰক্ষাকাৰী চিকিৎসা সামগ্ৰীৰ বাবে প্ৰাথমিকতাৰে মিলিটাৰী/SDRF এস্কৰ্ট আৰু শীতল শৃংখলা সুৰক্ষা প্ৰদান কৰক।",
      bn: "জীবনরক্ষাকারী চিকিৎসা সামগ্রীর জন্য অগ্রাধিকারের ভিত্তিতে সামরিক/SDRF এস্কর্ট এবং কোল্ড চেইন সুরক্ষা প্রদান করুন।",
      hi: "जीवनरक्षक चिकित्सा आपूर्ति के लिए सैन्य/SDRF एस्कॉर्ट और कोल्ड-चेन सुरक्षा तुरंत प्रदान करें।",
      mn: "Life-saving medicine supply ꯒꯤꯗꯃꯛ military/SDRF escort ꯑꯃꯁꯨꯡ cold-chain protection ꯄꯤꯌꯨ"
    },
    reason: {
      en: "Urgent medical escort and cold-chain temperature monitoring required through high-risk landslide zone.",
      as: "উচ্চ বিপদসংকুল ভূস্খলন অঞ্চলৰ মাজেৰে জৰুৰী চিকিৎসা এস্কৰ্ট আৰু শীতল শৃংখলা নিৰীক্ষণৰ প্ৰয়োজন।",
      bn: "উচ্চ ঝুঁকিপূর্ণ পাহাড় ধস অঞ্চলের মধ্য দিয়ে জরুরি চিকিৎসা এস্কর্ট এবং কোল্ড-চেইন নিরীক্ষণ প্রয়োজন।",
      hi: "उच्च जोखिम वाले भूस्खलन क्षेत्र के माध्यम से तत्काल चिकित्सा एस्कॉर्ट और कोल्ड-चेन निगरानी आवश्यक है।",
      mn: "Landslide area ꯗ urgent medical escort ꯑꯃꯁꯨꯡ cold-chain monitoring ꯃꯊꯧ ꯇꯥꯏ"
    }
  },
  "NER-FOOD-9102": {
    badge: "FCI GRAIN RELIEF ESCORT",
    badgeColor: "#F59E0B",
    notice: {
      en: "Priority dispatch for FCI essential grain convoys to prevent food supply disruptions and regional storage depletion across vulnerable flood-affected districts.",
      as: "বানপানী প্ৰভাৱিত জিলাসমূহত খাদ্য সামগ্ৰীৰ নাটনি ৰোধ কৰিবলৈ FCI শস্য কনভয়ৰ প্ৰাথমিক প্ৰেৰণ।",
      bn: "বন্যা কবলিত জেলাগুলিতে খাদ্য সংকট রোধ করতে এফসিআই শস্য কনভয়ের অগ্রাধিকার ভিত্তিতে জরুরি পাঠাও।",
      hi: "बाढ़ प्रभावित जिलों में खाद्य आपूर्ति संकट रोकने हेतु FCI खाद्यान्न काफिले की प्राथमिकता से निकासी।",
      mn: "Flood hit areas ꯗ food shortage ꯊꯤꯡꯅꯕ FCI grain convoy ꯒꯤ priority dispatch ꯄꯤꯌꯨ"
    },
    reason: {
      en: "Urgent FCI grain convoy clearance and SDRF heavy vehicle escort required across inundated highway corridor.",
      as: "বানপানী প্লাবিত হাইৱে কৰিডৰৰ মাজেৰে FCI শস্য কনভয়ৰ জৰুৰী SDRF এস্কৰ্টৰ প্ৰয়োজন।",
      bn: "প্লাবিত হাইওয়ে করিডোরের মধ্য দিয়ে এফসিআই শস্য কনভয়ের জন্য জরুরি এসডিআরএফ এস্কর্ট প্রয়োজন।",
      hi: "जलमग्न राजमार्ग गलियारे के माध्यम से FCI खाद्यान्न काफिले की तत्काल निकासी और SDRF एस्कॉर्ट आवश्यक।",
      mn: "Inundated highway corridor ꯗ FCI grain convoy ꯒꯤ Urgent SDRF escort ꯃꯊꯧ ꯇꯥꯏ"
    }
  },
  "NER-OXY-3055": {
    badge: "HAZMAT CRYOGENIC LMO ESCORT",
    badgeColor: "#EF4444",
    notice: {
      en: "CRITICAL LMO HAZMAT ESCORT: Immediate high-priority clearance with police pilot escort for cryogenic liquid medical oxygen tankers heading to district hospitals.",
      as: "অত্যন্ত গুৰুত্বপূৰ্ণ লিকুইড অক্সিজেন টেংকাৰ: জিলা চিকিৎসালয়লৈ যোৱা ক্ৰায়'জেনিক অক্সিজেন টেংকাৰৰ বাবে জৰুৰী পুলিচ পাইলট এস্কৰ্ট।",
      bn: "অত্যন্ত গুরুত্বপূর্ণ তরল অক্সিজেন ট্যাংকার: জেলা হাসপাতালে গমনকারী ক্রায়োজেনিক অক্সিজেন ট্যাংকারের জন্য জরুরি পুলিশ পাইলট এস্কর্ট।",
      hi: "अति-गंभीर LMO क्रायोजेनिक टैंकर: जिला अस्पतालों के लिए पुलिस पायलट एस्कॉर्ट के साथ तत्काल प्राथमिकता निकासी।",
      mn: "Hospital ꯗ ꯆꯠꯀꯗꯕ Cryogenic Oxygen Tanker ꯒꯤꯗꯃꯛ Immediate Police Pilot Escort ꯃꯊꯧ ꯇꯥꯏ"
    },
    reason: {
      en: "CRITICAL: Cryogenic LMO pressure alert & hazardous terrain escort needed. Zero-delay passage required for hospital oxygen supply.",
      as: "জৰুৰী: ক্ৰায়'জেনিক LMO চাপৰ সঁহাৰি আৰু বিপদসংকুল পথত আৰক্ষী এস্কৰ্টৰ প্ৰয়োজন।",
      bn: "জরুরি: ক্রায়োজেনিক এলএমও প্রেশার অ্যালার্ট ও ঝুঁকিপূর্ণ ট্র্যাকে জরুরি পুলিশ এস্কর্ট প্রয়োজন।",
      hi: "अत्यंत गंभीर: क्रायोजेनिक LMO दबाव अलर्ट और खतरनाक इलाके में त्वरित एस्कॉर्ट की आवश्यकता।",
      mn: "CRITICAL: Cryogenic LMO pressure alert! Zero-delay passage required for hospital oxygen supply"
    }
  },
  "NER-MAT-1104": {
    badge: "BRO BRIDGE MACHINERY VECTOR",
    badgeColor: "#8B5CF6",
    notice: {
      en: "Heavy BRO engineering clearance and structural equipment transport for immediate bailey bridge construction and road restoration teams.",
      as: "বেলী দলং নিৰ্মাণ আৰু পথ পুনৰুদ্ধাৰকাৰী দলৰ বাবে BRO ইঞ্জিনিয়াৰিং সঁজুলি আৰু গধুৰ বাহনৰ প্ৰাথমিকতা প্ৰদান।",
      bn: "বেইলি ব্রিজ নির্মাণ এবং সড়ক পুনর্বাসন দলের জন্য বিআরও ইঞ্জিনিয়ারিং সরঞ্জাম বহনকারী ভারী বাহনের অগ্রাধিকার গমন।",
      hi: "बेली ब्रिज निर्माण और सड़क बहाली टीमों के लिए भारी BRO इंजीनियरिंग उपकरण परिवहन की प्राथमिकता निकासी।",
      mn: "Bailey bridge ꯁꯥꯅꯕ ꯑꯃꯁꯨꯡ road repair team ꯒꯤꯗꯃꯛ Heavy BRO engineering equipment clearance ꯃꯊꯧ ꯇꯥꯏ"
    },
    reason: {
      en: "Priority BRO engineering escort for structural steel & bridge machinery deployment to washed-out river crossing.",
      as: "নদীৰ উটি যোৱা দলং স্থানলৈ ষ্টীল আৰু যন্ত্ৰপাতি প্ৰেৰণৰ বাবে BRO ইঞ্জিনিয়াৰিং এস্কৰ্ট।",
      bn: "ক্ষতিগ্রস্ত নদী পারাপারের স্থানে বেইলি ব্রিজের যন্ত্রপাতি পাঠাতে বিআরও ইঞ্জিনিয়ারিং এস্কর্ট প্রয়োজন।",
      hi: "क्षतिग्रस्त नदी पारगमन स्थल पर बेली ब्रिज मशीनरी की तैनाती के लिए प्राथमिकता BRO इंजीनियरिंग एस्कॉर्ट।",
      mn: "Washed-out river crossing ꯗ bridge machinery deploy ꯇꯧꯅꯕ BRO engineering escort ꯃꯊꯧ ꯇꯥꯏ"
    }
  },
  "NER-AGRI-5590": {
    badge: "PERISHABLE AGRI CORRIDOR CLEARANCE",
    badgeColor: "#10B981",
    notice: {
      en: "Time-sensitive agricultural corridor clearance for perishable organic produce and regional farmer supply chains under monsoon weather risks.",
      as: "পচনশীল জৈৱিক কৃষি সামগ্ৰী আৰু আঞ্চলিক কৃষকৰ যোগান শৃংখলা ৰক্ষাৰ বাবে সময়-সংবেদনশীল হাইৱে ক্লিয়াৰেন্স।",
      bn: "পচনশীল জৈব কৃষি পণ্য এবং আঞ্চলিক কৃষক সরবরাহ নিশ্চিত করতে সময়-সংবেদনশীল সড়ক অগ্রাধিকার প্রদান।",
      hi: "नाशवान जैविक कृषि उपज और क्षेत्रीय किसान आपूर्ति श्रृंखला के संरक्षण हेतु समय-संवेदनशील निकासी।",
      mn: "Perishable organic produce ꯒꯤ supply chain ꯉꯥꯛꯇꯨꯅ ꯊꯝꯅꯕ time-sensitive highway clearance ꯄꯤꯌꯨ"
    },
    reason: {
      en: "Priority clearance required for perishable organic produce convoy facing extended highway blockades.",
      as: "হাইৱে বন্ধৰ বাবে আবদ্ধ হৈ থকা পচনশীল জৈৱিক কৃষি সামগ্ৰীৰ কনভয়ৰ জৰুৰী ক্লিয়াৰেন্সৰ প্ৰয়োজন।",
      bn: "হাইওয়ে অবরোধে আটকে থাকা পচনশীল জৈব কৃষি পণ্যের কনভয়ের জন্য জরুরি অগ্রাধিকার প্রয়োজন।",
      hi: "राजमार्ग रुकावट में फंसे नाशवान जैविक उपज काफिले के लिए तत्काल प्राथमिकता निकासी आवश्यक।",
      mn: "Highway blockades ꯗ ꯁꯣꯛꯂꯕ organic produce convoy ꯒꯤ priority clearance ꯃꯊꯧ ꯇꯥꯏ"
    }
  }
};

export const AlertCenter = () => {
  const {
    t,
    alerts = [],
    isCommander,
    acknowledgeCommandAlert,
    resolveCommandAlert,
    broadcastAlerts,
    triggerSOSAlert,
    fleets,
    lang,
    user
  } = useApp();

  const [selectedFleetId, setSelectedFleetId] = useState(fleets[0]?.id || "NER-MED-8041");
  const [sosReason, setSosReason] = useState(() => {
    const initFleet = fleets[0]?.id || "NER-MED-8041";
    return fleetStatements[initFleet]?.reason?.en || "Urgent medical escort required through landslide zone";
  });

  const handleFleetChange = (newFleetId) => {
    setSelectedFleetId(newFleetId);
    const fleetConfig = fleetStatements[newFleetId];
    if (fleetConfig) {
      const defaultReason = fleetConfig.reason[lang] || fleetConfig.reason.en;
      setSosReason(defaultReason);
    }
  };

  const [broadcastMessage, setBroadcastMessage] = useState("");
  const [sentBroadcastFeedback, setSentBroadcastFeedback] = useState(false);
  const [sosFeedback, setSosFeedback] = useState(false);
  const [statusFilter, setStatusFilter] = useState('ALL');

  const handleManualSOS = async (e) => {
    e.preventDefault();
    await triggerSOSAlert(selectedFleetId, sosReason);
    setSosFeedback(true);
    setTimeout(() => setSosFeedback(false), 4500);
  };

  const currentStatement = fleetStatements[selectedFleetId] || {
    badge: "EMERGENCY DISASTER ESCALATION",
    badgeColor: "#DC2626",
    notice: {
      en: "Directly vector military/SDRF escorts and priority BRO clearing teams for stranded medical and essential commodity convoys.",
      as: "আৱদ্ধ হৈ থকা চিকিৎসা আৰু অপৰিহাৰ্য সামগ্ৰীৰ কনভয়ৰ বাবে প্ৰাথমিকতাৰে মিলিটাৰী/SDRF এস্কৰ্ট আৰু BRO দল প্ৰেৰণ কৰক।",
      bn: "আটকে থাকা চিকিৎসা এবং নিত্যপ্রয়োজনীয় পণ্যের কনভয়ের জন্য অগ্রাধিকারের ভিত্তিতে সামরিক/এসডিআরএফ এস্কর্ট পাঠাও।",
      hi: "फंसे हुए चिकित्सा और आवश्यक वस्तु काफ़िलों के लिए सैन्य/SDRF एस्कॉर्ट्स को तुरंत निर्देशित करें।",
      mn: "Medical and essential commodity convoys ꯒꯤꯗꯃꯛ military/SDRF escort ꯄꯤꯌꯨ"
    }
  };

  const handleCustomBroadcast = async (e) => {
    e.preventDefault();
    if (!broadcastMessage) return;
    try {
      await api.createAlert({
        title: "Operational Command Advisory",
        message: broadcastMessage,
        type: "OPERATIONAL_ADVISORY",
        severity: "HIGH",
        recipientScope: "ALL_COMMANDERS",
        district: "ASSAM"
      });
    } catch (err) {
      console.warn("Failed to persist broadcast alert to DynamoDB:", err);
    }
    setSentBroadcastFeedback(true);
    setTimeout(() => {
      setSentBroadcastFeedback(false);
      setBroadcastMessage("");
    }, 3000);
  };

  const filteredAlerts = alerts.filter((alert) => {
    if (statusFilter === 'ALL') return true;
    return alert.status === statusFilter;
  });

  return (
    <div className="planner-grid" style={{ gridTemplateColumns: '1fr 340px' }}>
      {/* Left Alert Feed & Broadcast Hub */}
      <div className="glass-panel" style={{ padding: '20px', height: '100%', display: 'flex', flexDirection: 'column', overflowY: 'auto' }}>
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexShrink: 0, flexWrap: 'wrap', gap: '8px' }}>
          <div>
            <h2 className="section-title">
              <Megaphone size={20} color="#FF2E93" />
              {t.broadcastingAlerts || "NERIS Command Alert Center"}
            </h2>
            <p style={{ fontSize: '0.78rem', color: 'var(--color-muted)' }}>
              {t.earlyWarningSub || "Real-time incident evaluation, risk alerts, and tactical command escalation"}
            </p>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            {isCommander ? (
              <span className="pill active" style={{ padding: '4px 12px', background: 'rgba(16, 185, 129, 0.15)', color: '#10B981', borderColor: '#10B981' }}>
                <ShieldCheck size={13} style={{ verticalAlign: 'middle', marginRight: '4px' }} />
                COMMANDER AUTHORIZED ({user?.name || 'Commander'})
              </span>
            ) : (
              <span className="pill warning" style={{ padding: '4px 12px', background: 'rgba(245, 158, 11, 0.15)', color: '#F59E0B', borderColor: '#F59E0B' }}>
                <Lock size={12} style={{ verticalAlign: 'middle', marginRight: '4px' }} />
                VIEWER MODE (Command Auth Required)
              </span>
            )}
            <span className="pill blocked" style={{ padding: '4px 12px' }}>
              <Radio size={12} className="sos-pulse-btn" style={{ borderRadius: '50%' }} /> {t.liveFeed || "LIVE WORKFLOW"}
            </span>
          </div>
        </div>

        {/* --- PERSISTENT NERIS COMMAND ALERTS SECTION --- */}
        <div style={{ marginBottom: '24px', flexShrink: 0 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px', flexWrap: 'wrap', gap: '8px' }}>
            <h3 style={{ fontSize: '0.95rem', fontWeight: 800, color: 'var(--color-text)', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <ShieldAlert size={18} color="#DC2626" />
              Incident-Generated Command Alerts
              <span style={{ fontSize: '0.75rem', background: 'var(--color-surface)', border: '1px solid var(--color-border)', padding: '2px 8px', borderRadius: '12px' }}>
                {filteredAlerts.length}
              </span>
            </h3>

            {/* Status Filter Tabs */}
            <div style={{ display: 'flex', gap: '4px', background: 'var(--color-surface)', padding: '3px', borderRadius: '8px', border: '1px solid var(--color-border)' }}>
              {['ALL', 'ACTIVE', 'ACKNOWLEDGED', 'RESOLVED'].map((statusKey) => (
                <button
                  key={statusKey}
                  onClick={() => setStatusFilter(statusKey)}
                  style={{
                    padding: '4px 10px',
                    borderRadius: '6px',
                    border: 'none',
                    background: statusFilter === statusKey ? 'var(--color-primary, #0284C7)' : 'transparent',
                    color: statusFilter === statusKey ? '#FFFFFF' : 'var(--color-muted)',
                    fontSize: '0.72rem',
                    fontWeight: 700,
                    cursor: 'pointer',
                    transition: 'all 0.2s ease'
                  }}
                >
                  {statusKey}
                </button>
              ))}
            </div>
          </div>

          {/* Persistent Alerts List */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {filteredAlerts.length === 0 ? (
              <div style={{ padding: '16px', borderRadius: '8px', border: '1px dashed var(--color-border)', textAlign: 'center', color: 'var(--color-muted)', fontSize: '0.8rem' }}>
                No alerts found matching filter status "{statusFilter}".
              </div>
            ) : (
              filteredAlerts.map((alert) => {
                const isCritical = alert.severity === 'CRITICAL';
                const isHigh = alert.severity === 'HIGH';
                const isActive = alert.status === 'ACTIVE';
                const isAcked = alert.status === 'ACKNOWLEDGED';
                const isResolved = alert.status === 'RESOLVED';

                return (
                  <div
                    key={alert.id}
                    className="glass-panel"
                    style={{
                      padding: '14px 16px',
                      borderRadius: '10px',
                      borderLeft: `4px solid ${isCritical ? '#DC2626' : isHigh ? '#F59E0B' : '#0284C7'}`,
                      background: isActive ? 'rgba(220, 38, 38, 0.03)' : 'var(--color-surface)',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '8px'
                    }}
                  >
                    {/* Top Row: Severity, Title, Status & Honest Delivery Badge */}
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '8px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flex: '1 1 260px' }}>
                        <span
                          className={`pill ${isCritical ? 'blocked' : isHigh ? 'warning' : 'active'}`}
                          style={{ fontSize: '0.7rem', padding: '2px 8px', fontWeight: 800 }}
                        >
                          {alert.severity}
                        </span>
                        <h4 style={{ fontSize: '0.9rem', fontWeight: 800, color: 'var(--color-text)', margin: 0 }}>
                          {alert.title}
                        </h4>
                      </div>

                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                        {/* Honest Delivery Label */}
                        <span
                          style={{
                            fontSize: '0.68rem',
                            fontWeight: 700,
                            padding: '3px 8px',
                            borderRadius: '6px',
                            background: 'rgba(59, 130, 246, 0.1)',
                            border: '1px solid rgba(59, 130, 246, 0.3)',
                            color: '#2563EB',
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '4px'
                          }}
                        >
                          <Shield size={11} /> {alert.delivery_mode ? alert.delivery_mode.replace(/\s*\(AWS DynamoDB\)/gi, '') : 'In-App Operational Alert'}
                        </span>

                        {/* Status Badge */}
                        <span
                          style={{
                            fontSize: '0.68rem',
                            fontWeight: 800,
                            padding: '3px 8px',
                            borderRadius: '6px',
                            background: isActive
                              ? 'rgba(220, 38, 38, 0.12)'
                              : isAcked
                              ? 'rgba(245, 158, 11, 0.12)'
                              : 'rgba(16, 185, 129, 0.12)',
                            color: isActive ? '#DC2626' : isAcked ? '#D97706' : '#059669',
                            border: `1px solid ${isActive ? '#DC2626' : isAcked ? '#F59E0B' : '#10B981'}`
                          }}
                        >
                          {alert.status}
                        </span>
                      </div>
                    </div>

                    {/* Clean & Concise Alert Message */}
                    <p style={{ fontSize: '0.8rem', color: 'var(--color-text)', margin: '2px 0 0 0', lineHeight: 1.45 }}>
                      {(alert.message || '')
                        .replace(/\s*\[Historical[^\]]+\]/g, '')
                        .replace(/\s*\([^\)]*Risk Evaluation:[^\)]*\)/g, '')
                        .trim()}
                    </p>

                    {/* Footer Row: Incident ID, Timestamp, Action Metadata & COMMANDER Action Button */}
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px', paddingTop: '6px', borderTop: '1px solid var(--color-border)', marginTop: '4px' }}>
                      <div style={{ fontSize: '0.72rem', color: 'var(--color-muted)', display: 'flex', alignItems: 'center', gap: '12px' }}>
                        <span>Ref: <strong style={{ color: 'var(--color-text)' }}>{alert.incident_id || alert.incidentId || alert.id}</strong></span>
                        <span><Clock size={11} style={{ verticalAlign: 'middle' }} /> {new Date(alert.created_at || alert.createdAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>

                        {isAcked && alert.acknowledged_by && (
                          <span style={{ color: '#D97706', fontWeight: 600 }}>
                            <UserCheck size={11} style={{ verticalAlign: 'middle' }} /> Ack'd by {alert.acknowledged_by}
                          </span>
                        )}

                        {isResolved && alert.resolved_by && (
                          <span style={{ color: '#059669', fontWeight: 600 }}>
                            <CheckCircle2 size={11} style={{ verticalAlign: 'middle' }} /> Resolved by {alert.resolved_by}
                          </span>
                        )}
                      </div>

                      {/* Commander Lifecycle Action Controls */}
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        {isActive && (
                          isCommander ? (
                            <button
                              onClick={() => acknowledgeCommandAlert(alert.id)}
                              style={{
                                padding: '6px 14px',
                                borderRadius: '6px',
                                background: '#F59E0B',
                                border: 'none',
                                color: '#FFFFFF',
                                fontSize: '0.75rem',
                                fontWeight: 700,
                                cursor: 'pointer',
                                display: 'flex',
                                alignItems: 'center',
                                gap: '6px'
                              }}
                            >
                              <UserCheck size={13} /> Acknowledge Alert
                            </button>
                          ) : (
                            <button
                              disabled
                              title="COMMANDER role required to acknowledge alerts"
                              style={{
                                padding: '6px 12px',
                                borderRadius: '6px',
                                background: 'var(--color-surface)',
                                border: '1px solid var(--color-border)',
                                color: 'var(--color-muted)',
                                fontSize: '0.72rem',
                                fontWeight: 600,
                                cursor: 'not-allowed',
                                display: 'flex',
                                alignItems: 'center',
                                gap: '4px'
                              }}
                            >
                              <Lock size={11} /> COMMANDER Auth Required
                            </button>
                          )
                        )}

                        {isAcked && (
                          isCommander ? (
                            <button
                              onClick={() => resolveCommandAlert(alert.id)}
                              style={{
                                padding: '6px 14px',
                                borderRadius: '6px',
                                background: '#10B981',
                                border: 'none',
                                color: '#FFFFFF',
                                fontSize: '0.75rem',
                                fontWeight: 700,
                                cursor: 'pointer',
                                display: 'flex',
                                alignItems: 'center',
                                gap: '6px'
                              }}
                            >
                              <CheckCircle2 size={13} /> Resolve Alert
                            </button>
                          ) : (
                            <button
                              disabled
                              title="COMMANDER role required to resolve alerts"
                              style={{
                                padding: '6px 12px',
                                borderRadius: '6px',
                                background: 'var(--color-surface)',
                                border: '1px solid var(--color-border)',
                                color: 'var(--color-muted)',
                                fontSize: '0.72rem',
                                fontWeight: 600,
                                cursor: 'not-allowed',
                                display: 'flex',
                                alignItems: 'center',
                                gap: '4px'
                              }}
                            >
                              <Lock size={11} /> COMMANDER Auth Required
                            </button>
                          )
                        )}

                        {isResolved && (
                          <span style={{ fontSize: '0.74rem', color: '#10B981', fontWeight: 800, display: 'flex', alignItems: 'center', gap: '4px' }}>
                            <CheckCircle2 size={14} /> Alert Resolved
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* --- LIVE BROADCAST FEED STACK --- */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px', flexShrink: 0 }}>
          <h3 style={{ fontSize: '0.88rem', fontWeight: 800, color: 'var(--color-text)', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Radio size={16} color="#0284C7" /> In-App Operational Alert Feed
          </h3>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginBottom: '20px', flex: 1, overflowY: 'auto' }}>
          {broadcastAlerts.map((alertItem) => {
            const isSos = alertItem.type === 'sos';
            const isWarning = alertItem.type === 'warning' || alertItem.type === 'disruption';

            const localizedTitles = {
              "b-101": {
                en: "RED ALERT: Heavy Rainfall in Dima Hasao & West Siang",
                as: "ৰাঙলী সতৰ্কতা: ডিমা হাছাও আৰু পশ্চিম ছিয়াঙত প্ৰবল বৰষুণ",
                bn: "রেড অ্যালার্ট: ডিমা হাসাও এবং পশ্চিম সিয়াঙে ভারী বৃষ্টিপাত",
                hi: "रेड अलर्ट: डिमा हसाओ एवं पश्चिम सियांग में भारी बारिश",
                mn: "RED ALERT: Dima Hasao ꯑꯃꯁꯨꯡ West Siang ꯗ ꯑꯀꯅꯕ ꯅꯣꯡ ꯆꯨꯕ"
              },
              "b-102": {
                en: "NH-2 Mao Gate Landslide - BRO Machinery Clearance Underway",
                as: "NH-2 মাও গেটত ভূস্খলন - BRO যন্ত্ৰপাতিৰ জৰিয়তে পৰিস্কাৰৰ কাম চলি আছে",
                bn: "NH-2 মাও গেটে পাহাড় ধস - বিআরও যন্ত্রপাতি দিয়ে রাস্তা পরিষ্কার চলছে",
                hi: "NH-2 माओ गेट भूस्खलन - BRO मशीनरी निकासी कार्य प्रगति पर",
                mn: "NH-2 Mao Gate ꯗ ꯂꯩꯕꯥꯛ ꯇꯥꯕ - BRO ꯅꯥ ꯂꯝꯕꯤ ꯁꯦꯡꯕ ꯆꯠꯂꯤ"
              }
            };

            const alertTitle = localizedTitles[alertItem.id]?.[lang] || alertItem.title;

            return (
              <div
                key={alertItem.id}
                className={`alert-banner ${isSos ? 'sos' : isWarning ? 'warning' : 'system'}`}
                style={{ flexWrap: 'wrap', gap: '10px' }}
              >
                <div style={{ display: 'flex', alignItems: 'flex-start', gap: '10px', flex: '1 1 200px' }}>
                  {isSos ? (
                    <ShieldAlert size={20} color="#FF2E93" />
                  ) : (
                    <AlertTriangle size={20} color="#F59E0B" />
                  )}
                  <div>
                    <h4 style={{ fontSize: '0.88rem', fontWeight: 800 }}>{alertTitle}</h4>
                    <p style={{ fontSize: '0.74rem', marginTop: '2px', opacity: 0.9 }}>
                      Source: {alertItem.source} • <span style={{ fontWeight: 600 }}>{alertItem.timestamp}</span>
                    </p>
                  </div>
                </div>

                {/* Honest Delivery Mode Indicator (Zero Fake Push/SMS Claim) */}
                <div
                  style={{
                    padding: '4px 10px',
                    borderRadius: '6px',
                    background: 'var(--color-surface)',
                    border: '1px solid var(--color-border)',
                    color: 'var(--color-text)',
                    fontSize: '0.72rem',
                    fontWeight: 700,
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px',
                    whiteSpace: 'nowrap'
                  }}
                >
                  <ShieldCheck size={13} color="#10B981" /> In-App Operational Alert
                </div>
              </div>
            );
          })}
        </div>

        {/* Broadcast Announcement Form */}
        <div className="advisory-panel" style={{ padding: '14px', borderRadius: '10px', flexShrink: 0 }}>
          <h3 style={{ fontSize: '0.85rem', fontWeight: 800, color: 'var(--color-text)', marginBottom: '8px' }}>
            <Volume2 size={15} color="#0284C7" style={{ verticalAlign: 'middle' }} /> Operational Advisory Dispatch
          </h3>

          {sentBroadcastFeedback && (
            <div style={{ padding: '8px 12px', borderRadius: '6px', background: 'rgba(16, 185, 129, 0.15)', border: '1px solid #10B981', color: '#065F46', fontSize: '0.76rem', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <CheckCircle2 size={15} /> Operational Advisory Logged!
            </div>
          )}

          <form onSubmit={handleCustomBroadcast}>
            <div className="form-group">
              <label htmlFor="advisory-input" className="form-label">{t.advisoryMessage || "Advisory Message"}</label>
              <input
                id="advisory-input"
                type="text"
                className="form-input"
                placeholder={t.placeholderAdvisory || "e.g. Weather Alert: Sela Pass closed from 18:00 hrs due to heavy snowfall..."}
                value={broadcastMessage}
                onChange={(e) => setBroadcastMessage(e.target.value)}
                required
              />
            </div>
            <button type="submit" className="btn-primary" style={{ width: 'auto', padding: '8px 16px', fontSize: '0.78rem', minHeight: '44px' }}>
              <Send size={14} /> Log In-App Operational Advisory
            </button>
          </form>
        </div>
      </div>

      {/* Right SOS Emergency Dispatch Control */}
      <div className="sidebar-panel">
        <div className="glass-panel" style={{ padding: '18px', height: '100%', display: 'flex', flexDirection: 'column', overflowY: 'auto' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '12px', flexShrink: 0 }}>
            <ShieldAlert size={22} color="#DC2626" />
            <div>
              <h3 style={{ fontSize: '0.95rem', fontWeight: 800, color: '#DC2626' }}>{t.sosDispatch}</h3>
              <p style={{ fontSize: '0.72rem', color: 'var(--color-muted)' }}>{t.emergencyEscalation || "Emergency disaster escalation"}</p>
            </div>
          </div>

          <form onSubmit={handleManualSOS} style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
            <div className="form-group">
              <label htmlFor="sos-fleet-select" className="form-label">{t.targetFleet}</label>
              <select
                id="sos-fleet-select"
                className="form-input"
                value={selectedFleetId}
                onChange={(e) => handleFleetChange(e.target.value)}
              >
                {fleets.map((f) => (
                  <option key={f.id} value={f.id}>
                    {f.id} — {localizedFleets[f.id]?.[lang]?.category || f.category}
                  </option>
                ))}
              </select>
            </div>

            {/* Dynamic Fleet-Specific Operational Directive Statement Panel */}
            <div style={{
              margin: '2px 0 14px 0',
              padding: '12px 14px',
              borderRadius: '8px',
              background: 'var(--color-surface)',
              border: `1px solid ${currentStatement.badgeColor}`,
              borderLeft: `5px solid ${currentStatement.badgeColor}`,
              display: 'flex',
              flexDirection: 'column',
              gap: '6px',
              boxShadow: '0 2px 8px rgba(0, 0, 0, 0.04)'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '8px' }}>
                <span style={{
                  fontSize: '0.64rem',
                  fontWeight: 900,
                  letterSpacing: '0.5px',
                  padding: '2px 8px',
                  borderRadius: '4px',
                  background: `${currentStatement.badgeColor}22`,
                  color: currentStatement.badgeColor,
                  border: `1px solid ${currentStatement.badgeColor}`
                }}>
                  {currentStatement.badge}
                </span>
                <span style={{ fontSize: '0.68rem', color: 'var(--color-muted)', fontWeight: 600 }}>
                  Target Directive
                </span>
              </div>

              <p style={{ fontSize: '0.76rem', color: 'var(--color-text)', margin: 0, lineHeight: 1.45, fontWeight: 500 }}>
                {currentStatement.notice[lang] || currentStatement.notice.en}
              </p>
            </div>

            <div className="form-group">
              <label htmlFor="sos-reason" className="form-label">{t.priorityReason}</label>
              <textarea
                id="sos-reason"
                className="form-input"
                rows={3}
                placeholder={t.placeholderSos || "Urgent medical escort required through landslide zone"}
                value={sosReason}
                onChange={(e) => setSosReason(e.target.value)}
              />
            </div>

            {sosFeedback && (
              <div style={{ padding: '8px 12px', borderRadius: '6px', background: 'rgba(220, 38, 38, 0.12)', border: '1px solid #DC2626', color: '#991B1B', fontSize: '0.76rem', marginBottom: '10px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                {t.sosFeedbackText || "🚨 Emergency SOS Vector Dispatched! SDRF & BRO notified."}
              </div>
            )}

            <button type="submit" className="btn-primary sos-pulse-btn" style={{ padding: '12px', marginTop: 'auto', minHeight: '44px' }}>
              <ShieldAlert size={16} />
              {t.sosDispatch}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};
