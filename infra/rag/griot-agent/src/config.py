"""Configuration for the Griot Agent."""

from typing import Annotated

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Agent configuration from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env.local",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # LLM settings (Llama-4-Scout-17B via MaaS)
    # Maps LLAMA_API_URL -> llm_api_url, etc.
    llm_api_url: Annotated[
        str,
        Field(
            default="https://llama-4-scout-17b-16e-w4a16-maas-apicast-production.apps.prod.rhoai.rh-aiservices-bu.com:443/v1",
            validation_alias="LLAMA_API_URL",
        ),
    ]
    llm_model: Annotated[
        str,
        Field(
            default="llama-4-scout-17b-16e-w4a16",
            validation_alias="LLAMA_MODEL",
        ),
    ]
    llm_api_key: Annotated[
        str,
        Field(
            default="",
            validation_alias="LLAMA_API_KEY",
        ),
    ]
    llm_temperature: float = 0.1
    llm_max_tokens: int = 2048

    # Retrieval MCP server
    retrieval_mcp_url: str = "https://retrieval-mcp-gng-user50.apps.ocp.tvbt2.sandbox3429.opentlc.com/mcp/"

    # Ingestion MCP server (for future use)
    ingestion_mcp_url: str = "https://ingestion-mcp-gng-user50.apps.ocp.tvbt2.sandbox3429.opentlc.com/mcp/"

    # Vector gateway (for direct access if needed)
    vector_gateway_url: str = "https://vector-gateway-gng-user50.apps.ocp.tvbt2.sandbox3429.opentlc.com"

    # Default collection
    default_collection: str = "griot"

    # Search settings
    search_top_k: int = 5
    search_score_threshold: float = 0.5


def get_settings() -> Settings:
    """Get settings instance."""
    return Settings()
