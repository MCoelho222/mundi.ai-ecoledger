// Copyright Bunting Labs, Inc. 2025

import { useEffect, useState, useCallback } from "react";
import { useParams, useSearchParams } from "react-router-dom";
import MapLibreMap from "./MapLibreMap";
import { toast } from "sonner";
import { buildApiUrl } from "../lib/config";
import "maplibre-gl/dist/maplibre-gl.css";

// interface Feature {
//   id: number;
//   user_id?: string;
//   name?: string;
//   description?: string;
//   status?: string;
//   start_date?: string; // Use string for date fields (ISO format) in TypeScript interfaces
//   end_date?: string;
//   area_hectares?: number;
//   carbon_credits_generated?: number;
//   location?: string;
//   project_type?: string;
//   certification_status?: string;
//   created_at?: string;
//   updated_at?: string;
// }

interface MapData {
  type: "FeatureCollection";
  features: Array<{
    type: "Feature";
    properties: any;
    geometry: any;
  }>;
}

export default function FeatureMap() {
  const { projectId } = useParams();
  const [searchParams] = useSearchParams();
  const featureId = searchParams.get("feature");
  const isEmbedMode = searchParams.get("embed") === "true";

  // const [feature, setFeature] = useState<Feature | null>(null);
  const [mapData, setMapData] = useState<MapData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load feature data
  const loadFeature = useCallback(async (id: string) => {
    try {
      setLoading(true);
      setError(null);

      // Use public API endpoint to avoid authentication issues in iframe embeds
      const apiUrl = buildApiUrl(`/public/feature/${id}`, true);

      const response = await fetch(apiUrl);
      if (!response.ok) {
        throw new Error(`Failed to load feature: ${response.statusText}`);
      }

      const featureData = await response.json();
      // setFeature(featureData);
      console.log(featureData);
      // Convert to MapLibre-compatible GeoJSON
      if (featureData.geometry) {
        const geoJsonFeature = {
          type: "Feature" as const,
          properties: featureData,
          geometry: featureData.geometry,
        };

        setMapData({
          type: "FeatureCollection",
          features: [geoJsonFeature],
        });
        console.log(mapData);
      }
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Unknown error occurred";
      setError(errorMessage);
      toast.error(`Error loading feature: ${errorMessage}`);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (featureId) {
      loadFeature(featureId);
    } else {
      setError("No feature ID provided in URL");
      setLoading(false);
    }
  }, [featureId, loadFeature]);

  // Render loading state
  if (loading) {
    return (
      <div
        className={`flex items-center justify-center ${
          isEmbedMode ? "h-screen" : "h-full min-h-96"
        }`}
      >
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading Feature...</p>
        </div>
      </div>
    );
  }

  // Render error state
  if (error) {
    return (
      <div
        className={`flex items-center justify-center ${
          isEmbedMode ? "h-screen" : "h-full min-h-96"
        }`}
      >
        <div className="text-center p-8">
          <div className="text-red-600 mb-4">
            <svg
              className="w-16 h-16 mx-auto"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 15.5c-.77.833.192 2.5 1.732 2.5z"
              />
            </svg>
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            Error Loading Feature
          </h3>
          <p className="text-gray-600 mb-4">{error}</p>
          {featureId && (
            <button
              onClick={() => loadFeature(featureId)}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
            >
              Try Again
            </button>
          )}
        </div>
      </div>
    );
  }

  // Render the map with feature data
  return (
    <div className={`${isEmbedMode ? "h-screen" : "h-full"} flex flex-col`}>
      {/* Feature Info Header (hidden in embed mode) */}
      {/* {!isEmbedMode && feature && (
        <div className="bg-white border-b border-gray-200 p-4">
          <div className="flex justify-between items-start">
            <div>
              <h2 className="text-xl font-semibold text-gray-900">
                {feature.area_name || `Feature ${feature.id}`}
              </h2>
              <p className="text-gray-600">
                {feature.municipality && `${feature.municipality} • `}
                {feature.total_carbon &&
                  `${feature.total_carbon.toFixed(2)}t Carbon`}
              </p>
            </div>
            <div className="text-right text-sm text-gray-500">
              <p>Feature ID: {feature.id}</p>
              {feature.monitoring_date && (
                <p>
                  Monitored:{" "}
                  {new Date(feature.monitoring_date).toLocaleDateString()}
                </p>
              )}
            </div>
          </div>
        </div>
      )} */}

      {/* Map Container */}
      <div className="flex-1 relative">
        {mapData && projectId ? (
          <MapLibreMap FeatureData={mapData} isEmbedMode={isEmbedMode} />
        ) : (
          <div className="flex items-center justify-center h-full">
            <p className="text-gray-600">
              No geometry data available for this feature
            </p>
          </div>
        )}
      </div>

      {/* Feature Details Panel (only in non-embed mode) */}
      {/* {!isEmbedMode && feature && (
        <div className="bg-white border-t border-gray-200 p-4 max-h-48 overflow-y-auto">
          <h3 className="text-lg font-semibold mb-3">
            Carbon Monitoring Details
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            {feature.total_area && (
              <div>
                <span className="font-medium text-gray-700">Total Area:</span>
                <p className="text-gray-600">
                  {feature.total_area.toFixed(2)} ha
                </p>
              </div>
            )}
            {feature.soil_carbon && (
              <div>
                <span className="font-medium text-gray-700">Soil Carbon:</span>
                <p className="text-gray-600">
                  {feature.soil_carbon.toFixed(2)}t
                </p>
              </div>
            )}
            {feature.tree_carbon && (
              <div>
                <span className="font-medium text-gray-700">Tree Carbon:</span>
                <p className="text-gray-600">
                  {feature.tree_carbon.toFixed(2)}t
                </p>
              </div>
            )}
            {feature.annual_carbon_capture && (
              <div>
                <span className="font-medium text-gray-700">
                  Annual Capture:
                </span>
                <p className="text-gray-600">
                  {feature.annual_carbon_capture.toFixed(2)}t/year
                </p>
              </div>
            )}
            {feature.vegetation_type && (
              <div>
                <span className="font-medium text-gray-700">Vegetation:</span>
                <p className="text-gray-600">{feature.vegetation_type}</p>
              </div>
            )}
            {feature.land_use && (
              <div>
                <span className="font-medium text-gray-700">Land Use:</span>
                <p className="text-gray-600">{feature.land_use}</p>
              </div>
            )}
            {feature.responsible && (
              <div>
                <span className="font-medium text-gray-700">Responsible:</span>
                <p className="text-gray-600">{feature.responsible}</p>
              </div>
            )}
            {feature.data_source && (
              <div>
                <span className="font-medium text-gray-700">Data Source:</span>
                <p className="text-gray-600">{feature.data_source}</p>
              </div>
            )}
          </div>
        </div>
      )} */}
    </div>
  );
}
