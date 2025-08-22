# 🌱 EcoLedger Carbon Monitoring Iframe Integration

# Run

`py -m uvicorn src.wsgi:app --host localhost --port 8000 --log-level debug --access-log --use-colors --reload `

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
# Environment variable-based CORS configuration
cors_origins = [
    os.getenv("FRONT_MUNDI_BASE_URL", "http://localhost:5173"),
    os.getenv("UNKNOWN_BASE_URL", "http://localhost:3000"),
    os.getenv("ECOLEDGER_FRONT_BASE_URL", "http://localhost:8081"),
    "null"  # Allow null origin for local file access
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)
```

**Environment Variables for CORS** (`.env`):

```bash
# CORS Configuration - individual frontend base URLs
FRONT_MUNDI_BASE_URL=http://localhost:5173
UNKNOWN_BASE_URL=http://localhost:3000
ECOLEDGER_FRONT_BASE_URL=http://localhost:8081
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

#### **Feature Map Component** (`frontendts/src/components/FeatureMap.tsx`)

```tsx
import { buildApiUrl } from "../lib/config";

// Environment-aware API integration
const apiUrl = buildApiUrl(`/public/feature/${id}`);

// Embed mode optimization
const isEmbedMode = searchParams.get("embed") === "true";
```

#### **Configuration Utility** (`frontendts/src/lib/config.ts`)

Centralized configuration management:

```tsx
// Get API base URL from environment variables
export const getApiBaseUrl = (): string => {
  return import.meta.env.VITE_WEBSITE_DOMAIN || window.location.origin;
};

// Build API URLs with proper base URL handling
export const buildApiUrl = (
  endpoint: string,
  useLocalhost?: boolean
): string => {
  const baseUrl = useLocalhost ? "http://localhost:8000" : getApiBaseUrl();
  return `${baseUrl}${endpoint}`;
};
```

**Frontend Environment Variables** (`frontendts/.env`):

```bash
VITE_WEBSITE_DOMAIN=http://localhost:8000
VITE_EMAIL_VERIFICATION=disable
VITE_AUTH_MODE=enabled
VITE_POSTHOG_API_KEY=
```

#### **Enhanced Map Component** (`frontendts/src/components/MapLibreMap.tsx`)

Key improvements:

- **Safe Authentication Wrappers**: Graceful degradation when auth unavailable
- **Optimized Zoom Levels**: `maxZoom: 18` with higher initial zoom
- **Green Geometry Highlighting**: Clear carbon feature visualization
- **Container-Responsive Design**: Chat components sized relative to iframe container
  - Chat panel: 30% width with 200px-300px constraints
  - Chat input: 70% width with 250px-500px constraints
- **Environment-Aware API Calls**: Uses `buildApiUrl` utility for consistent endpoint construction
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

### Backend Configuration (`.env`)

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

# CORS Configuration - individual frontend base URLs
FRONT_MUNDI_BASE_URL=http://localhost:5173
UNKNOWN_BASE_URL=http://localhost:3000
ECOLEDGER_FRONT_BASE_URL=http://localhost:8081

# DriftDB Configuration
DRIFTDB_SERVER_URL=http://localhost:8080

# QGIS Processing Configuration
QGIS_PROCESSING_HOST=localhost
QGIS_PROCESSING_PORT=8817
```

### Frontend Configuration (`frontendts/.env`)

```bash
# API Base URL - points to backend server
VITE_WEBSITE_DOMAIN=http://localhost:8000

# Authentication Configuration
VITE_EMAIL_VERIFICATION=disable
VITE_AUTH_MODE=enabled

# Analytics (optional)
VITE_POSTHOG_API_KEY=

# Development settings can be added as needed
```

### Environment Variable Benefits

- **Environment-Specific Configuration**: Different URLs for dev/staging/production
- **Centralized Management**: All configuration in environment files
- **Type Safety**: Frontend variables have TypeScript declarations
- **Flexible CORS**: Individual control over each frontend origin
- **Easy Deployment**: Configuration without code changes

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
      <iframe
        id="map-iframe"
        width="100%"
        height="600px"
        style="border: none; border-radius: 8px;"
      ></iframe>
    </div>

    <script>
      // Environment-aware configuration
      const API_BASE = "http://localhost:8000/public";
      const FRONTEND_BASE = "http://localhost:5173";

      // Load features with error handling
      async function loadFeatures() {
        try {
          const response = await fetch(`${API_BASE}/features`);
          if (!response.ok) throw new Error("Failed to load features");
          const data = await response.json();
          displayFeatures(data.features);
        } catch (error) {
          console.error("Error loading features:", error);
        }
      }

      // Create and display responsive map
      async function viewFeatureOnMap(featureId) {
        try {
          const response = await fetch(
            `${API_BASE}/create-map-for-feature/${featureId}`,
            { method: "POST" }
          );
          const mapData = await response.json();

          if (mapData.success) {
            const iframe = document.getElementById("map-iframe");
            iframe.src = `${FRONTEND_BASE}${mapData.embed_url}`;

            // Show map view with smooth transition
            document.getElementById("map-view").style.display = "block";
          }
        } catch (error) {
          console.error("Error creating map:", error);
        }
      }

      // Initialize dashboard
      loadFeatures();
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

   # Configure environment variables
   cp .env.example .env
   # Edit .env with your database and OpenAI credentials

   # Start FastAPI server
   python -m uvicorn src.wsgi:app --reload --port 8000
   ```

2. **Frontend Development**

   ```bash
   cd frontendts

   # Install dependencies
   npm install

   # Configure frontend environment
   cp .env.example .env
   # Edit .env with your frontend configuration

   # Start development server
   npm run dev  # Starts on localhost:5173
   ```

3. **Environment Setup**

   **Backend (`.env`):**

   ```bash
   # Copy example and configure
   cp .env.example .env

   # Required variables:
   POSTGRES_URL=postgresql://user:password@localhost:5432/database
   OPENAI_API_KEY=sk-proj-your-key-here
   FRONT_MUNDI_BASE_URL=http://localhost:5173
   UNKNOWN_BASE_URL=http://localhost:3000
   ECOLEDGER_FRONT_BASE_URL=http://localhost:8081
   ```

   **Frontend (`frontendts/.env`):**

   ```bash
   # API configuration
   VITE_WEBSITE_DOMAIN=http://localhost:8000
   VITE_AUTH_MODE=enabled
   ```

4. **Verify Setup**

   ```bash
   # Test backend API
   curl http://localhost:8000/public/features

   # Test frontend
   open http://localhost:5173

   # Test iframe embedding
   open external-frontend-demo.html
   ```

## 📊 Key Metrics & Benefits

- **Zero Authentication Friction**: Public access for embedded contexts
- **Container-Responsive Design**: Chat components adapt to iframe dimensions
- **Environment-Aware Configuration**: Seamless deployment across environments
- **Optimized UX**: Higher zoom levels show geometry immediately
- **Intelligent Responses**: Context-aware AI analysis of carbon data
- **Type-Safe Configuration**: TypeScript declarations for environment variables
- **Centralized API Management**: Single configuration utility for all endpoints
- **Progressive Enhancement**: Core features work without dependencies
- **Flexible CORS Policy**: Individual control per frontend origin

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
- **Multi-Environment Deployment**: Automated configuration for different stages
- **Enhanced Responsive Design**: Adaptive layouts for various iframe sizes
- **Configuration Validation**: Runtime validation of environment variables
- **API Rate Limiting**: Protection against abuse in production
- **Error Boundary Components**: Better error handling in iframe contexts

---

## 🤝 Contributing

This implementation provides a complete iframe embedding solution for carbon monitoring data with intelligent AI assistance. The modular architecture allows for easy extension and customization based on specific deployment requirements.

For questions or improvements, please refer to the main repository documentation or create an issue in the project repository.
