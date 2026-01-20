"""
Table implementation with CRUD, indexing, and constraints
"""
from typing import Dict, List, Any, Optional, Set
import re


class Table:
    """Represents a database table"""
    
    # Supported data types
    DATA_TYPES = {"INTEGER", "TEXT", "FLOAT", "BOOLEAN", "DATETIME"}
    
    def __init__(self, name: str, columns: Dict[str, str], 
                 primary_key: Optional[str] = None,
                 unique_keys: List[str] = None):
        self.name = name
        self.columns = self._validate_columns(columns)
        self.primary_key = primary_key
        self.unique_keys = unique_keys or []
        self.data: List[Dict] = []
        self.indexes: Dict[str, Dict] = {}
        
        # Validate keys exist in columns
        self._validate_keys()
        
        # Create indexes
        if self.primary_key:
            self._create_index(self.primary_key)
        for key in self.unique_keys:
            self._create_index(key)
    
    def _validate_columns(self, columns: Dict[str, str]) -> Dict[str, str]:
        """Validate column definitions"""
        for col_name, col_type in columns.items():
            if col_type.upper() not in self.DATA_TYPES:
                raise ValueError(f"Unsupported data type: {col_type}")
        return {k: v.upper() for k, v in columns.items()}
    
    def _validate_keys(self):
        """Validate that primary/unique keys exist in columns"""
        if self.primary_key and self.primary_key not in self.columns:
            raise ValueError(f"Primary key '{self.primary_key}' not in columns")
        
        for key in self.unique_keys:
            if key not in self.columns:
                raise ValueError(f"Unique key '{key}' not in columns")
    
    def _create_index(self, column: str):
        """Create an index on a column"""
        if column not in self.columns:
            raise ValueError(f"Column '{column}' does not exist")
        
        self.indexes[column] = {}
        # Build index from existing data
        for i, row in enumerate(self.data):
            if column in row:
                value = row[column]
                if value not in self.indexes[column]:
                    self.indexes[column][value] = []
                self.indexes[column][value].append(i)
    
    def _validate_constraints(self, row_data: Dict) -> bool:
        """Validate primary and unique key constraints"""
        # Check primary key
        if self.primary_key and self.primary_key in row_data:
            pk_value = row_data[self.primary_key]
            if self.primary_key in self.indexes and pk_value in self.indexes[self.primary_key]:
                raise ValueError(f"Primary key violation: {pk_value} already exists")
        
        # Check unique keys
        for unique_key in self.unique_keys:
            if unique_key in row_data:
                uq_value = row_data[unique_key]
                if unique_key in self.indexes and uq_value in self.indexes[unique_key]:
                    raise ValueError(f"Unique key violation on '{unique_key}': {uq_value} already exists")
        
        return True
    
    def _cast_value(self, column: str, value: Any) -> Any:
        """Cast value to appropriate type based on column definition"""
        col_type = self.columns.get(column)
        if col_type is None:
            return value
        
        try:
            if col_type == "INTEGER":
                return int(value)
            elif col_type == "FLOAT":
                return float(value)
            elif col_type == "BOOLEAN":
                if isinstance(value, str):
                    return value.lower() in ["true", "1", "yes", "y"]
                return bool(value)
            elif col_type == "DATETIME":
                # Simple datetime handling
                return str(value)
            else:  # TEXT or others
                return str(value)
        except (ValueError, TypeError):
            raise ValueError(f"Cannot cast {value} to {col_type} for column {column}")
    
    def insert(self, data: Dict) -> int:
        """Insert a row into the table"""
        # Validate columns exist
        for col in data.keys():
            if col not in self.columns:
                raise ValueError(f"Column '{col}' does not exist in table '{self.name}'")
        
        # Cast values to proper types
        casted_data = {}
        for col, value in data.items():
            casted_data[col] = self._cast_value(col, value)
        
        # Validate constraints
        self._validate_constraints(casted_data)
        
        # Add to data
        self.data.append(casted_data)
        row_index = len(self.data) - 1
        
        # Update indexes
        for col in self.indexes.keys():
            if col in casted_data:
                value = casted_data[col]
                if value not in self.indexes[col]:
                    self.indexes[col][value] = []
                self.indexes[col][value].append(row_index)
        
        return row_index
    
    def select(self, where: Optional[Dict] = None, 
              columns: Optional[List[str]] = None,
              limit: Optional[int] = None) -> List[Dict]:
        """Select rows from table"""
        results = []
        
        # Use index if possible
        if where and len(where) == 1:
            col, value = next(iter(where.items()))
            if col in self.indexes:
                # Use index for faster lookup
                if value in self.indexes[col]:
                    indices = self.indexes[col][value]
                    for idx in indices[:limit] if limit else indices:
                        row = self.data[idx]
                        if self._matches_conditions(row, where):
                            if columns:
                                results.append({c: row.get(c) for c in columns})
                            else:
                                results.append(row.copy())
                    return results
        
        # Linear scan (fallback)
        for row in self.data:
            if self._matches_conditions(row, where):
                if columns:
                    filtered_row = {col: row[col] for col in columns if col in row}
                    results.append(filtered_row)
                else:
                    results.append(row.copy())
                
                if limit and len(results) >= limit:
                    break
        
        return results
    
    def update(self, data: Dict, where: Optional[Dict] = None) -> int:
        """Update rows matching WHERE clause"""
        updated_count = 0
        
        for i, row in enumerate(self.data):
            if self._matches_conditions(row, where):
                # Validate unique constraints for updated values
                for unique_key in self.unique_keys:
                    if unique_key in data and unique_key in row:
                        new_value = data[unique_key]
                        old_value = row[unique_key]
                        
                        if new_value != old_value and unique_key in self.indexes:
                            if new_value in self.indexes[unique_key]:
                                # Check if it's the same row
                                indices = self.indexes[unique_key][new_value]
                                if len(indices) > 1 or (len(indices) == 1 and indices[0] != i):
                                    raise ValueError(f"Unique key violation on '{unique_key}'")
                
                # Update the row
                for key, value in data.items():
                    if key in self.columns:
                        # Remove old value from index
                        if key in self.indexes and key in row:
                            old_value = row[key]
                            if old_value in self.indexes[key]:
                                self.indexes[key][old_value].remove(i)
                                if not self.indexes[key][old_value]:
                                    del self.indexes[key][old_value]
                        
                        # Update value
                        row[key] = self._cast_value(key, value)
                        
                        # Add new value to index
                        if key in self.indexes:
                            new_value = row[key]
                            if new_value not in self.indexes[key]:
                                self.indexes[key][new_value] = []
                            self.indexes[key][new_value].append(i)
                
                updated_count += 1
        
        return updated_count
    
    def delete(self, where: Optional[Dict] = None) -> int:
        """Delete rows matching WHERE clause"""
        to_delete = []
        
        # Find indices to delete
        for i, row in enumerate(self.data):
            if self._matches_conditions(row, where):
                to_delete.append(i)
        
        # Delete in reverse order
        for i in sorted(to_delete, reverse=True):
            # Remove from indexes
            for col in self.indexes.keys():
                if col in self.data[i]:
                    value = self.data[i][col]
                    if value in self.indexes[col]:
                        self.indexes[col][value].remove(i)
                        if not self.indexes[col][value]:
                            del self.indexes[col][value]
            
            # Remove from data
            del self.data[i]
        
        return len(to_delete)
    
    def _matches_conditions(self, row: Dict, where: Optional[Dict]) -> bool:
        """Check if row matches WHERE conditions"""
        if not where:
            return True
        
        for key, value in where.items():
            if key not in row:
                return False
            
            # Try to cast the WHERE value
            try:
                casted_value = self._cast_value(key, value)
            except ValueError:
                casted_value = value
            
            # Compare
            if row[key] != casted_value:
                return False
        
        return True
    
    def join(self, other: 'Table', left_on: str, right_on: str, 
             join_type: str = "INNER") -> List[Dict]:
        """Perform a simple JOIN operation"""
        result = []
        
        if join_type.upper() == "INNER":
            # Build index on right table for faster join
            right_index = {}
            for i, row in enumerate(other.data):
                key = row.get(right_on)
                if key not in right_index:
                    right_index[key] = []
                right_index[key].append(i)
            
            # Perform inner join
            for left_row in self.data:
                key = left_row.get(left_on)
                if key in right_index:
                    for right_idx in right_index[key]:
                        right_row = other.data[right_idx]
                        merged_row = {**left_row}
                        # Prefix right table columns to avoid collisions
                        for k, v in right_row.items():
                            merged_row[f"{other.name}_{k}"] = v
                        result.append(merged_row)
        
        elif join_type.upper() == "LEFT":
            # Left join implementation
            right_index = {}
            for i, row in enumerate(other.data):
                key = row.get(right_on)
                if key not in right_index:
                    right_index[key] = []
                right_index[key].append(i)
            
            for left_row in self.data:
                key = left_row.get(left_on)
                if key in right_index:
                    for right_idx in right_index[key]:
                        right_row = other.data[right_idx]
                        merged_row = {**left_row}
                        for k, v in right_row.items():
                            merged_row[f"{other.name}_{k}"] = v
                        result.append(merged_row)
                else:
                    # No match in right table
                    merged_row = {**left_row}
                    for col in other.columns:
                        merged_row[f"{other.name}_{col}"] = None
                    result.append(merged_row)
        
        return result
    
    def count(self, where: Optional[Dict] = None) -> int:
        """Count rows matching conditions"""
        return len(self.select(where))
    
    def describe(self) -> Dict:
        """Get table description"""
        return {
            "name": self.name,
            "columns": self.columns,
            "primary_key": self.primary_key,
            "unique_keys": self.unique_keys,
            "row_count": len(self.data),
            "indexed_columns": list(self.indexes.keys())
        }