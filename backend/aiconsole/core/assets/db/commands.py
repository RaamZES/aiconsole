import click
from aiconsole.core.assets.db.recreate_assets_table import recreate_assets_table

@click.command()
def recreate_assets_table_command():
    """Recreates the assets table with the updated schema."""
    import asyncio
    asyncio.run(recreate_assets_table())
    click.echo("Assets table has been recreated successfully.") 