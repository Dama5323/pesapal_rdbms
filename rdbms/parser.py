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
    
    def _parse_create_table(self, sql: str, database) -> Dict:
        """Parse CREATE TABLE statement"""
        pattern = r'CREATE TABLE (\w+) \((.+)\)'
        match = re.match(pattern, sql, re.IGNORECASE | re.DOTALL)
        
        if not match:
            return {"error": "Invalid CREATE TABLE syntax"}
        
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
        
        table = database.create_table(table_name, columns, primary_key, unique_keys)
        return {"message": f"Table '{table_name}' created", "table": table.name}
    
    def _parse_insert(self, sql: str, database) -> Dict:
        """Parse INSERT statement"""
        pattern = r'INSERT INTO (\w+) \((.+?)\) VALUES \((.+?)\)'
        match = re.match(pattern, sql, re.IGNORECASE | re.DOTALL)
        
        if not match:
            return {"error": "Invalid INSERT syntax"}
        
        table_name = match.group(1)
        columns = [col.strip() for col in match.group(2).split(',')]
        values = [val.strip().strip("'") for val in match.group(3).split(',')]
        
        if len(columns) != len(values):
            return {"error": "Column count doesn't match value count"}
        
        table = database.get_table(table_name)
        if not table:
            return {"error": f"Table '{table_name}' not found"}
        
        row_data = {}
        for col, val in zip(columns, values):
            row_data[col] = val
        
        try:
            table.insert(row_data)
            return {"message": "Row inserted successfully", "rows_affected": 1}
        except Exception as e:
            return {"error": str(e)}
    
    def _parse_select(self, sql: str, database) -> Dict:
        """Parse SELECT statement"""
        # Check for JOIN
        if "JOIN" in sql.upper():
            return self._parse_join(sql, database)
        
        # Regular SELECT
        if 'WHERE' in sql.upper():
            pattern = r'SELECT (.+?) FROM (\w+) WHERE (.+)'
            match = re.match(pattern, sql, re.IGNORECASE)
            if not match:
                return {"error": "Invalid SELECT syntax"}
            
            columns_str = match.group(1).strip()
            table_name = match.group(2).strip()
            where_clause = match.group(3).strip()
        else:
            pattern = r'SELECT (.+?) FROM (\w+)'
            match = re.match(pattern, sql, re.IGNORECASE)
            if not match:
                return {"error": "Invalid SELECT syntax"}
            
            columns_str = match.group(1).strip()
            table_name = match.group(2).strip()
            where_clause = None
        
        table = database.get_table(table_name)
        if not table:
            return {"error": f"Table '{table_name}' not found"}
        
        # Parse columns
        columns = None
        if columns_str != '*':
            columns = [col.strip() for col in columns_str.split(',')]
        
        # Parse WHERE clause
        where = None
        if where_clause:
            where = self._parse_where_clause(where_clause)
        
        results = table.select(where, columns)
        return {
            "data": results,
            "count": len(results),
            "columns": columns if columns else list(table.columns.keys())
        }
    
    def _parse_join(self, sql: str, database) -> Dict:
        """Parse JOIN statement"""
        pattern = r'SELECT (.+?) FROM (\w+) (\w+) JOIN (\w+) ON (.+?)(?: WHERE (.+))?'
        match = re.match(pattern, sql, re.IGNORECASE)
        
        if not match:
            return {"error": "Invalid JOIN syntax"}
        
        columns_str = match.group(1).strip()
        table1_name = match.group(2).strip()
        join_type = match.group(3).strip().upper()  # INNER, LEFT, etc.
        table2_name = match.group(4).strip()
        on_clause = match.group(5).strip()
        where_clause = match.group(6)
        
        table1 = database.get_table(table1_name)
        table2 = database.get_table(table2_name)
        
        if not table1:
            return {"error": f"Table '{table1_name}' not found"}
        if not table2:
            return {"error": f"Table '{table2_name}' not found"}
        
        # Parse ON clause
        if '=' in on_clause:
            left, right = on_clause.split('=', 1)
            left_on = left.strip().split('.')[-1]
            right_on = right.strip().split('.')[-1]
        else:
            return {"error": "Invalid ON clause"}
        
        # Perform join
        results = table1.join(table2, left_on, right_on, join_type)
        
        # Apply WHERE clause if exists
        if where_clause:
            where = self._parse_where_clause(where_clause)
            filtered_results = []
            for row in results:
                if self._row_matches_where(row, where):
                    filtered_results.append(row)
            results = filtered_results
        
        return {
            "data": results,
            "count": len(results),
            "join_type": join_type
        }
    
    def _parse_where_clause(self, where_clause: str) -> Dict:
        """Parse WHERE clause into conditions dict"""
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
        """Check if row matches WHERE conditions"""
        for col, val in where.items():
            if col not in row or str(row[col]) != val:
                return False
        return True
    
    def _parse_update(self, sql: str, database) -> Dict:
        """Parse UPDATE statement"""
        pattern = r'UPDATE (\w+) SET (.+?)(?: WHERE (.+))?'
        match = re.match(pattern, sql, re.IGNORECASE)
        
        if not match:
            return {"error": "Invalid UPDATE syntax"}
        
        table_name = match.group(1).strip()
        set_clause = match.group(2).strip()
        where_clause = match.group(3)
        
        table = database.get_table(table_name)
        if not table:
            return {"error": f"Table '{table_name}' not found"}
        
        # Parse SET clause
        data = {}
        assignments = set_clause.split(',')
        for assignment in assignments:
            if '=' in assignment:
                left, right = assignment.split('=', 1)
                col = left.strip()
                val = right.strip().strip("'")
                data[col] = val
        
        # Parse WHERE clause
        where = None
        if where_clause:
            where = self._parse_where_clause(where_clause)
        
        try:
            count = table.update(data, where)
            return {"message": f"{count} row(s) updated", "rows_affected": count}
        except Exception as e:
            return {"error": str(e)}
    
    def _parse_delete(self, sql: str, database) -> Dict:
        """Parse DELETE statement"""
        pattern = r'DELETE FROM (\w+)(?: WHERE (.+))?'
        match = re.match(pattern, sql, re.IGNORECASE)
        
        if not match:
            return {"error": "Invalid DELETE syntax"}
        
        table_name = match.group(1).strip()
        where_clause = match.group(2)
        
        table = database.get_table(table_name)
        if not table:
            return {"error": f"Table '{table_name}' not found"}
        
        where = None
        if where_clause:
            where = self._parse_where_clause(where_clause)
        
        count = table.delete(where)
        return {"message": f"{count} row(s) deleted", "rows_affected": count}
    
    def _parse_drop_table(self, sql: str, database) -> Dict:
        """Parse DROP TABLE statement"""
        pattern = r'DROP TABLE (\w+)'
        match = re.match(pattern, sql, re.IGNORECASE)
        
        if not match:
            return {"error": "Invalid DROP TABLE syntax"}
        
        table_name = match.group(1).strip()
        
        if database.drop_table(table_name):
            return {"message": f"Table '{table_name}' dropped"}
        else:
            return {"error": f"Table '{table_name}' not found"}