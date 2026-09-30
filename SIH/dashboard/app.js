/**
 * UnLost — Primary Navigation Product & Engineering Dashboard Logic
 * Pure Vanilla JavaScript — Zero build step, zero CORS risk.
 *
 * Primary Product Flow:
 *   1. Destination Selection (Pune, Maharashtra, India)
 *   2. Route Preview (18 min, 8.6 km, Arrive 5:42 PM)
 *   3. Live Navigation Simulation:
 *      - Moving 3D Navigation Arrow with directional rotation & camera tracking
 *      - Live HUD turn-by-turn guidance and dynamic dock countdowns
 *      - Real-time GNSS outage handoff (NAVIGATING WITHOUT GPS)
 *      - Dead-reckoning continuation and GNSS recovery
 *      - Clean destination arrival
 *
 * Secondary Tabs:
 *   - System Evidence: Preserves all Phase 1–3 engineering calculations & canvases
 *   - Diagnostics: Verified hardware rates & Rodrigues alignment matrix
 */
(function () {
  'use strict';
  // ============================================================================
  // 1. PROTOTYPE PUNE ROUTES CONFIGURATION (REAL PUNE OSM ROAD CORRIDORS)
  // ============================================================================
  const PUNE_ROUTES = {
    'pune-airport': {
      id: 'pune-airport',
      name: 'Pune Airport',
      departure: 'Pune',
      corridor: 'Shivajinagar via Sangamwadi & Nagar Road Corridor',
      distKm: 8.6,
      durationMin: 11,
      arrivalDeterministic: '5:42 PM',
      datasetSource: 'S-Vta1a',
      arrivalName: 'Pune Airport Terminal 1',
      roadWaypoints: [
        [18.5314, 73.8446], // Shivajinagar Junction / Sancheti Chowk
        [18.5328, 73.8505], // Sancheti Flyover ramp onto Sangamwadi Rd
        [18.5358, 73.8585], // Sangamwadi Road corridor along Mula River
        [18.5390, 73.8680], // Sangamwadi BRTS corridor
        [18.5435, 73.8765], // Mula River Bridge crossing
        [18.5490, 73.8825], // Yerwada Parnakuti junction
        [18.5528, 73.8872], // Pune-Ahmednagar (Nagar) Road
        [18.5558, 73.8950], // Nagar Road Yerwada section
        [18.5585, 73.9018], // Gunjan Chowk (Turn onto Airport Road)
        [18.5632, 73.9068], // Airport Road, Tingre Nagar
        [18.5690, 73.9115], // Airport Road past Commerzone IT Park
        [18.5745, 73.9160], // Lohegaon Concourse loop approach
        [18.5804, 73.9200]  // Pune Airport Terminal 1 Departure
      ],
      sectors: [
        {
          title: 'Sector 1: Departure via Sancheti Flyover & Sangamwadi Rd',
          desc: 'Open-sky multi-constellation GNSS lock active. Inertial baseline steady.'
        },
        {
          title: 'Sector 2: Nagar Road Underpass Corridor (GNSS Outage Demo)',
          desc: 'Test seamless transition to inertial dead reckoning via SIMULATE GNSS OUTAGE.'
        },
        {
          title: 'Sector 3: Airport Road Approach & Terminal 1 Loop',
          desc: 'Satellite signal reacquisition and multi-sensor fusion re-engagement.'
        }
      ],
      instructionCues: [
        { pct: 0.00, dist: 'In 400m', title: 'Keep right on Sancheti Hospital Flyover', sub: 'Pune Airport Corridor · Continuous Inertial Monitoring Active', icon: '⬆' },
        { pct: 0.16, dist: 'In 800m', title: 'Continue onto Sangamwadi Road', sub: 'Mula-Mutha River Overpass · Ground Truth Reference Active', icon: '↗' },
        { pct: 0.35, dist: 'In 500m', title: 'Merge onto Nagar Road Arterial Corridor', sub: 'Approaching Underpass Sector · Inertial Alignment Checked', icon: '⬆' },
        { pct: 0.52, dist: 'In 1.1km', title: 'Continue straight through Nagar Road Underpass', sub: 'NAVIGATING WITHOUT GPS Zone · Dead Reckoning Active', icon: '⬆' },
        { pct: 0.72, dist: 'In 600m', title: 'Turn left onto Airport Road at Gunjan Chowk', sub: 'GNSS Signal Reacquired · Multi-sensor fusion locked', icon: '↰' },
        { pct: 0.88, dist: 'In 250m', title: 'Keep right towards Departure Terminal 1 Loop', sub: 'Approaching Lohegaon Airport Concourse', icon: '↗' },
        { pct: 0.98, dist: 'Arrived', title: 'You have arrived at Pune Airport', sub: 'Terminal 1 Departures · Trip Completed', icon: '🏁' }
      ]
    },
    'viman-nagar': {
      id: 'viman-nagar',
      name: 'Viman Nagar',
      departure: 'Pune',
      corridor: 'FC Road via Bund Garden & Koregaon Park North',
      distKm: 9.2,
      durationMin: 12,
      arrivalDeterministic: '5:50 PM',
      datasetSource: 'S-Vta2',
      arrivalName: 'Viman Nagar Symbiosis Hub',
      roadWaypoints: [
        [18.5240, 73.8415], // FC Road, Shivajinagar
        [18.5290, 73.8440], // FC Road to Modern College
        [18.5315, 73.8550], // Sancheti / COEP / Sangam Bridge
        [18.5300, 73.8680], // Sassoon Road past station
        [18.5365, 73.8820], // Bund Garden Road
        [18.5410, 73.8910], // Bund Garden Bridge over Mula-Mutha
        [18.5460, 73.8990], // Koregaon Park North Main Road
        [18.5520, 73.9060], // Central Avenue, Kalyani Nagar
        [18.5580, 73.9110], // Nagar Road arterial cross
        [18.5640, 73.9135], // Symbiosis Road
        [18.5679, 73.9143]  // Viman Nagar Symbiosis Hub
      ],
      sectors: [
        {
          title: 'Sector 1: FC Road onto Bund Garden Bridge',
          desc: 'Dense urban boulevard with elevated metro overhead.'
        },
        {
          title: 'Sector 2: Koregaon Park North Cutoff (GNSS Outage Demo)',
          desc: 'Tree canopy and rail underbridge GNSS denial simulation.'
        },
        {
          title: 'Sector 3: Symbiosis Road Approach',
          desc: 'Full GNSS reacquisition and route completion.'
        }
      ],
      instructionCues: [
        { pct: 0.00, dist: 'In 350m', title: 'Head east on Fergusson College Road', sub: 'Urban arterial corridor · Inertial alignment locked', icon: '⬆' },
        { pct: 0.22, dist: 'In 750m', title: 'Cross Bund Garden Bridge over Mula-Mutha', sub: 'Open sky satellite tracking active', icon: '↗' },
        { pct: 0.45, dist: 'In 400m', title: 'Pass Koregaon Park North Underpass', sub: 'Outage sector test · Dead reckoning propagation', icon: '⬆' },
        { pct: 0.75, dist: 'In 550m', title: 'Turn right onto Symbiosis Road', sub: 'Viman Nagar IT Corridor', icon: '↱' },
        { pct: 0.98, dist: 'Arrived', title: 'You have arrived at Viman Nagar Hub', sub: 'Destination reached successfully', icon: '🏁' }
      ]
    },
    'pune-station': {
      id: 'pune-station',
      name: 'Pune Railway Station',
      departure: 'Pune',
      corridor: 'Shivajinagar via Sangam Bridge & Sassoon Rd',
      distKm: 4.2,
      durationMin: 6,
      arrivalDeterministic: '5:38 PM',
      datasetSource: 'S-Vta1a',
      arrivalName: 'Pune Central Railway Station',
      roadWaypoints: [
        [18.5314, 73.8446], // Shivajinagar Central
        [18.5325, 73.8510], // Sancheti Chowk
        [18.5305, 73.8580], // COEP Flyover
        [18.5295, 73.8640], // Sangam Bridge Overpass
        [18.5270, 73.8695], // Sassoon Hospital Road
        [18.5284, 73.8744]  // Pune Central Railway Station Platform 1
      ],
      sectors: [
        {
          title: 'Sector 1: Shivajinagar Court Flyover Approach',
          desc: 'Arterial bridge transition with open sky tracking.'
        },
        {
          title: 'Sector 2: Sangam Bridge Rail Underpass (GNSS Outage Demo)',
          desc: 'Multi-track overhead steel bridge GNSS blockage simulation.'
        },
        {
          title: 'Sector 3: Station Drop-Off Concourse',
          desc: 'Recovery and final passenger drop-off approach.'
        }
      ],
      instructionCues: [
        { pct: 0.00, dist: 'In 250m', title: 'Depart Shivajinagar Court Road', sub: 'Heading towards Sangam Bridge', icon: '⬆' },
        { pct: 0.30, dist: 'In 500m', title: 'Cross Sangam Bridge Rail Overpass', sub: 'Rail infrastructure corridor', icon: '↗' },
        { pct: 0.60, dist: 'In 300m', title: 'Enter Sassoon Hospital Road Underpass', sub: 'Outage sector · Dead reckoning active', icon: '⬆' },
        { pct: 0.85, dist: 'In 200m', title: 'Turn left into Railway Station Concourse', sub: 'Main Passenger Drop-Off', icon: '↰' },
        { pct: 0.98, dist: 'Arrived', title: 'You have arrived at Pune Railway Station', sub: 'Platform 1 Portico · Trip Complete', icon: '🏁' }
      ]
    },
    'shivajinagar': {
      id: 'shivajinagar',
      name: 'Shivajinagar',
      departure: 'Pune',
      corridor: 'FC Road / JM Road Transit Corridor',
      distKm: 3.8,
      durationMin: 5,
      arrivalDeterministic: '5:36 PM',
      datasetSource: 'S-Vta1a',
      arrivalName: 'Shivajinagar Central Hub',
      roadWaypoints: [
        [18.5205, 73.8400], // FC Road Goodluck Chowk
        [18.5245, 73.8420], // FC Road Dnyaneshwar Paduka Chowk
        [18.5285, 73.8465], // Modern College Rd onto JM Road
        [18.5305, 73.8460], // Balgandharva Ranga Mandir, JM Road
        [18.5314, 73.8446]  // Shivajinagar Central Hub
      ],
      sectors: [
        {
          title: 'Sector 1: FC Road Arterial Corridor',
          desc: 'Dense commercial link with high GNSS satellite visibility.'
        },
        {
          title: 'Sector 2: Metro Viaduct Underpass (GNSS Outage Demo)',
          desc: 'Elevated transit overhead structure GNSS denial simulation.'
        },
        {
          title: 'Sector 3: Shivajinagar Terminal Approach',
          desc: 'Satellite signal reacquisition and final terminal arrival.'
        }
      ],
      instructionCues: [
        { pct: 0.00, dist: 'In 300m', title: 'Head north on Fergusson College Road', sub: 'Shivajinagar Corridor · Inertial Monitoring Active', icon: '⬆' },
        { pct: 0.30, dist: 'In 600m', title: 'Turn right onto Jangali Maharaj Road', sub: 'Approaching Transit Link', icon: '↗' },
        { pct: 0.60, dist: 'In 400m', title: 'Pass beneath Metro Viaduct Underpass', sub: 'NAVIGATING WITHOUT GPS Zone', icon: '⬆' },
        { pct: 0.85, dist: 'In 250m', title: 'Turn left into Shivajinagar Hub', sub: 'GNSS Signal Reacquired', icon: '↰' },
        { pct: 0.98, dist: 'Arrived', title: 'You have arrived at Shivajinagar', sub: 'Central Terminal · Trip Complete', icon: '🏁' }
      ]
    },
    'hinjawadi': {
      id: 'hinjawadi',
      name: 'Hinjawadi Phase 1',
      departure: 'Pune',
      corridor: 'Pune University Circle via Aundh & Wakad',
      distKm: 17.4,
      durationMin: 21,
      arrivalDeterministic: '6:06 PM',
      datasetSource: 'S-Vta2',
      arrivalName: 'Hinjawadi Phase 1 Campus',
      roadWaypoints: [
        [18.5314, 73.8446], // Shivajinagar
        [18.5365, 73.8370], // Ganeshkhind Road
        [18.5450, 73.8290], // Pune University Circle
        [18.5580, 73.8110], // Aundh Road
        [18.5645, 73.8050], // Bremen Chowk, Aundh
        [18.5710, 73.7930], // Rajiv Gandhi Bridge over Mula River
        [18.5830, 73.7680], // Wakad Bypass Flyover
        [18.5910, 73.7490], // Hinjawadi Flyover onto Phase 1 Spine
        [18.5913, 73.7389]  // Hinjawadi IT Park Phase 1 Circle
      ],
      sectors: [
        {
          title: 'Sector 1: University Circle onto Aundh Road',
          desc: 'Multi-lane arterial link with high satellite visibility.'
        },
        {
          title: 'Sector 2: Wakad Expressway Underpass (GNSS Outage Demo)',
          desc: 'Grade-separated interchange GNSS shadowing demonstration.'
        },
        {
          title: 'Sector 3: Rajiv Gandhi Infotech Park Phase 1 Loop',
          desc: 'Dead reckoning handoff back to dual-frequency GNSS.'
        }
      ],
      instructionCues: [
        { pct: 0.00, dist: 'In 600m', title: 'Take second exit at University Circle onto Aundh Rd', sub: 'West Pune Expressway link', icon: '⟳' },
        { pct: 0.35, dist: 'In 1.5km', title: 'Continue on Wakad Bypass Flyover', sub: 'High-speed corridor (~70 km/h)', icon: '⬆' },
        { pct: 0.65, dist: 'In 400m', title: 'Pass through Wakad Expressway Tunnel', sub: 'NAVIGATING WITHOUT GPS Zone', icon: '⬆' },
        { pct: 0.85, dist: 'In 800m', title: 'Merge onto Hinjawadi Phase 1 Spine Road', sub: 'Tech campus perimeter', icon: '↗' },
        { pct: 0.98, dist: 'Arrived', title: 'You have arrived at Hinjawadi IT Park', sub: 'Phase 1 Hub · Trip Complete', icon: '🏁' }
      ]
    },
    'wakad': {
      id: 'wakad',
      name: 'Wakad',
      departure: 'Pune',
      corridor: 'Pune University Circle via Aundh',
      distKm: 15.2,
      durationMin: 19,
      arrivalDeterministic: '6:15 PM',
      datasetSource: 'S-Vta2',
      arrivalName: 'Wakad Junction',
      roadWaypoints: [
        [18.5314, 73.8446],
        [18.5365, 73.8370], // Ganeshkhind Road
        [18.5450, 73.8290], // Pune University Circle
        [18.5580, 73.8110], // Aundh Road
        [18.5645, 73.8050], // Bremen Chowk, Aundh
        [18.5710, 73.7930], // Rajiv Gandhi Bridge
        [18.5830, 73.7680], // Wakad Bypass
        [18.5990, 73.7620]
      ],
      sectors: [{title: 'Sector 1: University Circle onto Aundh Road', desc: 'Arterial link.'}, {title: 'Sector 2: Aundh to Wakad Corridor', desc: 'High-speed corridor.'}],
      instructionCues: [
        { pct: 0.00, dist: 'In 600m', title: 'Take Aundh Rd', sub: 'West Pune link', icon: '?' },
        { pct: 0.98, dist: 'Arrived', title: 'You have arrived at Wakad', sub: 'Trip Complete', icon: '??' }
      ]
    }
  };
  // Pre-configured road corridors for typed Pune search queries
  const PUNE_TYPED_PRESETS = {
    'kothrud': {
      name: 'Kothrud (Chandani Chowk)',
      corridor: 'From Shivajinagar via FC Road & Karve Road Arterial',
      distKm: 6.8,
      durationMin: 9,
      arrivalName: 'Kothrud Chandani Chowk',
      roadWaypoints: [
        [18.5314, 73.8446],
        [18.5255, 73.8415],
        [18.5180, 73.8370],
        [18.5120, 73.8260],
        [18.5074, 73.8077]
      ]
    },
    'hadapsar': {
      name: 'Hadapsar (Magarpatta City)',
      corridor: 'From Shivajinagar via Pune Station & Solapur Road',
      distKm: 10.4,
      durationMin: 13,
      arrivalName: 'Magarpatta Cybercity Hub',
      roadWaypoints: [
        [18.5314, 73.8446],
        [18.5300, 73.8680],
        [18.5200, 73.8850],
        [18.5130, 73.9100],
        [18.5089, 73.9259]
      ]
    },
    'mumbai': {
      name: 'Mumbai Expressway Corridor',
      corridor: 'From Shivajinagar via Old Pune-Mumbai Highway',
      distKm: 22.0,
      durationMin: 27,
      arrivalName: 'Dehu Road Expressway Toll Plaza',
      roadWaypoints: [
        [18.5314, 73.8446],
        [18.5450, 73.8290], // Pune University Circle
        [18.5600, 73.8090],
        [18.5950, 73.7650],
        [18.6350, 73.7200],
        [18.6750, 73.6800]
      ]
    },
    'swargate': {
      name: 'Swargate Bus Terminal',
      corridor: 'From Shivajinagar via Shivaji Road / Bajirao Road',
      distKm: 4.8,
      durationMin: 6,
      arrivalName: 'Swargate Central Bus Station',
      roadWaypoints: [
        [18.5314, 73.8446],
        [18.5260, 73.8510],
        [18.5180, 73.8550],
        [18.5090, 73.8590],
        [18.5018, 73.8636]
      ]
    },
    'baner': {
      name: 'Baner High Street',
      corridor: 'From Shivajinagar via University Road & Baner Road',
      distKm: 9.6,
      durationMin: 12,
      arrivalName: 'Baner High Street Commercial Hub',
      roadWaypoints: [
        [18.5314, 73.8446],
        [18.5365, 73.8370],
        [18.5450, 73.8290],
        [18.5520, 73.8150],
        [18.5590, 73.7868]
      ]
    }
  };
  // ============================================================================
  // GEODESY & DENSE ROAD PATH INTERPOLATION
  // ============================================================================
  function haversineM(lat1, lon1, lat2, lon2) {
    const R = 6371000;
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const a = Math.sin(dLat / 2) ** 2 +
              Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
              Math.sin(dLon / 2) ** 2;
    return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  }
  function bearingDeg(lat1, lon1, lat2, lon2) {
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const y = Math.sin(dLon) * Math.cos(lat2 * Math.PI / 180);
    const x = Math.cos(lat1 * Math.PI / 180) * Math.sin(lat2 * Math.PI / 180) -
              Math.sin(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * Math.cos(dLon);
    return (Math.atan2(y, x) * 180 / Math.PI + 360) % 360;
  }
  function generateDenseRoute(waypoints, totalPoints) {
    // ENFORCING OSM PBF HARD RULE:
    // The AI must NEVER create, interpolate, invent, or hallucinate road geometry.
    // We strictly use the authoritative OSM nodes provided by the routing engine.
    if (!waypoints || waypoints.length < 2) return [];
    const strictRoute = [];
    for (let i = 0; i < waypoints.length; i++) {
      const p1 = waypoints[i];
      const p2 = waypoints[Math.min(i + 1, waypoints.length - 1)];
      let hdg = 0;
      if (i < waypoints.length - 1) {
        hdg = bearingDeg(p1[0], p1[1], p2[0], p2[1]);
      } else {
        hdg = bearingDeg(waypoints[i - 1][0], waypoints[i - 1][1], p1[0], p1[1]);
      }
      // ONLY push exact, existing OSM coordinates. No arbitrary geometric interpolation.
      strictRoute.push({ lat: p1[0], lng: p1[1], heading: hdg });
    }
    return strictRoute;
  }
  // ============================================================================
  // 2. GLOBAL APPLICATION STATE
  // ============================================================================
  const state = {
    activeTab: 'navigation', // 'navigation' | 'evidence' | 'diagnostics'
    dataset: 'S-Vta1a',
    scaleMode: 'full', // 'full' or 'zoom'
    layers: {
      gt: true,
      p2: true,
      p3: true
    },
    gnssOutage: false,
    hoveredIndex: -1,
    toastTimer: null
  };
  // Product Navigation State
  const navState = {
    currentRouteId: 'pune-airport',
    flowStep: 'destination', // 'destination' | 'preview' | 'navigating'
    index: 0,
    isPlaying: false,
    playbackSpeed: 1,
    playTimer: null,
    outageStartIdx: -1,
    isArrived: false,
    userInteracting: false
  };
  let dbData = null;
  // Leaflet map instance and managed layer references
  let leafletMap = null;
  let mapInitialized = false;
  let currentDenseRoute = [];
  let currentDenseCoords = [];
  let routeCasingLayer = null;
  let routeAheadLayer = null;
  let previewOutageLayer = null;
  let routePastLayer = null;
  let outageSegments = [];
  let vehicleMarker = null;
  let startMarker = null;
  let destMarker = null;
  let currentLocMarker = null;
  // ============================================================================
  // 3. CACHED DOM ELEMENTS
  // ============================================================================
  const dom = {
    // App View Switcher
    viewNavigation: document.getElementById('view-navigation'),
    viewEvidence: document.getElementById('view-evidence'),
    viewDiagnostics: document.getElementById('view-diagnostics'),
    tabNavBtn: document.getElementById('tab-nav-btn'),
    tabEvidenceBtn: document.getElementById('tab-evidence-btn'),
    tabDiagnosticsBtn: document.getElementById('tab-diagnostics-btn'),
    // Top Navigation Controls
    gnssBadge: document.getElementById('gnss-status-badge'),
    gnssStatusText: document.getElementById('gnss-status-text'),
    btnQuickOutage: document.getElementById('btn-quick-outage'),
    quickOutageText: document.getElementById('quick-outage-text'),
    // Alert Toast
    toast: document.getElementById('gnss-alert-toast'),
    toastIcon: document.getElementById('toast-icon'),
    toastTitle: document.getElementById('toast-title'),
    toastDesc: document.getElementById('toast-desc'),
    // Primary Navigation Screen Elements
    currentLocationText: document.getElementById('current-location-text'),
    stepBtnDest: document.getElementById('step-btn-dest'),
    stepBtnPreview: document.getElementById('step-btn-preview'),
    stepBtnNav: document.getElementById('step-btn-nav'),
    navOsmMap: document.getElementById('nav-osm-map'),
    navMapViewport: document.getElementById('nav-map-viewport'),
    // Flow Overlays
    flowViewDest: document.getElementById('flow-view-destination'),
    flowViewPreview: document.getElementById('flow-view-preview'),
    // Destination Cards & Search
    destSearchInput: document.getElementById('destination-search-input'),
    btnSearchGo: document.getElementById('btn-search-go'),
    destCardAirport: document.getElementById('dest-card-pune-airport'),
    destCardViman: document.getElementById('dest-card-viman-nagar'),
    destCardStation: document.getElementById('dest-card-pune-station'),
    destCardShivajinagar: document.getElementById('dest-card-shivajinagar'),
    destCardHinjawadi: document.getElementById('dest-card-hinjawadi'),
    destCardWakad: document.getElementById('dest-card-wakad'),
    // Preview Elements
    // Preview Elements
    previewRouteOrigin: document.getElementById('preview-route-origin'),
    previewRouteDest: document.getElementById('preview-route-dest'),
    previewDistVal: document.getElementById('preview-dist-val'),
    previewTimeVal: document.getElementById('preview-time-val'),
    previewArrivalVal: document.getElementById('preview-arrival-val'),
    previewSector1Title: document.getElementById('preview-sector-1-title'),
    previewSector1Desc: document.getElementById('preview-sector-1-desc'),
    previewSector2Title: document.getElementById('preview-sector-2-title'),
    previewSector2Desc: document.getElementById('preview-sector-2-desc'),
    previewSector3Title: document.getElementById('preview-sector-3-title'),
    previewSector3Desc: document.getElementById('preview-sector-3-desc'),
    // Live HUD Overlays
    navInstructionCard: document.getElementById('nav-instruction-card'),
    instructionIcon: document.getElementById('instruction-icon'),
    instructionDist: document.getElementById('instruction-dist'),
    instructionTitle: document.getElementById('instruction-title'),
    instructionSub: document.getElementById('instruction-sub'),
    compassArrowWrap: document.getElementById('compass-arrow-wrap'),
    compassBearingReadout: document.getElementById('compass-bearing-readout'),
    speedControlPanel: document.getElementById('speed-control-panel'),
    btnSpeed1: document.getElementById('btn-speed-1'),
    btnSpeed15: document.getElementById('btn-speed-15'),
    btnSpeed2: document.getElementById('btn-speed-2'),
    navBottomCard: document.getElementById('nav-bottom-card'),
    dockTimeRemaining: document.getElementById('dock-time-remaining'),
    dockDistRemaining: document.getElementById('dock-dist-remaining'),
    dockArriveTime: document.getElementById('dock-arrive-time'),
    dockCurrentTime: document.getElementById('dock-current-time'),
    dockDistTravelled: document.getElementById('dock-dist-travelled'),
    navSpeedDisplay: document.getElementById('nav-speed-display'),
    hudModeDot: document.getElementById('hud-mode-dot'),
    hudModeTitle: document.getElementById('hud-mode-title'),
    hudOutageAlert: document.getElementById('hud-outage-alert'),
    btnDockOutage: document.getElementById('btn-dock-outage'),
    dockOutageText: document.getElementById('dock-outage-text'),
    // Destination Reached Card
    navArrivalCard: document.getElementById('nav-arrival-card'),
    arrivalTitle: document.getElementById('arrival-title'),
    arrivalDesc: document.getElementById('arrival-desc'),
    // System Evidence Elements (Preserved)
    btnVta1a: document.getElementById('btn-vta1a'),
    btnVta2: document.getElementById('btn-vta2'),
    heroDatasetName: document.getElementById('hero-dataset-name'),
    heroDatasetDesc: document.getElementById('hero-dataset-desc'),
    valDistance: document.getElementById('val-distance'),
    valDuration: document.getElementById('val-duration'),
    valSamples: document.getElementById('val-samples'),
    valPeakSpeed: document.getElementById('val-peak-speed'),
    valMeanSpeed: document.getElementById('val-mean-speed'),
    valDriftPct: document.getElementById('val-drift-pct'),
    captionDist: document.getElementById('caption-dist'),
    captionErr: document.getElementById('caption-err'),
    captionTime: document.getElementById('caption-time'),
    p2FinalErr: document.getElementById('p2-final-err'),
    p2Rmse: document.getElementById('p2-rmse'),
    p2Drift: document.getElementById('p2-drift'),
    p3FinalErr: document.getElementById('p3-final-err'),
    p3Rmse: document.getElementById('p3-rmse'),
    p3Drift: document.getElementById('p3-drift'),
    valDelta: document.getElementById('val-delta'),
    valRoll: document.getElementById('val-roll'),
    valPitch: document.getElementById('val-pitch'),
    btnScaleFull: document.getElementById('btn-scale-full'),
    btnScaleZoom: document.getElementById('btn-scale-zoom'),
    canvasTrajectory: document.getElementById('trajectory-canvas'),
    canvasDrift: document.getElementById('drift-canvas'),
    tooltip: document.getElementById('canvas-tooltip')
  };
  // ============================================================================
  // 4. INITIALIZATION & DATA RESOLUTION
  // ============================================================================
  function init() {
    if (window.IDR_DATA) {
      dbData = window.IDR_DATA;
      setupApplication();
    } else {
      fetch('data/dashboard_data.json')
        .then((res) => res.json())
        .then((data) => {
          dbData = data;
          setupApplication();
        })
        .catch((err) => {
          console.error('Failed to load dashboard data JSON:', err);
        });
    }
    // Resize handling: Leaflet map & Evidence canvases
    window.addEventListener('resize', debounce(() => {
      if (state.activeTab === 'navigation') {
        if (leafletMap) leafletMap.invalidateSize();
      } else if (state.activeTab === 'evidence') {
        renderTrajectory();
        renderDriftChart();
      }
    }, 150));
    setupCanvasHover();
    setupNavLinks();
  }
  /**
   * Setup Navigation Link Scroll Observer
   */
  function setupNavLinks() {
    const navLinks = document.querySelectorAll('.nav-link');
    const sections = Array.from(navLinks).map(link => {
      const id = link.getAttribute('href').substring(1);
      return document.getElementById(id);
    }).filter(Boolean);
    const observer = new IntersectionObserver((entries) => {
      let activeSectionId = null;
      
      // Find the most visible intersecting section
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          activeSectionId = entry.target.id;
        }
      });
      if (activeSectionId) {
        navLinks.forEach(link => {
          if (link.getAttribute('href') === `#${activeSectionId}`) {
            link.classList.add('active');
          } else {
            link.classList.remove('active');
          }
        });
      }
    }, {
      rootMargin: '-20% 0px -60% 0px',
      threshold: 0
    });
    sections.forEach(section => observer.observe(section));
    // Also keep the click listener for immediate feedback and smooth scroll
    navLinks.forEach(link => {
      link.addEventListener('click', (e) => {
        e.preventDefault();
        navLinks.forEach(nav => nav.classList.remove('active'));
        link.classList.add('active');
        const targetId = link.getAttribute('href').substring(1);
        const targetEl = document.getElementById(targetId);
        if (targetEl) {
          targetEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
      });
    });
  }
  async function setupApplication() {
    // 1. Navigation is the primary default experience
    switchAppTab('navigation');
    initMap();
    await selectPuneRoute('pune-airport', true);
    setFlowStep('destination');
    // Attach search keydown listener
    const searchInput = document.getElementById('destination-search-input');
    if (searchInput) {
      searchInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
          submitDestinationSearch();
        }
      });
    }
    // Global resize listener for responsive full-screen map
    window.addEventListener('resize', () => {
      if (leafletMap && state.activeTab === 'navigation') {
        leafletMap.invalidateSize();
      }
    });
    // 2. Prepare System Evidence data
    updateMetricsUI();
    renderTrajectory();
    renderDriftChart();
  }
  // ============================================================================
  // 5. APPLICATION TAB SWITCHER (Navigation | System Evidence | Diagnostics)
  // ============================================================================
  window.switchAppTab = function (tabName) {
    state.activeTab = tabName;
    document.body.className = 'tab-' + tabName;
    // Manage tab buttons
    if (dom.tabNavBtn) dom.tabNavBtn.classList.toggle('active', tabName === 'navigation');
    if (dom.tabEvidenceBtn) dom.tabEvidenceBtn.classList.toggle('active', tabName === 'evidence');
    if (dom.tabDiagnosticsBtn) dom.tabDiagnosticsBtn.classList.toggle('active', tabName === 'diagnostics');
    // Manage views
    if (dom.viewNavigation) {
      dom.viewNavigation.classList.toggle('hidden', tabName !== 'navigation');
      dom.viewNavigation.classList.toggle('active', tabName === 'navigation');
    }
    if (dom.viewEvidence) {
      dom.viewEvidence.classList.toggle('hidden', tabName !== 'evidence');
      dom.viewEvidence.classList.toggle('active', tabName === 'evidence');
    }
    if (dom.viewDiagnostics) {
      dom.viewDiagnostics.classList.toggle('hidden', tabName !== 'diagnostics');
      dom.viewDiagnostics.classList.toggle('active', tabName === 'diagnostics');
    }
    // Re-render active view
    if (tabName === 'navigation') {
      setTimeout(() => {
        if (!mapInitialized) initMap();
        if (leafletMap) {
          leafletMap.invalidateSize();
          renderNavMap();
        }
      }, 50);
    } else if (tabName === 'evidence') {
      setTimeout(() => {
        renderTrajectory();
        renderDriftChart();
      }, 20);
    }
  };
  // ============================================================================
  // 6. LEAFLET MAP INITIALIZATION & INTERACTIVE OSM MANAGEMENT
  // ============================================================================
  function initMap() {
    if (mapInitialized || typeof L === 'undefined') return;
    const container = document.getElementById('nav-osm-map');
    if (!container) return;
    try {
      leafletMap = L.map('nav-osm-map', {
        zoomControl: true,
        attributionControl: true,
        maxZoom: 19,
        minZoom: 5, preferCanvas: true, zoomAnimation: true, markerZoomAnimation: true
      }).setView([18.5204, 73.8567], 13);
      // Real OpenStreetMap Standard Tile Layer
      L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a> contributors'
      }).addTo(leafletMap);
      if (leafletMap.zoomControl) {
        leafletMap.zoomControl.setPosition('topright');
      }
      // Outer road casing polyline for crisp contrast on OSM tiles
      routeCasingLayer = L.polyline([], {
        color: '#FFFFFF',
        weight: 9,
        opacity: 0.85,
        lineJoin: 'round',
        lineCap: 'round', smoothFactor: 1.5
      }).addTo(leafletMap);
      // Active road route (ahead of vehicle) — Sunset Orange
      routeAheadLayer = L.polyline([], {
        color: '#FF5841',
        weight: 6,
        opacity: 0.95,
        lineCap: 'round', smoothFactor: 1.5
      }).addTo(leafletMap);
      
      previewOutageLayer = L.polyline([], {
        color: '#A855F7',
        weight: 8, // slightly thicker to stand out on the red line
        opacity: 1.0,
        lineCap: 'round', smoothFactor: 1.5
      }).addTo(leafletMap);
      // Completed road route (behind vehicle) — Soft slate
      routePastLayer = L.polyline([], {
        color: '#FFFFFF',
        weight: 5,
        opacity: 0.8,
        lineJoin: 'round',
        lineCap: 'round', smoothFactor: 1.5
      }).addTo(leafletMap);
      // Single Primary Vehicle Arrow Marker (Sunset Orange #FF5841)
      const vehicleHtml = `
        <div class="nav-vehicle-marker" id="nav-vehicle-marker">
          <div class="nav-vehicle-arrow-wrap" id="nav-vehicle-arrow-wrap" style="transform: rotate(0deg);">
            <svg viewBox="0 0 36 36" width="36" height="36" class="nav-arrow-svg">
              <defs>
                <filter id="nav-arrow-shadow" x="-30%" y="-30%" width="160%" height="160%">
                  <feDropShadow dx="0" dy="2.5" stdDeviation="2.5" flood-color="#111827" flood-opacity="0.35"/>
                </filter>
              </defs>
              <path d="M 18 3 L 30 29 L 18 23 L 6 29 Z" 
                    fill="#FF5841" 
                    stroke="#FFFFFF" 
                    stroke-width="2.5" 
                    stroke-linejoin="round"
                    filter="url(#nav-arrow-shadow)" />
              <path d="M 18 7 L 18 22" stroke="rgba(255,255,255,0.85)" stroke-width="1.8" stroke-linecap="round"/>
            </svg>
          </div>
        </div>
      `;
      const vehicleIcon = L.divIcon({
        className: 'custom-vehicle-div-icon',
        html: vehicleHtml,
        iconSize: [36, 36],
        iconAnchor: [18, 18]
      });
      vehicleMarker = L.marker([18.5204, 73.8567], { icon: vehicleIcon, zIndexOffset: 1000 });
      // Start Origin Pin Marker
      const startHtml = `<div class="nav-pin-start" title="Departure Origin"><div class="start-pin-core"></div></div>`;
      const startIcon = L.divIcon({
        className: 'custom-start-div-icon',
        html: startHtml,
        iconSize: [20, 20],
        iconAnchor: [10, 10]
      });
      startMarker = L.marker([18.5314, 73.8446], { icon: startIcon, zIndexOffset: 500 });
      // Destination Pin Marker — Red-Violet #C53678
      const destHtml = `
        <div class="nav-pin-dest" title="Destination">
          <svg viewBox="0 0 32 40" width="32" height="40" class="dest-pin-svg">
            <defs>
              <filter id="dest-pin-shadow" x="-30%" y="-20%" width="160%" height="150%">
                <feDropShadow dx="0" dy="3" stdDeviation="3" flood-color="#111827" flood-opacity="0.35"/>
              </filter>
            </defs>
            <path d="M 16 0 C 7.16 0 0 7.16 0 16 C 0 26 16 40 16 40 C 16 40 32 26 32 16 C 32 7.16 24.84 0 16 0 Z" 
                  fill="#C53678" 
                  stroke="#FFFFFF" 
                  stroke-width="2" 
                  filter="url(#dest-pin-shadow)"/>
            <circle cx="16" cy="15" r="5.5" fill="#FFFFFF"/>
            <circle cx="16" cy="15" r="2.5" fill="#C53678"/>
          </svg>
        </div>
      `;
      const destIcon = L.divIcon({
        className: 'custom-dest-div-icon',
        html: destHtml,
        iconSize: [32, 40],
        iconAnchor: [16, 38]
      });
      destMarker = L.marker([18.5804, 73.9200], { icon: destIcon, zIndexOffset: 500 });
      // Subtle Current Location Marker (Home Screen: Shivajinagar, Pune)
      const currentLocHtml = `
        <div class="current-loc-marker-pulse" title="Current Location: Shivajinagar, Pune">
          <div class="current-loc-ring"></div>
          <div class="current-loc-dot"></div>
        </div>
      `;
      const currentLocIcon = L.divIcon({
        className: 'custom-current-loc-div-icon',
        html: currentLocHtml,
        iconSize: [24, 24],
        iconAnchor: [12, 12]
      });
      currentLocMarker = L.marker([18.5314, 73.8446], { icon: currentLocIcon, zIndexOffset: 700 });
      leafletMap.on('mousedown touchstart zoomstart', () => { navState.userInteracting = true; });
      leafletMap.on('mouseup touchend zoomend', () => { 
        setTimeout(() => { navState.userInteracting = false; }, 2000); 
      });
      mapInitialized = true;
    } catch (err) {
      console.error('Failed to initialize Leaflet OSM map:', err);
    }
  }
  // ============================================================================
  // 7. PRIMARY NAVIGATION PRODUCT FLOW: DESTINATION -> PREVIEW -> NAVIGATION
  // ============================================================================

  let recentSearchesOrder = ['pune-airport', 'viman-nagar', 'pune-station', 'shivajinagar', 'hinjawadi', 'wakad'];

    window.renderRecentSearches = function() {
    const listContainer = document.querySelector('.recent-searches-list');
    if (!listContainer) return;
    
    let html = '';
    for (const routeId of recentSearchesOrder) {
      const route = PUNE_ROUTES[routeId];
      if (!route) continue;
      
      const isActive = navState.currentRouteId === routeId ? ' active' : '';
      html += `
        <div class="recent-item${isActive}" id="dest-card=${routeId}" onclick="selectPuneRoute('${routeId}')">
          <div class="recent-item-icon">📍</div>
          <div class="recent-item-info">
            <div class="recent-item-name">${route.name}</div>
            <div class="recent-item-corridor">${route.corridor || 'Custom Destination Search'}</div>
          </div>
          <div class="recent-item-metrics">
            <span class="recent-pill-dist">${parseFloat(route.distKm).toFixed(1)} km</span>
            <span class="recent-pill-time">${route.durationMin} min</span>
            <span class="recent-arrow">↓</span>
          </div>
        </div>
      `;
    }
    listContainer.innerHTML = html;
  };

  /**
   * Select a destination (from recent searches or query)
   */
  window.selectPuneRoute = async function (routeId, skipPreview = false) {
    if (!PUNE_ROUTES[routeId]) return;
    navState.currentRouteId = routeId;
    const route = PUNE_ROUTES[routeId];
    state.dataset = route.datasetSource || 'S-Vta1a';
    navState.index = 0;
    navState.outageStartIdx = -1;
    navState.isArrived = false;
    
    // Dynamically figure out shortest path along real existence roads using OSRM!
    if (route.roadWaypoints && route.roadWaypoints.length >= 2) {
      try {
        const firstPt = route.roadWaypoints[0];
        const lastPt = route.roadWaypoints[route.roadWaypoints.length - 1];
        const coordString = `${firstPt[1]},${firstPt[0]};${lastPt[1]},${lastPt[0]}`;
        const routeRes = await fetch(`https://router.project-osrm.org/route/v1/driving/${coordString}?overview=full&geometries=geojson`);
        const routeData = await routeRes.json();
        
        if (routeData.routes && routeData.routes.length > 0) {
          const geom = routeData.routes[0].geometry.coordinates; // [lon, lat][]
          const trueNodes = geom.map(c => [c[1], c[0]]); // to [lat, lon]
          currentDenseRoute = generateDenseRoute(trueNodes, 1000);
          currentDenseCoords = currentDenseRoute.map(pt => [pt.lat, pt.lng]);
        } else {
          currentDenseRoute = generateDenseRoute(route.roadWaypoints, 1000);
          currentDenseCoords = currentDenseRoute.map(pt => [pt.lat, pt.lng]);
        }
      } catch (err) {
        currentDenseRoute = generateDenseRoute(route.roadWaypoints, 1000);
        currentDenseCoords = currentDenseRoute.map(pt => [pt.lat, pt.lng]);
      }
    }
    
    if (dom.destSearchInput) {
      dom.destSearchInput.value = route.name;
    }
    window.renderRecentSearches();
    if (dom.previewRouteOrigin) {
      dom.previewRouteOrigin.textContent = route.departure || 'Shivajinagar, Pune';
    }
    if (dom.previewRouteDest) {
      dom.previewRouteDest.textContent = route.name;
    }
    if (dom.previewDistVal) {
      dom.previewDistVal.innerHTML = `${route.distKm.toFixed(1)} <span class="p-met-unit">KM</span>`;
    }
        // Calculate ETA mathematically based on 50 km/h (13.8889 m/s)
    const TIME_ZONE = 'Asia/Kolkata';
    const distKm = route.totalDistKm || route.distKm;
    const calcDurationMin = Math.ceil((distKm / 50.0) * 60);
    
    if (dom.previewTimeVal) {
      dom.previewTimeVal.innerHTML = `~${calcDurationMin} <span class="p-met-unit">MIN</span>`;
    }
    if (dom.previewArrivalVal) {
      const now = new Date();
      const arrivalDate = new Date(now.getTime() + calcDurationMin * 60000);
      const timeFormatter = new Intl.DateTimeFormat('en-IN', {
        timeZone: TIME_ZONE,
        hour: '2-digit',
        minute: '2-digit'
      });
      const formattedArr = timeFormatter.format(arrivalDate);
      const parts = formattedArr.split(" ");
      dom.previewArrivalVal.innerHTML = `${parts[0]} <span class="p-met-unit">${parts[1] || ""} (IST)</span>`;
    }

    if (route.sectors && route.sectors.length >= 3) {
      if (dom.previewSector1Title) dom.previewSector1Title.textContent = route.sectors[0].title;
      if (dom.previewSector1Desc) dom.previewSector1Desc.textContent = route.sectors[0].desc;
      if (dom.previewSector2Title) dom.previewSector2Title.textContent = route.sectors[1].title;
      if (dom.previewSector2Desc) dom.previewSector2Desc.textContent = route.sectors[1].desc;
      if (dom.previewSector3Title) dom.previewSector3Title.textContent = route.sectors[2].title;
      if (dom.previewSector3Desc) dom.previewSector3Desc.textContent = route.sectors[2].desc;
    }
    if (!skipPreview) setFlowStep('preview');
  };
  /**
   * Handle user-typed destination search (supports arbitrary destinations)
   */
  window.submitDestinationSearch = async function () {
    const input = dom.destSearchInput || document.getElementById('destination-search-input');
    const query = input ? input.value.trim() : '';
    if (!query) return;
    // 1. Check if query matches any known recent route exactly
    const lower = query.toLowerCase();
    for (const [key, r] of Object.entries(PUNE_ROUTES)) {
      if (key === lower) {
        selectPuneRoute(key);
        return;
      }
    }
    // 2. Real Geocoding and Routing via OSM Nominatim and OSRM
    try {
      if (dom.btnSearchGo) dom.btnSearchGo.textContent = '...';
      const geoRes = await fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}&limit=1`);
      const geoData = await geoRes.json();
      
      if (!geoData || geoData.length === 0) {
        alert('Location not found. Please try a different search.');
        if (dom.btnSearchGo) dom.btnSearchGo.innerHTML = '<span class="search-icon">🔍</span>';
        return;
      }
      const destLat = parseFloat(geoData[0].lat);
      const destLon = parseFloat(geoData[0].lon);
      const destName = geoData[0].display_name.split(',')[0];
      // Route from current home (Shivajinagar) to Destination using OSRM
      const startLon = 73.8446;
      const startLat = 18.5314;
      
      const routeRes = await fetch(`https://router.project-osrm.org/route/v1/driving/${startLon},${startLat};${destLon},${destLat}?overview=full&geometries=geojson`);
      const routeData = await routeRes.json();
      if (dom.btnSearchGo) dom.btnSearchGo.innerHTML = '<span class="search-icon">🔍</span>';
      if (routeData.code !== 'Ok') {
        alert('Could not find a valid driving route to this location.');
        return;
      }
      const route = routeData.routes[0];
      const distKm = route.distance / 1000;
      // Force estimated time based on realistic 50km/h average speed
      const durationMin = Math.round((distKm / 50.0) * 60);
      
      // GeoJSON coordinates are [lon, lat], we need [lat, lon]
      const destWaypoints = route.geometry.coordinates.map(coord => [coord[1], coord[0]]);
      
      // Calculate deterministic arrival time
      const arrivalDate = new Date(Date.now() + durationMin * 60000);
      const arrivalDeterministic = arrivalDate.toLocaleTimeString('en-US', {timeZone: 'Asia/Kolkata', hour: '2-digit', minute:'2-digit'});
      const customId = 'custom-' + Date.now();
      PUNE_ROUTES[customId] = {
        id: customId,
        name: destName,
        departure: 'Shivajinagar, Pune',
        corridor: `Real-time OSM Route to ${destName}`,
        distKm: distKm,
        durationMin: durationMin,
        arrivalDeterministic: arrivalDeterministic,
        datasetSource: 'S-Vta1a',
        arrivalName: destName,
        isArbitrary: true,
        roadWaypoints: destWaypoints,
        sectors: [
          {
            title: `Sector 1: Departure towards ${destName}`,
            desc: 'Open-sky multi-constellation GNSS lock active. Inertial baseline steady.'
          },
          {
            title: 'Sector 2: Mid-route Transit (GNSS Outage Demo)',
            desc: 'Test seamless transition to inertial dead reckoning via SIMULATE GNSS OUTAGE.'
          },
          {
            title: `Sector 3: Final Approach to ${destName}`,
            desc: 'Satellite signal reacquisition and multi-sensor fusion re-engagement.'
          }
        ],
        instructionCues: [
          { pct: 0.00, dist: 'In 400m', title: `Head towards ${destName}`, sub: 'Continuous Inertial Monitoring Active', icon: '⬆' },
          { pct: 0.20, dist: 'In 800m', title: 'Continue on Main Route', sub: 'Ground Truth Reference Active', icon: '↗' },
          { pct: 0.45, dist: 'In 500m', title: 'Approaching Mid-route Sector', sub: 'Inertial Alignment Checked', icon: '⬆' },
          { pct: 0.65, dist: 'In 1.1km', title: 'Continue through GNSS-Denied Zone', sub: 'Dead Reckoning Active', icon: '⬆' },
          { pct: 0.85, dist: 'In 400m', title: `Approaching ${destName}`, sub: 'Multi-sensor fusion locked', icon: '↰' },
          { pct: 0.98, dist: 'Arrived', title: `You have arrived at ${destName}`, sub: 'Destination reached successfully', icon: '🏁' }
        ]
      };
      recentSearchesOrder.unshift(customId);
        if (recentSearchesOrder.length > 10) recentSearchesOrder.pop();
        selectPuneRoute(customId);
    } catch (err) {
      console.error("Routing error:", err);
      alert('Failed to retrieve real route. Please check network connection.');
      if (dom.btnSearchGo) dom.btnSearchGo.innerHTML = '<span class="search-icon">🔍</span>';
    }
  };
  /**
   * Set the flow step: 'destination' | 'preview' | 'navigating'
   */
  window.setFlowStep = function (step) {
    navState.flowStep = step;
    // Mini stepper buttons
    if (dom.stepBtnDest) dom.stepBtnDest.classList.toggle('active', step === 'destination');
    if (dom.stepBtnPreview) dom.stepBtnPreview.classList.toggle('active', step === 'preview');
    if (dom.stepBtnNav) dom.stepBtnNav.classList.toggle('active', step === 'navigating');
    // Manage card visibility
    if (dom.flowViewDest) dom.flowViewDest.classList.toggle('hidden', step !== 'destination');
    if (dom.flowViewPreview) dom.flowViewPreview.classList.toggle('hidden', step === 'destination');
      const btnStartNav = document.querySelector('.btn-start-navigation');
      if (btnStartNav) btnStartNav.style.display = step === 'navigating' ? 'none' : 'flex';
    // Manage live HUD visibility
    const isNav = step === 'navigating';
    if (dom.navInstructionCard) dom.navInstructionCard.classList.toggle('hidden', !isNav);
    if (dom.navBottomCard) dom.navBottomCard.classList.toggle('hidden', !isNav);
    if (dom.speedControlPanel) dom.speedControlPanel.classList.toggle('hidden', !isNav);
    if (dom.navArrivalCard) dom.navArrivalCard.classList.add('hidden');
    if (!isNav) {
      stopNavAnimation();
    }
    updateNavigationUI();
    renderNavMap();
    // Force Leaflet to recalculate tiles after Flexbox shifts side panel
    setTimeout(() => { if (leafletMap) leafletMap.invalidateSize(); }, 50);
    setTimeout(() => { if (leafletMap) leafletMap.invalidateSize(); }, 300);
  };
  /**
   * Start live navigation (auto-progresses at realistic road pace)
   */
  window.startNavigation = function () {
    setFlowStep('navigating');
    navState.index = 0;
    navState.outageStartIdx = -1;
    navState.isArrived = false;
    if (leafletMap) {
      leafletMap.setZoom(16);
    }
    updateNavigationUI();
    renderNavMap();
    startNavAnimation();
  };
  /**
   * Exit live navigation and return to destination selection
   */
  window.exitNavigation = function () {
    stopNavAnimation();
    setFlowStep('destination');
  };
  /**
   * Smooth, realistic-speed vehicle animation timer (~30 fps).
   * Pacing: ~6.5 points/second gives ~2.5 minutes for full trajectory traversal (1000 points).
   */
  let lastTimestamp = 0;
  function startNavAnimation() {
    stopNavAnimation();
    navState.isPlaying = true;
    lastTimestamp = performance.now();
    navState.playTimer = setInterval(() => {
      if (!navState.isPlaying) return;
      const now = performance.now();
      const dt = Math.min((now - lastTimestamp) / 1000, 0.1);
      lastTimestamp = now;
      if (currentDenseRoute && currentDenseRoute.length > 0) {
        const totalPts = currentDenseRoute.length;
        // 1x = 240 seconds demo duration, modified by playbackSpeed
        const pointsPerSec = (totalPts / 240.0) * navState.playbackSpeed; 
        navState.index += pointsPerSec * dt;
        if (navState.index >= totalPts - 1) {
          navState.index = totalPts - 1;
          handleDestinationArrival();
          return;
        }
        updateNavigationUI();
        renderNavMap();
      }
    }, 33);
  }
  function stopNavAnimation() {
    navState.isPlaying = false;
    if (navState.playTimer) {
      clearInterval(navState.playTimer);
      navState.playTimer = null;
    }
  }
  /**
   * Handle vehicle reaching destination
   */
  function handleDestinationArrival() {
    navState.isArrived = true;
    stopNavAnimation();
    const route = PUNE_ROUTES[navState.currentRouteId] || PUNE_ROUTES['pune-airport'];
    // Update bottom dock
    if (dom.dockTimeRemaining) dom.dockTimeRemaining.textContent = '0 min';
    if (dom.dockDistRemaining) dom.dockDistRemaining.textContent = '0.0 km';
    if (dom.dockDistTravelled) dom.dockDistTravelled.textContent = route.distKm.toFixed(1);
    if (dom.navSpeedDisplay) dom.navSpeedDisplay.textContent = '0.0';
    // Update top instruction card (Clean destination arrival, no floating flag)
    if (dom.instructionDist) dom.instructionDist.textContent = 'Arrived';
    if (dom.instructionTitle) dom.instructionTitle.textContent = `You have arrived at ${route.name}`;
    if (dom.instructionSub) dom.instructionSub.textContent = `${route.arrivalName} · Trip Complete`;
    if (dom.instructionIcon) dom.instructionIcon.textContent = '🏁';
    // Show arrival completion modal (No video/replay buttons)
    if (dom.arrivalTitle) {
      dom.arrivalTitle.textContent = `You have arrived at ${route.arrivalName}`;
    }
    if (dom.arrivalDesc) {
      dom.arrivalDesc.textContent = `Trip to ${route.name} completed successfully. Inertial dead reckoning maintained continuous vehicle guidance through simulated GNSS-denied sectors.`;
    }
    if (dom.navArrivalCard) {
      dom.navArrivalCard.classList.remove('hidden');
    }
    renderNavMap();
  }
  // ============================================================================
  // ============================================================================
  // 8. THEME & GNSS OUTAGE DEMONSTRATION & RECOVERY
  // ============================================================================
  window.toggleTheme = function () {
    const isDark = document.body.hasAttribute('data-theme');
    const iconSun = document.getElementById('icon-sun');
    const iconMoon = document.getElementById('icon-moon');
    
    if (isDark) {
      document.body.removeAttribute('data-theme');
      if (iconSun) iconSun.style.display = 'block';
      if (iconMoon) iconMoon.style.display = 'none';
    } else {
      document.body.setAttribute('data-theme', 'dark');
      if (iconSun) iconSun.style.display = 'none';
      if (iconMoon) iconMoon.style.display = 'block';
    }
  };
  window.toggleGnssOutage = function () {
    state.gnssOutage = !state.gnssOutage;
    if (state.gnssOutage) {
      // OUTAGE ACTIVE — NAVIGATING WITHOUT GPS
      navState.outageStartIdx = navState.index;
      
      // Spawn new purple segment for GNSS loss
      let newOutageLayer = L.polyline([], {
        color: '#A855F7',
        weight: 6,
        opacity: 0.95,
        lineCap: 'round', smoothFactor: 1.5
      }).addTo(leafletMap);
      outageSegments.push({ startIdx: Math.floor(navState.index), layer: newOutageLayer });

      // Top bar & buttons
      dom.gnssBadge.className = 'status-indicator outage';
      dom.gnssStatusText.textContent = 'GNSS LOST / DEAD RECKONING';
      if (dom.btnQuickOutage) dom.btnQuickOutage.classList.add('active-outage');
      if (dom.quickOutageText) dom.quickOutageText.textContent = 'RESTORE GNSS';
      // Bottom dock buttons
      if (dom.btnDockOutage) dom.btnDockOutage.classList.add('active-outage');
      if (dom.dockOutageText) dom.dockOutageText.textContent = 'RESTORE GNSS SIGNAL';
      // Live HUD indicator: Dead Reckoning (IMU-only)
      if (dom.hudModeDot) dom.hudModeDot.className = 'hud-mode-dot outage';
      if (dom.hudModeTitle) dom.hudModeTitle.textContent = 'DEAD RECKONING';
      if (dom.hudOutageAlert) {
        dom.hudOutageAlert.textContent = 'GNSS LOST / DEAD RECKONING';
        dom.hudOutageAlert.classList.remove('hidden');
      }
      showToast({
        type: 'outage',
        icon: '⚡',
        title: 'GNSS LOST / DEAD RECKONING',
        desc: 'Switched to inertial dead reckoning (IMU-only). Primary navigation arrow continues seamlessly.'
      });
    } else {
      // OUTAGE RECOVERED — GNSS RECOVERED -> GNSS + INS
      navState.outageStartIdx = -1;
      // Top bar & buttons
      dom.gnssBadge.className = 'status-indicator online';
      dom.gnssStatusText.textContent = 'GNSS AVAILABLE';
      if (dom.btnQuickOutage) dom.btnQuickOutage.classList.remove('active-outage');
      if (dom.quickOutageText) dom.quickOutageText.textContent = 'SIMULATE OUTAGE';
      // Bottom dock buttons
      if (dom.btnDockOutage) dom.btnDockOutage.classList.remove('active-outage');
      if (dom.dockOutageText) dom.dockOutageText.textContent = 'SIMULATE GNSS OUTAGE';
      // Live HUD indicator
      if (dom.hudModeDot) dom.hudModeDot.className = 'hud-mode-dot';
      if (dom.hudModeTitle) dom.hudModeTitle.textContent = 'GNSS AVAILABLE';
      if (dom.hudOutageAlert) dom.hudOutageAlert.classList.add('hidden');
      showToast({
        type: 'recovered',
        icon: '✓',
        title: 'GNSS RECOVERED',
        desc: 'Multi-constellation lock reacquired. Dual-sensor fusion active (GNSS + INS).'
      });
    }
    updateNavigationUI();
    renderNavMap();
  };
  // ============================================================================
  // 9. LIVE NAVIGATION TELEMETRY UPDATES & LEAFLET MAP RENDERER
  // ============================================================================
  function updateNavigationUI() {
    if (!currentDenseRoute || currentDenseRoute.length === 0) return;
    const totalPts = currentDenseRoute.length;
    
    // Smooth progress based on fractional index
    const exactIdx = Math.min(Math.max(0, navState.index), totalPts - 1);
    const progress = totalPts > 1 ? exactIdx / (totalPts - 1) : 1;
    const route = PUNE_ROUTES[navState.currentRouteId] || PUNE_ROUTES['pune-airport'];
    // Real recorded speed from IO-VNBD dataset
    if (dbData && dbData[state.dataset]) {
      const traj = dbData[state.dataset].trajectory;
      const totalTraj = traj.gt_east_m.length;
      const trajIdx = Math.min(Math.floor(progress * (totalTraj - 1)), totalTraj - 1);
      const currentSpeed = (traj.speed_kmh[trajIdx] || 0) * (navState.playbackSpeed || 1);
      if (dom.navSpeedDisplay) {
        dom.navSpeedDisplay.textContent = currentSpeed.toFixed(1);
      }
    }
    // Distance countdown
    const remDist = Math.max(0, route.distKm * (1 - progress));
    const doneDist = route.distKm * progress;
    if (dom.dockDistRemaining) dom.dockDistRemaining.textContent = `${remDist.toFixed(1)} km`;
    if (dom.dockDistTravelled) dom.dockDistTravelled.textContent = doneDist.toFixed(1);
    // Time countdown & ETA
    // ETA updated by setInterval loop based on 50km/h
    // Heading / Bearing readout and compass rotation
    const idxFloor = Math.floor(exactIdx);
    const pt = currentDenseRoute[idxFloor] || currentDenseRoute[0];
    const bearingDegVal = Math.round(pt.heading || 0);
    const cardinal = getCardinalDirection(bearingDegVal);
    const bearingStr = bearingDegVal.toString().padStart(3, '0');
    if (dom.compassBearingReadout) {
      dom.compassBearingReadout.textContent = `${bearingStr}° ${cardinal}`;
    }
    if (dom.compassArrowWrap) {
      dom.compassArrowWrap.style.transform = `rotate(${bearingDegVal}deg)`;
    }
    // Dynamic Turn-by-Turn Instruction Cues
    if (route.instructionCues && route.instructionCues.length > 0) {
      let activeCue = route.instructionCues[0];
      for (let i = 0; i < route.instructionCues.length; i++) {
        if (progress >= route.instructionCues[i].pct) {
          activeCue = route.instructionCues[i];
        }
      }
      if (dom.instructionDist) dom.instructionDist.textContent = activeCue.dist;
      if (dom.instructionTitle) dom.instructionTitle.textContent = activeCue.title;
      if (dom.instructionSub) dom.instructionSub.textContent = activeCue.sub;
      if (dom.instructionIcon) dom.instructionIcon.textContent = activeCue.icon;
    }
  }
  window.renderNavMap = renderNavMap;
  window.navState = navState;
  window.appState = state;
  function renderNavMap() {
    if (!mapInitialized) {
      initMap();
    }
    if (!leafletMap) return;
    const route = PUNE_ROUTES[navState.currentRouteId] || PUNE_ROUTES['pune-airport'];
    if (navState.flowStep === 'destination') {
      // Step 1: Destination Selection (Home) — Subtle current-location marker on Pune map
      if (routeCasingLayer) routeCasingLayer.setLatLngs([]);
      outageSegments.forEach(seg => { if(leafletMap.hasLayer(seg.layer)) leafletMap.removeLayer(seg.layer); });
      outageSegments = [];
      if (routeAheadLayer) routeAheadLayer.setLatLngs([]);
      if (previewOutageLayer) previewOutageLayer.setLatLngs([]);
      if (routePastLayer) routePastLayer.setLatLngs([]);
      if (vehicleMarker && leafletMap.hasLayer(vehicleMarker)) vehicleMarker.remove();
      if (startMarker && leafletMap.hasLayer(startMarker)) startMarker.remove();
      if (destMarker && leafletMap.hasLayer(destMarker)) destMarker.remove();
      if (currentLocMarker) {
        currentLocMarker.setLatLng([18.5314, 73.8446]).addTo(leafletMap);
      }
      leafletMap.setView([18.5314, 73.8446], 13);
      return;
    }
    // Remove home location marker during preview and active navigation
    if (currentLocMarker && leafletMap.hasLayer(currentLocMarker)) {
      currentLocMarker.remove();
    }
    if (!currentDenseRoute || currentDenseRoute.length === 0) {
      if (route && route.roadWaypoints) {
        currentDenseRoute = generateDenseRoute(route.roadWaypoints, 1000);
        currentDenseCoords = currentDenseRoute.map(pt => [pt.lat, pt.lng]);
      }
    }
    if (!currentDenseCoords || currentDenseCoords.length === 0) return;
    const startCoord = currentDenseCoords[0];
    const destCoord = currentDenseCoords[currentDenseCoords.length - 1];
    if (navState.flowStep === 'preview') {
      outageSegments.forEach(seg => { if(leafletMap.hasLayer(seg.layer)) leafletMap.removeLayer(seg.layer); });
      outageSegments = [];
      // Step 2: Route Preview — Full corridor overview on actual OSM road network
      routeCasingLayer.setLatLngs(currentDenseCoords);
      routeAheadLayer.setLatLngs(currentDenseCoords);
      routePastLayer.setLatLngs([]);
      startMarker.setLatLng(startCoord).addTo(leafletMap);
      destMarker.setLatLng(destCoord).addTo(leafletMap);
      vehicleMarker.setLatLng(startCoord).addTo(leafletMap);
      const arrowEl = document.getElementById('nav-vehicle-arrow-wrap');
      if (arrowEl && currentDenseRoute.length > 0) {
        arrowEl.style.transform = `rotate(${Math.round(currentDenseRoute[0].heading)}deg)`;
      }
      const bounds = L.latLngBounds(currentDenseCoords);
      const isMobile = window.innerWidth <= 768;
      leafletMap.fitBounds(bounds, {
        paddingTopLeft: isMobile ? [30, 30] : [480, 50],
        paddingBottomRight: isMobile ? [30, 280] : [50, 50],
        maxZoom: 15
      });
      return;
    }
    if (navState.flowStep === 'navigating') {
      if (previewOutageLayer) previewOutageLayer.setLatLngs([]); // clear static preview
      // Step 3: Live Navigation — Single primary navigation arrow, smooth camera tracking
      const totalDense = currentDenseRoute.length;
      const exactIdx = Math.min(Math.max(0, navState.index), totalDense - 1);
      const idxFloor = Math.floor(exactIdx);
      const idxCeil = Math.min(idxFloor + 1, totalDense - 1);
      const ratio = exactIdx - idxFloor;
      const p1 = currentDenseRoute[idxFloor];
      const p2 = currentDenseRoute[idxCeil];
      const pt = { lat: p1.lat + ratio * (p2.lat - p1.lat), lng: p1.lng + ratio * (p2.lng - p1.lng), heading: p1.heading };
      const idx = idxFloor;
      // 1. Primary Vehicle Arrow (Sunset Orange #FF5841) — ONLY arrow on the map
      vehicleMarker.setLatLng([pt.lat, pt.lng]).addTo(leafletMap);
      const arrowEl = document.getElementById('nav-vehicle-arrow-wrap');
      if (arrowEl) {
        arrowEl.style.transform = `rotate(${Math.round(pt.heading)}deg)`;
      }
      // 2. Route Progress Layers (Sunset orange path ahead, white completed)
      if (!navState.userInteracting) {
        const pastCoords = currentDenseCoords.slice(0, idx + 1);
        pastCoords.push([pt.lat, pt.lng]); // Extend white tail exactly to car
        routePastLayer.setLatLngs(pastCoords);
        
        // Update current purple outage segment if active
        if (state.gnssOutage && outageSegments.length > 0) {
            let currentSegment = outageSegments[outageSegments.length - 1];
            const segCoords = currentDenseCoords.slice(currentSegment.startIdx, idx + 1);
            segCoords.push([pt.lat, pt.lng]);
            currentSegment.layer.setLatLngs(segCoords);
        }
        
        const aheadCoords = currentDenseCoords.slice(Math.min(idx + 1, currentDenseCoords.length - 1));
        aheadCoords.unshift([pt.lat, pt.lng]); // Start orange path exactly from car
        routeAheadLayer.setLatLngs(aheadCoords);
      }
      // 3. Start Marker
      startMarker.setLatLng(startCoord).addTo(leafletMap);
      // 4. Destination pin (kept at all times as requested)
      destMarker.setLatLng(destCoord).addTo(leafletMap);
      // 5. Smooth Camera Tracking
      if (!navState.userInteracting) {
        leafletMap.setView([pt.lat, pt.lng], leafletMap.getZoom(), { animate: false });
      }
    }
  }
  // ============================================================================
  // 10. SYSTEM EVIDENCE SECTION CANVASES (Preserved Intact)
  // ============================================================================
  /**
   * Switch Active Dataset (S-Vta1a <-> S-Vta2) inside System Evidence
   */
  window.switchDataset = function (seqName) {
    if (state.dataset === seqName) return;
    state.dataset = seqName;
    if (seqName === 'S-Vta1a') {
      if (dom.btnVta1a) dom.btnVta1a.classList.add('active');
      if (dom.btnVta2) dom.btnVta2.classList.remove('active');
    } else {
      if (dom.btnVta2) dom.btnVta2.classList.add('active');
      if (dom.btnVta1a) dom.btnVta1a.classList.remove('active');
    }
    updateMetricsUI();
    renderTrajectory();
    renderDriftChart();
  };
  /**
   * Update scalar numbers on System Evidence tab
   */
  function updateMetricsUI() {
    if (!dbData || !dbData[state.dataset]) return;
    const cur = dbData[state.dataset];
    const m = cur.metrics;
    if (dom.heroDatasetName) dom.heroDatasetName.textContent = cur.name;
    if (dom.heroDatasetDesc) dom.heroDatasetDesc.textContent = cur.description;
    if (dom.valDistance) dom.valDistance.textContent = m.distance_km.toFixed(2);
    if (dom.valDuration) dom.valDuration.textContent = m.duration_min.toFixed(1);
    if (dom.valSamples) dom.valSamples.textContent = `${m.total_samples.toLocaleString()} samples @ 10 Hz`;
    if (dom.valPeakSpeed) dom.valPeakSpeed.textContent = m.peak_speed_kmh.toFixed(1);
    if (dom.valMeanSpeed) dom.valMeanSpeed.textContent = m.mean_speed_kmh.toFixed(1);
    if (dom.valDriftPct) dom.valDriftPct.textContent = m.p3_drift_pct.toFixed(1);
    if (dom.captionDist) dom.captionDist.textContent = m.distance_km.toFixed(2);
    if (dom.captionErr) dom.captionErr.textContent = m.p3_final_err_km.toFixed(2);
    if (dom.captionTime) dom.captionTime.textContent = m.duration_min.toFixed(1);
    if (dom.p2FinalErr) dom.p2FinalErr.textContent = m.p2_final_err_km.toFixed(1);
    if (dom.p2Rmse) dom.p2Rmse.textContent = m.p2_rmse_km.toFixed(1);
    if (dom.p2Drift) dom.p2Drift.textContent = m.p2_drift_pct.toFixed(1);
    if (dom.p3FinalErr) dom.p3FinalErr.textContent = m.p3_final_err_km.toFixed(1);
    if (dom.p3Rmse) dom.p3Rmse.textContent = m.p3_rmse_km.toFixed(1);
    if (dom.p3Drift) dom.p3Drift.textContent = m.p3_drift_pct.toFixed(1);
    if (dom.valRoll && dom.valPitch) {
      dom.valRoll.textContent = m.roll_tilt_deg.toFixed(2);
      dom.valPitch.textContent = m.pitch_tilt_deg.toFixed(2);
    }
    const sign = m.delta_final_km >= 0 ? '+' : '';
    if (dom.valDelta) {
      dom.valDelta.textContent = `${sign}${m.delta_final_km.toFixed(2)} km (${sign}${(m.p3_drift_pct - m.p2_drift_pct).toFixed(1)}% drift change)`;
    }
  }
  window.setScaleMode = function (mode) {
    if (state.scaleMode === mode) return;
    state.scaleMode = mode;
    if (mode === 'full') {
      if (dom.btnScaleFull) dom.btnScaleFull.classList.add('active');
      if (dom.btnScaleZoom) dom.btnScaleZoom.classList.remove('active');
    } else {
      if (dom.btnScaleZoom) dom.btnScaleZoom.classList.add('active');
      if (dom.btnScaleFull) dom.btnScaleFull.classList.remove('active');
    }
    renderTrajectory();
  };
  window.toggleLayer = function (layerId) {
    state.layers[layerId] = !state.layers[layerId];
    renderTrajectory();
  };
  /**
   * Trajectory Canvas Renderer (Phase 1 Ground Truth vs Phase 2 vs Phase 3)
   */
  function renderTrajectory() {
    if (!dom.canvasTrajectory || !dbData || !dbData[state.dataset]) return;
    const traj = dbData[state.dataset].trajectory;
    const { ctx, width, height } = setupCanvas(dom.canvasTrajectory);
    ctx.clearRect(0, 0, width, height);
    let minE, maxE, minN, maxN;
    if (state.scaleMode === 'zoom') {
      minE = Math.min(...traj.gt_east_m);
      maxE = Math.max(...traj.gt_east_m);
      minN = Math.min(...traj.gt_north_m);
      maxN = Math.max(...traj.gt_north_m);
      const spanE = Math.max(maxE - minE, 1000);
      const spanN = Math.max(maxN - minN, 1000);
      minE -= spanE * 0.15;
      maxE += spanE * 0.15;
      minN -= spanN * 0.15;
      maxN += spanN * 0.15;
    } else {
      const allE = [];
      const allN = [];
      if (state.layers.gt) { allE.push(...traj.gt_east_m); allN.push(...traj.gt_north_m); }
      if (state.layers.p2) { allE.push(...traj.p2_east_m); allN.push(...traj.p2_north_m); }
      if (state.layers.p3) { allE.push(...traj.p3_east_m); allN.push(...traj.p3_north_m); }
      if (allE.length === 0) {
        allE.push(...traj.gt_east_m);
        allN.push(...traj.gt_north_m);
      }
      minE = Math.min(...allE);
      maxE = Math.max(...allE);
      minN = Math.min(...allN);
      maxN = Math.max(...allN);
      const spanE = Math.max(maxE - minE, 5000);
      const spanN = Math.max(maxN - minN, 5000);
      minE -= spanE * 0.1;
      maxE += spanE * 0.1;
      minN -= spanN * 0.1;
      maxN += spanN * 0.1;
    }
    const dataWidth = maxE - minE;
    const dataHeight = maxN - minN;
    const padding = 50;
    const drawW = width - padding * 2;
    const drawH = height - padding * 2;
    const scale = Math.min(drawW / dataWidth, drawH / dataHeight);
    const offsetX = padding + (drawW - dataWidth * scale) / 2;
    const offsetY = padding + (drawH - dataHeight * scale) / 2;
    function toScreen(e, n) {
      const x = offsetX + (e - minE) * scale;
      const y = height - (offsetY + (n - minN) * scale);
      return { x, y };
    }
    dom.canvasTrajectory._toScreen = toScreen;
    // Engineering grid
    drawEngineeringGrid(ctx, width, height, minE, maxE, minN, maxN, toScreen);
    const nPts = traj.time_s.length;
    // Phase 2: Pure Body INS
    if (state.layers.p2) {
      ctx.save();
      ctx.strokeStyle = '#888888';
      ctx.lineWidth = 1.8;
      ctx.setLineDash([4, 4]);
      ctx.beginPath();
      for (let i = 0; i < nPts; i++) {
        const pt = toScreen(traj.p2_east_m[i], traj.p2_north_m[i]);
        if (i === 0) ctx.moveTo(pt.x, pt.y);
        else ctx.lineTo(pt.x, pt.y);
      }
      ctx.stroke();
      ctx.restore();
      const p2End = toScreen(traj.p2_east_m[nPts - 1], traj.p2_north_m[nPts - 1]);
      drawMarker(ctx, p2End.x, p2End.y, '#888888', 'P2 END');
    }
    // Phase 3: Leveled Vehicle INS
    if (state.layers.p3) {
      ctx.save();
      ctx.strokeStyle = '#C5AA6A';
      ctx.lineWidth = 2.2;
      ctx.setLineDash([6, 3]);
      ctx.beginPath();
      for (let i = 0; i < nPts; i++) {
        const pt = toScreen(traj.p3_east_m[i], traj.p3_north_m[i]);
        if (i === 0) ctx.moveTo(pt.x, pt.y);
        else ctx.lineTo(pt.x, pt.y);
      }
      ctx.stroke();
      ctx.restore();
      const p3End = toScreen(traj.p3_east_m[nPts - 1], traj.p3_north_m[nPts - 1]);
      drawMarker(ctx, p3End.x, p3End.y, '#C5AA6A', 'P3 END');
    }
    // Ground Truth
    if (state.layers.gt) {
      ctx.save();
      ctx.strokeStyle = '#2563EB';
      ctx.lineWidth = 2.5;
      ctx.setLineDash([]);
      ctx.beginPath();
      for (let i = 0; i < nPts; i++) {
        const pt = toScreen(traj.gt_east_m[i], traj.gt_north_m[i]);
        if (i === 0) ctx.moveTo(pt.x, pt.y);
        else ctx.lineTo(pt.x, pt.y);
      }
      ctx.stroke();
      ctx.restore();
      const gtEnd = toScreen(traj.gt_east_m[nPts - 1], traj.gt_north_m[nPts - 1]);
      drawMarker(ctx, gtEnd.x, gtEnd.y, '#2563EB', 'GT END');
    }
    const origin = toScreen(0, 0);
    drawOriginMarker(ctx, origin.x, origin.y);
  }
  function drawEngineeringGrid(ctx, width, height, minE, maxE, minN, maxN, toScreen) {
    ctx.save();
    ctx.strokeStyle = '#EAE7E1';
    ctx.lineWidth = 1;
    ctx.fillStyle = '#8C857E';
    ctx.font = '10px "JetBrains Mono", monospace';
    const spanKm = Math.max(maxE - minE, maxN - minN) / 1000.0;
    let stepKm = 10;
    if (spanKm <= 5) stepKm = 1;
    else if (spanKm <= 20) stepKm = 5;
    else if (spanKm <= 80) stepKm = 20;
    else if (spanKm <= 200) stepKm = 50;
    else stepKm = 100;
    const stepM = stepKm * 1000;
    const startEM = Math.floor(minE / stepM) * stepM;
    const endEM = Math.ceil(maxE / stepM) * stepM;
    for (let em = startEM; em <= endEM; em += stepM) {
      const p1 = toScreen(em, minN);
      ctx.beginPath();
      ctx.moveTo(p1.x, 0);
      ctx.lineTo(p1.x, height);
      ctx.stroke();
      ctx.fillText(`${(em / 1000).toFixed(0)}k E`, p1.x + 4, height - 12);
    }
    const startNM = Math.floor(minN / stepM) * stepM;
    const endNM = Math.ceil(maxN / stepM) * stepM;
    for (let nm = startNM; nm <= endNM; nm += stepM) {
      const p1 = toScreen(minE, nm);
      ctx.beginPath();
      ctx.moveTo(0, p1.y);
      ctx.lineTo(width, p1.y);
      ctx.stroke();
      ctx.fillText(`${(nm / 1000).toFixed(0)}k N`, 10, p1.y - 4);
    }
    ctx.restore();
  }
  function drawOriginMarker(ctx, x, y) {
    ctx.save();
    ctx.fillStyle = '#2A854E';
    ctx.beginPath();
    ctx.arc(x, y, 5, 0, Math.PI * 2);
    ctx.fill();
    ctx.strokeStyle = '#2F2626';
    ctx.lineWidth = 1.5;
    ctx.stroke();
    ctx.fillStyle = '#2F2626';
    ctx.font = '600 10px "Space Grotesk", sans-serif';
    ctx.fillText('ORIGIN (0,0)', x + 8, y + 3);
    ctx.restore();
  }
  function drawMarker(ctx, x, y, color, label) {
    ctx.save();
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.arc(x, y, 4.5, 0, Math.PI * 2);
    ctx.fill();
    ctx.strokeStyle = '#FFFFFF';
    ctx.lineWidth = 1.5;
    ctx.stroke();
    ctx.fillStyle = color;
    ctx.font = '600 9px "JetBrains Mono", monospace';
    ctx.fillText(label, x + 7, y + 3);
    ctx.restore();
  }
  function setupCanvasHover() {
    if (!dom.canvasTrajectory) return;
    dom.canvasTrajectory.addEventListener('mousemove', (e) => {
      if (!dbData || !dbData[state.dataset] || !dom.canvasTrajectory._toScreen) return;
      const rect = dom.canvasTrajectory.getBoundingClientRect();
      const mouseX = e.clientX - rect.left;
      const mouseY = e.clientY - rect.top;
      const traj = dbData[state.dataset].trajectory;
      const toScreen = dom.canvasTrajectory._toScreen;
      let closestIdx = -1;
      let minPixelDist = 20;
      for (let i = 0; i < traj.time_s.length; i++) {
        const pt = toScreen(traj.gt_east_m[i], traj.gt_north_m[i]);
        const dist = Math.hypot(pt.x - mouseX, pt.y - mouseY);
        if (dist < minPixelDist) {
          minPixelDist = dist;
          closestIdx = i;
        }
      }
      if (closestIdx !== -1) {
        state.hoveredIndex = closestIdx;
        const pt = toScreen(traj.gt_east_m[closestIdx], traj.gt_north_m[closestIdx]);
        if (dom.tooltip) {
          dom.tooltip.style.left = `${pt.x + 12}px`;
          dom.tooltip.style.top = `${pt.y - 12}px`;
          dom.tooltip.innerHTML = `
            <strong>t = ${traj.time_min[closestIdx].toFixed(1)} min</strong> (${traj.time_s[closestIdx].toFixed(0)}s)<br>
            GT Pos: (${(traj.gt_east_m[closestIdx] / 1000).toFixed(2)}k, ${(traj.gt_north_m[closestIdx] / 1000).toFixed(2)}k) km<br>
            Speed: ${traj.speed_kmh[closestIdx].toFixed(1)} km/h<br>
            Distance: ${traj.distance_km[closestIdx].toFixed(2)} km<br>
            P3 INS Error: <span style="color:#C5AA6A">${traj.p3_err_km[closestIdx].toFixed(2)} km</span>
          `;
          dom.tooltip.classList.remove('hidden');
        }
      } else {
        if (dom.tooltip) dom.tooltip.classList.add('hidden');
      }
    });
    dom.canvasTrajectory.addEventListener('mouseleave', () => {
      if (dom.tooltip) dom.tooltip.classList.add('hidden');
    });
  }
  /**
   * Drift Analysis Chart Renderer (Phase 2 vs Phase 3 Error)
   */
  function renderDriftChart() {
    if (!dom.canvasDrift || !dbData || !dbData[state.dataset]) return;
    const traj = dbData[state.dataset].trajectory;
    const { ctx, width, height } = setupCanvas(dom.canvasDrift);
    ctx.clearRect(0, 0, width, height);
    const padLeft = 55;
    const padRight = 30;
    const padTop = 30;
    const padBottom = 40;
    const maxT = Math.max(...traj.time_min);
    const maxErr = Math.max(...traj.p2_err_km, ...traj.p3_err_km) * 1.1;
    const plotW = width - padLeft - padRight;
    const plotH = height - padTop - padBottom;
    function getX(t) {
      return padLeft + (t / maxT) * plotW;
    }
    function getY(err) {
      return height - padBottom - (err / maxErr) * plotH;
    }
    // Grid & Axes
    ctx.save();
    ctx.strokeStyle = '#EAE7E1';
    ctx.lineWidth = 1;
    ctx.fillStyle = '#8C857E';
    ctx.font = '10px "JetBrains Mono", monospace';
    const errStep = maxErr > 300 ? 100 : 50;
    for (let e = 0; e <= maxErr; e += errStep) {
      const y = getY(e);
      ctx.beginPath();
      ctx.moveTo(padLeft, y);
      ctx.lineTo(width - padRight, y);
      ctx.stroke();
      ctx.fillText(`${e} km`, 8, y + 3);
    }
    const tStep = maxT > 30 ? 10 : 5;
    for (let t = 0; t <= maxT; t += tStep) {
      const x = getX(t);
      ctx.beginPath();
      ctx.moveTo(x, padTop);
      ctx.lineTo(x, height - padBottom);
      ctx.stroke();
      ctx.fillText(`${t}m`, x - 8, height - padBottom + 16);
    }
    ctx.fillStyle = '#2F2626';
    ctx.font = '600 10px "Space Grotesk", sans-serif';
    ctx.fillText('ELAPSED TIME (MINUTES)', padLeft + plotW / 2 - 50, height - 10);
    ctx.save();
    ctx.translate(14, padTop + plotH / 2 + 40);
    ctx.rotate(-Math.PI / 2);
    ctx.fillText('2D POSITION ERROR (KM)', 0, 0);
    ctx.restore();
    ctx.restore();
    // Plot Phase 2 Curve (Gray Dotted)
    ctx.save();
    ctx.strokeStyle = '#888888';
    ctx.lineWidth = 2.0;
    ctx.setLineDash([4, 4]);
    ctx.beginPath();
    for (let i = 0; i < traj.time_min.length; i++) {
      const x = getX(traj.time_min[i]);
      const y = getY(traj.p2_err_km[i]);
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.stroke();
    ctx.restore();
    // Plot Phase 3 Curve (Warning Red)
    ctx.save();
    ctx.strokeStyle = '#C95232';
    ctx.lineWidth = 2.5;
    ctx.setLineDash([]);
    ctx.beginPath();
    for (let i = 0; i < traj.time_min.length; i++) {
      const x = getX(traj.time_min[i]);
      const y = getY(traj.p3_err_km[i]);
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.stroke();
    ctx.restore();
    // Final Callout
    const lastIdx = traj.time_min.length - 1;
    const finalX = getX(traj.time_min[lastIdx]);
    const finalY = getY(traj.p3_err_km[lastIdx]);
    ctx.save();
    ctx.fillStyle = '#C95232';
    ctx.beginPath();
    ctx.arc(finalX, finalY, 4, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = '#2F2626';
    ctx.font = '700 11px "Space Grotesk", sans-serif';
    ctx.fillText(`${traj.p3_err_km[lastIdx].toFixed(1)} km`, finalX - 55, finalY - 8);
    ctx.restore();
  }
  // ============================================================================
  // 11. HELPER UTILITIES
  // ============================================================================
  function showToast(info) {
    if (!dom.toast) return;
    if (state.toastTimer) clearTimeout(state.toastTimer);
    dom.toast.className = `gnss-toast ${info.type}`;
    if (dom.toastIcon) dom.toastIcon.textContent = info.icon;
    if (dom.toastTitle) dom.toastTitle.textContent = info.title;
    if (dom.toastDesc) dom.toastDesc.textContent = info.desc;
    state.toastTimer = setTimeout(() => {
      dismissToast();
    }, 7000);
  }
  window.dismissToast = function () {
    if (dom.toast) dom.toast.classList.add('hidden');
    if (state.toastTimer) {
      clearTimeout(state.toastTimer);
      state.toastTimer = null;
    }
  };
  function setupCanvas(canvas) {
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    const w = rect.width || canvas.clientWidth || (canvas.parentElement ? canvas.parentElement.clientWidth : 1200) || 1200;
    const h = rect.height || canvas.clientHeight || (canvas.parentElement ? canvas.parentElement.clientHeight : 600) || 600;
    canvas.width = w * dpr;
    canvas.height = h * dpr;
    const ctx = canvas.getContext('2d');
    ctx.resetTransform();
    ctx.scale(dpr, dpr);
    return { ctx, width: w, height: h };
  }
  function getCardinalDirection(deg) {
    const directions = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW'];
    const idx = Math.round(((deg % 360) + 360) % 360 / 22.5) % 16;
    return directions[idx];
  }
  function debounce(fn, ms) {
    let timer;
    return function (...args) {
      clearTimeout(timer);
      timer = setTimeout(() => fn.apply(this, args), ms);
    };
  }
  // Speed Controls
  window.setPlaybackSpeed = function(speed) {
    navState.playbackSpeed = speed;
    if (dom.btnSpeed1) dom.btnSpeed1.classList.toggle("active", speed === 1);
    if (dom.btnSpeed15) dom.btnSpeed15.classList.toggle("active", speed === 1.5);
    if (dom.btnSpeed2) dom.btnSpeed2.classList.toggle("active", speed === 2);
  };
  // Initialize on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
// Real-time clock and ETA updater
setInterval(() => {
  const TIME_ZONE = "Asia/Kolkata";
  const now = new Date();
  const timeFormatter = new Intl.DateTimeFormat("en-IN", {
    timeZone: TIME_ZONE,
    hour: "2-digit",
    minute: "2-digit",
  });
  
  if (dom.dockCurrentTime) {
    dom.dockCurrentTime.textContent = timeFormatter.format(now) + " (IST)";
  }

  if (navState && navState.flowStep === 'navigating' && currentDenseRoute && currentDenseRoute.length > 0) {
    const route = PUNE_ROUTES[navState.currentRouteId];
    const totalDist = route ? (route.totalDistKm || route.distKm) : null;
    if (route && totalDist) {
      const progress = Math.min(1, Math.max(0, navState.index / Math.max(1, currentDenseCoords.length - 1)));
      const remainingDistKm = Math.max(0, totalDist * (1 - progress));
      const playbackSpeed = navState.playbackSpeed || 1;
      const speedKmH = 50.0 * playbackSpeed;
      const durationMin = Math.ceil((remainingDistKm / speedKmH) * 60);
      
      if (dom.dockTimeRemaining) dom.dockTimeRemaining.textContent = `${durationMin} min`;
      const now = new Date();
      const arrivalDate = new Date(now.getTime() + durationMin * 60000);
      const timeFormatter = new Intl.DateTimeFormat('en-IN', {
        timeZone: 'Asia/Kolkata',
        hour: '2-digit',
        minute: '2-digit'
      });
      if (dom.dockArriveTime) dom.dockArriveTime.textContent = timeFormatter.format(arrivalDate) + ' (IST)';
    }
  } else if (navState && navState.flowStep !== 'navigating') {
      if (dom.dockTimeRemaining) dom.dockTimeRemaining.textContent = `-- min`;
      if (dom.dockArriveTime) dom.dockArriveTime.textContent = `--:--`;
  }
}, 1000);
})();













