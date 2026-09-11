"""Shared response schema for CSV import endpoints."""

from pydantic import BaseModel, Field


class CsvImportRowError(BaseModel):
    row: int
    message: str


class CsvImportResponse(BaseModel):
    imported: int = Field(ge=0)
    errors: list[CsvImportRowError] = Field(default_factory=list)
