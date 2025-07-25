# Copyright (C) 2025 Bunting Labs, Inc.

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from typing import List, Optional
from datetime import date
from uuid import UUID
import logging
import json
import secrets
import string

from ..dependencies.session import verify_session_required, UserContext
from ..structures import get_async_db_connection
from .carira_layer_utils import ensure_carira_layer_exists

logger = logging.getLogger(__name__)

carira_router = APIRouter()


class CariraFeatureCreate(BaseModel):
    property_code: Optional[str] = None
    municipality: Optional[str] = None
    area_id: Optional[str] = None
    area_name: Optional[str] = None
    app_area: Optional[float] = None
    total_area: Optional[float] = None
    biomass_area: Optional[float] = None
    carbon_area: Optional[float] = None
    soil_carbon: Optional[float] = None
    tree_carbon: Optional[float] = None
    herbaceous_carbon: Optional[float] = None
    litter_carbon: Optional[float] = None
    total_carbon: Optional[float] = None
    annual_carbon_capture: Optional[float] = None
    co2_emission: Optional[float] = None
    monitoring_date: Optional[date] = None
    vegetation_type: Optional[str] = None
    land_use: Optional[str] = None
    reforestation_age: Optional[int] = None
    estimation_method: Optional[str] = None
    data_source: Optional[str] = None
    estimation_error: Optional[float] = None
    responsible: Optional[str] = None
    geometry: Optional[dict] = None  # GeoJSON geometry object


class CariraFeatureResponse(BaseModel):
    id: int
    owner_uuid: UUID
    property_code: Optional[str] = None
    municipality: Optional[str] = None
    area_id: Optional[str] = None
    area_name: Optional[str] = None
    app_area: Optional[float] = None
    total_area: Optional[float] = None
    biomass_area: Optional[float] = None
    carbon_area: Optional[float] = None
    soil_carbon: Optional[float] = None
    tree_carbon: Optional[float] = None
    herbaceous_carbon: Optional[float] = None
    litter_carbon: Optional[float] = None
    total_carbon: Optional[float] = None
    annual_carbon_capture: Optional[float] = None
    co2_emission: Optional[float] = None
    monitoring_date: Optional[date] = None
    vegetation_type: Optional[str] = None
    land_use: Optional[str] = None
    reforestation_age: Optional[int] = None
    estimation_method: Optional[str] = None
    data_source: Optional[str] = None
    estimation_error: Optional[float] = None
    responsible: Optional[str] = None
    geometry: Optional[dict] = None  # GeoJSON geometry object


class CariraFeatureCreateResponse(BaseModel):
    success: bool
    message: str
    feature_id: Optional[int] = None


class CariraFeaturesListResponse(BaseModel):
    features: List[CariraFeatureResponse]
    total_count: int


class BulkImportResponse(BaseModel):
    success: bool
    message: str
    created_count: int
    errors: List[str] = []


@carira_router.post(
    "/",
    response_model=CariraFeatureCreateResponse,
    operation_id="create_carira_feature",
)
async def create_carira_feature(
    feature_data: CariraFeatureCreate,
    session: UserContext = Depends(verify_session_required),
):
    """
    Create a new Carira feature record.
    """
    user_id = session.get_user_id()

    try:
        async with get_async_db_connection() as conn:
            # Prepare geometry parameter
            geometry_param = None
            if feature_data.geometry:
                geometry_param = json.dumps(feature_data.geometry)

            # Insert the new feature
            if geometry_param:
                feature_id = await conn.fetchval(
                    """
                    INSERT INTO carira_features (
                        owner_uuid, property_code, municipality, area_id, area_name,
                        app_area, total_area, biomass_area, carbon_area, soil_carbon,
                        tree_carbon, herbaceous_carbon, litter_carbon, total_carbon,
                        annual_carbon_capture, co2_emission, monitoring_date,
                        vegetation_type, land_use, reforestation_age, estimation_method,
                        data_source, estimation_error, responsible, geometry
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
                        $11, $12, $13, $14, $15, $16, $17, $18, $19, $20,
                        $21, $22, $23, $24, ST_GeomFromGeoJSON($25)
                    ) RETURNING id
                    """,
                    user_id,
                    feature_data.property_code,
                    feature_data.municipality,
                    feature_data.area_id,
                    feature_data.area_name,
                    feature_data.app_area,
                    feature_data.total_area,
                    feature_data.biomass_area,
                    feature_data.carbon_area,
                    feature_data.soil_carbon,
                    feature_data.tree_carbon,
                    feature_data.herbaceous_carbon,
                    feature_data.litter_carbon,
                    feature_data.total_carbon,
                    feature_data.annual_carbon_capture,
                    feature_data.co2_emission,
                    feature_data.monitoring_date,
                    feature_data.vegetation_type,
                    feature_data.land_use,
                    feature_data.reforestation_age,
                    feature_data.estimation_method,
                    feature_data.data_source,
                    feature_data.estimation_error,
                    feature_data.responsible,
                    geometry_param,
                )
            else:
                feature_id = await conn.fetchval(
                    """
                    INSERT INTO carira_features (
                        owner_uuid, property_code, municipality, area_id, area_name,
                        app_area, total_area, biomass_area, carbon_area, soil_carbon,
                        tree_carbon, herbaceous_carbon, litter_carbon, total_carbon,
                        annual_carbon_capture, co2_emission, monitoring_date,
                        vegetation_type, land_use, reforestation_age, estimation_method,
                        data_source, estimation_error, responsible
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
                        $11, $12, $13, $14, $15, $16, $17, $18, $19, $20,
                        $21, $22, $23, $24
                    ) RETURNING id
                    """,
                    user_id,
                    feature_data.property_code,
                    feature_data.municipality,
                    feature_data.area_id,
                    feature_data.area_name,
                    feature_data.app_area,
                    feature_data.total_area,
                    feature_data.biomass_area,
                    feature_data.carbon_area,
                    feature_data.soil_carbon,
                    feature_data.tree_carbon,
                    feature_data.herbaceous_carbon,
                    feature_data.litter_carbon,
                    feature_data.total_carbon,
                    feature_data.annual_carbon_capture,
                    feature_data.co2_emission,
                    feature_data.monitoring_date,
                    feature_data.vegetation_type,
                    feature_data.land_use,
                    feature_data.reforestation_age,
                    feature_data.estimation_method,
                    feature_data.data_source,
                    feature_data.estimation_error,
                    feature_data.responsible,
                )

            logger.info(f"Created Carira feature {feature_id} for user {user_id}")

            return CariraFeatureCreateResponse(
                success=True,
                message="Carira feature created successfully",
                feature_id=feature_id,
            )

    except Exception as e:
        logger.error(f"Error creating Carira feature: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create Carira feature",
        )


@carira_router.get(
    "/", response_model=CariraFeaturesListResponse, operation_id="list_carira_features"
)
async def list_carira_features(
    session: UserContext = Depends(verify_session_required),
    limit: int = 50,
    offset: int = 0,
):
    """
    List Carira features owned by the authenticated user.
    """
    user_id = session.get_user_id()

    try:
        async with get_async_db_connection() as conn:
            # Get total count
            total_count = await conn.fetchval(
                """
                SELECT COUNT(*) FROM carira_features 
                WHERE owner_uuid = $1
                """,
                user_id,
            )

            # Get features with geometry
            features_data = await conn.fetch(
                """
                SELECT 
                    id, owner_uuid, property_code, municipality, area_id, area_name,
                    app_area, total_area, biomass_area, carbon_area, soil_carbon,
                    tree_carbon, herbaceous_carbon, litter_carbon, total_carbon,
                    annual_carbon_capture, co2_emission, monitoring_date,
                    vegetation_type, land_use, reforestation_age, estimation_method,
                    data_source, estimation_error, responsible,
                    ST_AsGeoJSON(geometry)::jsonb as geometry
                FROM carira_features 
                WHERE owner_uuid = $1
                ORDER BY id DESC
                LIMIT $2 OFFSET $3
                """,
                user_id,
                limit,
                offset,
            )

            features = []
            for feature in features_data:
                feature_dict = dict(feature)
                # Parse geometry JSON if it exists
                if feature_dict.get("geometry"):
                    try:
                        feature_dict["geometry"] = json.loads(feature_dict["geometry"])
                    except (json.JSONDecodeError, TypeError):
                        feature_dict["geometry"] = None
                features.append(CariraFeatureResponse(**feature_dict))

            return CariraFeaturesListResponse(
                features=features, total_count=total_count
            )

    except Exception as e:
        logger.error(f"Error listing Carira features: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list Carira features",
        )


@carira_router.get(
    "/{feature_id}",
    response_model=CariraFeatureResponse,
    operation_id="get_carira_feature",
)
async def get_carira_feature(
    feature_id: int,
    session: UserContext = Depends(verify_session_required),
):
    """
    Get a specific Carira feature by ID.
    """
    user_id = session.get_user_id()

    try:
        async with get_async_db_connection() as conn:
            feature_data = await conn.fetchrow(
                """
                SELECT 
                    id, owner_uuid, property_code, municipality, area_id, area_name,
                    app_area, total_area, biomass_area, carbon_area, soil_carbon,
                    tree_carbon, herbaceous_carbon, litter_carbon, total_carbon,
                    annual_carbon_capture, co2_emission, monitoring_date,
                    vegetation_type, land_use, reforestation_age, estimation_method,
                    data_source, estimation_error, responsible,
                    ST_AsGeoJSON(geometry)::jsonb as geometry
                FROM carira_features 
                WHERE id = $1 AND owner_uuid = $2
                """,
                feature_id,
                user_id,
            )

            if not feature_data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Carira feature {feature_id} not found",
                )

            feature_dict = dict(feature_data)
            # Parse geometry JSON if it exists
            if feature_dict.get("geometry"):
                try:
                    feature_dict["geometry"] = json.loads(feature_dict["geometry"])
                except (json.JSONDecodeError, TypeError):
                    feature_dict["geometry"] = None

            return CariraFeatureResponse(**feature_dict)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting Carira feature {feature_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get Carira feature",
        )


@carira_router.delete("/{feature_id}", operation_id="delete_carira_feature")
async def delete_carira_feature(
    feature_id: int,
    session: UserContext = Depends(verify_session_required),
):
    """
    Delete a Carira feature by ID.
    """
    user_id = session.get_user_id()

    try:
        async with get_async_db_connection() as conn:
            # Check if feature exists and belongs to user
            feature_exists = await conn.fetchval(
                """
                SELECT id FROM carira_features 
                WHERE id = $1 AND owner_uuid = $2
                """,
                feature_id,
                user_id,
            )

            if not feature_exists:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Carira feature {feature_id} not found",
                )

            # Delete the feature
            await conn.execute(
                """
                DELETE FROM carira_features 
                WHERE id = $1 AND owner_uuid = $2
                """,
                feature_id,
                user_id,
            )

            logger.info(f"Deleted Carira feature {feature_id} for user {user_id}")

            return {"message": f"Carira feature {feature_id} deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting Carira feature {feature_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete Carira feature",
        )


@carira_router.post(
    "/bulk-import",
    response_model=BulkImportResponse,
    operation_id="bulk_import_carira_features",
)
async def bulk_import_carira_features(
    geojson_data: dict,
    session: UserContext = Depends(verify_session_required),
):
    """
    Bulk import Carira features from GeoJSON data.
    Expects a GeoJSON FeatureCollection.
    """
    user_id = session.get_user_id()

    if geojson_data.get("type") != "FeatureCollection":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Expected GeoJSON FeatureCollection",
        )

    features = geojson_data.get("features", [])
    created_count = 0
    errors = []

    # Mapping from Portuguese field names to our database field names
    field_mapping = {
        "cod_imovel": "property_code",
        "municipio": "municipality",
        "id_area": "area_id",
        "nome_area": "area_name",
        "app_area": "app_area",
        "total_area": "total_area",
        "biomassa_area": "biomass_area",
        "carbono_area": "carbon_area",
        "carbono_solo": "soil_carbon",
        "carbono_arvore": "tree_carbon",
        "carbono_herbaceo": "herbaceous_carbon",
        "carbono_serapilheira": "litter_carbon",
        "carbono_total": "total_carbon",
        "captura_carbono_anual": "annual_carbon_capture",
        "emissao_co2": "co2_emission",
        "data_monitoramento": "monitoring_date",
        "tipo_vegetacao": "vegetation_type",
        "uso_solo": "land_use",
        "idade_reflorestamento": "reforestation_age",
        "metodo_estimativa": "estimation_method",
        "fonte_dados": "data_source",
        "erro_estimativa": "estimation_error",
        "responsavel": "responsible",
    }

    try:
        async with get_async_db_connection() as conn:
            for i, feature in enumerate(features):
                try:
                    if (
                        not isinstance(feature, dict)
                        or feature.get("type") != "Feature"
                    ):
                        errors.append(f"Feature {i}: Invalid feature format")
                        continue

                    properties = feature.get("properties", {})
                    geometry = feature.get("geometry")

                    # Skip features without properties
                    if not properties:
                        errors.append(f"Feature {i}: No properties found")
                        continue

                    # Map Portuguese field names to English
                    mapped_data = {}
                    for pt_field, en_field in field_mapping.items():
                        if pt_field in properties and properties[pt_field] is not None:
                            value = properties[pt_field]

                            # Convert string numbers to appropriate types
                            if en_field in [
                                "app_area",
                                "total_area",
                                "biomass_area",
                                "carbon_area",
                                "soil_carbon",
                                "tree_carbon",
                                "herbaceous_carbon",
                                "litter_carbon",
                                "total_carbon",
                                "annual_carbon_capture",
                                "co2_emission",
                                "estimation_error",
                            ]:
                                try:
                                    mapped_data[en_field] = (
                                        float(value) if value != "" else None
                                    )
                                except (ValueError, TypeError):
                                    mapped_data[en_field] = None
                            elif en_field == "reforestation_age":
                                try:
                                    mapped_data[en_field] = (
                                        int(float(value)) if value != "" else None
                                    )
                                except (ValueError, TypeError):
                                    mapped_data[en_field] = None
                            elif en_field == "monitoring_date":
                                # Convert DD/MM/YYYY to date object
                                try:
                                    if "/" in str(value):
                                        day, month, year = str(value).split("/")
                                        mapped_data[en_field] = date(
                                            int(year), int(month), int(day)
                                        )
                                    else:
                                        # Handle YYYY-MM-DD format or try to parse as date
                                        if isinstance(value, str) and len(value) == 10:
                                            year, month, day = value.split("-")
                                            mapped_data[en_field] = date(
                                                int(year), int(month), int(day)
                                            )
                                        else:
                                            mapped_data[en_field] = None
                                except (ValueError, AttributeError, TypeError):
                                    mapped_data[en_field] = None
                            else:
                                mapped_data[en_field] = (
                                    str(value) if value != "" else None
                                )

                    # Insert the feature
                    geometry_param = None
                    if geometry:
                        geometry_param = json.dumps(geometry)

                    if geometry_param:
                        await conn.execute(
                            """
                            INSERT INTO carira_features (
                                owner_uuid, property_code, municipality, area_id, area_name,
                                app_area, total_area, biomass_area, carbon_area, soil_carbon,
                                tree_carbon, herbaceous_carbon, litter_carbon, total_carbon,
                                annual_carbon_capture, co2_emission, monitoring_date,
                                vegetation_type, land_use, reforestation_age, estimation_method,
                                data_source, estimation_error, responsible, geometry
                            ) VALUES (
                                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
                                $11, $12, $13, $14, $15, $16, $17, $18, $19, $20,
                                $21, $22, $23, $24, ST_GeomFromGeoJSON($25)
                            )
                            """,
                            user_id,
                            mapped_data.get("property_code"),
                            mapped_data.get("municipality"),
                            mapped_data.get("area_id"),
                            mapped_data.get("area_name"),
                            mapped_data.get("app_area"),
                            mapped_data.get("total_area"),
                            mapped_data.get("biomass_area"),
                            mapped_data.get("carbon_area"),
                            mapped_data.get("soil_carbon"),
                            mapped_data.get("tree_carbon"),
                            mapped_data.get("herbaceous_carbon"),
                            mapped_data.get("litter_carbon"),
                            mapped_data.get("total_carbon"),
                            mapped_data.get("annual_carbon_capture"),
                            mapped_data.get("co2_emission"),
                            mapped_data.get("monitoring_date"),
                            mapped_data.get("vegetation_type"),
                            mapped_data.get("land_use"),
                            mapped_data.get("reforestation_age"),
                            mapped_data.get("estimation_method"),
                            mapped_data.get("data_source"),
                            mapped_data.get("estimation_error"),
                            mapped_data.get("responsible"),
                            geometry_param,
                        )
                    else:
                        await conn.execute(
                            """
                            INSERT INTO carira_features (
                                owner_uuid, property_code, municipality, area_id, area_name,
                                app_area, total_area, biomass_area, carbon_area, soil_carbon,
                                tree_carbon, herbaceous_carbon, litter_carbon, total_carbon,
                                annual_carbon_capture, co2_emission, monitoring_date,
                                vegetation_type, land_use, reforestation_age, estimation_method,
                                data_source, estimation_error, responsible
                            ) VALUES (
                                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
                                $11, $12, $13, $14, $15, $16, $17, $18, $19, $20,
                                $21, $22, $23, $24
                            )
                            """,
                            user_id,
                            mapped_data.get("property_code"),
                            mapped_data.get("municipality"),
                            mapped_data.get("area_id"),
                            mapped_data.get("area_name"),
                            mapped_data.get("app_area"),
                            mapped_data.get("total_area"),
                            mapped_data.get("biomass_area"),
                            mapped_data.get("carbon_area"),
                            mapped_data.get("soil_carbon"),
                            mapped_data.get("tree_carbon"),
                            mapped_data.get("herbaceous_carbon"),
                            mapped_data.get("litter_carbon"),
                            mapped_data.get("total_carbon"),
                            mapped_data.get("annual_carbon_capture"),
                            mapped_data.get("co2_emission"),
                            mapped_data.get("monitoring_date"),
                            mapped_data.get("vegetation_type"),
                            mapped_data.get("land_use"),
                            mapped_data.get("reforestation_age"),
                            mapped_data.get("estimation_method"),
                            mapped_data.get("data_source"),
                            mapped_data.get("estimation_error"),
                            mapped_data.get("responsible"),
                        )

                    created_count += 1

                except Exception as e:
                    error_msg = f"Feature {i}: {str(e)}"
                    errors.append(error_msg)
                    logger.warning(f"Error importing feature {i}: {str(e)}")
                    continue

        logger.info(
            f"Bulk import completed for user {user_id}: {created_count} created, {len(errors)} errors"
        )

        # Ensure CariraFeatures layer exists and is updated after successful import
        if created_count > 0:
            try:
                layer_id = await ensure_carira_layer_exists(user_id)
                if layer_id:
                    logger.info(
                        f"CariraFeatures layer {layer_id} ready for user {user_id}"
                    )
            except Exception as e:
                logger.warning(
                    f"Could not create/update CariraFeatures layer: {str(e)}"
                )
                # Don't fail the import if layer creation fails

        return BulkImportResponse(
            success=True,
            message=f"Bulk import completed. Created {created_count} features.",
            created_count=created_count,
            errors=errors,
        )

    except Exception as e:
        logger.error(f"Error in bulk import: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to import features",
        )


@carira_router.post("/create-map-layer", operation_id="create_carira_map_layer")
async def create_carira_map_layer(
    session: UserContext = Depends(verify_session_required),
):
    """
    Create or update the CariraFeatures map layer for the authenticated user.
    This makes CariraFeatures visible on the map.
    """
    user_id = session.get_user_id()

    try:
        # Check if user has any CariraFeatures
        async with get_async_db_connection() as conn:
            feature_count = await conn.fetchval(
                "SELECT COUNT(*) FROM carira_features WHERE owner_uuid = $1", user_id
            )

        if feature_count == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No CariraFeatures found. Please import some features first.",
            )

        # Create/update the layer
        layer_id = await ensure_carira_layer_exists(user_id)

        if not layer_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create CariraFeatures layer",
            )

        return {
            "success": True,
            "message": "CariraFeatures layer created/updated successfully",
            "layer_id": layer_id,
            "feature_count": feature_count,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating CariraFeatures map layer: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create CariraFeatures map layer",
        )


@carira_router.post("/create-default-map")
async def create_default_carira_map(
    session: UserContext = Depends(verify_session_required),
):
    """
    Create a default map with CariraFeatures for the current user.
    This endpoint is designed to be called when the user first accesses the application
    to ensure they can see the CariraFeatures on the map.
    """
    user_id = session.get_user_id()

    try:
        async with get_async_db_connection() as conn:
            # Check if user already has a map with CariraFeatures
            existing_map = await conn.fetchrow(
                """
                SELECT m.id, m.title, p.id as project_id
                FROM user_mundiai_maps m
                JOIN user_mundiai_projects p ON m.project_id = p.id
                WHERE p.owner_uuid = $1 AND m.title LIKE '%Carira%'
                AND m.soft_deleted_at IS NULL
                ORDER BY m.created_on DESC
                LIMIT 1
                """,
                user_id,
            )

            if existing_map:
                return {
                    "success": True,
                    "message": "Carira map already exists",
                    "project_id": existing_map["project_id"],
                    "map_id": existing_map["id"],
                    "map_title": existing_map["title"],
                }

            # Create a project first
            project_id = "P" + "".join(
                secrets.choice(string.ascii_letters + string.digits) for _ in range(11)
            )

            await conn.execute(
                """
                INSERT INTO user_mundiai_projects (
                    id, owner_uuid, link_accessible, created_on
                ) VALUES ($1, $2, $3, NOW())
                """,
                project_id,
                user_id,
                True,  # Make publicly accessible
            )

            # Create a map within this project
            map_id = "M" + "".join(
                secrets.choice(string.ascii_letters + string.digits) for _ in range(11)
            )

            await conn.execute(
                """
                INSERT INTO user_mundiai_maps (
                    id, project_id, owner_uuid, title, description, created_on
                ) VALUES ($1, $2, $3, $4, $5, NOW())
                """,
                map_id,
                project_id,
                user_id,  # owner_uuid
                "Carira Carbon Features Map",  # title
                "Interactive map showing carbon monitoring features from Carira municipality",  # description
            )

            # Update project to include this map
            await conn.execute(
                """
                UPDATE user_mundiai_projects
                SET maps = ARRAY[$1]
                WHERE id = $2
                """,
                map_id,
                project_id,
            )

            # Update CariraFeatures to be owned by this user (for demo purposes)
            # In production, you'd filter by user ownership instead
            await conn.execute(
                """
                UPDATE carira_features 
                SET owner_uuid = $1
                WHERE owner_uuid = '00000000-0000-0000-0000-000000000000'
                """,
                user_id,
            )

            # Create the CariraFeatures layer for this user
            logger.info("About to call ensure_carira_layer_exists...")
            try:
                layer_id = await ensure_carira_layer_exists(user_id)
                logger.info(f"ensure_carira_layer_exists returned: {layer_id}")
            except Exception as layer_error:
                logger.error(f"Error in ensure_carira_layer_exists: {str(layer_error)}")
                import traceback

                traceback.print_exc()
                layer_id = None

            if layer_id:
                # Associate the layer with the map
                await conn.execute(
                    """
                    UPDATE user_mundiai_maps
                    SET layers = ARRAY[$1]
                    WHERE id = $2
                    """,
                    layer_id,
                    map_id,
                )

            return {
                "success": True,
                "message": "Default Carira map created successfully",
                "project_id": project_id,
                "map_id": map_id,
                "layer_id": layer_id,
            }

    except Exception as e:
        logger.error(f"Error creating default Carira map: {str(e)}")
        import traceback

        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create default Carira map: {str(e)}",
        )
