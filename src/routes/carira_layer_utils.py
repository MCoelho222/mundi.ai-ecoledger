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

import logging
import secrets
import string
import json
from typing import Optional
from ..structures import get_async_db_connection

logger = logging.getLogger(__name__)


def generate_layer_id() -> str:
    """Generate a unique 12-character layer ID starting with 'L'."""
    # Generate 11 random alphanumeric characters
    chars = string.ascii_letters + string.digits
    random_part = "".join(secrets.choice(chars) for _ in range(11))
    return f"L{random_part}"


async def create_carira_postgis_connection(owner_uuid: str) -> str:
    """
    Create a PostGIS connection that points to the internal database
    for accessing CariraFeatures.

    Returns the connection ID.
    """
    try:
        async with get_async_db_connection() as conn:
            # Generate a unique connection ID
            connection_id = "C" + "".join(
                secrets.choice(string.ascii_letters + string.digits) for _ in range(11)
            )

            # First we need to create a project for this user if they don't have one
            # or find an existing project to associate the connection with
            existing_project = await conn.fetchval(
                "SELECT id FROM user_mundiai_projects WHERE owner_uuid = $1 AND soft_deleted_at IS NULL LIMIT 1",
                owner_uuid,
            )

            if not existing_project:
                # Create a project for this connection
                project_id = "P" + "".join(
                    secrets.choice(string.ascii_letters + string.digits)
                    for _ in range(11)
                )
                await conn.execute(
                    """
                    INSERT INTO user_mundiai_projects (
                        id, owner_uuid, title, description, created_on, last_edited
                    ) VALUES (
                        $1, $2, $3, $4, NOW(), NOW()
                    )
                    """,
                    project_id,
                    owner_uuid,
                    "Internal CariraFeatures Project",
                    "Auto-generated project for CariraFeatures layer",
                )
            else:
                project_id = existing_project

            # Create the PostGIS connection with connection URI
            connection_uri = (
                "postgresql://mundiuser:gdalpassword@postgresdb:5432/mundidb"
            )

            await conn.execute(
                """
                INSERT INTO project_postgres_connections (
                    id, project_id, user_id, connection_uri, connection_name, created_at
                ) VALUES (
                    $1, $2, $3, $4, $5, NOW()
                )
                """,
                connection_id,
                project_id,
                owner_uuid,
                connection_uri,
                "Internal CariraFeatures",
            )

            logger.info(
                f"Created internal PostGIS connection {connection_id} for CariraFeatures"
            )
            return connection_id

    except Exception as e:
        logger.error(f"Error creating CariraFeatures PostGIS connection: {str(e)}")
        raise


async def create_carira_layer(owner_uuid: str, postgis_connection_id: str) -> str:
    """
    Create a CariraFeatures layer that shows all CariraFeatures on the map.

    Returns the layer ID.
    """
    try:
        async with get_async_db_connection() as conn:
            layer_id = generate_layer_id()

            # SQL query to get CariraFeatures as GeoJSON
            postgis_query = """
            SELECT 
                id,
                property_code,
                municipality,
                area_id,
                area_name,
                app_area,
                total_area,
                biomass_area,
                carbon_area,
                soil_carbon,
                tree_carbon,
                herbaceous_carbon,
                litter_carbon,
                total_carbon,
                annual_carbon_capture,
                co2_emission,
                monitoring_date,
                vegetation_type,
                land_use,
                reforestation_age,
                estimation_method,
                data_source,
                estimation_error,
                responsible,
                geometry
            FROM carira_features
            WHERE owner_uuid = $1
            """

            # Get bounds and feature count
            bounds_result = await conn.fetchrow(
                """
                SELECT 
                    ST_XMin(ST_Extent(geometry)) as xmin,
                    ST_YMin(ST_Extent(geometry)) as ymin,
                    ST_XMax(ST_Extent(geometry)) as xmax,
                    ST_YMax(ST_Extent(geometry)) as ymax,
                    COUNT(*) as feature_count
                FROM carira_features 
                WHERE owner_uuid = $1 AND geometry IS NOT NULL
                """,
                owner_uuid,
            )

            bounds = None
            feature_count = 0

            if bounds_result and bounds_result["feature_count"] > 0:
                bounds = [
                    bounds_result["xmin"],
                    bounds_result["ymin"],
                    bounds_result["xmax"],
                    bounds_result["ymax"],
                ]
                feature_count = bounds_result["feature_count"]

            # Create the layer
            await conn.execute(
                """
                INSERT INTO map_layers (
                    layer_id, owner_uuid, name, path, type,
                    postgis_connection_id, postgis_query, metadata,
                    bounds, geometry_type, feature_count, size_bytes, created_on, last_edited
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, NOW(), NOW()
                )
                """,
                layer_id,
                owner_uuid,
                "Carira Carbon Features",
                "",  # path (not used for PostGIS layers)
                "postgis",
                postgis_connection_id,
                postgis_query,
                json.dumps(
                    {
                        "description": "Carbon monitoring features from Carira municipality",
                        "source": "CariraFeatures table",
                        "auto_generated": True,
                    }
                ),
                bounds,
                "polygon",
                feature_count,
                0,  # size_bytes (not applicable for PostGIS)
            )

            logger.info(
                f"Created CariraFeatures layer {layer_id} with {feature_count} features"
            )
            return layer_id

    except Exception as e:
        logger.error(f"Error creating CariraFeatures layer: {str(e)}")
        raise


async def ensure_carira_layer_exists(owner_uuid: str) -> Optional[str]:
    """
    Ensure that a CariraFeatures layer exists for the given user.
    If it doesn't exist, create it.

    Returns the layer ID or None if creation failed.
    """
    try:
        async with get_async_db_connection() as conn:
            # Check if CariraFeatures layer already exists
            existing_layer = await conn.fetchval(
                """
                SELECT layer_id FROM map_layers 
                WHERE owner_uuid = $1 
                AND name = 'Carira Carbon Features'
                AND type = 'postgis'
                """,
                owner_uuid,
            )

            if existing_layer:
                logger.info(f"CariraFeatures layer {existing_layer} already exists")
                return existing_layer

            # Check if we have any CariraFeatures to display
            feature_count = await conn.fetchval(
                "SELECT COUNT(*) FROM carira_features WHERE owner_uuid = $1", owner_uuid
            )

            logger.info(f"Found {feature_count} CariraFeatures for user {owner_uuid}")

            if feature_count == 0:
                logger.info("No CariraFeatures found, skipping layer creation")
                return None

            # Create PostGIS connection and layer
            logger.info("Creating PostGIS connection...")
            postgis_connection_id = await create_carira_postgis_connection(owner_uuid)
            logger.info(f"PostGIS connection created: {postgis_connection_id}")

            logger.info("Creating Carira layer...")
            layer_id = await create_carira_layer(owner_uuid, postgis_connection_id)
            logger.info(f"Carira layer created: {layer_id}")

            logger.info(
                f"Created new CariraFeatures layer {layer_id} for user {owner_uuid}"
            )
            return layer_id

    except Exception as e:
        logger.error(f"Error ensuring CariraFeatures layer exists: {str(e)}")
        return None
