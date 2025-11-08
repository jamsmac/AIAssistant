"""
Schema Generator - Auto-generate SQL schemas from OpenAPI specifications
"""

import re
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class SchemaGenerator:
    """Generator for SQL schemas from OpenAPI/JSON schemas"""

    # Mapping from OpenAPI/JSON Schema types to PostgreSQL types
    TYPE_MAPPING = {
        'string': 'TEXT',
        'integer': 'INTEGER',
        'number': 'DECIMAL',
        'boolean': 'BOOLEAN',
        'array': 'JSONB',
        'object': 'JSONB',
        'date': 'DATE',
        'date-time': 'TIMESTAMP',
        'uuid': 'UUID',
        'email': 'VARCHAR(255)',
        'uri': 'TEXT',
        'binary': 'BYTEA'
    }

    def __init__(self, db_pool):
        self.db_pool = db_pool

    def sanitize_table_name(self, name: str) -> str:
        """Convert name to valid SQL identifier"""
        # Remove special characters, replace with underscore
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', name)
        # Replace multiple underscores with single
        sanitized = re.sub(r'_+', '_', sanitized)
        # Convert to lowercase
        sanitized = sanitized.lower()
        # Remove leading/trailing underscores
        sanitized = sanitized.strip('_')
        # Ensure it doesn't start with a number
        if sanitized and sanitized[0].isdigit():
            sanitized = 'tbl_' + sanitized

        return sanitized or 'generated_table'

    def get_postgres_type(self, property_schema: Dict[str, Any]) -> str:
        """Determine PostgreSQL type from property schema"""
        # Check format first (for string subtypes)
        format_type = property_schema.get('format')
        if format_type and format_type in self.TYPE_MAPPING:
            return self.TYPE_MAPPING[format_type]

        # Check main type
        schema_type = property_schema.get('type', 'string')

        # Handle string with format
        if schema_type == 'string':
            format_type = property_schema.get('format')
            if format_type == 'date':
                return 'DATE'
            elif format_type == 'date-time':
                return 'TIMESTAMP'
            elif format_type == 'email':
                return 'VARCHAR(255)'
            elif format_type == 'uuid':
                return 'UUID'
            elif format_type == 'uri' or format_type == 'url':
                return 'TEXT'

            # Check maxLength for VARCHAR
            max_length = property_schema.get('maxLength')
            if max_length and max_length <= 255:
                return f'VARCHAR({max_length})'

            return 'TEXT'

        # Handle number with precision
        if schema_type == 'number':
            # Check if integer is specified in multipleOf
            if property_schema.get('multipleOf') == 1:
                return 'INTEGER'
            return 'DECIMAL'

        return self.TYPE_MAPPING.get(schema_type, 'TEXT')

    def generate_create_table_sql(self, schema_name: str, schema: Dict[str, Any],
                                 include_audit_fields: bool = True) -> str:
        """Generate CREATE TABLE SQL statement from schema"""
        table_name = self.sanitize_table_name(schema_name)
        properties = schema.get('properties', {})
        required_fields = schema.get('required', [])
        description = schema.get('description', '')

        # Start building SQL
        fields = []

        # Add primary key
        fields.append('id UUID PRIMARY KEY DEFAULT gen_random_uuid()')

        # Add properties as fields
        for field_name, field_schema in properties.items():
            sanitized_field_name = self.sanitize_table_name(field_name)

            # Get PostgreSQL type
            pg_type = self.get_postgres_type(field_schema)

            # Add NOT NULL if required
            not_null = ' NOT NULL' if field_name in required_fields else ''

            # Add default if specified
            default_value = field_schema.get('default')
            default_clause = ''
            if default_value is not None:
                if isinstance(default_value, str):
                    default_clause = f" DEFAULT '{default_value}'"
                elif isinstance(default_value, bool):
                    default_clause = f" DEFAULT {str(default_value).upper()}"
                elif isinstance(default_value, (int, float)):
                    default_clause = f" DEFAULT {default_value}"

            field_sql = f'{sanitized_field_name} {pg_type}{not_null}{default_clause}'
            fields.append(field_sql)

        # Add audit fields if requested
        if include_audit_fields:
            fields.append('created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
            fields.append('updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP')

        # Build complete SQL
        fields_sql = ',\n    '.join(fields)

        sql = f"""-- Auto-generated from OpenAPI schema: {schema_name}
CREATE TABLE IF NOT EXISTS {table_name} (
    {fields_sql}
);
"""

        # Add table comment
        if description:
            escaped_desc = description.replace("'", "''")
            sql += f"\nCOMMENT ON TABLE {table_name} IS '{escaped_desc}';\n"

        # Add column comments
        for field_name, field_schema in properties.items():
            field_description = field_schema.get('description', '')
            if field_description:
                sanitized_field_name = self.sanitize_table_name(field_name)
                escaped_field_desc = field_description.replace("'", "''")
                sql += (f"COMMENT ON COLUMN {table_name}.{sanitized_field_name} "
                       f"IS '{escaped_field_desc}';\n")

        # Add indexes for common fields
        indexed_fields = []
        for field_name, field_schema in properties.items():
            # Index fields commonly used for searching
            if any(keyword in field_name.lower() for keyword in ['email', 'username', 'name', 'code', 'status']):
                sanitized_field_name = self.sanitize_table_name(field_name)
                indexed_fields.append(sanitized_field_name)

        for field in indexed_fields:
            sql += f"\nCREATE INDEX IF NOT EXISTS idx_{table_name}_{field} ON {table_name}({field});"

        # Add timestamp index
        if include_audit_fields:
            sql += f"\nCREATE INDEX IF NOT EXISTS idx_{table_name}_created_at ON {table_name}(created_at DESC);"

        return sql

    def generate_crud_queries(self, schema_name: str, schema: Dict[str, Any]) -> Dict[str, str]:
        """Generate basic CRUD SQL queries for a schema"""
        table_name = self.sanitize_table_name(schema_name)
        properties = schema.get('properties', {})

        # Get field names
        field_names = [self.sanitize_table_name(name) for name in properties.keys()]

        # SELECT query
        select_query = f"""
-- Get all {schema_name} records
SELECT id, {', '.join(field_names)}, created_at, updated_at
FROM {table_name}
ORDER BY created_at DESC
LIMIT 100;
"""

        # INSERT query
        placeholders = ', '.join([f'${i+1}' for i in range(len(field_names))])
        insert_query = f"""
-- Insert new {schema_name} record
INSERT INTO {table_name} ({', '.join(field_names)})
VALUES ({placeholders})
RETURNING id;
"""

        # UPDATE query
        update_sets = ', '.join([f'{name} = ${i+2}' for i, name in enumerate(field_names)])
        update_query = f"""
-- Update {schema_name} record
UPDATE {table_name}
SET {update_sets}, updated_at = CURRENT_TIMESTAMP
WHERE id = $1
RETURNING *;
"""

        # DELETE query
        delete_query = f"""
-- Delete {schema_name} record
DELETE FROM {table_name}
WHERE id = $1;
"""

        return {
            'select': select_query.strip(),
            'insert': insert_query.strip(),
            'update': update_query.strip(),
            'delete': delete_query.strip()
        }

    async def generate_schemas_for_api(self, schemas: Dict[str, Any]) -> Dict[str, str]:
        """Generate SQL for all schemas in an API spec"""
        generated_sql = {}

        for schema_name, schema_def in schemas.items():
            try:
                sql = self.generate_create_table_sql(schema_name, schema_def)
                generated_sql[schema_name] = sql
                logger.info(f"Generated SQL for schema: {schema_name}")
            except Exception as e:
                logger.error(f"Failed to generate SQL for schema {schema_name}: {e}")

        return generated_sql

    async def execute_create_table(self, sql: str, schema_name: str) -> bool:
        """Execute CREATE TABLE SQL statement"""
        table_name = self.sanitize_table_name(schema_name)

        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute(sql)
                logger.info(f"Successfully created table: {table_name}")
                return True
        except Exception as e:
            logger.error(f"Failed to create table {table_name}: {e}")
            return False

    async def save_generated_schema(self, doc_schema_id: str, table_name: str,
                                   sql_statement: str, status: str = "pending",
                                   error_message: Optional[str] = None):
        """Save generated table info to doc_generated_tables"""
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO doc_generated_tables (
                    doc_schema_id, table_name, sql_statement, status, error_message
                ) VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (table_name) DO UPDATE SET
                    sql_statement = EXCLUDED.sql_statement,
                    status = EXCLUDED.status,
                    error_message = EXCLUDED.error_message
            """, doc_schema_id, table_name, sql_statement, status, error_message)

    def generate_migration_file(self, schemas: Dict[str, str], api_name: str) -> str:
        """Generate a complete migration file for all schemas"""
        timestamp = __import__('datetime').datetime.now().strftime('%Y%m%d_%H%M%S')
        file_name = f"{timestamp}_{self.sanitize_table_name(api_name)}_schema.sql"

        migration_sql = f"""-- Auto-generated migration for {api_name}
-- Generated: {timestamp}

BEGIN;

"""

        for schema_name, sql in schemas.items():
            migration_sql += sql + "\n\n"

        migration_sql += """
COMMIT;
"""

        return migration_sql
