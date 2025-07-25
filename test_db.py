import asyncpg
import asyncio
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()


async def test_connection():
    try:
        # Use the credentials from .env file
        conn = await asyncpg.connect(os.getenv("POSTGRES_URL"))
        print("Connection to external Supabase database successful!")
        await conn.close()
    except Exception as e:
        print(f"Connection failed: {e}")


if __name__ == "__main__":
    asyncio.run(test_connection())
