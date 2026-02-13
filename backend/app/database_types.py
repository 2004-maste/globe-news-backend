"""
Database type compatibility layer for SQLite and PostgreSQL.
Simplified version using String for IDs.
"""
import uuid
from sqlalchemy import types
from sqlalchemy.dialects import postgresql
import json
from sqlalchemy.types import TypeDecorator, CHAR
import uuid

class UUID(TypeDecorator):
    impl = CHAR

    def load_dialect_impl(self, dialect):
        return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if not isinstance(value, str):
            return str(value)
        return value

    def process_result_value(self, value, dialect):
        return value



class CompatibleUUID(types.TypeDecorator):
    """
    Compatible UUID type that works with both SQLite and PostgreSQL.
    Stores as CHAR(36) in SQLite and UUID in PostgreSQL.
    """
    impl = types.String(36)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if isinstance(value, uuid.UUID):
            return str(value)
        return value

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        return str(value)


class CompatibleJSON(types.TypeDecorator):
    """
    Compatible JSON type.
    """
    impl = types.Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return json.dumps(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return json.loads(value)


class CompatibleArray(types.TypeDecorator):
    """
    Compatible Array type for SQLite.
    Stores arrays as JSON strings.
    """
    impl = types.Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return json.dumps(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return json.loads(value)