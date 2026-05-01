import { MapContainer, TileLayer, Marker, Polyline, useMapEvents, useMap } from 'react-leaflet'
import L from 'leaflet'
import { useState, useEffect, useRef } from 'react'
import axios from 'axios'
import 'leaflet/dist/leaflet.css'

const API_BASE = 'http://localhost:5002'

// Realistic drone speed: 15 m/s (54 km/h) - typical delivery drone speed
const DRONE_SPEED_MS = 15.0  // meters per second
const SIMULATION_INTERVAL_MS = 100  // Update every 100ms

// Icons
const baseIcon = L.icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-blue.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
})

const deliveryIcon = L.icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-red.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
})

const droneIcon = L.icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-green.png',
  iconSize: [30, 46],
  iconAnchor: [15, 46],
  popupAnchor: [1, -34],
})

// Fix for default marker icons
delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
})

// Helper: Calculate distance between two lat/lon points in meters
function haversineDistance(lat1, lon1, lat2, lon2) {
  const R = 6371000 // Earth radius in meters
  const dLat = (lat2 - lat1) * Math.PI / 180
  const dLon = (lon2 - lon1) * Math.PI / 180
  const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
    Math.sin(dLon / 2) * Math.sin(dLon / 2)
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
  return R * c
}

function DeliveryClickHandler({ onAdd, enabled }) {
  useMapEvents({
    click(e) {
      if (enabled) {
        onAdd([e.latlng.lat, e.latlng.lng])
      }
    },
  })
  return null
}

function DroneMarker({ position }) {
  const map = useMap()
  const markerRef = useRef(null)

  useEffect(() => {
    if (position && markerRef.current) {
      markerRef.current.setLatLng(position)
      map.setView(position, map.getZoom())
    }
  }, [position, map])

  if (!position) return null

  return <Marker position={position} icon={droneIcon} ref={markerRef} />
}

export default function MapPage({ onExit }) {
  const [base, setBase] = useState(null)
  const [deliveries, setDeliveries] = useState([])
  const [route, setRoute] = useState([])
  const [path, setPath] = useState([])
  const [isPlanning, setIsPlanning] = useState(false)
  const [isSimulating, setIsSimulating] = useState(false)
  const [dronePosition, setDronePosition] = useState(null)
  const [currentPathIndex, setCurrentPathIndex] = useState(0)
  const [addingEnabled, setAddingEnabled] = useState(true)
  
  // Search functionality
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState([])
  const [showSearchResults, setShowSearchResults] = useState(false)

  // Load base location
  useEffect(() => {
    axios.get(`${API_BASE}/base`)
      .then(res => {
        setBase([res.data.lat, res.data.lon])
      })
      .catch(err => {
        console.error('Failed to load base:', err)
        alert('Failed to load base location. Please check backend.')
      })
  }, [])

  // Geocode search
  async function handleSearch(query) {
    if (!query.trim()) {
      setSearchResults([])
      setShowSearchResults(false)
      return
    }

    try {
      const res = await axios.get(`${API_BASE}/geocode`, {
        params: { q: query }
      })
      setSearchResults(res.data)
      setShowSearchResults(true)
    } catch (err) {
      console.error('Search failed:', err)
      setSearchResults([])
    }
  }

  function selectSearchResult(result) {
    setBase([result.lat, result.lon])
    setSearchQuery('')
    setSearchResults([])
    setShowSearchResults(false)
  }

  function addDelivery(point) {
    setDeliveries(prev => [...prev, { lat: point[0], lon: point[1] }])
  }

  function removeDelivery(index) {
    setDeliveries(prev => prev.filter((_, i) => i !== index))
  }

  function clearAll() {
    setDeliveries([])
    setRoute([])
    setPath([])
    setDronePosition(null)
    setCurrentPathIndex(0)
    setIsSimulating(false)
  }

  async function planRoute() {
    if (deliveries.length === 0) {
      alert('Please add at least one delivery point')
      return
    }

    setIsPlanning(true)
    setAddingEnabled(false)

    try {
      // Set delivery points
      await axios.post(`${API_BASE}/deliveries`, {
        points: deliveries
      })

      // Plan route
      const res = await axios.post(`${API_BASE}/route/plan`)
      setPath(res.data.path)
      setRoute(res.data.path.map((p, i) => ({ ...p, index: i })))
      alert(`Route planned with ${res.data.path.length} waypoints (includes return to base)`)
    } catch (err) {
      console.error('Planning failed:', err)
      alert(`Planning failed: ${err.response?.data?.error || err.message}`)
    } finally {
      setIsPlanning(false)
      setAddingEnabled(true)
    }
  }

  function startSimulation() {
    if (path.length === 0) {
      alert('Please plan a route first')
      return
    }

    setIsSimulating(true)
    setAddingEnabled(false)
    setCurrentPathIndex(0)
    setDronePosition([path[0][0], path[0][1]])
  }

  function stopSimulation() {
    setIsSimulating(false)
    setAddingEnabled(true)
  }

  // Realistic simulation loop - moves based on distance and speed
  useEffect(() => {
    if (!isSimulating || path.length === 0) return

    let currentSegmentIndex = 0
    let currentSegmentProgress = 0  // 0 to 1

    const interval = setInterval(() => {
      if (currentSegmentIndex >= path.length - 1) {
        // Reached end (returned to base)
        setIsSimulating(false)
        setAddingEnabled(true)
        return
      }

      const start = path[currentSegmentIndex]
      const end = path[currentSegmentIndex + 1]
      
      // Calculate distance for this segment
      const segmentDistance = haversineDistance(start[0], start[1], end[0], end[1])
      
      // Calculate how much to move in this interval
      const distancePerInterval = DRONE_SPEED_MS * (SIMULATION_INTERVAL_MS / 1000)
      const progressIncrement = distancePerInterval / segmentDistance
      
      currentSegmentProgress += progressIncrement

      if (currentSegmentProgress >= 1.0) {
        // Move to next segment
        currentSegmentProgress = 0
        currentSegmentIndex++
        if (currentSegmentIndex < path.length) {
          setDronePosition([path[currentSegmentIndex][0], path[currentSegmentIndex][1]])
          setCurrentPathIndex(currentSegmentIndex)
        }
      } else {
        // Interpolate position along current segment
        const lat = start[0] + (end[0] - start[0]) * currentSegmentProgress
        const lon = start[1] + (end[1] - start[1]) * currentSegmentProgress
        setDronePosition([lat, lon])
        setCurrentPathIndex(currentSegmentIndex)
      }
    }, SIMULATION_INTERVAL_MS)

    return () => clearInterval(interval)
  }, [isSimulating, path])

  if (!base) {
    return <div style={{ padding: 20 }}>Loading base location...</div>
  }

  return (
    <div style={{ display: 'flex', height: '100vh', margin: 0, padding: 0 }}>
      {/* Sidebar */}
      <div style={{ 
        width: 320, 
        padding: 20, 
        background: '#1e293b', 
        color: 'white',
        overflowY: 'auto'
      }}>
        <h2 style={{ marginTop: 0 }}>Drone Delivery Planner</h2>
        
        {/* Search Bar */}
        <div style={{ marginBottom: 20 }}>
          <input
            type="text"
            placeholder="Search location..."
            value={searchQuery}
            onChange={(e) => {
              setSearchQuery(e.target.value)
              handleSearch(e.target.value)
            }}
            style={{
              width: '100%',
              padding: '8px',
              borderRadius: 4,
              border: '1px solid #475569',
              background: '#334155',
              color: 'white',
              fontSize: 14
            }}
          />
          {showSearchResults && searchResults.length > 0 && (
            <div style={{
              position: 'absolute',
              zIndex: 1000,
              background: '#334155',
              border: '1px solid #475569',
              borderRadius: 4,
              marginTop: 4,
              maxHeight: 200,
              overflowY: 'auto',
              width: 280
            }}>
              {searchResults.map((result, i) => (
                <div
                  key={i}
                  onClick={() => selectSearchResult(result)}
                  style={{
                    padding: '8px 12px',
                    cursor: 'pointer',
                    borderBottom: i < searchResults.length - 1 ? '1px solid #475569' : 'none'
                  }}
                  onMouseEnter={(e) => e.target.style.background = '#475569'}
                  onMouseLeave={(e) => e.target.style.background = 'transparent'}
                >
                  <div style={{ fontSize: 13, fontWeight: 'bold' }}>
                    {result.display_name}
                  </div>
                  <div style={{ fontSize: 11, color: '#94a3b8', marginTop: 2 }}>
                    {result.lat.toFixed(6)}, {result.lon.toFixed(6)}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
        
        <div style={{ marginBottom: 20, padding: 10, background: '#334155', borderRadius: 4 }}>
          <strong>Base:</strong> {base ? `${base[0].toFixed(6)}, ${base[1].toFixed(6)}` : 'Loading...'}<br />
          <small style={{ color: '#94a3b8' }}>Click search to change base location</small>
        </div>

        <h3>Delivery Points ({deliveries.length})</h3>
        {deliveries.length === 0 ? (
          <p style={{ color: '#94a3b8' }}>Click on map to add delivery points</p>
        ) : (
          <div>
            {deliveries.map((d, i) => (
              <div key={i} style={{ 
                marginBottom: 8, 
                padding: 8, 
                background: '#334155', 
                borderRadius: 4,
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center'
              }}>
                <div>
                  <strong>#{i + 1}</strong> {d.lat.toFixed(5)}, {d.lon.toFixed(5)}
                </div>
                <button 
                  onClick={() => removeDelivery(i)}
                  style={{ padding: '4px 8px', fontSize: 12 }}
                >
                  Remove
                </button>
              </div>
            ))}
          </div>
        )}

        <div style={{ marginTop: 20 }}>
          <button
            onClick={planRoute}
            disabled={isPlanning || deliveries.length === 0}
            style={{
              width: '100%',
              padding: 12,
              fontSize: 16,
              background: '#3b82f6',
              color: 'white',
              border: 'none',
              borderRadius: 4,
              cursor: isPlanning ? 'not-allowed' : 'pointer',
              marginBottom: 10
            }}
          >
            {isPlanning ? 'Planning...' : 'Plan Route'}
          </button>

          {path.length > 0 && (
            <div style={{ marginBottom: 10, padding: 10, background: '#334155', borderRadius: 4 }}>
              <strong>Path:</strong> {path.length} waypoints<br />
              <small style={{ color: '#94a3b8' }}>Includes return to base</small>
            </div>
          )}

          {path.length > 0 && (
            <button
              onClick={isSimulating ? stopSimulation : startSimulation}
              style={{
                width: '100%',
                padding: 12,
                fontSize: 16,
                background: isSimulating ? '#ef4444' : '#10b981',
                color: 'white',
                border: 'none',
                borderRadius: 4,
                cursor: 'pointer',
                marginBottom: 10
              }}
            >
              {isSimulating ? 'Stop Simulation' : 'Start Simulation'}
            </button>
          )}

          <button
            onClick={clearAll}
            style={{
              width: '100%',
              padding: 12,
              fontSize: 16,
              background: '#64748b',
              color: 'white',
              border: 'none',
              borderRadius: 4,
              cursor: 'pointer',
              marginBottom: 10
            }}
          >
            Clear All
          </button>

          <button
            onClick={onExit}
            style={{
              width: '100%',
              padding: 12,
              fontSize: 16,
              background: '#475569',
              color: 'white',
              border: 'none',
              borderRadius: 4,
              cursor: 'pointer'
            }}
          >
            Exit
          </button>
        </div>
      </div>

      {/* Map */}
      <div style={{ flex: 1, position: 'relative' }}>
        <MapContainer
          center={base}
          zoom={17}
          style={{ height: '100%', width: '100%' }}
        >
          {/* ESRI Satellite */}
          <TileLayer
            url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
            attribution="&copy; Esri"
          />

          {/* OSM Labels Overlay */}
          <TileLayer
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            attribution="&copy; OpenStreetMap"
            opacity={0.4}
          />

          {/* Base marker */}
          <Marker position={base} icon={baseIcon} />

          {/* Delivery points */}
          {deliveries.map((d, i) => (
            <Marker
              key={i}
              position={[d.lat, d.lon]}
              icon={deliveryIcon}
            />
          ))}

          {/* Planned path */}
          {path.length > 1 && (
            <Polyline
              positions={path}
              color="#3b82f6"
              weight={3}
              opacity={0.7}
            />
          )}

          {/* Drone marker */}
          <DroneMarker position={dronePosition} />

          {/* Click handler */}
          <DeliveryClickHandler onAdd={addDelivery} enabled={addingEnabled} />
        </MapContainer>
      </div>
    </div>
  )
}
