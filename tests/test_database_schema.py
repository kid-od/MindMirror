import importlib
import os
import sys
import types
import unittest
from unittest.mock import MagicMock, patch


class DatabaseSchemaCompatibilityTest(unittest.TestCase):
    def test_ensure_parent_chunk_schema_adds_missing_scope_columns_and_indexes(self):
        with patch.dict(os.environ, {"DATABASE_URL": "sqlite:///:memory:"}):
            import backend.database as database_module

            database_module = importlib.reload(database_module)
        connection = MagicMock()
        engine = MagicMock()
        engine.begin.return_value.__enter__.return_value = connection

        inspector = MagicMock()
        inspector.has_table.return_value = True
        inspector.get_columns.return_value = [
            {"name": "chunk_id"},
            {"name": "text"},
            {"name": "filename"},
            {"name": "file_type"},
            {"name": "file_path"},
            {"name": "page_number"},
            {"name": "parent_chunk_id"},
            {"name": "root_chunk_id"},
            {"name": "chunk_level"},
            {"name": "chunk_idx"},
            {"name": "updated_at"},
        ]
        inspector.get_indexes.return_value = []

        with patch.object(database_module, "inspect", return_value=inspector):
            database_module.ensure_parent_chunk_schema(engine, force=True)

        executed = "\n".join(str(call.args[0]) for call in connection.execute.call_args_list)
        self.assertIn("ALTER TABLE parent_chunks ADD COLUMN visibility", executed)
        self.assertIn("ALTER TABLE parent_chunks ADD COLUMN owner_id", executed)
        self.assertIn("ALTER TABLE parent_chunks ADD COLUMN document_domain", executed)
        self.assertIn("CREATE INDEX IF NOT EXISTS ix_parent_chunks_visibility", executed)
        self.assertIn("CREATE INDEX IF NOT EXISTS ix_parent_chunks_owner_id", executed)
        self.assertIn("CREATE INDEX IF NOT EXISTS ix_parent_chunks_document_domain", executed)

    def test_init_db_runs_schema_compatibility_check_after_create_all(self):
        with patch.dict(os.environ, {"DATABASE_URL": "sqlite:///:memory:"}):
            import backend.database as database_module

            database_module = importlib.reload(database_module)
        fake_models_module = types.ModuleType("models")

        with patch.object(database_module.Base.metadata, "create_all") as create_all, \
             patch.object(database_module, "ensure_parent_chunk_schema") as ensure_parent_chunk_schema, \
             patch.dict(sys.modules, {"models": fake_models_module}):
            database_module.init_db()

        create_all.assert_called_once_with(bind=database_module.engine)
        ensure_parent_chunk_schema.assert_called_once_with(database_module.engine)


if __name__ == "__main__":
    unittest.main()
