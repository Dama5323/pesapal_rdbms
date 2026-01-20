"""
Core database engine - Main DB class
"""
import json
import os
from typing import Dict, List, Any, Optional, Set
from rdbms.table import Table 
from .storage import JSONStorage
from .parser import SQLParser


class Database:
    """Main database class"""
    
    def __init__(self, name: str = "default"):
        self.name = name
        self.tables: Dict[str, Table] = {}
        self.storage = JSONStorage(name)
        self.parser = SQLParser()  
        
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
    
    # === CRUD OPERATIONS ===
    
    def insert(self, table_name: str, data: Dict[str, Any]) -> bool:
        """Insert data into table"""
        if table_name not in self.tables:
            raise ValueError(f"Table '{table_name}' doesn't exist")
        
        table = self.tables[table_name]
        success = table.insert(data)
        if success:
            self.storage.save_table(table_name, table.data, table.indexes)
        return success
    
    def select(self, table_name: str, conditions: Dict[str, Any] = None) -> List[Dict]:
        """Select data from table"""
        if table_name not in self.tables:
            raise ValueError(f"Table '{table_name}' doesn't exist")
        
        table = self.tables[table_name]
        return table.select(conditions or {})
    
    def update(self, table_name: str, updates: Dict[str, Any], 
               conditions: Dict[str, Any] = None) -> int:
        """Update data in table"""
        if table_name not in self.tables:
            raise ValueError(f"Table '{table_name}' doesn't exist")
        
        table = self.tables[table_name]
        count = table.update(updates, conditions or {})
        if count > 0:
            self.storage.save_table(table_name, table.data, table.indexes)
        return count
    
    def delete(self, table_name: str, conditions: Dict[str, Any] = None) -> int:
        """Delete data from table"""
        if table_name not in self.tables:
            raise ValueError(f"Table '{table_name}' doesn't exist")
        
        table = self.tables[table_name]
        count = table.delete(conditions or {})
        if count > 0:
            self.storage.save_table(table_name, table.data, table.indexes)
        return count
    
    # === SQL EXECUTION ===
    
    
    def execute(self, sql: str) -> Dict[str, Any]:
        """
        Execute SQL statement and return results
        
        Args:
            sql: SQL statement to execute
            
        Returns:
            Dictionary with 'status', 'message', and 'data' if applicable
        """
        try:
            sql = sql.strip()
            
            # Parse the SQL
            parsed = self.parser.parse(sql)
            
            if parsed is None or 'type' not in parsed:
                return {
                    'status': 'error',
                    'message': f'Unknown syntax: {sql}'
                }
            
            # Handle SHOW TABLES
            if parsed.get('type') == 'SHOW_TABLES':
                tables = self.list_tables()
                return {
                    'status': 'success',
                    'message': f'Found {len(tables)} table(s)',
                    'data': tables,
                    'count': len(tables)
                }
            
            # Handle DROP TABLE
            elif parsed.get('type') == 'DROP_TABLE':
                table_name = parsed['table_name']
                success = self.drop_table(table_name)
                if success:
                    return {
                        'status': 'success',
                        'message': f'Table "{table_name}" dropped',
                        'data': None
                    }
                else:
                    return {
                        'status': 'error',
                        'message': f'Table "{table_name}" not found'
                    }
            
            elif parsed.get('type') == 'CREATE_TABLE':
                table_name = parsed['table_name']
                columns = parsed['columns']
                primary_key = parsed.get('primary_key')
                unique_keys = parsed.get('unique_keys', [])
                
                self.create_table(table_name, columns, primary_key, unique_keys)
                return {
                    'status': 'success',
                    'message': f'Table "{table_name}" created successfully',
                    'data': None
                }
                
            elif parsed.get('type') == 'INSERT':
                table_name = parsed['table_name']
                values = parsed['values']
                
                self.insert(table_name, values)
                return {
                    'status': 'success', 
                    'message': f'Record inserted into "{table_name}"',
                    'data': None
                }
                
            elif parsed.get('type') == 'SELECT':
                table_name = parsed['table_name']
                conditions = parsed.get('conditions', {})
                join_info = parsed.get('join', None)
                
                if join_info:
                    # Handle JOIN
                    main_table = table_name
                    join_table = join_info['table']
                    main_key = join_info['main_key']
                    join_key = join_info['join_key']
                    join_type = join_info.get('type', 'INNER')
                    
                    result = self.join_tables(
                        main_table, join_table, 
                        main_key, join_key, join_type
                    )
                else:
                    # Simple SELECT
                    result = self.select(table_name, conditions)
                    
                return {
                    'status': 'success',
                    'message': f'Query executed successfully',
                    'data': result,
                    'count': len(result)
                }
                
            elif parsed.get('type') == 'UPDATE':
                table_name = parsed['table_name']
                updates = parsed['updates']
                conditions = parsed.get('conditions', {})
                
                self.update(table_name, updates, conditions)
                return {
                    'status': 'success',
                    'message': f'Table "{table_name}" updated',
                    'data': None
                }
                
            elif parsed.get('type') == 'DELETE':
                table_name = parsed['table_name']
                conditions = parsed.get('conditions', {})
                
                self.delete(table_name, conditions)
                return {
                    'status': 'success',
                    'message': f'Records deleted from "{table_name}"',
                    'data': None
                }
                
            elif parsed.get('type') == 'ERROR':
                return {
                    'status': 'error',
                    'message': parsed.get('error', 'Unknown parser error')
                }
                
            else:
                return {
                    'status': 'error',
                    'message': f'Unsupported SQL type: {parsed.get("type")}'
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }
    
    # === JOIN OPERATIONS ===
    
    def join_tables(self, table1: str, table2: str, 
                    key1: str, key2: str, 
                    join_type: str = 'INNER') -> List[Dict]:
        """
        Perform JOIN operation between two tables
        
        Args:
            table1: First table name
            table2: Second table name  
            key1: Join key from table1
            key2: Join key from table2
            join_type: JOIN type ('INNER', 'LEFT', 'RIGHT')
            
        Returns:
            List of joined records
        """
        if table1 not in self.tables or table2 not in self.tables:
            raise ValueError(f"Table not found: {table1 if table1 not in self.tables else table2}")
        
        data1 = self.tables[table1].data
        data2 = self.tables[table2].data
        
        result = []
        
        if join_type.upper() == 'INNER':
            # INNER JOIN
            for row1 in data1:
                for row2 in data2:
                    if row1.get(key1) == row2.get(key2):
                        joined = {**row1, **{f"{table2}_{k}": v for k, v in row2.items()}}
                        result.append(joined)
                        
        elif join_type.upper() == 'LEFT':
            # LEFT JOIN (all from table1, matching from table2)
            for row1 in data1:
                matched = False
                for row2 in data2:
                    if row1.get(key1) == row2.get(key2):
                        joined = {**row1, **{f"{table2}_{k}": v for k, v in row2.items()}}
                        result.append(joined)
                        matched = True
                if not matched:
                    # Add row1 with NULLs for table2 columns
                    null_row2 = {f"{table2}_{k}": None for k in data2[0].keys() if data2}
                    result.append({**row1, **null_row2})
                    
        elif join_type.upper() == 'RIGHT':
            # RIGHT JOIN (all from table2, matching from table1)
            for row2 in data2:
                matched = False
                for row1 in data1:
                    if row1.get(key1) == row2.get(key2):
                        joined = {**row1, **{f"{table2}_{k}": v for k, v in row2.items()}}
                        result.append(joined)
                        matched = True
                if not matched:
                    # Add row2 with NULLs for table1 columns
                    null_row1 = {f"{table1}_{k}": None for k in data1[0].keys() if data1}
                    result.append({**null_row1, **row2})
        
        return result
    
    # === DATABASE MANAGEMENT ===
    
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