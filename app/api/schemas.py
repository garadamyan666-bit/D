"""Public API schemas."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ErrorResponse(BaseModel):
    detail: str


class HealthResponse(BaseModel):
    status: str
    binance_connected: bool
    analysis_only: bool = True


class AnalysisResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    symbol: str
    timeframe: str
    timestamp: str
    current_price: float
    signal: str
    confidence: float
    trend: str
    reasons: list[str]
    warnings: list[str]
    analysis_only: bool


class AlertCreate(BaseModel):
    source: str = "BINANCE"
    symbol: str
    timeframe: str
    min_confidence: float = Field(default=70, ge=1, le=100)


class AlertLanguageUpdate(BaseModel):
    language: str
