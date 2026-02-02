"""Static file serving for production build.

Serves the React production build from FastAPI.
"""

from fastapi import APIRouter
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import os

router = APIRouter()

# Path to frontend build directory
BUILD_DIR = Path(__file__).parent.parent.parent.parent / "frontend" / "build"
STATIC_DIR = BUILD_DIR / "static"

# Check if build directory exists
BUILD_EXISTS = BUILD_DIR.exists() and BUILD_DIR.is_dir()


def mount_static_files(app):
    """Mount static file serving to FastAPI app.
    
    Args:
        app: FastAPI application instance
    """
    if not BUILD_EXISTS:
        print(f"⚠️  Frontend build directory not found at: {BUILD_DIR}")
        print("   Run 'npm run build' in frontend directory to create production build.")
        return

    # Mount static assets (JS, CSS, images, etc.)
    if STATIC_DIR.exists():
        app.mount(
            "/static",
            StaticFiles(directory=str(STATIC_DIR)),
            name="static"
        )
        print(f"✅ Mounted static assets from: {STATIC_DIR}")

    # Mount other build assets (favicon, manifest, etc.)
    build_assets = [
        "favicon.ico",
        "logo192.png",
        "logo512.png",
        "manifest.json",
        "robots.txt",
    ]
    
    for asset in build_assets:
        asset_path = BUILD_DIR / asset
        if asset_path.exists():
            @app.get(f"/{asset}")
            async def serve_asset(path=asset_path):
                return FileResponse(str(path))

    print(f"✅ Production build ready at: {BUILD_DIR}")


@router.get("/{full_path:path}")
async def serve_react_app(full_path: str):
    """Serve React app for all frontend routes.
    
    This is a catch-all route that serves index.html for any path
    that doesn't match an API route. This enables client-side routing.
    
    Args:
        full_path: The requested path
        
    Returns:
        index.html or 404
    """
    if not BUILD_EXISTS:
        return HTMLResponse(
            content="""
            <html>
                <head>
                    <title>Build Not Found</title>
                    <style>
                        body {
                            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            height: 100vh;
                            margin: 0;
                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                            color: white;
                        }
                        .container {
                            text-align: center;
                            padding: 2rem;
                            background: rgba(0,0,0,0.2);
                            border-radius: 1rem;
                            backdrop-filter: blur(10px);
                        }
                        code {
                            background: rgba(0,0,0,0.3);
                            padding: 0.5rem 1rem;
                            border-radius: 0.5rem;
                            display: inline-block;
                            margin: 1rem 0;
                        }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h1>⚠️ Frontend Build Not Found</h1>
                        <p>The production build has not been created yet.</p>
                        <p>Run the following command in the frontend directory:</p>
                        <code>npm run build</code>
                        <p style="margin-top: 2rem; font-size: 0.9rem; opacity: 0.8;">
                            Build directory: """ + str(BUILD_DIR) + """
                        </p>
                    </div>
                </body>
            </html>
            """,
            status_code=503
        )
    
    # Serve index.html for all routes (client-side routing)
    index_path = BUILD_DIR / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path), media_type="text/html")
    
    return HTMLResponse(content="<h1>404 - Not Found</h1>", status_code=404)
