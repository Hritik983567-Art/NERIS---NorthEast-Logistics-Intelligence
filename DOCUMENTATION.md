# 🗺️ NERIS System Architecture & Technical Documentation

> **Project**: NERIS — North-East Regional Emergency Transit System  
> **Deployment Region**: `ap-south-1` (AWS Asia Pacific - Mumbai)  
> **Frameworks**: React 18 SPA + Vite | Python 3.11 + FastAPI  
> **Cloud Provider**: Amazon Web Services (AWS Serverless)  
> **Disclaimer**: Independent student emergency logistics project.

---

## 📋 Table of Contents
1. [High-Level System Architecture](#1-high-level-system-architecture)
2. [Offline-First Incident Sync & Payload Pipeline](#2-offline-first-incident-sync--payload-pipeline)
3. [Target Fleet SOS Emergency Vectoring Workflow](#3-target-fleet-sos-emergency-vectoring-workflow)
4. [Real-Time Telemetry & Geodesic Hazard Intercept](#4-real-time-telemetry--geodesic-hazard-intercept)
5. [Amazon Bedrock AI Incident Intelligence Pipeline](#5-amazon-bedrock-ai-incident-intelligence-pipeline)
6. [Incident & Alert Lifecycle State Machine](#6-incident--alert-lifecycle-state-machine)
7. [Multi-Source Historical Analytics & Data Ingestion](#7-multi-source-historical-analytics--data-ingestion)

---

## 1. High-Level System Architecture

The **NERIS Platform** decouples client rendering, offline persistence, backend REST execution, cloud database storage, identity management, and artificial intelligence into dedicated, resilient modules.

```mermaid
flowchart TD
    subgraph Client ["Frontend Layer (React 18 SPA + Vite)"]
        UI["7-Tab Command Center UI"]
        Ctx["AppContext (React Context + Hooks)"]
        IDB[("IndexedDB Offline Queue Store")]
        UI --> Ctx
        Ctx <--> IDB
    end

    subgraph API ["Backend Layer (FastAPI Engine)"]
        Gateway["REST Router Engine"]
        Auth["Cognito RBAC & JWT Guard"]
        RouterInc["Incidents Router (/api/v1/incidents)"]
        RouterTel["Telemetry Router (/api/v1/fleet)"]
        RouterAlt["Alerts Router (/api/v1/alerts)"]
        RouterAI["Bedrock AI Router"]

        Gateway --> Auth
        Auth --> RouterInc
        Auth --> RouterTel
        Auth --> RouterAlt
        Auth --> RouterAI
    end

    subgraph AWS ["AWS Cloud Infrastructure (ap-south-1)"]
        DDB[("Amazon DynamoDB - ner_incidents, ner_alerts, ner_fleet")]
        S3["Amazon S3 Bucket (neris-evidence-photos)"]
        Cognito["Amazon Cognito User Pool"]
        Bedrock["Amazon Bedrock (Claude 3 Haiku)"]
    end

    Ctx <-->|"HTTPS / REST API"| Gateway
    RouterInc --> DDB
    RouterInc --> S3
    RouterTel --> DDB
    RouterAlt --> DDB
    RouterAI --> Bedrock
    Auth <--> Cognito
```

---

## 2. Offline-First Incident Sync & Payload Pipeline

When field officers operate in zero-connectivity mountain zones, reports are enqueued into browser **IndexedDB**. Once network access is restored, payloads are sanitized and synchronized with automatic backoff delays for auto-sync and instant execution for manual force-sync.

```mermaid
sequenceDiagram
    autonumber
    actor Officer as "Field Officer (Mobile / Offline)"
    participant UI as "FieldReporter Component"
    participant IDB as "IndexedDB (neris_offline_db)"
    participant Sync as "AppContext Sync Worker"
    participant API as "FastAPI Backend"
    participant DDB as "AWS DynamoDB"

    Officer->>UI: Submit Incident (Draft / Offline)
    UI->>IDB: Enqueue Item (status: "PENDING SYNC")
    Note over Officer,IDB: Offline Mode: Zero Network Available

    window->>Sync: Trigger "online" Event
    Sync->>IDB: Fetch Pending & Failed Queue Items
    
    rect rgb(240, 248, 255)
        Note over Sync: Payload Sanitization Engine
        Sync->>Sync: Inject fallback title, description, coordinates, type & severity
    end

    alt Manual Force Sync Clicked
        Sync->>IDB: Update status to "SYNCING" (Skip Backoff Delay)
    else Background Auto-Sync
        Sync->>Sync: Apply Exponential Backoff (1s to 8s)
        Sync->>IDB: Update status to "SYNCING"
    end

    Sync->>API: POST /api/v1/incidents (Sanitized Payload + JWT)
    API->>DDB: Save Item to "ner_incidents"
    DDB-->>API: 201 Created Confirmation
    API-->>Sync: Return Persisted Record (dynamodb_confirmed: true)

    Sync->>IDB: Update Item status to "SYNCED"
    Sync->>UI: Update Incidents State & Refresh Map Markers
```

---

## 3. Target Fleet SOS Emergency Vectoring Workflow

Logistics Commanders can dispatch emergency SDRF, military, and BRO priority escorts tailored specifically to target fleet cargo requirements.

```mermaid
flowchart LR
    subgraph FleetSel ["Target Fleet Selection"]
        F1["NER-MED-8041 (Medicines)"]
        F2["NER-FOOD-9102 (FCI Grain)"]
        F3["NER-OXY-3055 (Liquid Oxygen)"]
        F4["NER-MAT-1104 (Bridge Steel)"]
        F5["NER-AGRI-5590 (Organic Produce)"]
    end

    subgraph Directive ["Dynamic Directive Engine"]
        B1["COLD-CHAIN MEDICAL ESCORT"]
        B2["FCI GRAIN RELIEF ESCORT"]
        B3["HAZMAT CRYOGENIC LMO ESCORT"]
        B4["BRO BRIDGE MACHINERY VECTOR"]
        B5["PERISHABLE AGRI CLEARANCE"]

        F1 --> B1
        F2 --> B2
        F3 --> B3
        F4 --> B4
        F5 --> B5
    end

    subgraph Dispatch ["Emergency SOS Dispatch"]
        Form["Priority Reason Preset Form"]
        POST["POST /api/v1/alerts/sos-dispatch"]
        Alert["Command Center Alert Feed"]

        B1 & B2 & B3 & B4 & B5 --> Form
        Form --> POST
        POST --> Alert
    end
```

---

## 4. Real-Time Telemetry & Geodesic Hazard Intercept

Continuous GPS telemetry pings monitor fleet coordinates against active hazard locations using geodesic distance math.

```mermaid
sequenceDiagram
    autonumber
    participant Sim as "Telemetry Simulator (telemetry_simulation.py)"
    participant UI as "VehicleTracker & Diagnostic Panel"
    participant Engine as "Geodesic Proximity Engine"
    participant Alert as "Alert Matrix"

    Sim->>Sim: Calculate smooth sinusoidal speed, bearing & cold-chain temp
    Sim->>UI: Update Fleets State (Polling interval 2.5s)
    UI->>Engine: POST /api/v1/telemetry/ping (lat, lng, speed, heading)
    
    Engine->>Engine: Compute Haversine Geodesic Distance to Active Hazards

    alt Hazard Distance < 25.0 km
        Engine->>Engine: Flag Convoy Status = "ROUTE AT RISK"
        Engine->>Alert: Trigger Automatic Proximity Warning Alert
        Engine-->>UI: Return 200 OK + hazard_in_proximity: true
        Note over UI: Display Red Warning Banner & Detour Node
    else Corridor Clear (Distance >= 25.0 km)
        Engine-->>UI: Return 200 OK + hazard_in_proximity: false
        Note over UI: Display Green Clear Status & Diagnostic Metadata
    end
```

---

## 5. Amazon Bedrock AI Incident Intelligence Pipeline

AI incident evaluations use prompt sanitization and XML input tagging to ensure safety and factual grounding without exposing technical errors.

```mermaid
flowchart TD
    A["User Clicks 'AI Hazard Intelligence'"] --> B["POST /api/v1/incidents/{id}/ai-intelligence"]
    B --> C["Fetch Incident Payload from DynamoDB"]
    C --> D["Sanitize Untrusted Text & Wrap in XML Tags"]
    
    subgraph Guard ["Bedrock Security Guard"]
        D --> E["Construct Grounded Prompt"]
        E --> F["Invoke Model (anthropic.claude-3-haiku)"]
    end

    F --> G{"Model Response Valid?"}
    G -- Yes --> H["Validate JSON Schema & Attach Human Disclaimer"]
    G -- No / Error --> I["Emit User-Friendly Operational Advisory Message"]
    
    H --> J["Persist Assessment to DynamoDB ('aiAnalysis')"]
    I --> J
    J --> K["Render AI Intelligence Modal in Map Inspector"]
```

---

## 6. Incident & Alert Lifecycle State Machine

```mermaid
stateDiagram-v2
    [*] --> REPORTED: Incident Created Offline/Online
    
    state OfflineQueue {
        REPORTED --> PENDING_SYNC: Enqueued in IndexedDB
        PENDING_SYNC --> SYNCING: Sync Triggered
        SYNCING --> FAILED: API 400/500 Error
        FAILED --> SYNCING: Force Sync Clicked / Retry
    }

    SYNCING --> ACTIVE_VERIFIED: Persisted to DynamoDB
    REPORTED --> ACTIVE_VERIFIED: Online Direct Submission

    state AlertLifecycle {
        [*] --> ACTIVE: Alert Dispatched
        ACTIVE --> ACKNOWLEDGED: Commander Acknowledges (UserCheck)
        ACKNOWLEDGED --> RESOLVED: Disaster Resolved (CheckCircle2)
    }

    ACTIVE_VERIFIED --> AlertLifecycle: High Risk Triggers Command Alert
    RESOLVED --> [*]
```

---

## 7. Multi-Source Historical Analytics & Data Ingestion

```mermaid
flowchart LR
    subgraph Datasets ["Ingested Historical Datasets"]
        D1["IMD 117-Year Rainfall Dataset (1901-2017)"]
        D2["NASA / Kaggle Landslide & Flood Catalog (2000-2023)"]
        D3["Road Accident Risk Vulnerability Index (2022-2025)"]
        D4["NER Emergency Resource Inventory"]
    end

    subgraph Services ["Analytics Micro-Services"]
        S1["RainfallService"]
        S2["LandslideFloodService"]
        S3["RoadAccidentService"]
        S4["EmergencyResourceService"]
    end

    subgraph UI ["Analytics & Intelligence Dashboards"]
        GIS["GIS Map Environmental Layers"]
        Dashboard["Logistics Analytics Dashboard"]
        News["Disaster News & Advisory Feed"]
    end

    D1 --> S1
    D2 --> S2
    D3 --> S3
    D4 --> S4

    S1 & S2 & S3 & S4 --> GIS
    S1 & S2 & S3 & S4 --> Dashboard
    S1 & S2 & S3 & S4 --> News
```

---

## 📁 Key File Map

| System Component | File Location | Purpose |
|---|---|---|
| **GIS Map** | [`GISMap.jsx`](file:///c:/Users/Lenovo/OneDrive/Desktop/New%20folder/frontend/src/components/GISMap.jsx) | Interactive Leaflet GIS map with incident popups & AI modals |
| **Fleet Tracker** | [`VehicleTracker.jsx`](file:///c:/Users/Lenovo/OneDrive/Desktop/New%20folder/frontend/src/components/VehicleTracker.jsx) | Live convoy telemetry tracking & diagnostic stream inspector |
| **Alert Matrix** | [`AlertCenter.jsx`](file:///c:/Users/Lenovo/OneDrive/Desktop/New%20folder/frontend/src/components/AlertCenter.jsx) | Command alerts, target fleet SOS vectors & operational advisories |
| **Field Reporter** | [`FieldReporter.jsx`](file:///c:/Users/Lenovo/OneDrive/Desktop/New%20folder/frontend/src/components/FieldReporter.jsx) | Field incident reporting form & IndexedDB offline queue manager |
| **State Context** | [`AppContext.jsx`](file:///c:/Users/Lenovo/OneDrive/Desktop/New%20folder/frontend/src/context/AppContext.jsx) | Global React context, offline sync worker & simulated telemetry polling |
| **API Client** | [`api.js`](file:///c:/Users/Lenovo/OneDrive/Desktop/New%20folder/frontend/src/services/api.js) | Frontend REST client with error sanitization & Cognito auth headers |
| **Bedrock Adapter** | [`aws_bedrock.py`](file:///c:/Users/Lenovo/OneDrive/Desktop/New%20folder/backend/app/adapters/aws_bedrock.py) | Amazon Bedrock Claude 3 Haiku adapter with prompt security controls |
| **Alert Service** | [`alert_service.py`](file:///c:/Users/Lenovo/OneDrive/Desktop/New%20folder/backend/app/services/alert_service.py) | Risk evaluation engine & persistent alert dispatch |
