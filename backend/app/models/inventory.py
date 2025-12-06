"""Inventory model."""

from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

if TYPE_CHECKING:
    from app.models.player import Player
    from app.models.item import Item


class Inventory(Base):
    """Player inventory model."""

    __tablename__ = "inventory"
    __table_args__ = (
        UniqueConstraint("player_id", "item_id", name="unique_player_item"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    player_id: Mapped[int] = mapped_column(Integer, ForeignKey("players.id"), nullable=False)
    item_id: Mapped[int] = mapped_column(Integer, ForeignKey("items.id"), nullable=False)
    
    # Quantity
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    
    # Equipment status
    equipped: Mapped[bool] = mapped_column(default=False)
    
    # Timestamps
    acquired_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    player: Mapped["Player"] = relationship("Player", back_populates="inventory")
    item: Mapped["Item"] = relationship("Item")

    def __repr__(self) -> str:
        return f"<Inventory(player_id={self.player_id}, item_id={self.item_id}, quantity={self.quantity})>"
