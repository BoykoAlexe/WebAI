import typer
import uvicorn
from config import get_app_settings
from app import app as apps

app_cli = typer.Typer()
config = get_app_settings()


@app_cli.command()
def api():
    uvicorn.run(
        apps,
        host=config.HOST,
        port=config.PORT,
        workers=config.WORKERS,
    )


if __name__ == "__main__":
    app_cli()