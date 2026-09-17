# 🏗️ System Architecture — NERIS — North-East Regional Emergency Transit System

> **Project**: NERIS — North-East Regional Emergency Transit System  
> **Target Region**: `ap-south-1` (Asia Pacific - Mumbai)  
> **AWS First Commit Track**: Ship It Track  
> **Disclaimer**: NERIS is an independent student project and is not affiliated with the U.S. NERIS framework.

---

## 1. High-Level System Architecture

NERIS is designed as an event-driven, serverless logistics and emergency transit platform. The system decouples client rendering, API execution, data persistence, object storage, identity management, and artificial intelligence into dedicated cloud components.

```mermaid
flowchart TD
    subgraph SPA ["React 18 SPA (Hosted on AWS Amplify / S3 Static)"]
        GIS["Leaflet GIS Map & Layer Dock"]
        Planner["AI Route Planner"]
        FleetUI["Vehicle Telemetry Tracker"]
        ReportUI["Field Incident Reporter (IndexedDB)"]
        AlertUI["Command Alert Center & SOS Vectoring"]
    end

    subgraph API ["Amazon API Gateway + AWS Lambda Engine"]
        APIGW["Amazon API Gateway HTTP API (ap-south-1)"]
        Lambda["AWS Lambda API Engine (Python 3.11 + FastAPI + Mangum)"]
        APIGW --> Lambda
    end

    subgraph AWS ["AWS Cloud Infrastructure Services"]
        Cognito["Amazon Cognito User Pool (JWT Auth)"]
        DynamoDB[("Amazon DynamoDB - ner_incidents, ner_alerts, ner_fleet")]
        S3["Amazon S3 Bucket (neris-evidence-photos)"]
        Bedrock["Amazon Bedrock (Claude 3 Haiku)"]
        CloudWatch["Amazon CloudWatch Logs"]
    end

    SPA -->|"HTTPS / REST (Bearer Auth)"| APIGW
    Lambda --> Cognito
    Lambda --> DynamoDB
    Lambda --> S3
    Lambda --> Bedrock
    Lambda --> CloudWatch
```

---

## 2. Core Subsystem Workflows

### 2.1 Field Incident Reporting & Media Storage Workflow

```mermaid
sequenceDiagram
    autonumber
    actor Officer as "Field Officer"
    participant Auth as "Amazon Cognito Token Guard"
    participant API as "AWS Lambda API Engine"
    participant DDB as "Amazon DynamoDB (ner_incidents)"
    participant S3 as "Amazon S3 (neris-evidence-photos)"
    participant Alert as "Alert Engine (ner_alerts)"
    participant GIS as "Interactive GIS Map"

    Officer->>API: POST /api/v1/incidents (Incident Data + Photo Payload)
    API->>Auth: Validate Bearer JWT & FIELD_OFFICER Role
    Auth-->>API: Authentication Verified
    
    par Persistence & Evidence Pipeline
        API->>DDB: Save Incident Record
        API->>S3: Upload Image with AES256 SSE
        API->>Alert: Evaluate Risk & Create Command Alert
    end

    API-->>Officer: HTTP 201 Created (dynamodb_confirmed: true)
    API->>GIS: Trigger Active Hazard Marker Update
```

---

### 2.2 Amazon Bedrock AI Incident Intelligence Workflow

```mermaid
flowchart TD
    A["Command Center Dispatcher"] -->|"Clicks AI Hazard Intelligence"| B["POST /api/v1/incidents/{id}/ai-intelligence"]
    B --> C["AWS Lambda API Engine"]
    C -->|"Fetch Incident Details"| D[("Amazon DynamoDB ner_incidents Table")]
    C -->|"Construct Grounded Prompt with XML Tags"| E["Amazon Bedrock Claude 3 Haiku"]
    E -->|"Generate Structured Assessment JSON"| F["JSON Schema Validator"]
    F -->|"Persist Result to aiAnalysis Field"| D
    F -->|"200 OK Response"| G["Render AI Intelligence Modal with Disclaimer Badge"]
```

---

### 2.3 Terrain-Aware Corridor Risk Routing Workflow

```mermaid
flowchart LR
    subgraph Request ["Logistics Commander"]
        Req["POST /api/v1/routes/compute (Origin, Destination, Cargo)"]
    end

    subgraph Processing ["AWS Lambda API Engine"]
        FetchInc["Query Active Incidents from DynamoDB"]
        Graph["Load 15-Node Topological Highway Network"]
        RiskPen["Calculate Edge Risk Penalties: Base * (1 + Landslide_Sev * 1.5)"]
        Dijkstra["Solve Shortest Path & Secondary Detour via Dijkstra"]
    end

    subgraph Output ["GIS Map Rendering"]
        Map["Display Primary Route (Blue) & Alternate Detour (Orange)"]
    end

    Req --> FetchInc --> Graph --> RiskPen --> Dijkstra --> Map
```

---

### 2.4 Convoy Telemetry & Proximity Alerting Workflow

```mermaid
sequenceDiagram
    autonumber
    participant Sim as "Telemetry Simulation Worker"
    participant API as "POST /api/v1/telemetry/ping"
    participant DDB as "Amazon DynamoDB (ner_fleet)"
    participant Geo as "Geodesic Proximity Engine"
    participant UI as "Fleet Tracker UI"

    loop Every 2.5 Seconds
        Sim->>API: Send GPS Ping (Lat, Lng, Speed, Bearing, Temp)
        API->>DDB: Save Telemetry Snapshot
        API->>Geo: Calculate Haversine Distance to Active Blockades
        
        alt Distance < 25.0 km
            Geo->>DDB: Flag Vehicle Status = "ROUTE AT RISK"
            Geo-->>UI: Return Proximity Alert Warning Banner
        else Distance >= 25.0 km
            Geo-->>UI: Return 200 OK (Corridor Clear)
        end
    end
```

---

### 2.5 Offline-First Incident Queue & Idempotent Sync Workflow

```mermaid
sequenceDiagram
    autonumber
    actor Officer as "Field Officer (No Cellular Signal)"
    participant IDB as "IndexedDB (neris_offline_db)"
    participant Sync as "AppContext Sync Worker"
    participant API as "POST /api/v1/incidents/batch-sync"
    participant DDB as "Amazon DynamoDB"

    Officer->>IDB: Submit Report -> Enqueue with `localQueueId` & `operation_id`
    Note over Officer,IDB: Network Restored (online event)
    Sync->>IDB: Read Pending Items & Sanitize Payloads
    Sync->>API: Transmit Batch Payload (operation_id)
    
    API->>DDB: Check operation_id Index (Idempotency Guard)
    alt Operation ID Exists
        DDB-->>API: Duplicate Request Replayed
        API-->>Sync: Return duplicate_prevented: true
    else New Record
        API->>DDB: Write Batch Items to DynamoDB
        API-->>Sync: Return 200 OK (dynamodb_confirmed: true)
    end

    Sync->>IDB: Mark Queue Items as "SYNCED"
```

---

### 2.6 Historical Emergency Resource Allocation Intelligence Subsystem

```mermaid
flowchart LR
    subgraph Data ["Ingestion Pipeline (scripts/ingest_*.py)"]
        Kaggle["Kaggle / IMD Raw Datasets"]
        Norm["Normalization & Validation Engine"]
        Kaggle --> Norm
    end

    subgraph Storage ["Persistence"]
        S3["Amazon S3 Raw/Processed"]
        DB["Local JSON Cache & DynamoDB"]
        Norm --> S3 & DB
    end

    subgraph Service ["Micro-Services & Endpoints"]
        Svc["EmergencyResourceService / RainfallService"]
        Endpoints["/api/v1/emergency-resources/* & /api/v1/rainfall/*"]
        Svc --> Endpoints
    end

    subgraph Dashboards ["Command Dashboards"]
        GISLayer["GIS Map Layers"]
        Analytics["Analytics Dashboard Charts"]
        NewsFeed["Disaster News & Advisories"]
        Endpoints --> GISLayer & Analytics & NewsFeed
    end
```

---

## 3. Technology Stack Summary

* **Frontend**: React 18, Vite, Vanilla CSS Design System, Leaflet GIS, Recharts, IndexedDB.
* **API & Compute**: AWS Lambda (Python 3.11), Amazon API Gateway, Mangum ASGI, FastAPI.
* **Persistence & Storage**: Amazon DynamoDB, Amazon S3 (`PublicAccessBlockConfiguration` + `AES256`).
* **Authentication**: Amazon Cognito User Pools (`NerisCommandUserPool`), JWT RSA-256 validation.
* **Artificial Intelligence**: Amazon Bedrock (`anthropic.claude-3-haiku-20240307-v1:0`).
* **Observability & Scheduled Events**: Amazon CloudWatch Logs, Amazon EventBridge.
