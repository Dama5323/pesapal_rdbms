"""
Minimal SQL-like parser - Handles basic SQL commands
"""
import re
from typing import Dict, List, Any, Optional, Tuple

class SQLParser:
    """Simple SQL parser"""
    
    def parse_and_execute(self, sql: str, database) -> Dict:
        """Parse SQL and execute against database"""
        sql = sql.strip()
        sql_upper = sql.upper()
        
        try:
            if sql_upper.startswith("CREATE TABLE"):
                return self._parse_create_table(sql, database)
            elif sql_upper.startswith("INSERT INTO"):
                return self._parse_insert(sql, database)
            elif sql_upper.startswith("SELECT"):
                return self._parse_select(sql, database)
            elif sql_upper.startswith("UPDATE"):
                return self._parse_update(sql, database)
            elif sql_upper.startswith("DELETE FROM"):
                return self._parse_delete(sql, database)
            elif sql_upper.startswith("DROP TABLE"):
                return self._parse_drop_table(sql, database)
            else:
                return {"error": f"Unsupported SQL command: {sql}"}
        except Exception as e:
            return {"error": str(e)}
    
    def parse(self, sql: str) -> Dict:
        """
        Parse SQL into structured format for Database.execute()
        
        Args:
            sql: SQL statement to parse
            
        Returns:
            Dictionary with parsed SQL components
        """
        sql = sql.strip()
        sql_upper = sql.upper()
        
        try:
            if sql_upper.startswith("CREATE TABLE"):
                return self._parse_create_table_structure(sql)
            elif sql_upper.startswith("INSERT INTO"):
                return self._parse_insert_structure(sql)
            elif sql_upper.startswith("SELECT"):
                return self._parse_select_structure(sql)
            elif sql_upper.startswith("UPDATE"):
                return self._parse_update_structure(sql)
            elif sql_upper.startswith("DELETE FROM"):
                return self._parse_delete_structure(sql)
            else:
                return {"type": "UNKNOWN", "error": f"Unsupported SQL: {sql}"}
        except Exception as e:
            return {"type": "ERROR", "error": str(e)}
    
    def _parse_create_table_structure(self, sql: str) -> Dict:
        """Parse CREATE TABLE into structure"""
        pattern = r'CREATE TABLE (\w+) \((.+)\)'
        match = re.match(pattern, sql, re.IGNORECASE | re.DOTALL)
        
        if not match:
            return {"type": "ERROR", "error": "Invalid CREATE TABLE syntax"}
        
        table_name = match.group(1)
        columns_def = match.group(2).strip()
        
        columns = {}
        primary_key = None
        unique_keys = []
        
        # Parse column definitions
        lines = [line.strip() for line in columns_def.split(',')]
        for line in lines:
            line = line.strip()
            if line.upper().startswith('PRIMARY KEY'):
                match_pk = re.match(r'PRIMARY KEY \((\w+)\)', line, re.IGNORECASE)
                if match_pk:
                    primary_key = match_pk.group(1)
            elif line.upper().startswith('UNIQUE'):
                match_uq = re.match(r'UNIQUE \((\w+)\)', line, re.IGNORECASE)
                if match_uq:
                    unique_keys.append(match_uq.group(1))
            else:
                parts = line.split()
                if len(parts) >= 2:
                    col_name = parts[0]
                    col_type = parts[1].upper()
                    columns[col_name] = col_type
        
        return {
            "type": "CREATE_TABLE",
            "table_name": table_name,
            "columns": columns,
            "primary_key": primary_key,
            "unique_keys": unique_keys
        }
    
    def _parse_insert_structure(self, sql: str) -> Dict:
        """Parse INSERT statement into structure"""
        pattern = r'INSERT INTO (\w+) \((.+?)\) VALUES \((.+?)\)'
        match = re.match(pattern, sql, re.IGNORECASE | re.DOTALL)
        
        if not match:
            return {"type": "ERROR", "error": "Invalid INSERT syntax"}
        
        table_name = match.group(1)
        columns = [col.strip() for col in match.group(2).split(',')]
        values = [val.strip().strip("'") for val in match.group(3).split(',')]
        
        if len(columns) != len(values):
            return {"type": "ERROR", "error": "Column count doesn't match value count"}
        
        row_data = {}
        for col, val in zip(columns, values):
            row_data[col] = val
        
        return {
            "type": "INSERT",
            "table_name": table_name,
            "values": row_data
        }
    
    def _parse_select_structure(self, sql: str) -> Dict:
        """Parse SELECT statement into structure"""
        # Check for JOIN
        if "JOIN" in sql.upper():
            return self._parse_join_structure(sql)
        
        # Regular SELECT
        if 'WHERE' in sql.upper():
            pattern = r'SELECT (.+?) FROM (\w+) WHERE (.+)'
            match = re.match(pattern, sql, re.IGNORECASE)
            if not match:
                return {"type": "ERROR", "error": "Invalid SELECT syntax"}
            
            columns_str = match.group(1).strip()
            table_name = match.group(2).strip()
            where_clause = match.group(3).strip()
        else:
            pattern = r'SELECT (.+?) FROM (\w+)'
            match = re.match(pattern, sql, re.IGNORECASE)
            if not match:
                return {"type": "ERROR", "error": "Invalid SELECT syntax"}
            
            columns_str = match.group(1).strip()
            table_name = match.group(2).strip()
            where_clause = None
        
        # Parse columns
        columns = None
        if columns_str != '*':
            columns = [col.strip() for col in columns_str.split(',')]
        
        # Parse WHERE clause
        conditions = {}
        if where_clause:
            # Simple equality conditions only
            cond_parts = where_clause.split('AND')
            for part in cond_parts:
                part = part.strip()
                if '=' in part:
                    left, right = part.split('=', 1)
                    col = left.strip()
                    val = right.strip().strip("'")
                    conditions[col] = val
        
        return {
            "type": "SELECT",
            "table_name": table_name,
            "columns": columns,
            "conditions": conditions,
            "join": None
        }
    
    def _parse_join_structure(self, sql: str) -> Dict:
        """Parse JOIN statement into structure"""
        # Match patterns like: SELECT * FROM table1 INNER JOIN table2 ON table1.id = table2.user_id
        pattern = r'SELECT (.+?) FROM (\w+)\s+(\w+)?\s+JOIN (\w+)\s+ON\s+(.+?)(?:\s+WHERE\s+(.+))?$'
        match = re.match(pattern, sql, re.IGNORECASE)
        
        if not match:
            # Try without JOIN type
            pattern = r'SELECT (.+?) FROM (\w+)\s+JOIN (\w+)\s+ON\s+(.+?)(?:\s+WHERE\s+(.+))?$'
            match = re.match(pattern, sql, re.IGNORECASE)
            if match:
                columns_str = match.group(1).strip()
                table1_name = match.group(2).strip()
                table2_name = match.group(3).strip()
                on_clause = match.group(4).strip()
                where_clause = match.group(5)
                join_type = 'INNER'  # Default
            else:
                return {"type": "ERROR", "error": "Invalid JOIN syntax"}
        else:
            columns_str = match.group(1).strip()
            table1_name = match.group(2).strip()
            join_type = match.group(3).strip().upper() if match.group(3) else 'INNER'
            table2_name = match.group(4).strip()
            on_clause = match.group(5).strip()
            where_clause = match.group(6)
        
        # Parse ON clause
        if '=' in on_clause:
            left, right = on_clause.split('=', 1)
            left_parts = left.strip().split('.')
            right_parts = right.strip().split('.')
            
            if len(left_parts) == 2:
                main_key = left_parts[1].strip()
            else:
                main_key = left_parts[0].strip()
            
            if len(right_parts) == 2:
                join_key = right_parts[1].strip()
            else:
                join_key = right_parts[0].strip()
        else:
            return {"type": "ERROR", "error": "Invalid ON clause"}
        
        # Parse WHERE clause
        conditions = {}
        if where_clause:
            # Simple equality conditions
            cond_parts = where_clause.split('AND')
            for part in cond_parts:
                part = part.strip()
                if '=' in part:
                    left, right = part.split('=', 1)
                    col = left.strip()
                    val = right.strip().strip("'")
                    conditions[col] = val
        
        # Parse columns
        columns = None
        if columns_str != '*':
            columns = [col.strip() for col in columns_str.split(',')]
        
        return {
            "type": "SELECT",
            "table_name": table1_name,
            "columns": columns,
            "conditions": conditions,
            "join": {
                "type": join_type,
                "table": table2_name,
                "main_key": main_key,
                "join_key": join_key
            }
        }
    
    def _parse_update_structure(self, sql: str) -> Dict:
        """Parse UPDATE statement into structure"""
        pattern = r'UPDATE (\w+) SET (.+?)(?: WHERE (.+))?'
        match = re.match(pattern, sql, re.IGNORECASE)
        
        if not match:
            return {"type": "ERROR", "error": "Invalid UPDATE syntax"}
        
        table_name = match.group(1).strip()
        set_clause = match.group(2).strip()
        where_clause = match.group(3)
        
        # Parse SET clause
        updates = {}
        assignments = set_clause.split(',')
        for assignment in assignments:
            if '=' in assignment:
                left, right = assignment.split('=', 1)
                col = left.strip()
                val = right.strip().strip("'")
                updates[col] = val
        
        # Parse WHERE clause
        conditions = {}
        if where_clause:
            # Simple equality conditions
            cond_parts = where_clause.split('AND')
            for part in cond_parts:
                part = part.strip()
                if '=' in part:
                    left, right = part.split('=', 1)
                    col = left.strip()
                    val = right.strip().strip("'")
                    conditions[col] = val
        
        return {
            "type": "UPDATE",
            "table_name": table_name,
            "updates": updates,
            "conditions": conditions
        }
    
    def _parse_delete_structure(self, sql: str) -> Dict:
        """Parse DELETE statement into structure"""
        pattern = r'DELETE FROM (\w+)(?: WHERE (.+))?'
        match = re.match(pattern, sql, re.IGNORECASE)
        
        if not match:
            return {"type": "ERROR", "error": "Invalid DELETE syntax"}
        
        table_name = match.group(1).strip()
        where_clause = match.group(2)
        
        # Parse WHERE clause
        conditions = {}
        if where_clause:
            # Simple equality conditions
            cond_parts = where_clause.split('AND')
            for part in cond_parts:
                part = part.strip()
                if '=' in part:
                    left, right = part.split('=', 1)
                    col = left.strip()
                    val = right.strip().strip("'")
                    conditions[col] = val
        
        return {
            "type": "DELETE",
            "table_name": table_name,
            "conditions": conditions
        }
    
    # === OLD METHODS (for backward compatibility) ===
    
    def _parse_create_table(self, sql: str, database) -> Dict:
        """Parse CREATE TABLE statement (legacy)"""
        result = self._parse_create_table_structure(sql)
        if "error" in result:
            return result
        
        table = database.create_table(
            result["table_name"],
            result["columns"],
            result["primary_key"],
            result["unique_keys"]
        )
        return {"message": f"Table '{result['table_name']}' created", "table": table.name}
    
    def _parse_insert(self, sql: str, database) -> Dict:
        """Parse INSERT statement (legacy)"""
        result = self._parse_insert_structure(sql)
        if "error" in result:
            return result
        
        table = database.get_table(result["table_name"])
        if not table:
            return {"error": f"Table '{result['table_name']}' not found"}
        
        try:
            table.insert(result["values"])
            return {"message": "Row inserted successfully", "rows_affected": 1}
        except Exception as e:
            return {"error": str(e)}
    
    def _parse_select(self, sql: str, database) -> Dict:
        """Parse SELECT statement (legacy)"""
        result = self._parse_select_structure(sql)
        if "error" in result:
            return result
        
        table = database.get_table(result["table_name"])
        if not table:
            return {"error": f"Table '{result['table_name']}' not found"}
        
        if result["join"]:
            # Use database join_tables method
            join_result = database.join_tables(
                result["table_name"],
                result["join"]["table"],
                result["join"]["main_key"],
                result["join"]["join_key"],
                result["join"]["type"]
            )
            
            # Apply WHERE conditions
            if result["conditions"]:
                filtered = []
                for row in join_result:
                    matches = True
                    for col, val in result["conditions"].items():
                        if col not in row or str(row[col]) != val:
                            matches = False
                            break
                    if matches:
                        filtered.append(row)
                join_result = filtered
            
            return {
                "data": join_result,
                "count": len(join_result),
                "join_type": result["join"]["type"]
            }
        else:
            # Regular select
            results = table.select(result["conditions"], result["columns"])
            return {
                "data": results,
                "count": len(results),
                "columns": result["columns"] if result["columns"] else list(table.columns.keys())
            }
    
    def _parse_update(self, sql: str, database) -> Dict:
        """Parse UPDATE statement (legacy)"""
        result = self._parse_update_structure(sql)
        if "error" in result:
            return result
        
        table = database.get_table(result["table_name"])
        if not table:
            return {"error": f"Table '{result['table_name']}' not found"}
        
        try:
            count = table.update(result["updates"], result["conditions"])
            return {"message": f"{count} row(s) updated", "rows_affected": count}
        except Exception as e:
            return {"error": str(e)}
    
    def _parse_delete(self, sql: str, database) -> Dict:
        """Parse DELETE statement (legacy)"""
        result = self._parse_delete_structure(sql)
        if "error" in result:
            return result
        
        table = database.get_table(result["table_name"])
        if not table:
            return {"error": f"Table '{result['table_name']}' not found"}
        
        count = table.delete(result["conditions"])
        return {"message": f"{count} row(s) deleted", "rows_affected": count}
    
    def _parse_drop_table(self, sql: str, database) -> Dict:
        """Parse DROP TABLE statement (legacy)"""
        pattern = r'DROP TABLE (\w+)'
        match = re.match(pattern, sql, re.IGNORECASE)
        
        if not match:
            return {"error": "Invalid DROP TABLE syntax"}
        
        table_name = match.group(1).strip()
        
        if database.drop_table(table_name):
            return {"message": f"Table '{table_name}' dropped"}
        else:
            return {"error": f"Table '{table_name}' not found"}
    
    def _parse_where_clause(self, where_clause: str) -> Dict:
        """Parse WHERE clause into conditions dict (legacy)"""
        where = {}
        # Simple equality conditions only
        conditions = where_clause.split('AND')
        for condition in conditions:
            condition = condition.strip()
            if '=' in condition:
                left, right = condition.split('=', 1)
                col = left.strip()
                val = right.strip().strip("'")
                where[col] = val
        return where
    
    def _row_matches_where(self, row: Dict, where: Dict) -> bool:
        """Check if row matches WHERE conditions (legacy)"""
        for col, val in where.items():
            if col not in row or str(row[col]) != val:
                return False
        return True
    
    def _parse_join(self, sql: str, database) -> Dict:
        """Parse JOIN statement (legacy)"""
        result = self._parse_join_structure(sql)
        if "error" in result:
            return result
        
        table1 = database.get_table(result["table_name"])
        table2 = database.get_table(result["join"]["table"])
        
        if not table1:
            return {"error": f"Table '{result['table_name']}' not found"}
        if not table2:
            return {"error": f"Table '{result['join']['table']}' not found"}
        
        # Perform join
        results = table1.join(
            table2, 
            result["join"]["main_key"], 
            result["join"]["join_key"], 
            result["join"]["type"]
        )
        
        # Apply WHERE clause if exists
        if result["conditions"]:
            filtered_results = []
            for row in results:
                if self._row_matches_where(row, result["conditions"]):
                    filtered_results.append(row)
            results = filtered_results
        
        return {
            "data": results,
            "count": len(results),
            "join_type": result["join"]["type"]
        }