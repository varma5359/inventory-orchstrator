
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class InventoryManifestItem(BaseModel):
    """One inventory record received from an external ledger."""

    model_config = ConfigDict(extra="forbid")

    sku: str = Field(min_length=1, max_length=100)
    stock_quantity: int = Field(ge=0)

    @field_validator("sku")
    @classmethod
    def validate_sku(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("SKU cannot be empty.")

        return value


class InventoryManifestRequest(BaseModel):
    """Bulk inventory reconciliation request."""

    model_config = ConfigDict(extra="forbid")

    manifest: list[InventoryManifestItem] = Field(
        min_length=1,
        max_length=1000,
    )

    @model_validator(mode="after")
    def validate_unique_skus(self):
        skus = [item.sku for item in self.manifest]

        if len(skus) != len(set(skus)):
            raise ValueError("Duplicate SKUs are not allowed.")

        return self
