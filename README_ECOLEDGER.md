# 🌱 EcoLedger Carbon Monitoring Iframe Integration

## Overview

This document details the implementation of a public iframe embedding system for Carira carbon monitoring features. The system allows external websites to embed interactive carbon monitoring maps with AI-powered chat functionality without requiring user authentication.

## 🎯 Key Features

- **Public API Access**: Carbon monitoring data accessible without authentication
- **Iframe Embedding**: Seamless integration with external websites
- **Interactive Maps**: MapLibre-based visualization with geometry highlighting
- **AI-Powered Chat**: OpenAI integration for intelligent carbon data analysis
- **Responsive Design**: Optimized for embedded contexts

## 🏗️ Architecture Overview

```
External Website
    ↓ (HTML/JavaScript)
Iframe Embedding
    ↓ (React Frontend)
Public API Endpoints
    ↓ (FastAPI Backend)
PostgreSQL + PostGIS
    ↓ (Geospatial Queries)
OpenAI API
    ↓ (Intelligent Responses)
```

## 📋 Implementation Details

### 1. Backend API Infrastructure

#### **Public Routes** (`src/routes_routes.py`)

**List Carbon Features**

```python
@iframe_public_router.get("/public/features")
async def list_features_public()
```

- Returns paginated list of carbon monitoring features
- Includes geometry, carbon data, and metadata
- No authentication required

**Get Feature Details**

```python
@iframe_public_router.get("/public/feature/{feature_id}")
async def get_feature_public(feature_id: int)
```

- Returns detailed feature data with geometry
- Calculates centroid and bounding box for map centering
- PostGIS integration for geospatial operations

**Create Public Map**

```python
@iframe_public_router.post("/public/create-map-for-feature/{feature_id}")
async def create_public_map_for_feature(feature_id: int)
```

- Creates/reuses map instance for feature visualization
- Returns embed URL for iframe integration
- Uses system user for public map ownership

**AI Chat Integration**

```python
@iframe_public_router.post("/public/feature/{feature_id}/chat")
async def chat_with_carira_feature(feature_id: int, request: dict)
```

- Context-aware AI responses about carbon data
- OpenAI GPT-4o-mini integration
- Feature-specific carbon analysis

#### **CORS Configuration** (`src/wsgi.py`)

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "null"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 2. Frontend Components

#### **Public Route Handler** (`frontendts/src/App.tsx`)

```tsx
// Conditional SuperTokens initialization
function initializeSuperTokens() {
  /* ... */
}

// Public route for iframe embedding
<Route path="/feature/:projectId" element={<FeatureMap />} />;
```

#### **Feature Map Component** (`frontendts/src/componentsFeatureMap.tsx`)

```tsx
// Public API integration
const apiUrl =
  window.location.hostname === "localhost"
    ? `http://localhost:8000/public/feature/${id}`
    : `/public/feature/${id}`;

// Embed mode optimization
const isEmbedMode = searchParams.get("embed") === "true";
```

#### **Enhanced Map Component** (`frontendts/src/components/MapLibreMap.tsx`)

Key improvements:

- **Safe Authentication Wrappers**: Graceful degradation when auth unavailable
- **Optimized Zoom Levels**: `maxZoom: 18` with higher initial zoom
- **Green Geometry Highlighting**: Clear carbon feature visualization
- **Redesigned Chat UI**: Right-side panel with bottom input
- **Hidden Version Search**: Removed confusing changelog interface

### 3. AI Intelligence System

#### **Model Configuration** (`src/dependencies/chat_completions.py`)

```python
class DefaultChatArgsProvider(ChatArgsProvider):
    async def get_args(self, user_id: str, resource_type: str) -> dict:
        return {
            "model": os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
            "max_tokens": 500,
            "temperature": 0.7,
        }
```

#### **OpenAI Client Setup** (`src/utils.py`)

```python
def get_openai_client() -> AsyncOpenAI:
    base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
    return AsyncOpenAI(base_url=base_url)
```

### 4. External Integration

#### **Demo Implementation** (`external-frontend-demo.html`)

Complete external website example showing:

- Feature listing from public API
- Map creation and iframe embedding
- Interactive carbon monitoring dashboard

## 🔄 Request Flow Diagram

```mermaid
sequenceDiagram
    participant EXT as External Website
    participant API as Backend API
    participant DB as PostgreSQL
    participant IFRAME as React Iframe
    participant OPENAI as OpenAI API

    EXT->>API: GET /public/features
    API->>DB: Query carbon features
    DB-->>API: Feature list
    API-->>EXT: JSON response

    EXT->>API: POST /public/create-map-for-feature/1
    API->>DB: Create/find map
    DB-->>API: Map details
    API-->>EXT: Embed URL

    EXT->>IFRAME: Load iframe with embed URL
    IFRAME->>API: GET /public/feature/1
    API->>DB: Feature geometry & data
    DB-->>API: Detailed feature
    API-->>IFRAME: Feature with geometry

    IFRAME->>API: POST /public/feature/1/chat
    API->>OPENAI: Context-aware prompt
    OPENAI-->>API: AI response
    API-->>IFRAME: Intelligent carbon analysis
```

## ⚙️ Environment Configuration

Required environment variables in `.env`:

```bash
# Database Configuration
POSTGRES_URL=postgresql://user:password@host:port/database

# OpenAI Integration
OPENAI_API_KEY=sk-proj-...
OPENAI_MODEL=gpt-4o-mini

# Optional: Custom OpenAI endpoint
OPENAI_BASE_URL=https://api.openai.com/v1

# Authentication Mode
MUNDI_AUTH_MODE=edit
```

## 🚀 Usage Example

### External Website Integration

```html
<!DOCTYPE html>
<html>
  <head>
    <title>Carbon Monitoring Dashboard</title>
  </head>
  <body>
    <div id="features-list"></div>
    <div id="map-view" style="display: none;">
      <iframe id="map-iframe" width="100%" height="600px"></iframe>
    </div>

    <script>
      const API_BASE = "http://localhost:8000/public";
      const FRONTEND_BASE = "http://localhost:5173";

      // Load features
      async function loadFeatures() {
        const response = await fetch(`${API_BASE}/features`);
        const data = await response.json();
        // Display features...
      }

      // Create and display map
      async function viewFeatureOnMap(featureId) {
        const response = await fetch(
          `${API_BASE}/create-map-for-feature/${featureId}`,
          { method: "POST" }
        );
        const mapData = await response.json();

        if (mapData.success) {
          document.getElementById(
            "map-iframe"
          ).src = `${FRONTEND_BASE}${mapData.embed_url}`;
        }
      }
    </script>
  </body>
</html>
```

### API Response Examples

**Features List Response:**

```json
{
  "features": [
    {
      "id": 1,
      "area_name": "Carbon Reserve Area 1",
      "municipality": "São Paulo",
      "total_area": 150.75,
      "total_carbon": 2543.67,
      "monitoring_date": "2024-12-15T00:00:00Z",
      "geometry_geojson": "{\"type\":\"Polygon\",\"coordinates\":[...]}"
    }
  ],
  "total_count": 25
}
```

**Map Creation Response:**

```json
{
  "success": true,
  "message": "Public map created successfully",
  "project_id": "proj_abc123",
  "map_id": "map_def456",
  "feature_id": 1,
  "embed_url": "/feature/proj_abc123?feature=1&embed=true"
}
```

**AI Chat Response:**

```json
{
  "response": "Based on the carbon monitoring data for Carbon Reserve Area 1 in São Paulo, this 150.75 hectare area currently stores approximately 2,543.67 tons of CO₂ equivalent. This represents a healthy carbon sequestration rate of about 16.87 tons CO₂/hectare, which is above average for this region..."
}
```

## 🛠️ Development Setup

1. **Backend Services**

   ```bash
   # Start PostgreSQL with PostGIS
   docker-compose up postgres

   # Start FastAPI server
   python -m uvicorn src.wsgi:app --reload --port 8000
   ```

2. **Frontend Development**

   ```bash
   cd frontendts
   npm install
   npm run dev  # Starts on localhost:5173
   ```

3. **Environment Setup**
   ```bash
   cp .env.example .env
   # Configure database and OpenAI credentials
   ```

## 📊 Key Metrics & Benefits

- **Zero Authentication Friction**: Public access for embedded contexts
- **Optimized UX**: Higher zoom levels show geometry immediately
- **Intelligent Responses**: Context-aware AI analysis of carbon data
- **Responsive Design**: Works seamlessly in iframe environments
- **Progressive Enhancement**: Core features work without dependencies

## 🔒 Security Considerations

- **Public Data Only**: No sensitive user data exposed via public endpoints
- **Rate Limiting**: Consider implementing for production deployment
- **CORS Policy**: Specific origins configuration prevents abuse
- **Input Validation**: All user inputs sanitized and validated
- **System User Isolation**: Public maps use dedicated system account

## 📈 Future Enhancements

- **Caching Layer**: Redis caching for frequently accessed features
- **Analytics Integration**: Usage tracking for embedded maps
- **Advanced Filtering**: Support for geographic and temporal filters
- **Batch Operations**: Bulk feature processing capabilities
- **Real-time Updates**: WebSocket integration for live data

---

## 🤝 Contributing

This implementation provides a complete iframe embedding solution for carbon monitoring data with intelligent AI assistance. The modular architecture allows for easy extension and customization based on specific deployment requirements.

For questions or improvements, please refer to the main repository documentation or create an issue in the project repository.
