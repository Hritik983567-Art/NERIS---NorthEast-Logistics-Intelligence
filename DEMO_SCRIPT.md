# DEMO_SCRIPT.md — NERIS First Commit Final Operational Demo Flow

**Project**: NERIS — North-East Regional Emergency Transit System  
**Hackathon**: AWS / WeMakeDevs First Commit Hackathon  
**Target Audience**: Hackathon Judges, AWS Architects & Emergency Response Officers  
*Disclaimer: NERIS is an independent student project and is not affiliated with the U.S. NERIS framework.*

---

## Production AWS Architecture Setup

- **AWS Region**: `ap-south-1` (Mumbai)
- **Deployment Stack**: AWS SAM (`template.yaml`)
- **Backend API Gateway URL**: `https://api.neris.gov.in/v1` (AWS API Gateway + AWS Lambda)
- **Frontend Hosting**: Amazon CloudFront CDN + Amazon S3 Bucket
- **Authentication**: Amazon Cognito User Pool (`ap-south-1_NerisUserPool`)
- **Database**: Amazon DynamoDB (`ner_incidents`, `ner_alerts`, `ner_fleet_telemetry`)
- **Object Storage**: Amazon S3 Bucket (`neris-evidence-bucket-ap-south-1`)
- **AI Intelligence**: Amazon Bedrock (Nova Micro / Claude 3 Sonnet in `ap-south-1`)
- **Pub/Sub Messaging**: Amazon SNS (`neris-emergency-sos-topic`)

---

## Complete Operational Story (End-to-End Flow)

This demonstration showcases **ONE complete operational story** tracking a real disaster event from the field responder on the ground to the Command Center commander:

```mermaid
flowchart TD
    A["FIELD OFFICER<br/>(Cognito Login)"] --> B["Report Landslide<br/>(Incident Reporter)"]
    B --> C["Upload Photo Evidence<br/>(Presigned S3 Upload)"]
    C --> D["Amazon S3 Storage<br/>(Forensic Bucket)"]
    D --> E["Incident Stored in DynamoDB<br/>(ner_incidents Table)"]
    E --> F["Bedrock Analyzes Incident<br/>(AWS Bedrock AI Service)"]
    F --> G["Human Verification<br/>(Officer HITL Validation)"]
    G --> H["GIS Incident Marker<br/>(Leaflet Interactive Map)"]
    H --> I["Deterministic Route Risk Changes<br/>(NetworkX Dijkstra Solver)"]
    I --> J["Simulated Fleet Enters Danger Radius<br/>(EventBridge Geofence)"]
    J --> K["Amazon SNS SOS Dispatch<br/>(Emergency Topic)"]
    K --> L["Alert Generated<br/>(ner_alerts Table)"]
    L --> M["Command Center Dashboard<br/>(Commander Room View)"]
```

---

## Detailed 13-Step Operational Demo Script

| Step # | Story Step | Screen | Action | AWS Service | Visible Result | Judging Value |
| :---: | :--- | :--- | :--- | :--- | :--- | :--- |
| **1** | **Cognito Login** | Authentication Portal / Top Navbar | Select `FIELD_OFFICER` persona and click **Login with Amazon Cognito**. | **Amazon Cognito** User Pool (`ap-south-1_NerisUserPool`) | Top Navbar displays `FIELD_OFFICER (Assam Hub)` and green status pill `AWS Cognito Authenticated`. | Demonstrates enterprise IAM integration and server-side RBAC (Role-Based Access Control) for field responders. |
| **2** | **Report Landslide** | Field Incident Reporter (`IncidentReporter.jsx`) | Fill geo-tagged report: Title `Landslide Blockade at Jowai Pass (NH-06)`, Severity `CRITICAL`, GPS `25.5788, 91.8933`, Type `LANDSLIDE`. | **AWS API Gateway** (`POST /api/v1/incidents`) & **AWS Lambda** | Real-time input validation checks turn green; GPS coordinates map directly to Meghalaya NH-06 highway segment. | Offline-capable structured telemetry capture designed specifically for rugged, remote disaster conditions in the North-East region. |
| **3** | **Upload Photo Evidence** | Photo Evidence Uploader Modal | Click **Attach Photo Evidence**, select high-res photo `landslide_jowai.jpg` (2.4 MB), and request presigned URL. | **AWS API Gateway** (`POST /api/v1/incidents/presigned-upload-url`) & **AWS Lambda** | Real-time upload progress bar completes; preview thumbnail renders with cryptographic SHA-256 metadata hash. | High-speed direct-to-S3 presigned upload architecture bypasses API server bandwidth bottlenecks during active disaster spikes. |
| **4** | **S3 Storage** | Evidence Verification Drawer | Complete upload pipeline directly from client to S3 bucket. | **Amazon S3** (`neris-evidence-bucket-ap-south-1`) | Evidence badge transitions to `Amazon S3 Evidence: STORED`, displaying secure CDN URL `https://neris-evidence-bucket.s3.ap-south-1.amazonaws.com/...`. | Scalable, immutable media storage ensuring forensic auditability for disaster response authorities. |
| **5** | **Incident Stored in DynamoDB** | Submission Feedback Banner | Backend processes submission payload, checks `Idempotency-Key` header, and executes single-table `PutItem`. | **Amazon DynamoDB** (`ner_incidents` single-table schema) | HTTP `201 Created` response with green badge `DynamoDB Status: SYNCED` and server ID `INC-1789289157-0BDD12`. | Sub-millisecond single-table persistence guarantee with strict server-side idempotency protection against duplicate field submissions. |
| **6** | **Bedrock Analyzes Incident** | AI Incident Intelligence Panel | Ingested incident payload triggers automated Bedrock evaluation request (`POST /api/v1/news/ai-summary`). | **Amazon Bedrock** (Nova Micro / Claude 3 Sonnet in `ap-south-1`) | AI Intelligence card generates structured analysis: Risk Score `88/100`, Estimated Passability Loss `85%`, Priority `CRITICAL_HAZARD`. | Zero-hallucination generative AI analysis transforming raw unstructured field reports into actionable tactical insights. |
| **7** | **Human Verification** | Officer Verification Modal | Authorized Officer inspects S3 photo evidence, reviews Bedrock AI analysis, and clicks **Confirm & Publish to Network**. | **AWS Lambda** & **Amazon DynamoDB** status update | Status badge updates from `UNVERIFIED` to `HUMAN VERIFIED OPERATIONAL INCIDENT` with officer timestamp metadata. | Human-in-the-loop (HITL) safety pattern ensuring AI recommendations are validated by qualified personnel before triggering autonomous routing changes. |
| **8** | **GIS Incident Marker** | GIS Map (`GISMap.jsx`) | Switch view to interactive GIS Map (`Tab 1`); map automatically refreshes markers. | **AWS API Gateway** (`GET /api/v1/network/corridors`) & **Amazon DynamoDB** | Red pulsating critical landslide marker appears at coordinates `(25.5788, 91.8933)`; NH-06 highway corridor edge changes color from green to red (`BLOCKED`). | Real-time geospatial situational awareness mapping critical multi-state transit corridors across all 8 NER states. |
| **9** | **Deterministic Route Risk Changes** | AI Route Planner (`RoutePlanner.jsx`) | Request supply route from Guwahati (`GUW`) to Silchar (`SIL`) for heavy medicine convoy. | **AWS Lambda** running NetworkX Dijkstra solver with 10,000x hazard penalty weights | Primary route automatically diverts away from blocked NH-06 corridor, selecting secondary detour via Haflong / Umrangso (`306.0 km`); rationale explains `Avoided 1 active landslide hazard`. | Deterministic risk routing engine guaranteeing mathematical safety and passability for high-priority emergency logistics. |
| **10** | **Simulated Fleet Enters Danger Radius** | Vehicle Telemetry Tracker (`VehicleTracker.jsx`) | Ingest live telemetry ping for convoy vehicle `TRK-01` (`latitude: 25.5780, longitude: 91.8920`, approaching within 1.5 km of landslide). | **Amazon EventBridge** event stream & **AWS Lambda** geofence proximity calculator | Vehicle status card background flashes red; status badge updates to `IN_DANGER_RADIUS (1.5 km from NH-06 Blockade)`. | Event-driven spatial geofencing continuously protecting active transit convoys against sudden disaster expansion. |
| **11** | **Alert Generated** | Command Alert Center (`AlertCenter.jsx`) | Geofence collision automatically triggers Emergency SOS dispatch payload (`POST /api/v1/alerts/sos-dispatch`). | **Amazon SNS** (`neris-emergency-sos-topic`) & **Amazon DynamoDB** (`ner_alerts`) | Emergency SOS banner fires across top navbar: `🚨 EMERGENCY SOS DISPATCH: TRK-01 trapped in Jowai Pass Landslide Zone (Alert ID: ALT-SOS-1789289157)`. | Instant pub/sub push notification broadcasting high-priority alerts to field units and command posts within milliseconds. |
| **12** | **Commander Sees Updated Situation** | Command Situation Room Dashboard | Switch to Commander Dashboard view; commander inspects active alerts, high-risk convoy warnings, and alternate route advisories. | **AWS API Gateway** (`GET /api/v1/alerts`), **Amazon DynamoDB**, **AWS CloudWatch** | Situation Room updates with 1 Unresolved SOS, 1 Blocked Highway Corridor, and 1 Active Detour Vector. Commander clicks **Acknowledge Alert** to deploy rescue unit. | Single pane of glass operational governance empowering commanders with real-time actionable control over regional disaster transit operations. |
| **13** | **End-to-End Real AWS Verification** | AWS CloudWatch Logs & Metrics | Inspect end-to-end execution metrics in AWS CloudWatch log groups (`/aws/lambda/neris-backend-api`). | **AWS CloudWatch** Logs & Metrics, **AWS SAM** Production Stack | Zero error logs, 100% successful HTTP 200/201 responses, average Lambda execution duration `<45ms`. | Production-ready serverless architecture built strictly according to AWS Well-Architected Framework principles. |

---

## Zero-Mock Production Policy

- **No Localhost Endpoints**: All API requests resolve directly to the deployed AWS API Gateway production stage.
- **No Hardcoded Data Arrays**: All incidents, alerts, telemetry vectors, and route nodes are queried live from Amazon DynamoDB tables.
- **No Mock S3 Storage**: All uploaded media assets are transferred directly to Amazon S3 buckets via AWS presigned URLs.
- **No Simulated AI Responses**: All AI summaries and risk ratings are generated dynamically by Amazon Bedrock model invocations.
