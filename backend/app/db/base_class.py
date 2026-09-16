from typing import Any
from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase, declared_attr

# ==============================================================================
# Database Naming Conventions
# ==============================================================================
# Standardizes constraints generation to prevent database-specific name clashes,
# particularly important when operating on PostgreSQL.
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

# Consolidate metadata registry with convention mapping
db_metadata = MetaData(naming_convention=NAMING_CONVENTION)


class Base(DeclarativeBase):
    """
    Unified Declarative Base for all JobCatalyst AI database entities.
    Automatically formats snake_case table names and binds standard index metadata.
    """
    metadata = db_metadata

    @declared_attr.directive
    def __tablename__(cls) -> str:
        """
        Dynamically infers the PostgreSQL database table name from class name.
        Example: UserProfile -> user_profile
        """
        name = cls.__name__
        parts = []
        current_part = []
        for char in name:
            if char.isupper():
                if current_part:
                    parts.append("".join(current_part).lower())
                    current_part = []
            current_part.append(char)
        if current_part:
            parts.append("".join(current_part).lower())
        return "_".join(parts)
