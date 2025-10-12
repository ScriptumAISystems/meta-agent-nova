"""Entry point for the LangChain ↔︎ n8n bridge container."""

from nova.automation import BridgeSettings, create_bridge_app

settings = BridgeSettings.from_env()
app = create_bridge_app(settings=settings)


if __name__ == "__main__":  # pragma: no cover - manual execution
    import uvicorn

    uvicorn.run("deploy.automation.bridge.app:app", host="0.0.0.0", port=8080, reload=True)
