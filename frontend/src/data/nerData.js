export const nerStates = [
  { id: "all", name: "All 8 NER States", lat: 26.2006, lng: 92.9376, zoom: 7 },
  { id: "assam", name: "Assam", capital: "Dispur / Guwahati", lat: 26.1433, lng: 91.7898, zoom: 8, connectivityIndex: 84 },
  { id: "arunachal", name: "Arunachal Pradesh", capital: "Itanagar", lat: 27.0844, lng: 93.6053, zoom: 8, connectivityIndex: 62 },
  { id: "meghalaya", name: "Meghalaya", capital: "Shillong", lat: 25.5788, lng: 91.8933, zoom: 9, connectivityIndex: 71 },
  { id: "nagaland", name: "Nagaland", capital: "Kohima", lat: 25.6751, lng: 94.1086, zoom: 9, connectivityIndex: 65 },
  { id: "manipur", name: "Manipur", capital: "Imphal", lat: 24.817, lng: 93.9368, zoom: 9, connectivityIndex: 58 },
  { id: "mizoram", name: "Mizoram", capital: "Aizawl", lat: 23.7271, lng: 92.7176, zoom: 9, connectivityIndex: 60 },
  { id: "tripura", name: "Tripura", capital: "Agartala", lat: 23.8315, lng: 91.2868, zoom: 9, connectivityIndex: 78 },
  { id: "sikkim", name: "Sikkim", capital: "Gangtok", lat: 27.3389, lng: 88.6065, zoom: 9, connectivityIndex: 68 }
];

export const majorCorridors = [
  {
    id: "nh-27",
    name: "NH-27 (East-West Highway Corridor)",
    route: "Siliguri ➔ Guwahati ➔ Nagaon ➔ Lumding ➔ Silchar",
    status: "caution", // clear, caution, blocked
    state: "assam",
    lengthKm: 650,
    activeAlert: "Landslide risk near Dima Hasao section (KM 184-192)",
    riskScore: 68,
    coordinates: [
      [26.7271, 88.4173], // Siliguri
      [26.1433, 91.7898], // Guwahati
      [26.3464, 92.684],  // Nagaon
      [25.7533, 93.1706], // Lumding / Haflong
      [24.8333, 92.7789]  // Silchar
    ]
  },
  {
    id: "nh-2",
    name: "NH-2 (Indo-Myanmar Trade Lifeline)",
    route: "Dimapur ➔ Kohima ➔ Imphal ➔ Moreh Border",
    status: "blocked",
    state: "manipur",
    lengthKm: 310,
    activeAlert: "Severe mudslide at Mao Gate - Highway fully blocked",
    riskScore: 92,
    coordinates: [
      [25.9068, 93.7273], // Dimapur
      [25.6751, 94.1086], // Kohima
      [25.432, 94.15],   // Mao Gate
      [24.817, 93.9368],  // Imphal
      [24.242, 94.305]   // Moreh
    ]
  },
  {
    id: "nh-10",
    name: "NH-10 (Sikkim Lifeline)",
    route: "Siliguri ➔ Sevoke ➔ Kalimpong ➔ Rangpo ➔ Gangtok",
    status: "caution",
    state: "sikkim",
    lengthKm: 120,
    activeAlert: "Teesta river erosion near Swetikhora - Single lane traffic",
    riskScore: 75,
    coordinates: [
      [26.7271, 88.4173], // Siliguri
      [26.89, 88.47],     // Sevoke
      [27.17, 88.51],     // Rangpo
      [27.3389, 88.6065]  // Gangtok
    ]
  },
  {
    id: "nh-44",
    name: "NH-44 (Tripura-Meghalaya Corridor)",
    route: "Shillong ➔ Jowai ➔ Sonapur ➔ Badarpur ➔ Agartala",
    status: "caution",
    state: "meghalaya",
    lengthKm: 440,
    activeAlert: "Sonapur Tunnel waterlogging & rockfall hazard",
    riskScore: 71,
    coordinates: [
      [25.5788, 91.8933], // Shillong
      [25.45, 92.20],     // Jowai
      [25.12, 92.38],     // Sonapur
      [24.87, 92.58],     // Badarpur
      [23.8315, 91.2868]  // Agartala
    ]
  },
  {
    id: "nh-13",
    name: "Trans-Arunachal Highway (NH-13)",
    route: "Tawang ➔ Bomdila ➔ Ziro ➔ Daporijo ➔ Pasighat",
    status: "caution",
    state: "arunachal",
    lengthKm: 820,
    activeAlert: "Sela Pass snow accumulation & dense fog warning",
    riskScore: 84,
    coordinates: [
      [27.586, 91.866],   // Tawang
      [27.264, 92.42],    // Bomdila
      [27.54, 93.83],     // Ziro
      [27.99, 94.12],     // Daporijo
      [28.06, 95.32]      // Pasighat
    ]
  },
  {
    id: "nh-54",
    name: "NH-54 (Mizoram Gateway)",
    route: "Silchar ➔ Vairengte ➔ Kolasib ➔ Aizawl ➔ Lunglei",
    status: "clear",
    state: "mizoram",
    lengthKm: 340,
    activeAlert: "Normal operational status with light rain",
    riskScore: 28,
    coordinates: [
      [24.8333, 92.7789], // Silchar
      [24.18, 92.76],     // Vairengte
      [23.97, 92.68],     // Kolasib
      [23.7271, 92.7176], // Aizawl
      [22.88, 92.73]      // Lunglei
    ]
  }
];

export const activeFleets = [
  {
    id: "NER-MED-8041",
    driver: "Tashi Norbu",
    phone: "+91 94361-XXXXX",
    category: "Medicines & Essential Drugs",
    payload: "Life-Saving Vaccines & Insulin (Cold-Chain)",
    vehicleType: "Refrigerated Truck 10T",
    origin: "Guwahati Central Depot",
    destination: "Tawang District Hospital",
    currentLocationName: "Sela Tunnel Approach (KM 112)",
    lat: 27.51,
    lng: 92.12,
    speedKm: 38,
    cargoTempC: 3.2, // Cold chain status
    tempAlert: false,
    fuelPercent: 78,
    status: "rerouting", // normal, rerouting, delayed, emergency
    eta: "4h 15m",
    delayMinutes: 35,
    state: "arunachal",
    telemetryHistory: [
      { time: "14:00", temp: 3.1, speed: 45 },
      { time: "15:00", temp: 3.2, speed: 40 },
      { time: "16:00", temp: 3.4, speed: 32 },
      { time: "17:00", temp: 3.2, speed: 38 }
    ]
  },
  {
    id: "NER-FOOD-9102",
    driver: "Bikramjit Singh",
    phone: "+91 98620-XXXXX",
    category: "Food Grains (FCI Supply)",
    payload: "18 Tonnes Fortified Rice & Pulses",
    vehicleType: "Multi-Axle Heavy Hauler",
    origin: "Silchar FCI Hub",
    destination: "Imphal West Distribution Center",
    currentLocationName: "Mao Gate Bypass Junction",
    lat: 25.432,
    lng: 94.15,
    speedKm: 34,
    cargoTempC: 24.5,
    tempAlert: false,
    fuelPercent: 62,
    status: "normal",
    eta: "5h 15m",
    delayMinutes: 0,
    state: "manipur",
    telemetryHistory: [
      { time: "14:00", temp: 24.0, speed: 45 },
      { time: "15:00", temp: 24.2, speed: 38 },
      { time: "16:00", temp: 24.5, speed: 32 },
      { time: "17:00", temp: 24.5, speed: 34 }
    ]
  },
  {
    id: "NER-OXY-3055",
    driver: "Debashish Das",
    phone: "+91 97740-XXXXX",
    category: "Liquid Medical Oxygen",
    payload: "12,000 Liters Cryogenic Oxygen",
    vehicleType: "Cryogenic Oxygen Tanker",
    origin: "Bongaigaon Refinery",
    destination: "NEIGRIHMS Shillong",
    currentLocationName: "Nongpoh Expressway (NH-27)",
    lat: 25.90,
    lng: 91.88,
    speedKm: 52,
    cargoTempC: -182.0,
    tempAlert: false,
    fuelPercent: 88,
    status: "normal",
    eta: "1h 10m",
    delayMinutes: 0,
    state: "meghalaya",
    telemetryHistory: [
      { time: "14:00", temp: -182.2, speed: 55 },
      { time: "15:00", temp: -182.1, speed: 54 },
      { time: "16:00", temp: -182.0, speed: 50 },
      { time: "17:00", temp: -182.0, speed: 52 }
    ]
  },
  {
    id: "NER-MAT-1104",
    driver: "Renedy Chingtham",
    phone: "+91 94022-XXXXX",
    category: "Bridge Construction Materials",
    payload: "Modular Bailey Bridge Steel Girders",
    vehicleType: "Heavy Equipment Carrier",
    origin: "Dimapur Logistics Yard",
    destination: "Tuensang BRO Detachment",
    currentLocationName: "Mokokchung Hill Route",
    lat: 26.32,
    lng: 94.52,
    speedKm: 28,
    cargoTempC: 22.0,
    tempAlert: false,
    fuelPercent: 54,
    status: "normal",
    eta: "6h 40m",
    delayMinutes: 15,
    state: "nagaland",
    telemetryHistory: [
      { time: "14:00", temp: 21.0, speed: 30 },
      { time: "15:00", temp: 21.5, speed: 25 },
      { time: "16:00", temp: 22.0, speed: 28 },
      { time: "17:00", temp: 22.0, speed: 28 }
    ]
  },
  {
    id: "NER-AGRI-5590",
    driver: "Lalthlamuana",
    phone: "+91 96121-XXXXX",
    category: "Horticulture & Organic Spices",
    payload: "8.5 Tonnes Export Grade Bird's Eye Chilli & Pineapple",
    vehicleType: "Insulated Cargo Van",
    origin: "Aizawl Agri Market",
    destination: "Guwahati Cargo Airport Complex",
    currentLocationName: "Kolasib Checkpost",
    lat: 23.97,
    lng: 92.68,
    speedKm: 46,
    cargoTempC: 18.5,
    tempAlert: false,
    fuelPercent: 82,
    status: "normal",
    eta: "7h 20m",
    delayMinutes: 0,
    state: "mizoram",
    telemetryHistory: [
      { time: "14:00", temp: 18.0, speed: 45 },
      { time: "15:00", temp: 18.2, speed: 48 },
      { time: "16:00", temp: 18.5, speed: 44 },
      { time: "17:00", temp: 18.5, speed: 46 }
    ]
  }
];

export const incidentMarkers = [
  {
    id: "INC-2026-081",
    title: "Major Landslide - NH-2 Mao Gate",
    type: "landslide", // landslide, flood, road_damage, bridge_out
    severity: "critical", // critical, high, medium
    state: "manipur",
    locationName: "Mao Gate (KM 142), Senapati District",
    lat: 25.432,
    lng: 94.15,
    timestamp: "Today, 08:30 AM",
    reporter: "Field Inspector K. Sharma (PWD Manipur)",
    description: "Approximately 3,500 cu.m of debris blocks both lanes. BRO heavy machinery deployed. Clearance expected in 18-24 hours.",
    photoUrl: "https://images.unsplash.com/photo-1544620347-c4fd4a3d5957?auto=format&fit=crop&w=600&q=80",
    alternateAvailable: true,
    affectedConvoys: ["NER-FOOD-9102"]
  },
  {
    id: "INC-2026-084",
    title: "Flash Flood Waterlogging - NH-10 Teesta Basin",
    type: "flood",
    severity: "high",
    state: "sikkim",
    locationName: "Swetikhora Section (KM 38)",
    lat: 26.98,
    lng: 88.48,
    timestamp: "Today, 11:15 AM",
    reporter: "Disaster Cell Sikkim",
    description: "Teesta river level rising above warning line. Heavy vehicles restricted. Light vehicles escorted via single lane.",
    photoUrl: "https://images.unsplash.com/photo-1515694346937-94d85e41e6f0?auto=format&fit=crop&w=600&q=80",
    alternateAvailable: true,
    affectedConvoys: []
  },
  {
    id: "INC-2026-089",
    title: "Bridge Approach Subsidence - Dima Hasao",
    type: "bridge_out",
    severity: "high",
    state: "assam",
    locationName: "Jatinga Bridge Approach (NH-27)",
    lat: 25.18,
    lng: 93.02,
    timestamp: "Today, 02:40 PM",
    reporter: "BRO Detachment 31",
    description: "Approach embankment eroded by flash stream. Heavy goods vehicles (>12T) diverted via Haflong bypass.",
    photoUrl: "https://images.unsplash.com/photo-1508873696983-2df515122519?auto=format&fit=crop&w=600&q=80",
    alternateAvailable: true,
    affectedConvoys: ["NER-MED-8041"]
  }
];

export const districtBuffers = [
  { district: "Tawang", state: "Arunachal Pradesh", foodDays: 4, medDays: 3, fuelDays: 5, status: "critical" },
  { district: "Tuensang", state: "Nagaland", foodDays: 6, medDays: 5, fuelDays: 4, status: "warning" },
  { district: "Ukhrul", state: "Manipur", foodDays: 3, medDays: 2, fuelDays: 3, status: "critical" },
  { district: "Lunglei", state: "Mizoram", foodDays: 12, medDays: 9, fuelDays: 11, status: "healthy" },
  { district: "South Garo Hills", state: "Meghalaya", foodDays: 7, medDays: 6, fuelDays: 5, status: "warning" },
  { district: "Mangan", state: "Sikkim", foodDays: 5, medDays: 4, fuelDays: 4, status: "warning" },
  { district: "Dhalai", state: "Tripura", foodDays: 14, medDays: 12, fuelDays: 15, status: "healthy" },
  { district: "Dima Hasao", state: "Assam", foodDays: 8, medDays: 7, fuelDays: 6, status: "healthy" }
];

export const hubLocations = [
  { name: "Guwahati Logistics Hub", state: "Assam", lat: 26.1433, lng: 91.7898 },
  { name: "Silchar Transit Center", state: "Assam", lat: 24.8333, lng: 92.7789 },
  { name: "Dimapur Railhead Depot", state: "Nagaland", lat: 25.9068, lng: 93.7273 },
  { name: "Shillong Command Center", state: "Meghalaya", lat: 25.5788, lng: 91.8933 },
  { name: "Itanagar Supply Hub", state: "Arunachal Pradesh", lat: 27.0844, lng: 93.6053 },
  { name: "Imphal Emergency Yard", state: "Manipur", lat: 24.817, lng: 93.9368 },
  { name: "Aizawl Logistics Yard", state: "Mizoram", lat: 23.7271, lng: 92.7176 },
  { name: "Agartala Multi-Modal Hub", state: "Tripura", lat: 23.8315, lng: 91.2868 },
  { name: "Gangtok Transit Depot", state: "Sikkim", lat: 27.3389, lng: 88.6065 }
];

// AI Route Generator calculation utility
export function calculateAIRoutes(originName, destName, commodityType) {
  // Mock intelligent calculation based on selected locations
  const isHighRisk = destName.includes("Tawang") || destName.includes("Imphal") || destName.includes("Gangtok");

  return {
    origin: originName,
    destination: destName,
    commodity: commodityType,
    aiRiskIndex: isHighRisk ? 78 : 34, // 0 - 100 risk score
    weatherAlert: isHighRisk ? "Heavy monsoon precipitation (85mm/24h) in mountain passes" : "Fair weather / Light drizzle",
    routes: [
      {
        id: "route-primary",
        name: "Primary Highway Corridor",
        via: "Direct National Highway",
        distanceKm: isHighRisk ? 420 : 210,
        estimatedTime: isHighRisk ? "11 hours 45 mins" : "4 hours 30 mins",
        landslideRisk: isHighRisk ? "HIGH (78% probability)" : "LOW (15% probability)",
        safetyScore: isHighRisk ? 45 : 90,
        status: isHighRisk ? "caution" : "recommended",
        roadQuality: "Paved National Highway with active hill slopes",
        delayImpact: isHighRisk ? "+ 3 hrs potential blockage" : "Minimal delay expected",
        recommendation: isHighRisk ? "NOT RECOMMENDED FOR HEAVY GOODS" : "FASTEST ROUTE FOR NORMAL CONVOYS"
      },
      {
        id: "route-ai-safe",
        name: "AI-Optimized Safe Tactical Route",
        via: "All-Weather Tunnel & Ridge Bypass",
        distanceKm: isHighRisk ? 465 : 235,
        estimatedTime: isHighRisk ? "9 hours 15 mins" : "4 hours 50 mins",
        landslideRisk: "LOW (12% probability)",
        safetyScore: 94,
        status: "recommended",
        roadQuality: "Reinforced ridge road with BRO avalanche sheds",
        delayImpact: "Zero active blockades detected",
        recommendation: "HIGHLY RECOMMENDED BY AI ENGINE (SAFEST & OPTIMAL SLA)"
      },
      {
        id: "route-emergency",
        name: "Emergency Tactical Detour",
        via: "Secondary State Highway & River Ferry Link",
        distanceKm: isHighRisk ? 510 : 280,
        estimatedTime: isHighRisk ? "14 hours 20 mins" : "6 hours 15 mins",
        landslideRisk: "VERY LOW (5% probability)",
        safetyScore: 82,
        status: "alternative",
        roadQuality: "Narrow single-lane mountain road, low speed clearance",
        delayImpact: "+ 2.5 hrs due to narrow terrain",
        recommendation: "BACKUP ROUTE IF PRIMARY CORRIDOR SEVERS COMPLETELY"
      }
    ]
  };
}
