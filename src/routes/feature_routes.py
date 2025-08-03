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
from ..dependencies.chat_completions import get_chat_args_provider, ChatArgsProvider
from ..structures import get_async_db_connection
from ..utils import get_openai_client
from .feature_layer_utils import ensure_carira_layer_exists

logger = logging.getLogger(__name__)

iframe_router = APIRouter()
iframe_public_router = APIRouter()


async def generate_intelligent_response(
    user_message: str, feature_context: dict, chat_args: ChatArgsProvider
) -> str:
    """
    Generate an intelligent AI response using OpenAI for the user's question about carbon monitoring data.
    """
    try:
        # Get OpenAI client and model configuration
        client = get_openai_client()
        chat_completions_args = await chat_args.get_args(
            "public_user", "carira_feature_chat"
        )

        # Create context about the carbon monitoring feature
        area_name = (
            feature_context.get("name")
            or f"Project {feature_context.get('project_id')}"
        )

        # Build a comprehensive context string for the AI
        context_parts = []
        context_parts.append(f"Carbon monitoring project data for {area_name}:")

        if feature_context.get("location"):
            context_parts.append(f"- Location: {feature_context['location']}")

        if feature_context.get("area_hectares") is not None:
            context_parts.append(
                f"- Project Area: {feature_context['area_hectares']:.2f} hectares"
            )

        if feature_context.get("carbon_credits_generated") is not None:
            context_parts.append(
                f"- Carbon Credits Generated: {feature_context['carbon_credits_generated']:.2f} credits"
            )

        if feature_context.get("project_type"):
            context_parts.append(f"- Project Type: {feature_context['project_type']}")

        if feature_context.get("status"):
            context_parts.append(f"- Status: {feature_context['status']}")

        if feature_context.get("certification_status"):
            context_parts.append(
                f"- Certification Status: {feature_context['certification_status']}"
            )

        if feature_context.get("start_date"):
            context_parts.append(f"- Start Date: {feature_context['start_date']}")

        if feature_context.get("end_date"):
            context_parts.append(f"- End Date: {feature_context['end_date']}")

        if feature_context.get("description"):
            context_parts.append(f"- Description: {feature_context['description']}")

        if feature_context.get("created_at"):
            context_parts.append(f"- Created: {feature_context['created_at']}")

        if feature_context.get("updated_at"):
            context_parts.append(f"- Last Updated: {feature_context['updated_at']}")

        if feature_context.get("project_area_id"):
            context_parts.append(f"- Area ID: {feature_context['project_area_id']}")

        if feature_context.get("geometry"):
            context_parts.append(
                f"- Geometry present (GeoJSON): {feature_context['geometry']}"
            )

        if feature_context.get("properties"):
            context_parts.append(
                f"- Additional Properties: {feature_context['properties']}"
            )

        context_text = "\n".join(context_parts)

        # Create system prompt for carbon project analysis
        system_prompt = f"""You are an expert carbon monitoring and environmental project analyst. You help users understand carbon credit projects, environmental monitoring data, and project management information.

Current carbon project data:
{context_text}

Guidelines:
- Provide accurate, helpful information about carbon credit projects and environmental data
- Explain concepts clearly for both technical and non-technical users
- Use the specific project data provided when answering questions
- If asked about comparisons, provide context about typical project values
- Be concise but informative
- Focus on actionable insights when possible
- Discuss project status, certification, and carbon credit generation when relevant

Answer the user's question about this carbon monitoring project."""

        # Call OpenAI API
        response = await client.chat.completions.create(
            **chat_completions_args,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            max_tokens=500,  # Keep responses focused
            temperature=0.7,  # Balanced creativity and accuracy
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        logger.error(f"Error generating AI response: {str(e)}")
        # Fallback to rule-based response if AI fails
        return generate_fallback_response(user_message, feature_context)


def generate_fallback_response(user_message: str, feature_context: dict) -> str:
    """
    Generate an intelligent response based on the user's question and feature context.
    This function analyzes the user's message and provides relevant information.
    """
    message_lower = user_message.lower()
    project_name = (
        feature_context.get("name") or f"Project {feature_context.get('project_id')}"
    )

    # Carbon-related questions
    if any(word in message_lower for word in ["carbon", "co2", "emissions", "credits"]):
        if "credits" in message_lower or "generated" in message_lower:
            carbon_credits = feature_context.get("carbon_credits_generated")
            if carbon_credits:
                return f"The project {project_name} has generated {carbon_credits:.2f} carbon credits. These credits represent verified carbon sequestration or emission reductions."
            else:
                return f"Carbon credits data is not available for {project_name}."

        else:
            # General carbon overview
            parts = []
            if feature_context.get("carbon_credits_generated"):
                parts.append(
                    f"Carbon credits generated: {feature_context['carbon_credits_generated']:.2f} credits"
                )
            if feature_context.get("project_type"):
                parts.append(f"Project type: {feature_context['project_type']}")

            if parts:
                return f"Carbon information for {project_name}: {', '.join(parts)}."
            else:
                return f"Carbon data is not available for {project_name}."

    # Area and size questions
    elif any(
        word in message_lower for word in ["area", "size", "hectare", "big", "large"]
    ):
        area_hectares = feature_context.get("area_hectares")
        if area_hectares:
            return f"The project area of {project_name} is {area_hectares:.2f} hectares. For reference, that's equivalent to {area_hectares * 10000:.0f} square meters."
        else:
            return f"Area data is not available for {project_name}."

    # Location questions
    elif any(word in message_lower for word in ["location", "where", "place"]):
        location = feature_context.get("location")
        if location:
            return f"{project_name} is located in {location}."
        else:
            return f"Location information is not available for {project_name}."

    # Project type and status questions
    elif any(
        word in message_lower for word in ["type", "status", "certification", "project"]
    ):
        project_type = feature_context.get("project_type")
        status = feature_context.get("status")
        certification_status = feature_context.get("certification_status")

        response_parts = []
        if project_type:
            response_parts.append(f"Project type: {project_type}")
        if status:
            response_parts.append(f"Status: {status}")
        if certification_status:
            response_parts.append(f"Certification: {certification_status}")

        if response_parts:
            return f"For {project_name}: {', '.join(response_parts)}."
        else:
            return f"Project details are not available for {project_name}."

    # Date and timeline questions
    elif any(
        word in message_lower for word in ["date", "when", "start", "end", "timeline"]
    ):
        start_date = feature_context.get("start_date")
        end_date = feature_context.get("end_date")

        response_parts = []
        if start_date:
            response_parts.append(f"Start date: {start_date}")
        if end_date:
            response_parts.append(f"End date: {end_date}")

        if response_parts:
            return f"Timeline for {project_name}: {', '.join(response_parts)}."
        else:
            return f"Timeline information is not available for {project_name}."

    # Comparison questions
    elif any(
        word in message_lower for word in ["compare", "better", "worse", "good", "bad"]
    ):
        return f"To properly compare {project_name}, I would need data from other similar projects. Currently, I can provide detailed information about this specific project's characteristics and performance."

    # General/greeting questions
    elif any(
        word in message_lower for word in ["hello", "hi", "help", "what can", "about"]
    ):
        return f"Hello! I can help you analyze the carbon project data for {project_name}. You can ask me about carbon credits, project area, location, project type, status, certification, timeline, or request specific information. What would you like to know?"

    # Default response with summary
    else:
        summary_parts = []
        if feature_context.get("carbon_credits_generated"):
            summary_parts.append(
                f"has generated {feature_context['carbon_credits_generated']:.2f} carbon credits"
            )
        if feature_context.get("area_hectares"):
            summary_parts.append(
                f"covers {feature_context['area_hectares']:.2f} hectares"
            )
        if feature_context.get("location"):
            summary_parts.append(f"is located in {feature_context['location']}")

        summary = (
            f"{project_name} " + " and ".join(summary_parts)
            if summary_parts
            else f"{project_name} has carbon project data available"
        )

        return f'I understand you\'re asking about: "{user_message}"\n\n{summary}. You can ask me specific questions about carbon credits, project area, location, project type, status, certification, or timeline.'


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


class FeatureResponse(BaseModel):
    id: int
    project_id: Optional[str] = None
    geometry: Optional[dict] = None  # GeoJSON geometry object
    properties: Optional[dict] = None  # Feature properties


class CariraFeatureCreateResponse(BaseModel):
    success: bool
    message: str
    feature_id: Optional[int] = None


class CariraFeaturesListResponse(BaseModel):
    features: List[FeatureResponse]
    total_count: int


class BulkImportResponse(BaseModel):
    success: bool
    message: str
    created_count: int
    errors: List[str] = []


class FeaturePublicResponse(BaseModel):
    """Public response model for external frontend - limited fields"""

    id: int
    user_id: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    area_hectares: Optional[float] = None
    carbon_credits_generated: Optional[float] = None
    location: Optional[str] = None
    project_type: Optional[str] = None
    certification_status: Optional[str] = None
    created_at: Optional[date] = None
    updated_at: Optional[date] = None


class FeaturesPublicListResponse(BaseModel):
    features: List[FeaturePublicResponse]
    total_count: int


# PUBLIC ENDPOINTS FOR EXTERNAL FRONTEND
@iframe_public_router.get(
    "/features",
    response_model=FeaturesPublicListResponse,
    operation_id="list_features_public",
)
async def list_features_public(
    limit: int = 50,
    offset: int = 0,
):
    """
    Public endpoint to list features for external frontend.
    Returns limited information without requiring authentication.
    """
    try:
        async with get_async_db_connection() as conn:
            # Get total count
            total_count = await conn.fetchval("SELECT COUNT(*) FROM projects")

            # Get features with limited fields
            features_data = await conn.fetch(
                """
                SELECT 
                    id,
                    user_id,
                    name,
                    description,
                    status,
                    start_date,
                    end_date,
                    area_hectares,
                    carbon_credits_generated,
                    location,
                    project_type,
                    certification_status,
                    created_at,
                    updated_at
                FROM projects 
                ORDER BY start_date DESC, id DESC
                LIMIT $1 OFFSET $2
                """,
                limit,
                offset,
            )

            features = [
                FeaturePublicResponse(**dict(feature)) for feature in features_data
            ]

            return FeaturesPublicListResponse(
                features=features, total_count=total_count
            )

    except Exception as e:
        logger.error(f"Error listing public Features: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list Features",
        )


@iframe_public_router.get(
    "/feature/{feature_id}",
    response_model=FeatureResponse,
    operation_id="get_feature_public",
)
async def get_feature_public(feature_id: str):
    """
    Public endpoint to get a specific Feature by ID for map display.
    Returns full feature data including geometry for map visualization.
    """
    try:
        async with get_async_db_connection() as conn:
            feature_data = await conn.fetchrow(
                """
                SELECT 
                    id, project_id, properties, geometry
                FROM project_areas 
                WHERE project_id = $1
                """,
                feature_id,
            )
            if not feature_data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Feature {feature_id} not found",
                )

            feature_dict = dict(feature_data)
            feature_dict["project_id"] = str(feature_dict["project_id"])
            # Parse geometry JSON if it exists
            if feature_dict.get("geometry"):
                try:
                    feature_dict["geometry"] = json.loads(feature_dict["geometry"])
                except (json.JSONDecodeError, TypeError):
                    feature_dict["geometry"] = None
            # Parse geometry JSON if it exists
            if feature_dict.get("properties"):
                try:
                    feature_dict["properties"] = json.loads(feature_dict["properties"])
                except (json.JSONDecodeError, TypeError):
                    feature_dict["properties"] = None

            return FeatureResponse(**feature_dict)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting public Feature {feature_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get Feature",
        )


@iframe_public_router.post(
    "/create-map-for-feature/{feature_id}",
    operation_id="create_public_map_for_feature",
)
async def create_public_map_for_feature(feature_id: str):
    """
    Create a public map that displays a specific Feature.
    This endpoint creates a temporary map that can be embedded in iframes.
    """
    try:
        async with get_async_db_connection() as conn:
            # Check if feature exists
            feature_data = await conn.fetchrow(
                """
                SELECT id, project_id, geometry, properties
                FROM project_areas 
                WHERE project_id = $1
                """,
                feature_id,
            )

            if not feature_data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Ecoledger project {feature_id} not found",
                )

            # Use a default system user UUID for public maps
            system_user_id = "00000000-0000-0000-0000-000000000001"

            # Check if a public map already exists for this feature
            existing_map = await conn.fetchrow(
                """
                SELECT m.id, m.title, p.id as project_id
                FROM user_mundiai_maps m
                JOIN user_mundiai_projects p ON m.project_id = p.id
                WHERE p.owner_uuid = $1 AND m.title LIKE $2
                AND m.soft_deleted_at IS NULL
                ORDER BY m.created_on DESC
                LIMIT 1
                """,
                system_user_id,
                f"%Project - {feature_id}%",
            )
            print(
                {
                    "success": True,
                    "message": "Public map already exists for this feature",
                    "project_id": existing_map["project_id"],
                    "map_id": existing_map["id"],
                    "feature_id": feature_id,
                    "map_url": f"/feature/{existing_map['project_id']}?feature={feature_id}",
                    "embed_url": f"/feature/{existing_map['project_id']}?feature={feature_id}&embed=true",
                }
            )
            if existing_map:
                return {
                    "success": True,
                    "message": "Public map already exists for this feature",
                    "project_id": existing_map["project_id"],
                    "map_id": existing_map["id"],
                    "feature_id": feature_id,
                    "map_url": f"/feature/{existing_map['project_id']}?feature={feature_id}",
                    "embed_url": f"/feature/{existing_map['project_id']}?feature={feature_id}&embed=true",
                }

            # Create a public project
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
                system_user_id,
                True,  # Make publicly accessible
            )

            # Create a map for this specific feature
            map_id = "M" + "".join(
                secrets.choice(string.ascii_letters + string.digits) for _ in range(11)
            )

            map_title = f"Project - {feature_id}"
            map_description = "Map showing carbon monitoring feature"

            await conn.execute(
                """
                INSERT INTO user_mundiai_maps (
                    id, project_id, owner_uuid, title, description, created_on
                ) VALUES ($1, $2, $3, $4, $5, NOW())
                """,
                map_id,
                project_id,
                system_user_id,
                map_title,
                map_description,
            )
            print(
                f"Created public map {map_id} for feature {feature_id} in project {project_id}"
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

            print(f"Public map created successfully for feature {feature_id}: {map_id}")
            return {
                "success": True,
                "message": "Public map created successfully for feature",
                "project_id": project_id,
                "map_id": map_id,
                "feature_id": feature_id,
                "map_url": f"/feature/{project_id}?feature={feature_id}",
                "embed_url": f"/feature/{project_id}?feature={feature_id}&embed=true",
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating public map for feature {feature_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create public map for feature",
        )


@iframe_public_router.post(
    "/feature/{feature_id}/chat", operation_id="chat_with_carira_feature"
)
async def chat_with_carira_feature(
    feature_id: str,
    request: dict,  # Simple dict to receive the chat message
    chat_args: ChatArgsProvider = Depends(get_chat_args_provider),
):
    """
    Chat endpoint for analyzing Carira features.
    Allows users to ask questions about carbon monitoring data and geometry.
    """
    try:
        message = request.get("content", "").strip()
        if not message:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message content is required",
            )

        async with get_async_db_connection() as conn:
            # Get feature data from projects
            feature_data_from_projects = await conn.fetchrow(
                """
                SELECT 
                    id,
                    user_id,
                    name,
                    description,
                    status,
                    start_date,
                    end_date,
                    area_hectares,
                    carbon_credits_generated,
                    location,
                    project_type,
                    certification_status,
                    created_at,
                    updated_at
                FROM projects 
                WHERE id = $1
                """,
                feature_id,
            )
            print(feature_data_from_projects)
            if not feature_data_from_projects:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Feature not found in projects",
                )

            # Get feature data with geometry
            feature_data_from_project_areas = await conn.fetchrow(
                """
                SELECT 
                    id,
                    project_id,
                    geometry,
                    properties
                FROM project_areas 
                WHERE project_id = $1
                """,
                feature_id,
            )

            if not feature_data_from_project_areas:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Feature not found in project areas",
                )

            # Create context about the feature for the AI
            feature_context = {
                "project_id": str(feature_data_from_projects["id"]),
                "user_id": str(feature_data_from_projects["user_id"]),
                "name": feature_data_from_projects["name"],
                "description": feature_data_from_projects["description"],
                "status": feature_data_from_projects["status"],
                "start_date": feature_data_from_projects["start_date"].isoformat()
                if feature_data_from_projects["start_date"]
                else None,
                "end_date": feature_data_from_projects["end_date"].isoformat()
                if feature_data_from_projects["end_date"]
                else None,
                "area_hectares": feature_data_from_projects["area_hectares"],
                "carbon_credits_generated": feature_data_from_projects[
                    "carbon_credits_generated"
                ],
                "location": feature_data_from_projects["location"],
                "project_type": feature_data_from_projects["project_type"],
                "certification_status": feature_data_from_projects[
                    "certification_status"
                ],
                "created_at": feature_data_from_projects["created_at"].isoformat()
                if feature_data_from_projects["created_at"]
                else None,
                "updated_at": feature_data_from_projects["updated_at"].isoformat()
                if feature_data_from_projects["updated_at"]
                else None,
                "project_area_id": str(feature_data_from_project_areas["id"]),
                "geometry": feature_data_from_project_areas["geometry"],
                "properties": feature_data_from_project_areas["properties"]
            }

            # Create an intelligent AI-powered response based on the user's question
            response_text = await generate_intelligent_response(
                message, feature_context, chat_args
            )

            return {
                "role": "assistant",
                "content": response_text,
                "feature_data": feature_context,
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in chat for feature {feature_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process chat message",
        )


# AUTHENTICATED ENDPOINTS


@iframe_router.post(
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


@iframe_router.get(
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
                features.append(FeatureResponse(**feature_dict))

            return CariraFeaturesListResponse(
                features=features, total_count=total_count
            )

    except Exception as e:
        logger.error(f"Error listing Carira features: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list Carira features",
        )


@iframe_router.get(
    "/{feature_id}",
    response_model=FeatureResponse,
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

            return FeatureResponse(**feature_dict)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting Feature {feature_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get Feature",
        )


@iframe_router.delete("/{feature_id}", operation_id="delete_carira_feature")
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


@iframe_router.post(
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


@iframe_router.post("/create-map-layer", operation_id="create_carira_map_layer")
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


@iframe_router.post("/create-default-map")
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
