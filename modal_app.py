"""
Modal deployment configuration for the FastAPI RAG API.

This file lets you:
- Run the API on Modal's infrastructure (`modal deploy modal_app.py`)
- Exercise the app locally via Modal's CLI (`modal run modal_app.py`)
"""

import modal

# -----------------------------------------------------------------------------
# 1. Modal App
# -----------------------------------------------------------------------------
# The App is the top-level container for all Modal objects (functions, images,
# schedules, etc.). The name is what you'll see in the Modal dashboard.
app = modal.App("rag-api")


# -----------------------------------------------------------------------------
# 2. Modal Image
# -----------------------------------------------------------------------------
# The Image defines the container environment: base OS + pip packages.
# Local files are copied into the image at build time.
image = (
    modal.Image.debian_slim()
    .pip_install(
        "fastapi",
        "uvicorn",
        "openai",
        "faiss-cpu",
        "pydantic",
        "langchain",
        "langchain-openai",
        "langchain-community",
        "python-dotenv",
    )
    .add_local_file("api.py", remote_path="/root/api.py", copy=True)
    .add_local_file("SimpleRag.py", remote_path="/root/SimpleRag.py", copy=True)
    .add_local_file("RagDocument.txt", remote_path="/root/RagDocument.txt", copy=True)
)


# -----------------------------------------------------------------------------
# 3. ASGI FastAPI deployment
# -----------------------------------------------------------------------------
# @app.function:
#   - Declares a Modal function that can be invoked remotely.
#   - Binds config such as the image, secrets, timeouts, etc.
#
# @modal.asgi_app():
#   - Tells Modal this function returns an ASGI application (FastAPI/Starlette).
#   - Modal will automatically serve it behind an HTTP endpoint.
#
# Secrets:
#   - `modal.Secret.from_name("openai-secret")` should contain your OPENAI_API_KEY
#     (and any other relevant env vars) configured in the Modal UI/CLI.


@app.function(image=image)
def debug_files():
    """Debug: List all files in the container"""
    import os

    print("Files in /root:")
    for root, dirs, files in os.walk("/root"):
        for file in files:
            print(f"  {os.path.join(root, file)}")

    print("\nCurrent working directory:", os.getcwd())
    print("Files in current directory:")
    for file in os.listdir("."):
        print(f"  {file}")


@app.function(
    image=image,
    secrets=[modal.Secret.from_name("openai-secret")],
)
@modal.asgi_app()
def fastapi_app():
    """
    Entrypoint for the FastAPI ASGI app on Modal.

    Modal will call this once per container to get the ASGI application object.
    """
    import sys

    sys.path.insert(0, "/root")
    from api import app

    return app


# -----------------------------------------------------------------------------
# 4. Local entrypoint for development
# -----------------------------------------------------------------------------
# @app.local_entrypoint:
#   - Runs on your local machine when you execute:
#       `modal run modal_app.py`
#   - Does NOT deploy to Modal; it's just a convenient local helper.
#
# Typical usage:
#   - Sanity-check configuration.
#   - Print information or run quick, local-only tests.
@app.local_entrypoint()
def main():
    print("Modal RAG API configuration loaded.")
    print("To run the API on Modal:")
    print("  1) Ensure your 'openai-secret' is configured with OPENAI_API_KEY.")
    print("  2) Deploy with:  modal deploy modal_app.py")
    print("  3) View the endpoint URL in the Modal dashboard.")
    print()
    print("For a one-off local test of this file via Modal CLI:")
    print("  modal run modal_app.py")

