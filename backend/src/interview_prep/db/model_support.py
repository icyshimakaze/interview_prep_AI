"Shared relational conventions; private aggregates always retain their owner."

from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.schema import SchemaItem

from interview_prep.db.base import Base


def enum_column(enum: type[StrEnum], name: str) -> Enum:
    # Named CHECK enums make additions reversible without PostgreSQL type replacement.
    return Enum(
        enum,
        name=name,
        native_enum=False,
        create_constraint=True,
        validate_strings=True,
        values_callable=lambda values: [item.value for item in values],
    )


def owned_fk(column: str, parent: str, *, cascade: bool = True) -> ForeignKeyConstraint:
    return ForeignKeyConstraint(
        ["owner_id", column],
        [f"{parent}.owner_id", f"{parent}.id"],
        ondelete="CASCADE" if cascade else "NO ACTION",
        deferrable=not cascade,
        initially=None if cascade else "DEFERRED",
    )


def history_fk(column: str) -> ForeignKey:
    # Checked at commit: allows whole-principal erasure but rejects isolated
    # deletion of content that is still referenced by retained history.
    return ForeignKey(column, ondelete="NO ACTION", deferrable=True, initially="DEFERRED")


def owned_args(table: str, *items: SchemaItem) -> tuple[SchemaItem, ...]:
    return (
        UniqueConstraint("owner_id", "id"),
        CheckConstraint("updated_at >= created_at", name="timestamp_order"),
        Index(f"ix_{table}_owner_created", "owner_id", "created_at"),
        *items,
    )


class Record(Base):
    __abstract__ = True

    id: Mapped[UUID] = mapped_column(
        primary_key=True, default=uuid4, server_default=text("gen_random_uuid()")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class OwnedRecord(Record):
    __abstract__ = True

    owner_id: Mapped[UUID] = mapped_column(ForeignKey("principals.id", ondelete="CASCADE"))
