"""
Scalar API documentation integration for FastAPI
"""

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

def get_scalar_api_reference(
    openapi_url: str,
    title: str = "API Documentation",
    theme: str = "purple"
) -> HTMLResponse:
    """
    Generate Scalar API documentation HTML
    
    Args:
        openapi_url: URL to the OpenAPI JSON specification
        title: Title for the documentation page
        theme: Color theme (purple, blue, green, etc.)
    
    Returns:
        HTMLResponse with Scalar documentation
    """
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{title} - Scalar API Reference</title>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <style>
            body {{
                margin: 0;
                padding: 0;
            }}
        </style>
    </head>
    <body>
        <script
            id="api-reference"
            data-url="{openapi_url}"
            data-configuration='{{
                "theme": "{theme}",
                "darkMode": true,
                "layout": "modern",
                "searchHotKey": "k",
                "showSidebar": true,
                "customCss": ".darklight {{ display: none; }}"
            }}'
        ></script>
        <script src="https://cdn.jsdelivr.net/npm/@scalar/api-reference"></script>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html)

def setup_scalar_docs(app: FastAPI, path: str = "/scalar", **kwargs):
    """
    Add Scalar documentation endpoint to a FastAPI app
    
    Args:
        app: FastAPI application instance
        path: URL path for the documentation
        **kwargs: Additional arguments passed to get_scalar_api_reference
    """
    @app.get(path, include_in_schema=False)
    async def scalar_docs():
        return get_scalar_api_reference(
            openapi_url=app.openapi_url,
            title=app.title,
            **kwargs
        )