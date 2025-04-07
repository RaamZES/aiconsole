from sqlalchemy import text
from aiconsole.core.assets.database import get_db
from aiconsole.core.assets.models import Base, AssetModel

async def recreate_assets_table():
    """
    Recreates the assets table with the updated schema.
    WARNING: This will delete all existing data in the assets table.
    """
    async for db in get_db():
        # Drop the existing table
        await db.execute(text("DROP TABLE IF EXISTS assets"))
        
        # Create the table with the new schema
        await db.execute(text("""
            CREATE TABLE assets (
                id VARCHAR PRIMARY KEY,
                name VARCHAR,
                version VARCHAR DEFAULT '0.0.1',
                usage VARCHAR,
                usage_examples VARCHAR,
                defined_in VARCHAR,
                type VARCHAR,
                default_status VARCHAR DEFAULT 'ENABLED',
                status VARCHAR DEFAULT 'ENABLED',
                override BOOLEAN DEFAULT FALSE,
                content_type VARCHAR,
                content VARCHAR,
                system VARCHAR,
                gpt_mode VARCHAR,
                execution_mode VARCHAR
            )
        """))
        
        await db.commit()
        print("Assets table has been recreated successfully.")

if __name__ == "__main__":
    import asyncio
    asyncio.run(recreate_assets_table()) 