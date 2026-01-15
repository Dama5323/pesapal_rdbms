"""
Core database engine - Main DB class
"""
import json
import os
from typing import Dict, List, Any, Optional, Set
from table import Table
from storage import StorageEngine
from parser import SQLParser

class Database:
    """Main database class"""
    
    def __init__(self, name: str = "default"):
        self.name = name
        self.tables: Dict[str, Table] = {}
        self.storage = StorageEngine(name)
        
        # Load existing database if exists
        if os.path.exists(f"data/{name}/metadata.json"):
            self._load_from_storage()
    
    def _load_from_storage(self):
        """Load database from storage"""
        metadata = self.storage.load_metadata()
        for table_name, table_info in metadata.get("tables", {}).items():
            table = Table(
                name=table_name,
                columns=table_info["columns"],
                primary_key=table_info["primary_key"],
                unique_keys=table_info["unique_keys"]
            )
            table.data = self.storage.load_table_data(table_name)
            # Rebuild indexes
            if table.primary_key:
                table._create_index(table.primary_key)
            for key in table.unique_keys:
                table._create_index(key)
            self.tables[table_name] = table
    
    def create_table(self, name: str, columns: Dict[str, str], 
                    primary_key: Optional[str] = None,
                    unique_keys: List[str] = None) -> Table:
        """Create a new table"""
        if name in self.tables:
            raise ValueError(f"Table '{name}' already exists")
        
        table = Table(name, columns, primary_key, unique_keys or [])
        self.tables[name] = table
        
        # Save metadata
        self._save_metadata()
        return table
    
    def drop_table(self, name: str) -> bool:
        """Drop a table"""
        if name in self.tables:
            del self.tables[name]
            self._save_metadata()
            self.storage.delete_table(name)
            return True
        return False
    
    def get_table(self, name: str) -> Optional[Table]:
        """Get a table by name"""
        return self.tables.get(name)
    
    def execute(self, sql: str) -> Dict:
        """Execute SQL command"""
        from .parser import SQLParser
        return SQLParser().parse_and_execute(sql, self)
    
    def save(self):
        """Save entire database"""
        for table_name, table in self.tables.items():
            self.storage.save_table(table_name, table.data, table.indexes)
        self._save_metadata()
    
    def _save_metadata(self):
        """Save database metadata"""
        metadata = {
            "name": self.name,
            "tables": {}
        }
        
        for table_name, table in self.tables.items():
            metadata["tables"][table_name] = {
                "columns": table.columns,
                "primary_key": table.primary_key,
                "unique_keys": table.unique_keys,
                "row_count": len(table.data)
            }
        
        self.storage.save_metadata(metadata)
    
    def list_tables(self) -> List[str]:
        """List all table names"""
        return list(self.tables.keys())