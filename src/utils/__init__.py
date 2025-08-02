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

# Import functions from the parent utils.py module
import importlib.util
import os

# Get the parent directory path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Import the utils module from the parent directory
spec = importlib.util.spec_from_file_location(
    "utils", os.path.join(parent_dir, "utils.py")
)
utils_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(utils_module)

# Re-export all the utility functions
generate_id = utils_module.generate_id
get_s3_client = utils_module.get_s3_client
get_async_s3_client = utils_module.get_async_s3_client
get_bucket_name = utils_module.get_bucket_name
process_zip_with_shapefile = utils_module.process_zip_with_shapefile
get_openai_client = utils_module.get_openai_client

__all__ = [
    "generate_id",
    "get_s3_client",
    "get_async_s3_client",
    "get_bucket_name",
    "process_zip_with_shapefile",
    "get_openai_client",
]
