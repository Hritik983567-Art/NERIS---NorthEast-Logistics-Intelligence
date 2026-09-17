# NERIS Frontend Web Application Specification

> **Project:** NERIS — North-East Regional Emergency Transit System  
> **Tech Stack:** React 18 + Vite + Leaflet + Recharts + Lucide Icons + Vanilla CSS  
> **Architecture:** Offline-First Modular Component Architecture  
> *Disclaimer: NERIS is an independent student project and is not affiliated with the U.S. NERIS framework.*

---

## Component Architecture & State Flow

```mermaid
flowchart TD
    App["App.jsx<br/>(Main Application Container & Tab Router)"]
    Nav["Navbar.jsx<br/>(Header, Persona Selector, Multi-Lingual Sync)"]

    subgraph Tabs["Operational Views (7 Tabs)"]
        Tab1["GISMap.jsx<br/>(Tab 1: Interactive GIS & Multi-Layer Hazards)"]
        Tab2["AIRoutePlanner.jsx<br/>(Tab 2: NetworkX Risk Detour Solver)"]
        Tab3["VehicleTracker.jsx<br/>(Tab 3: Convoy Telemetry & Haversine Geofencing)"]
        Tab4["FieldReporter.jsx<br/>(Tab 4: Field Incident Submission & S3 Upload)"]
        Tab5["AlertCenter.jsx<br/>(Tab 5: Command SOS & Fleet Directives)"]
        Tab6["AnalyticsDashboard.jsx<br/>(Tab 6: Recharts Vulnerability Analytics)"]
        Tab7["NewsCenter.jsx<br/>(Tab 7: Multi-Lingual Regional News Feed)"]
    end

    subgraph Services["Core Data & Offline Layer"]
        API["api.js<br/>(Axios Axios REST Adapter & Error Sanitization)"]
        IDB["IndexedDB<br/>(offlineQueueDB Storage & Failure Recovery)"]
        Context["AppContext.jsx<br/>(Global State & Background Sync Execution)"]
    end

    App --> Nav
    App --> Tabs
    Tabs --> Services
    Services --> IDB
    Services --> API
```

---

## Key Features

1. **7 Operational Tabs**: GIS Map, AI Route Planner, Convoy Telemetry, Field Reporter, Command Alert Center, Vulnerability Analytics, and Regional News.
2. **Offline Queue Management**: Reports saved to IndexedDB (`offlineQueueDB`) when offline, with manual queue item deletion and instant "Force Sync Now" capabilities.
3. **Target Fleet Directives**: Dynamic operational statement badges tailored per target fleet (`NER-MED-8041`, `NER-FOOD-9102`, `NER-OXY-3055`, `NER-MAT-1104`, `NER-AGRI-5590`).
4. **Sanitized Operational Advisories**: Clean user-facing error banners removing backend internal stack traces and database provider names.

---

## Local Development Commands

```bash
# Install dependencies
npm install

# Start Vite local development server
npm run dev

# Build production bundle
npm run build
```
