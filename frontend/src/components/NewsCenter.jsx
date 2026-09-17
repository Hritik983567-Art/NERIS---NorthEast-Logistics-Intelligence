import React, { useState, useEffect, useCallback } from 'react';
import { useApp } from '../context/AppContext';
import { api } from '../services/api';
import { getLocalizedCategory, getLocalizedLocation, getLocalizedSeverity, getLocalizedNewsText } from '../data/newsTranslations';
import {
  Newspaper,
  AlertTriangle,
  Search,
  ExternalLink,
  Share2,
  Clock,
  MapPin,
  CheckCircle2,
  Filter,
  Flame,
  Radio,
  BookOpen,
  Sparkles,
  RefreshCw,
  FileWarning,
  SlidersHorizontal,
  ShieldAlert,
  Layers,
  ArrowUpDown
} from 'lucide-react';

const CATEGORIES_LIST = [
  { id: 'ALL', label: 'All Categories', icon: '🌐' },
  { id: 'DISASTER', label: 'Disaster', icon: '🚨' },
  { id: 'WEATHER', label: 'Weather', icon: '🌧️' },
  { id: 'ROAD & TRANSPORT', label: 'Road & Transport', icon: '🚚' },
  { id: 'FLOOD', label: 'Flood', icon: '🌊' },
  { id: 'LANDSLIDE', label: 'Landslide', icon: '⛰️' },
  { id: 'INFRASTRUCTURE', label: 'Infrastructure', icon: '🏗️' },
  { id: 'GOVERNMENT ADVISORY', label: 'Govt Advisory', icon: '🏛️' },
  { id: 'EMERGENCY RESPONSE', label: 'Emergency Response', icon: '🚑' },
  { id: 'LOGISTICS', label: 'Logistics', icon: '📦' },
  { id: 'GENERAL', label: 'General', icon: '📰' }
];

const LOCATIONS_LIST = [
  'ALL NER',
  'ASSAM',
  'ARUNACHAL PRADESH',
  'MEGHALAYA',
  'MANIPUR',
  'MIZORAM',
  'NAGALAND',
  'TRIPURA',
  'SIKKIM'
];

export const NewsCenter = () => {
  const { lang, setLang, t, stateFilter, setStateFilter, setActiveTab, addIncidentReport } = useApp();

  // State management for API filtering and options
  const [selectedCategory, setSelectedCategory] = useState('ALL');
  const [selectedLocation, setSelectedLocation] = useState(() => {
    return stateFilter && stateFilter !== 'all' ? stateFilter.toUpperCase() : 'ALL NER';
  });
  const [selectedSeverity, setSelectedSeverity] = useState('ALL');
  const [selectedLanguage, setSelectedLanguage] = useState('ALL');
  const [sortBy, setSortBy] = useState('relevance');
  const [isDemoMode] = useState(false);

  // Feed status & data state
  const [articlesList, setArticlesList] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [providerStatus, setProviderStatus] = useState('LIVE_EXTERNAL_FEED');
  const [isCached, setIsCached] = useState(false);
  const [lastRetrievedAt, setLastRetrievedAt] = useState(null);
  const [errorNotice, setErrorNotice] = useState(null);
  const [refreshNotice, setRefreshNotice] = useState(false);

  // Modal state
  const [activeArticleModal, setActiveArticleModal] = useState(null);
  const [aiSummaryData, setAiSummaryData] = useState(null);
  const [isGeneratingAi, setIsGeneratingAi] = useState(false);
  const [sharedNotice, setSharedNotice] = useState(false);
  const [leadNotice, setLeadNotice] = useState(null);

  // Synchronize global stateFilter with news location filter
  useEffect(() => {
    if (stateFilter && stateFilter !== 'all') {
      setSelectedLocation(stateFilter.toUpperCase());
    }
  }, [stateFilter]);

  // Strip HTML tags and entities from RSS headlines and summaries
  const stripHtmlTags = (rawStr = '', fallbackTitle = '') => {
    if (!rawStr) return fallbackTitle ? `Regional disaster & logistics update regarding ${fallbackTitle}.` : '';
    let clean = String(rawStr)
      .replace(/<[^>]*>/g, ' ')
      .replace(/&nbsp;/gi, ' ')
      .replace(/&amp;/gi, '&')
      .replace(/&lt;/gi, '<')
      .replace(/&gt;/gi, '>')
      .replace(/&quot;/gi, '"')
      .replace(/&#39;/g, "'")
      .replace(/\s+/g, ' ')
      .trim();
    if (clean.length < 15 && fallbackTitle) {
      return `Regional disaster & logistics update regarding ${fallbackTitle}.`;
    }
    return clean;
  };

  // Authentic Photojournalistic Daily Newspaper Image Fallback Resolver
  const resolveNewsImage = (title = '', summary = '', category = '', image_url = null) => {
    // If a non-generic custom image URL is provided, use it
    if (image_url && image_url.startsWith('http') && !image_url.includes('photo-1464822759023') && !image_url.includes('photo-1506744038136')) {
      return image_url;
    }
    if (image_url && image_url.startsWith('/images/')) return image_url;

    const text = (title + " " + summary + " " + category).toLowerCase();

    if (text.includes("landslide") || text.includes("rockfall") || text.includes("debris") || text.includes("mudslide") || text.includes("slump") || text.includes("sela pass") || text.includes("hillside")) {
      return "/images/news/landslide.jpg";
    }
    if (text.includes("flood") || text.includes("inundation") || text.includes("teesta") || text.includes("brahmaputra") || text.includes("overflow") || text.includes("submerged") || text.includes("waterlog")) {
      return "/images/news/flood.jpg";
    }
    if (text.includes("bro") || text.includes("clearance") || text.includes("machinery") || text.includes("bulldozer") || text.includes("excavator") || text.includes("vartak") || text.includes("swastik") || text.includes("nhidcl")) {
      return "/images/news/road_clearing.jpg";
    }
    if (text.includes("truck") || text.includes("convoy") || text.includes("freight") || text.includes("fci") || text.includes("vaccine") || text.includes("supply") || text.includes("logistics") || text.includes("carrier")) {
      return "/images/news/truck_convoy.jpg";
    }
    if (text.includes("bridge") || text.includes("washout") || text.includes("collapse") || text.includes("structure") || text.includes("abutment")) {
      return "/images/news/bridge_damage.jpg";
    }
    if (text.includes("rain") || text.includes("monsoon") || text.includes("fog") || text.includes("imd") || text.includes("cloudburst") || text.includes("storm") || text.includes("downpour") || text.includes("weather")) {
      return "/images/news/heavy_rain.jpg";
    }

    return "/images/news/landslide.jpg";
  };

  // Resolve direct source URL for news articles
  const resolveSourceUrl = (article) => {
    if (!article) return 'https://news.google.com';
    const rawUrl = article.source_url || article.url || '';
    if (rawUrl && (rawUrl.startsWith('http://') || rawUrl.startsWith('https://')) && rawUrl !== '#') {
      return rawUrl;
    }
    return 'https://news.google.com';
  };

  // Fetch news feed from backend API
  const fetchNewsFeed = useCallback(async (forceRefresh = false) => {
    setIsLoading(true);
    setErrorNotice(null);

    const response = await api.getNewsFeed({
      category: selectedCategory,
      location: selectedLocation,
      severity: selectedSeverity,
      language: 'ALL',
      sortBy: sortBy,
      isDemo: isDemoMode,
      refresh: forceRefresh
    });

    setIsLoading(false);

    if (response && response.articles && response.articles.length > 0) {
      setArticlesList(response.articles);
      setProviderStatus(response.provider_status || 'LIVE_EXTERNAL_FEED');
      setIsCached(response.is_cached || false);
      setLastRetrievedAt(response.retrieved_at || new Date().toLocaleTimeString());

      if (forceRefresh) {
        setRefreshNotice(true);
        setTimeout(() => setRefreshNotice(false), 3000);
      }
    } else {
      // Robust Fallback: load regional news seed from local data
      import('../data/newsData').then(({ regionalNewsArticles }) => {
        const fallbacks = (regionalNewsArticles || []).map(item => ({
          id: item.id,
          title: typeof item.title === 'object' ? (item.title[lang] || item.title.en) : item.title,
          summary: typeof item.summary === 'object' ? (item.summary[lang] || item.summary.en) : item.summary,
          title_native: typeof item.title === 'object' ? (item.title[item.language] || item.title.en) : item.title,
          summary_native: typeof item.summary === 'object' ? (item.summary[item.language] || item.summary.en) : item.summary,
          original_language: item.language || 'en',
          category: item.category ? item.category.toUpperCase() : 'DISASTER',
          location: item.state ? item.state.toUpperCase() : 'ASSAM',
          severity: item.urgency === 'critical' ? 'CRITICAL' : (item.urgency === 'warning' ? 'HIGH' : 'LOW'),
          source: item.source || 'Regional Command Bulletin',
          source_url: '#',
          published_at: item.timestamp || 'Recent',
          retrieved_at: new Date().toLocaleTimeString(),
          image_url: item.image || '/images/news/landslide.jpg',
          relevance_score: 95
        }));
        setArticlesList(fallbacks);
        setProviderStatus('LOCAL_FALLBACK');
        setLastRetrievedAt(new Date().toLocaleTimeString());
      }).catch(() => {
        setArticlesList([]);
      });
    }
  }, [selectedCategory, selectedLocation, selectedSeverity, selectedLanguage, sortBy, isDemoMode, lang]);

  useEffect(() => {
    fetchNewsFeed(false);

    // Auto-refresh live news feed every 1 minute (60,000 ms) for automatic media article sync
    const ONE_MINUTE_MS = 60 * 1000;
    const intervalId = setInterval(() => {
      fetchNewsFeed(true);
    }, ONE_MINUTE_MS);

    return () => clearInterval(intervalId);
  }, [fetchNewsFeed]);

  const handleManualRefresh = () => {
    fetchNewsFeed(true);
  };

  const handleShare = (article) => {
    setSharedNotice(article.id);
    setTimeout(() => setSharedNotice(false), 2500);
  };

  const getLanguageBadge = (langCode) => {
    const code = (langCode || 'en').toLowerCase();
    switch (code) {
      case 'as': return { label: '🇮🇳 অসমীয়া (Assamese)', bg: 'rgba(217, 119, 6, 0.15)', color: '#D97706', border: '#D97706' };
      case 'bn': return { label: '🇮🇳 বাংলা (Bengali)', bg: 'rgba(16, 185, 129, 0.15)', color: '#059669', border: '#10B981' };
      case 'hi': return { label: '🇮🇳 हिंदी (Hindi)', bg: 'rgba(225, 29, 72, 0.15)', color: '#E11D48', border: '#E11D48' };
      case 'mn': return { label: '🇮🇳 ꯃꯩꯇꯩꯂꯣꯟ (Manipuri)', bg: 'rgba(147, 51, 234, 0.15)', color: '#9333EA', border: '#9333EA' };
      default: return { label: '🇬🇧 English', bg: 'rgba(37, 99, 235, 0.15)', color: '#2563EB', border: '#2563EB' };
    }
  };

  // Request optional Bedrock / AI factual summary
  const handleGenerateAiSummary = async (articleId) => {
    setIsGeneratingAi(true);
    const summaryRes = await api.getArticleAISummary(articleId);
    setIsGeneratingAi(false);
    if (summaryRes) {
      setAiSummaryData(summaryRes);
    }
  };

  // Requirement 17: Operational Connection — Convert news article into an Unverified External Report
  const handleConvertToOperationalLead = async (article) => {
    const reportRes = await api.convertToUnverifiedReport(article.id);

    const unverifiedLead = {
      title: `[Unverified External Report] ${article.title}`,
      type: article.category === 'FLOOD' ? 'flood' : (article.category === 'LANDSLIDE' ? 'landslide' : 'roadblock'),
      severity: article.severity || 'HIGH',
      state: (article.location || 'ASSAM').toLowerCase(),
      locationName: `${article.location} Corridor (Source: ${article.source})`,
      lat: 26.1445,
      lng: 91.7362,
      description: `UNVERIFIED EXTERNAL REPORT — Requires commander verification before operational dispatch.\n\nSource: ${article.source} (${article.source_url})\nPublished: ${article.published_at}\nRetrieved: ${article.retrieved_at}\n\nHeadline: ${article.title}\nSummary: ${article.summary}`,
      reporter: `Unverified External Report (${article.source})`,
      photoUrl: resolveNewsImage(article.title, article.summary, article.category, article.image_url)
    };

    addIncidentReport(unverifiedLead);
    setLeadNotice(article.id);
    setTimeout(() => {
      setLeadNotice(null);
      setActiveArticleModal(null);
      setActiveTab('incidents'); // Navigate to Field Reporter / Incidents tab
    }, 1200);
  };

  const getSeverityBadgeClass = (sev) => {
    switch (sev) {
      case 'CRITICAL': return 'blocked';
      case 'HIGH': return 'caution';
      case 'MODERATE': return 'caution';
      default: return 'clear';
    }
  };

  // Ensure robust client-side language sorting order (Assamese -> Bengali -> Hindi -> Manipuri -> English)
  const displayArticles = [...articlesList].sort((a, b) => {
    if (sortBy === 'language') {
      const order = { as: 1, bn: 2, hi: 3, mn: 4, en: 5 };
      const langA = (a.original_language || 'en').toLowerCase();
      const langB = (b.original_language || 'en').toLowerCase();
      return (order[langA] || 99) - (order[langB] || 99);
    }
    if (sortBy === 'newest') {
      return (b.published_timestamp || 0) - (a.published_timestamp || 0);
    }
    if (sortBy === 'severity') {
      const sevRank = { CRITICAL: 4, HIGH: 3, MODERATE: 2, LOW: 1 };
      return (sevRank[b.severity] || 0) - (sevRank[a.severity] || 0);
    }
    return (b.relevance_score || 0) - (a.relevance_score || 0);
  });

  const featuredArticle = displayArticles[0];

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column', gap: '16px', overflowY: 'auto' }}>
      
      {/* Top Header & Interactive Control Toolbar */}
      <div className="glass-panel" style={{ padding: '18px 20px', flexShrink: 0 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '14px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <Newspaper size={26} color="#2563EB" />
              <h2 className="section-title" style={{ fontSize: '1.25rem', margin: 0 }}>
                {t.navNews || "Disaster & Logistics Intelligence Feed"}
              </h2>
            </div>
            <p style={{ fontSize: '0.78rem', color: 'var(--color-muted)', marginTop: '4px' }}>
              Real-time regional intelligence feed mapping transit blockades, extreme weather, and emergency logistics across Northeast India.
            </p>
          </div>

          {/* Action Toolbar */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
            <button
              onClick={handleManualRefresh}
              className="btn-secondary"
              disabled={isLoading}
              style={{ height: '32px', fontSize: '0.76rem', padding: '4px 12px', display: 'flex', alignItems: 'center', gap: '6px' }}
            >
              <RefreshCw size={13} className={isLoading ? 'spin' : ''} />
              {isLoading ? 'Syncing Feed...' : 'Sync Intelligence Feed'}
            </button>
          </div>
        </div>

        {/* Notifications & System Alerts */}
        {refreshNotice && (
          <div style={{ marginTop: '10px', padding: '8px 12px', borderRadius: '6px', background: 'rgba(16, 185, 129, 0.15)', border: '1px solid #10B981', color: '#059669', fontSize: '0.76rem', fontWeight: 700 }}>
            ✅ Feed Synchronized: Retransmitted queries across IMD, BRO Vartak/Swastik commands, and State Operations Centers.
          </div>
        )}

        {errorNotice && (
          <div style={{ marginTop: '10px', padding: '8px 12px', borderRadius: '6px', background: 'rgba(220, 38, 38, 0.12)', border: '1px solid #DC2626', color: '#DC2626', fontSize: '0.76rem', fontWeight: 700, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span>⚠️ {errorNotice}</span>
            <button onClick={handleManualRefresh} style={{ background: '#DC2626', color: '#FFF', border: 'none', padding: '3px 8px', borderRadius: '4px', fontSize: '0.7rem', cursor: 'pointer' }}>
              Retry
            </button>
          </div>
        )}

        {/* Category Classification Chips Bar */}
        <div style={{ display: 'flex', gap: '8px', marginTop: '14px', flexWrap: 'nowrap', overflowX: 'auto', alignItems: 'center', paddingBottom: '4px', scrollbarWidth: 'thin' }}>
          <span style={{ fontSize: '0.72rem', fontWeight: 800, color: 'var(--color-muted)', marginRight: '4px', flexShrink: 0 }}>
            Categories:
          </span>

          {CATEGORIES_LIST.map((cat) => (
            <button
              key={cat.id}
              onClick={() => setSelectedCategory(cat.id)}
              className={`demo-chip-btn ${selectedCategory === cat.id ? 'active' : ''}`}
              style={{
                background: selectedCategory === cat.id ? '#2563EB' : undefined,
                color: selectedCategory === cat.id ? '#FFF' : undefined,
                padding: '4px 10px',
                fontSize: '0.72rem',
                whiteSpace: 'nowrap',
                flexShrink: 0
              }}
            >
              {cat.icon} {getLocalizedCategory(cat.id, lang)}
            </button>
          ))}
        </div>

        {/* Secondary Filter & Sorting Control Toolbar */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '14px', paddingTop: '12px', borderTop: '1px solid var(--color-border)', flexWrap: 'wrap', gap: '10px' }}>
          
          {/* Location Selection Filter */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
            <span style={{ fontSize: '0.72rem', fontWeight: 800, color: 'var(--color-muted)' }}>
              Location Filter:
            </span>
            <select
              className="custom-select"
              value={selectedLocation}
              onChange={(e) => {
                const val = e.target.value;
                setSelectedLocation(val);
                if (val !== 'ALL NER') {
                  setStateFilter(val.toLowerCase());
                } else {
                  setStateFilter('all');
                }
              }}
              style={{ height: '30px', fontSize: '0.76rem', padding: '0 10px', borderRadius: '6px', border: '1px solid var(--color-border)', background: 'var(--color-surface)', fontWeight: 700 }}
            >
              {LOCATIONS_LIST.map((loc) => (
                <option key={loc} value={loc}>
                  📍 {getLocalizedLocation(loc, lang)}
                </option>
              ))}
            </select>
          </div>

          {/* Severity Filter */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '0.72rem', fontWeight: 800, color: 'var(--color-muted)' }}>
              Severity:
            </span>
            <select
              className="custom-select"
              value={selectedSeverity}
              onChange={(e) => setSelectedSeverity(e.target.value)}
              style={{ height: '30px', fontSize: '0.76rem', padding: '0 10px', borderRadius: '6px', border: '1px solid var(--color-border)', background: 'var(--color-surface)', fontWeight: 700 }}
            >
              <option value="ALL">All Severities</option>
              <option value="CRITICAL">🔴 CRITICAL</option>
              <option value="HIGH">🟠 HIGH</option>
              <option value="MODERATE">🟡 MODERATE</option>
              <option value="LOW">🔵 LOW</option>
            </select>
          </div>

          {/* Language Filter */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '0.72rem', fontWeight: 800, color: 'var(--color-muted)' }}>
              Language:
            </span>
            <select
              className="custom-select"
              value={selectedLanguage}
              onChange={(e) => setSelectedLanguage(e.target.value)}
              style={{ height: '30px', fontSize: '0.76rem', padding: '0 10px', borderRadius: '6px', border: '1px solid var(--color-border)', background: 'var(--color-surface)', fontWeight: 700 }}
            >
              <option value="ALL">🌐 All Languages</option>
              <option value="en">🇬🇧 English</option>
              <option value="as">🇮🇳 Assamese (অসমীয়া)</option>
              <option value="bn">🇮🇳 Bengali (বাংলা)</option>
              <option value="hi">🇮🇳 Hindi (हिंदी)</option>
              <option value="mn">🇮🇳 Manipuri (ꯃꯩꯇꯩꯂꯣꯟ)</option>
            </select>
          </div>

          {/* Sorting Control */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <ArrowUpDown size={14} color="var(--color-muted)" />
            <span style={{ fontSize: '0.72rem', fontWeight: 800, color: 'var(--color-muted)' }}>
              Sort By:
            </span>
            <select
              className="custom-select"
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              style={{ height: '30px', fontSize: '0.76rem', padding: '0 10px', borderRadius: '6px', border: '1px solid var(--color-border)', background: 'var(--color-surface)', fontWeight: 700 }}
            >
              <option value="relevance">⚡ Most Relevant (NERIS Score)</option>
              <option value="language">🌐 By Language (Regional / Multi-Lingual)</option>
              <option value="newest">🕒 Newest First</option>
              <option value="severity">🚨 Highest Severity</option>
            </select>
          </div>

        </div>
      </div>

      {/* Operational Disclaimer & Metadata Bar */}
      <div style={{ padding: '8px 16px', borderRadius: '8px', background: 'var(--color-surface)', border: '1px solid var(--color-border)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.76rem', color: 'var(--color-text)', flexShrink: 0, flexWrap: 'wrap', gap: '8px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <ShieldAlert size={15} color="#D97706" />
          <span style={{ color: 'var(--color-muted)', fontSize: '0.72rem' }}>
            <em>"External reports are informational and should be independently verified before operational decisions."</em>
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', fontSize: '0.72rem', flexWrap: 'wrap' }}>
          <span style={{ padding: '3px 8px', borderRadius: '4px', background: 'rgba(16, 185, 129, 0.12)', color: '#059669', border: '1px solid #10B981', fontWeight: 800 }}>
            ⚡ Scheduled Intelligence Sync: ACTIVE
          </span>
          {lastRetrievedAt && (
            <span style={{ color: 'var(--color-muted)' }}>
              Last synchronized: <strong>{lastRetrievedAt}</strong> {isCached && '(Cached)'}
            </span>
          )}
          <span style={{ fontWeight: 800, color: '#2563EB' }}>
            {displayArticles.length} articles found
          </span>
        </div>
      </div>

      {/* Featured Top Headline Story (Hero Banner) */}
      {featuredArticle && !isLoading && (
        <div className="glass-panel" style={{ padding: '20px', position: 'relative', overflow: 'hidden', flexShrink: 0, background: 'var(--color-surface)', border: '1px solid var(--color-border)' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '20px', alignItems: 'center' }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px', flexWrap: 'wrap' }}>
                <span className={`pill ${getSeverityBadgeClass(featuredArticle.severity)}`} style={{ fontSize: '0.72rem', fontWeight: 800 }}>
                  FEATURED • {getLocalizedCategory(featuredArticle.category, lang)} • {getLocalizedSeverity(featuredArticle.severity, lang)}
                </span>
                <span style={{ fontSize: '0.72rem', color: 'var(--color-muted)', fontWeight: 700 }}>
                  📍 {getLocalizedLocation(featuredArticle.location, lang)}
                </span>
                {featuredArticle.original_language && (
                  <span
                    className="pill"
                    style={{
                      fontSize: '0.64rem',
                      padding: '2px 8px',
                      background: getLanguageBadge(featuredArticle.original_language).bg,
                      color: getLanguageBadge(featuredArticle.original_language).color,
                      border: `1px solid ${getLanguageBadge(featuredArticle.original_language).border}`,
                      fontWeight: 800
                    }}
                  >
                    {getLanguageBadge(featuredArticle.original_language).label}
                  </span>
                )}
              </div>

              <h3
                onClick={() => setActiveArticleModal(featuredArticle)}
                style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--color-text)', lineHeight: 1.35, marginBottom: '4px', cursor: 'pointer' }}
              >
                {stripHtmlTags(getLocalizedNewsText(featuredArticle.title, lang), featuredArticle.title)}
              </h3>
              {featuredArticle.title_native && featuredArticle.title_native !== featuredArticle.title && (
                <p style={{ fontSize: '0.78rem', color: 'var(--color-muted)', fontStyle: 'italic', marginBottom: '8px' }}>
                  Original: {stripHtmlTags(featuredArticle.title_native)}
                </p>
              )}

              <p style={{ fontSize: '0.84rem', color: 'var(--color-muted)', lineHeight: 1.5, marginBottom: '14px' }}>
                {stripHtmlTags(getLocalizedNewsText(featuredArticle.summary, lang), featuredArticle.title)}
              </p>

              <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
                <button
                  onClick={() => setActiveArticleModal(featuredArticle)}
                  className="btn-primary"
                  style={{ width: 'auto', padding: '8px 16px', fontSize: '0.78rem', minHeight: '38px' }}
                >
                  <BookOpen size={15} /> Read Full Intelligence Bulletin
                </button>

                {/* Requirement 17: Operational Lead Button */}
                <button
                  onClick={() => handleConvertToOperationalLead(featuredArticle)}
                  style={{
                    background: 'rgba(217, 119, 6, 0.12)',
                    border: '1px solid #D97706',
                    color: '#D97706',
                    padding: '8px 14px',
                    borderRadius: '6px',
                    fontSize: '0.78rem',
                    fontWeight: 800,
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px'
                  }}
                >
                  <FileWarning size={15} /> Flag as Unverified Report
                </button>

                <a
                  href={resolveSourceUrl(featuredArticle)}
                  target="_blank"
                  rel="noopener noreferrer"
                  onClick={(e) => {
                    e.stopPropagation();
                  }}
                  style={{
                    background: 'transparent',
                    border: '1px solid var(--color-border)',
                    color: '#2563EB',
                    padding: '8px 12px',
                    borderRadius: '6px',
                    fontSize: '0.78rem',
                    fontWeight: 700,
                    textDecoration: 'none',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px',
                    cursor: 'pointer'
                  }}
                >
                  <ExternalLink size={14} /> Read Source
                </a>
              </div>

              <div style={{ marginTop: '12px', fontSize: '0.72rem', color: 'var(--color-muted)', display: 'flex', gap: '14px', flexWrap: 'wrap' }}>
                <span>Source: <strong>{featuredArticle.source}</strong></span>
                <span>Published: <strong>{featuredArticle.published_at}</strong></span>
                <span>Retrieved: <strong>{featuredArticle.retrieved_at}</strong></span>
              </div>
            </div>

            <div
              onClick={() => setActiveArticleModal(featuredArticle)}
              style={{ position: 'relative', height: '190px', borderRadius: '12px', overflow: 'hidden', border: '1px solid var(--color-border)', cursor: 'pointer' }}
            >
              <img
                src={resolveNewsImage(featuredArticle.title, featuredArticle.summary, featuredArticle.category, featuredArticle.image_url)}
                alt="News Feature"
                style={{ width: '100%', height: '100%', objectFit: 'cover' }}
              />
            </div>
          </div>
        </div>
      )}

      {/* Loading Skeleton */}
      {isLoading && (
        <div className="glass-panel" style={{ padding: '40px', textAlign: 'center', color: 'var(--color-muted)' }}>
          <RefreshCw size={28} className="sos-pulse" style={{ marginBottom: '10px' }} />
          <p style={{ fontWeight: 700 }}>Fetching NERIS Disaster & Logistics Feed...</p>
        </div>
      )}

      {/* Empty State */}
      {!isLoading && displayArticles.length === 0 && (
        <div className="glass-panel" style={{ padding: '40px', textAlign: 'center', color: 'var(--color-muted)' }}>
          <FileWarning size={36} color="#9CA3AF" style={{ marginBottom: '10px' }} />
          <h4 style={{ fontSize: '1rem', fontWeight: 800, color: 'var(--color-text)' }}>No Matching Bulletins Found</h4>
          <p style={{ fontSize: '0.82rem', marginTop: '4px' }}>
            No disaster or transit articles matched your category or regional filter selection.
          </p>
          <button
            onClick={() => {
              setSelectedCategory('ALL');
              setSelectedLocation('ALL NER');
              setSelectedSeverity('ALL');
            }}
            className="btn-primary"
            style={{ width: 'auto', margin: '14px auto 0', padding: '6px 16px', fontSize: '0.76rem' }}
          >
            Clear All Filters
          </button>
        </div>
      )}

      {/* Classified News Grid */}
      {!isLoading && displayArticles.length > 0 && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '16px', flex: 1 }}>
          {displayArticles.map((article) => {
            const isShared = sharedNotice === article.id;
            const isLeadAdded = leadNotice === article.id;
            const langBadge = getLanguageBadge(article.original_language);

            return (
              <div
                key={article.id}
                className="glass-panel"
                onClick={() => setActiveArticleModal(article)}
                style={{
                  padding: '16px',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                  border: '1px solid var(--color-border)',
                  background: 'var(--color-surface)',
                  borderRadius: '12px',
                  cursor: 'pointer'
                }}
              >
                <div>
                  {/* Card Header Badges */}
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px', gap: '6px', flexWrap: 'wrap' }}>
                    <span className={`pill ${getSeverityBadgeClass(article.severity)}`} style={{ fontSize: '0.64rem', padding: '2px 8px' }}>
                      {getLocalizedCategory(article.category, lang)} • {getLocalizedSeverity(article.severity, lang)}
                    </span>

                    <span
                      className="pill"
                      style={{
                        fontSize: '0.62rem',
                        padding: '2px 8px',
                        background: langBadge.bg,
                        color: langBadge.color,
                        border: `1px solid ${langBadge.border}`,
                        fontWeight: 800
                      }}
                    >
                      {langBadge.label}
                    </span>
                  </div>

                  {/* Article Image Container */}
                  <div style={{ position: 'relative', height: '140px', borderRadius: '8px', overflow: 'hidden', marginBottom: '12px', border: '1px solid var(--color-border)' }}>
                    <img
                      src={resolveNewsImage(article.title, article.summary, article.category, article.image_url)}
                      alt={article.title}
                      style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                    />
                    <div style={{ position: 'absolute', bottom: '6px', right: '6px', background: 'rgba(0, 0, 0, 0.75)', color: '#FFF', padding: '2px 6px', borderRadius: '4px', fontSize: '0.62rem', fontWeight: 700 }}>
                      Score: {article.relevance_score}
                    </div>
                  </div>

                  {/* Article Title */}
                  <h4 style={{ fontSize: '0.94rem', fontWeight: 800, color: 'var(--color-text)', lineHeight: 1.35, marginBottom: '4px', minHeight: '40px' }}>
                    {stripHtmlTags(getLocalizedNewsText(article.title, lang), article.title)}
                  </h4>
                  {article.title_native && article.title_native !== article.title && (
                    <p style={{ fontSize: '0.74rem', color: 'var(--color-muted)', fontStyle: 'italic', marginBottom: '8px' }}>
                      Original: {stripHtmlTags(article.title_native)}
                    </p>
                  )}

                  {/* Article Summary */}
                  <p style={{ fontSize: '0.78rem', color: 'var(--color-muted)', lineHeight: 1.45, marginBottom: '12px' }}>
                    {stripHtmlTags(getLocalizedNewsText(article.summary, lang), article.title)}
                  </p>
                </div>

                {/* Card Footer with Timestamps & Actions */}
                <div style={{ paddingTop: '10px', borderTop: '1px solid var(--color-border)' }}>
                  
                  {/* Source & Timestamps */}
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '2px', marginBottom: '10px', fontSize: '0.7rem', color: 'var(--color-muted)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span>Source: <strong>{article.source}</strong></span>
                      <span>Pub: <strong>{article.published_at}</strong></span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span>Retrieved: <strong>{article.retrieved_at}</strong></span>
                    </div>
                  </div>

                  {/* Action Buttons */}
                  <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setActiveArticleModal(article);
                      }}
                      className="btn-primary"
                      style={{ flex: 1, minHeight: '34px', fontSize: '0.74rem', padding: '4px 8px' }}
                    >
                      <BookOpen size={14} /> Read Bulletin
                    </button>

                    <a
                      href={resolveSourceUrl(article)}
                      target="_blank"
                      rel="noopener noreferrer"
                      onClick={(e) => {
                        e.stopPropagation();
                      }}
                      style={{
                        background: 'var(--color-surface)',
                        border: '1px solid var(--color-border)',
                        color: '#2563EB',
                        borderRadius: '6px',
                        padding: '0 10px',
                        fontSize: '0.74rem',
                        fontWeight: 700,
                        display: 'flex',
                        alignItems: 'center',
                        gap: '4px',
                        textDecoration: 'none',
                        height: '34px',
                        cursor: 'pointer'
                      }}
                    >
                      <ExternalLink size={14} /> Read Source
                    </a>

                    {/* Operational Lead Conversion */}
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleConvertToOperationalLead(article);
                      }}
                      title="Convert article to an Unverified External Report in Field Reporter"
                      style={{
                        background: isLeadAdded ? 'rgba(16, 185, 129, 0.15)' : 'rgba(217, 119, 6, 0.1)',
                        border: isLeadAdded ? '1px solid #10B981' : '1px solid #D97706',
                        color: isLeadAdded ? '#059669' : '#D97706',
                        borderRadius: '6px',
                        padding: '0 8px',
                        fontSize: '0.74rem',
                        fontWeight: 700,
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '4px',
                        height: '34px'
                      }}
                    >
                      {isLeadAdded ? <CheckCircle2 size={14} /> : <FileWarning size={14} />}
                      {isLeadAdded ? 'Logged!' : 'Investigate'}
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Article Detail Modal View */}
      {activeArticleModal && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)', zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '20px' }}>
          <div className="glass-panel" style={{ width: '100%', maxWidth: '650px', background: 'var(--color-surface)', padding: '24px', borderRadius: '16px', border: '1px solid var(--color-border)', maxHeight: '90vh', overflowY: 'auto' }}>
            
            {/* Modal Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '14px' }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                  <span className={`pill ${getSeverityBadgeClass(activeArticleModal.severity)}`}>
                    {getLocalizedCategory(activeArticleModal.category, lang)} • {getLocalizedSeverity(activeArticleModal.severity, lang)}
                  </span>
                  <span style={{ fontSize: '0.76rem', fontWeight: 800, color: 'var(--color-muted)' }}>
                    📍 {getLocalizedLocation(activeArticleModal.location, lang)}
                  </span>
                  <span className="pill warning" style={{ fontSize: '0.64rem', padding: '2px 6px' }}>
                    APPROXIMATE LOCATION — REQUIRES VERIFICATION
                  </span>
                  <span className={`pill ${providerStatus === 'LOCAL_FALLBACK' ? 'warning' : 'clear'}`} style={{ fontSize: '0.64rem' }}>
                    {providerStatus === 'LOCAL_FALLBACK' ? 'LOCAL FALLBACK — NOT LIVE EXTERNAL FEED' : 'LIVE EXTERNAL FEED'}
                  </span>
                </div>

                <h3 style={{ fontSize: '1.25rem', fontWeight: 800, marginTop: '8px', color: 'var(--color-text)', lineHeight: 1.35 }}>
                  {getLocalizedNewsText(activeArticleModal.title, lang)}
                </h3>
              </div>

              <button
                onClick={() => {
                  setActiveArticleModal(null);
                  setAiSummaryData(null);
                }}
                style={{ background: 'transparent', border: 'none', fontSize: '1.4rem', cursor: 'pointer', color: 'var(--color-muted)' }}
              >
                ✕
              </button>
            </div>

            {/* Banner Image */}
            <img
              src={resolveNewsImage(activeArticleModal.title, activeArticleModal.summary, activeArticleModal.category, activeArticleModal.image_url)}
              alt="Article Banner"
              style={{ width: '100%', height: '220px', objectFit: 'cover', borderRadius: '10px', marginBottom: '14px', border: '1px solid var(--color-border)' }}
            />

            {/* Article Content Summary */}
            <div style={{ fontSize: '0.88rem', color: 'var(--color-text)', lineHeight: 1.6, marginBottom: '16px' }}>
              <p style={{ fontWeight: 600, color: 'var(--color-text)', marginBottom: '14px' }}>
                {getLocalizedNewsText(activeArticleModal.summary, lang)}
              </p>

              {/* Relevance Score Breakdown Box */}
              <div style={{ padding: '10px 14px', borderRadius: '8px', background: 'rgba(37, 99, 235, 0.08)', border: '1px solid rgba(37, 99, 235, 0.2)', fontSize: '0.78rem', color: 'var(--color-muted)', marginBottom: '14px' }}>
                <strong style={{ color: '#2563EB' }}>NERIS Relevance Scoring: {activeArticleModal.relevance_score}/100</strong>
                <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', marginTop: '6px', fontSize: '0.72rem' }}>
                  <span>Location: +{activeArticleModal.relevance_breakdown?.location_relevance || 0}</span>
                  <span>Disaster: +{activeArticleModal.relevance_breakdown?.disaster_relevance || 0}</span>
                  <span>Transport: +{activeArticleModal.relevance_breakdown?.transport_relevance || 0}</span>
                  <span>Recency: +{activeArticleModal.relevance_breakdown?.recency_score || 0}</span>
                </div>
              </div>

              {/* Requirement 16: Optional Amazon Bedrock AI Summary Section */}
              {aiSummaryData ? (
                <div style={{ padding: '12px 14px', borderRadius: '8px', background: 'rgba(124, 58, 237, 0.1)', border: '1px solid #7C3AED', color: 'var(--color-text)', fontSize: '0.8rem', marginBottom: '14px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#7C3AED', fontWeight: 800, marginBottom: '4px' }}>
                    <Sparkles size={16} /> Factual AI Summary
                  </div>
                  <p style={{ lineHeight: 1.5 }}>{aiSummaryData.ai_summary}</p>
                  <p style={{ fontSize: '0.7rem', color: '#7C3AED', marginTop: '6px', fontWeight: 700 }}>
                    ⚠️ {aiSummaryData.disclaimer}
                  </p>
                </div>
              ) : (
                <button
                  onClick={() => handleGenerateAiSummary(activeArticleModal.id)}
                  disabled={isGeneratingAi}
                  style={{
                    background: 'rgba(124, 58, 237, 0.12)',
                    border: '1px solid #7C3AED',
                    color: '#7C3AED',
                    padding: '8px 14px',
                    borderRadius: '8px',
                    fontSize: '0.78rem',
                    fontWeight: 800,
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    marginBottom: '14px'
                  }}
                >
                  <Sparkles size={15} className={isGeneratingAi ? 'sos-pulse' : ''} />
                  {isGeneratingAi ? 'Generating Factual AI Summary...' : 'Generate Factual AI Summary'}
                </button>
              )}
            </div>

            {/* Source Transparency & Operational Disclaimer */}
            <div style={{ padding: '10px 12px', borderRadius: '8px', background: 'var(--color-surface)', border: '1px solid var(--color-border)', fontSize: '0.74rem', color: 'var(--color-muted)', marginBottom: '16px' }}>
              <div>Publisher Source: <strong>{activeArticleModal.source}</strong></div>
              <div>Published: <strong>{activeArticleModal.published_at}</strong> | Retrieved by NERIS: <strong>{activeArticleModal.retrieved_at}</strong></div>
              <div style={{ marginTop: '4px', color: '#D97706', fontSize: '0.7rem' }}>
                <em>External reports are informational and should be independently verified before operational decisions.</em>
              </div>
            </div>

            {/* Modal Actions */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: '14px', borderTop: '1px solid var(--color-border)', flexWrap: 'wrap', gap: '10px' }}>
              
              <a
                href={resolveSourceUrl(activeArticleModal)}
                target="_blank"
                rel="noopener noreferrer"
                onClick={(e) => {
                  e.stopPropagation();
                }}
                className="btn-primary"
                style={{ width: 'auto', padding: '8px 16px', fontSize: '0.78rem', textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: '6px', cursor: 'pointer' }}
              >
                <ExternalLink size={15} /> Read Original Source
              </a>

              {/* Requirement 17: Operational Connection */}
              <button
                onClick={() => handleConvertToOperationalLead(activeArticleModal)}
                style={{
                  background: 'rgba(217, 119, 6, 0.15)',
                  border: '1px solid #D97706',
                  color: '#D97706',
                  padding: '8px 14px',
                  borderRadius: '6px',
                  fontSize: '0.78rem',
                  fontWeight: 800,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px'
                }}
              >
                <FileWarning size={15} /> Investigate in NERIS (Create Unverified Report)
              </button>

            </div>
          </div>
        </div>
      )}
    </div>
  );
};
