import React from 'react';
import { useApp } from '../context/AppContext';
import { districtBuffers } from '../data/nerData';
import {
  BarChart3,
  TrendingUp,
  AlertCircle,
  Clock,
  PackageCheck,
  Building2,
  PieChart
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart as RePieChart,
  Pie,
  Cell
} from 'recharts';

export const AnalyticsDashboard = () => {
  const { nerStates, t } = useApp();

  const connectivityData = (nerStates || [])
    .filter((s) => s && s.id !== 'all')
    .map((s) => {
      const localizedName = (t?.stateNames && t.stateNames[s.id]) || s.name || s.id || '';
      return {
        name: localizedName ? String(localizedName).split(' ')[0] : (s.id || ''),
        fullName: localizedName || s.name || s.id,
        connectivity: s.connectivityIndex || 0
      };
    });

  const hazardBreakdownData = [
    { name: t?.landslideRockfall || "Landslide / Rockfall", value: 48, color: "#FF2E93" },
    { name: t?.flashFloodTeesta || "Flash Flood / Teesta River", value: 28, color: "#00F2FE" },
    { name: t?.bridgeDamage || "Bridge Approach Damage", value: 16, color: "#F59E0B" },
    { name: t?.monsoonFog || "Monsoon Fog / Snow", value: 8, color: "#A855F7" }
  ];

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column', gap: '16px', overflowY: 'auto' }}>
      {/* Top Key Performance Indicators Row */}
      <div className="stats-cards-row" style={{ flexShrink: 0 }}>
        <div className="glass-panel stat-box">
          <div className="stat-box-icon" style={{ background: 'rgba(16, 185, 129, 0.15)' }}>
            <TrendingUp size={22} color="#10B981" />
          </div>
          <div>
            <div style={{ fontSize: '0.72rem', color: 'var(--color-muted)', textTransform: 'uppercase', fontWeight: 700 }}>{t.regionalCorridorIndex}</div>
            <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#34D399' }}>68.5 %</div>
            <div style={{ fontSize: '0.7rem', color: 'var(--color-muted)' }}>{t.opPassability || "Operational Passability"}</div>
          </div>
        </div>

        <div className="glass-panel stat-box">
          <div className="stat-box-icon" style={{ background: 'rgba(0, 242, 254, 0.15)' }}>
            <PackageCheck size={22} color="#00F2FE" />
          </div>
          <div>
            <div style={{ fontSize: '0.72rem', color: 'var(--color-muted)', textTransform: 'uppercase', fontWeight: 700 }}>{t.essentialDeliverySla || "Essential Delivery SLA"}</div>
            <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#2563EB' }}>92.4 %</div>
            <div style={{ fontSize: '0.7rem', color: 'var(--color-muted)' }}>{t.onTimeTransit || "On-Time Commodity Transit"}</div>
          </div>
        </div>

        <div className="glass-panel stat-box">
          <div className="stat-box-icon" style={{ background: 'rgba(255, 46, 147, 0.15)' }}>
            <AlertCircle size={22} color="#FF2E93" />
          </div>
          <div>
            <div style={{ fontSize: '0.72rem', color: 'var(--color-muted)', textTransform: 'uppercase', fontWeight: 700 }}>{t.criticalStockBuffer || "Critical Stock Buffer"}</div>
            <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#FF66B2' }}>2 {t.districtCol || "Districts"}</div>
            <div style={{ fontSize: '0.7rem', color: 'var(--color-muted)' }}>{t.tawangUkhrulWarning || "Tawang & Ukhrul Stock Warnings"}</div>
          </div>
        </div>

        <div className="glass-panel stat-box">
          <div className="stat-box-icon" style={{ background: 'rgba(168, 85, 247, 0.15)' }}>
            <Clock size={22} color="#A855F7" />
          </div>
          <div>
            <div style={{ fontSize: '0.72rem', color: 'var(--color-muted)', textTransform: 'uppercase', fontWeight: 700 }}>{t.avgClearanceTime || "Average Clearance Time"}</div>
            <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#C084FC' }}>6.4 {t.hoursUnit || "Hours"}</div>
            <div style={{ fontSize: '0.7rem', color: 'var(--color-muted)' }}>{t.broClearanceSla || "BRO Landslide Clearance SLA"}</div>
          </div>
        </div>
      </div>

      {/* Main Charts Grid Row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px', flexShrink: 0 }}>
        {/* District Accessibility Bar Chart */}
        <div className="glass-panel" style={{ padding: '16px' }}>
          <h2 className="section-title" style={{ marginBottom: '12px', fontSize: '0.95rem' }}>
            <BarChart3 size={18} color="#00F2FE" />
            {t.districtConnectivity} (%)
          </h2>

          <div style={{ width: '100%', height: '220px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={connectivityData}>
                <XAxis dataKey="name" stroke="var(--color-dim)" fontSize={11} />
                <YAxis stroke="var(--color-dim)" domain={[0, 100]} fontSize={11} />
                <Tooltip contentStyle={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)', color: 'var(--color-text)' }} />
                <Bar dataKey="connectivity" fill="#2563EB" radius={[4, 4, 0, 0]} name={`${t.districtConnectivity} (%)`} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Hazard Causes Breakdown */}
        <div className="glass-panel" style={{ padding: '16px' }}>
          <h2 className="section-title" style={{ marginBottom: '12px', fontSize: '0.95rem' }}>
            <PieChart size={18} color="#A855F7" />
            {t.disruptionCausesBreakdown || "Corridor Disruption Causes Breakdown"}
          </h2>

          <div style={{ display: 'flex', alignItems: 'center', gap: '16px', flexWrap: 'wrap' }}>
            <div style={{ flex: '1 1 140px', height: '200px', minWidth: '140px' }}>
              <ResponsiveContainer width="100%" height="100%">
                <RePieChart>
                  <Pie
                    data={hazardBreakdownData}
                    cx="50%"
                    cy="50%"
                    innerRadius={45}
                    outerRadius={70}
                    paddingAngle={4}
                    dataKey="value"
                  >
                    {hazardBreakdownData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)', color: 'var(--color-text)' }} />
                </RePieChart>
              </ResponsiveContainer>
            </div>

            <div style={{ flex: '1 1 160px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {hazardBreakdownData.map((item, idx) => (
                <div key={idx} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.78rem' }}>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--color-text)' }}>
                    <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: item.color }}></span>
                    {item.name}
                  </span>
                  <strong style={{ fontFamily: 'var(--font-mono)' }}>{item.value}%</strong>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* District Essential Commodity Stock Buffer Table (Mobile Card Transformation) */}
      <div className="glass-panel table-to-cards" style={{ padding: '16px', flex: 1, overflowY: 'auto' }}>
        <h2 className="section-title" style={{ marginBottom: '12px', fontSize: '0.95rem' }}>
          <Building2 size={18} color="#F59E0B" />
          {t.districtSupplyBuffer}
        </h2>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.82rem', textAlign: 'left' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--color-border)', color: 'var(--color-muted)' }}>
                <th style={{ padding: '8px' }}>{t.districtCol}</th>
                <th style={{ padding: '8px' }}>{t.stateCol}</th>
                <th style={{ padding: '8px' }}>{t.foodGrainsStock}</th>
                <th style={{ padding: '8px' }}>{t.medicalSupplies}</th>
                <th style={{ padding: '8px' }}>{t.fuelReserve}</th>
                <th style={{ padding: '8px' }}>{t.alertLevel}</th>
              </tr>
            </thead>
            <tbody>
              {(districtBuffers || []).map((d, idx) => {
                const dState = d?.state || '';
                const stateObj = (nerStates || []).find(s => s?.name && dState && (s.name.toLowerCase().includes(dState.toLowerCase()) || dState.toLowerCase().includes(s.name.toLowerCase())));
                const localizedState = stateObj && t?.stateNames ? t.stateNames[stateObj.id] : dState;
                const statusText = d?.status === 'critical' ? (t?.blocked || 'Blocked / Disrupted') : d?.status === 'warning' ? (t?.caution || 'High Risk / Caution') : (t?.clear || 'Clear / Operational');

                return (
                  <tr key={idx} style={{ borderBottom: '1px solid var(--color-border)' }}>
                    <td data-label={t?.districtCol || "District"} style={{ padding: '10px', fontWeight: 700, color: 'var(--color-text)' }}>{d.district}</td>
                    <td data-label={t?.stateCol || "State"} style={{ padding: '10px', color: 'var(--color-muted)' }}>{localizedState}</td>
                    <td data-label={t?.foodGrainsStock || "Food Grains"} style={{ padding: '10px', fontFamily: 'var(--font-mono)' }}>
                      <span style={{ color: d.foodDays < 5 ? '#EF4444' : '#10B981', fontWeight: 700 }}>{d.foodDays} {t?.daysUnit || 'Days'}</span>
                    </td>
                    <td data-label={t?.medicalSupplies || "Medical Supplies"} style={{ padding: '10px', fontFamily: 'var(--font-mono)' }}>
                      <span style={{ color: d.medDays < 4 ? '#EF4444' : '#10B981', fontWeight: 700 }}>{d.medDays} {t?.daysUnit || 'Days'}</span>
                    </td>
                    <td data-label={t?.fuelReserve || "Fuel Reserve"} style={{ padding: '10px', fontFamily: 'var(--font-mono)' }}>
                      <span style={{ color: d.fuelDays < 5 ? '#EF4444' : '#10B981', fontWeight: 700 }}>{d.fuelDays} {t?.daysUnit || 'Days'}</span>
                    </td>
                    <td data-label={t?.alertLevel || "Alert Level"} style={{ padding: '10px' }}>
                      <span className={`pill ${d.status === 'critical' ? 'blocked' : d.status === 'warning' ? 'caution' : 'clear'}`}>
                        {statusText}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
