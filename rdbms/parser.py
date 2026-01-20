"""
Minimal SQL-like parser - Handles basic SQL commands
"""
import re
import shlex
from typing import Dict, List, Any, Optional, Tuple

class SQLParser:
    """Simple SQL parser"""
    
    def parse(self, sql: str) -> Dict:
        """
        Parse SQL into structured format for Database.execute()
        
        Args:
            sql: SQL statement to parse
            
        Returns:
            Dictionary with parsed SQL components
        """
        # Remove trailing semicolon and whitespace
        sql = sql.strip().rstrip(';').strip()
        sql_upper = sql.upper()
        
        try:
            # Handle SHOW TABLES
            if sql_upper == "SHOW TABLES":
                return {"type": "SHOW_TABLES"}
            
            elif sql_upper.startswith("CREATE TABLE"):
                return self._parse_create_table(sql)
                
            elif sql_upper.startswith("INSERT INTO"):
                return self._parse_insert(sql)
                
            elif sql_upper.startswith("SELECT"):
                return self._parse_select(sql)
                
            elif sql_upper.startswith("UPDATE"):
                return self._parse_update(sql)
                
            elif sql_upper.startswith("DELETE FROM"):
                return self._parse_delete(sql)
                
            elif sql_upper.startswith("DROP TABLE"):
                return self._parse_drop_table(sql)
                
            else:
                # Try ledger commands
                return self._parse_ledger_command(sql)
                
        except Exception as e:
            return {"type": "ERROR", "error": str(e)}
    
    def _parse_create_table(self, sql: str) -> Dict:
        """Parse CREATE TABLE statement"""
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
    
    def _parse_insert(self, sql: str) -> Dict:
        """Parse INSERT statement"""
        pattern = r'INSERT INTO (\w+) \((.+?)\) VALUES \((.+?)\)'
        match = re.match(pattern, sql, re.IGNORECASE | re.DOTALL)
        
        if not match:
            return {"type": "ERROR", "error": "Invalid INSERT syntax"}
        
        table_name = match.group(1)
        columns = [col.strip() for col in match.group(2).split(',')]
        values = self._parse_values(match.group(3).strip())
        
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
    
    def _parse_values(self, values_str: str) -> List:
        """Parse VALUES clause, handling quoted strings with commas"""
        values = []
        current = ""
        in_quotes = False
        quote_char = None
        
        for char in values_str:
            if char in "'\"" and (not in_quotes or quote_char == char):
                in_quotes = not in_quotes
                quote_char = char if in_quotes else None
                current += char
            elif char == ',' and not in_quotes:
                values.append(current.strip())
                current = ""
            else:
                current += char
        
        if current:
            values.append(current.strip())
        
        # Remove quotes from values
        parsed_values = []
        for val in values:
            if (val.startswith("'") and val.endswith("'")) or \
               (val.startswith('"') and val.endswith('"')):
                val = val[1:-1]
            parsed_values.append(val)
        
        return parsed_values
    
    def _parse_select(self, sql: str) -> Dict:
        """Parse SELECT statement"""
        # Check for JOIN
        if "JOIN" in sql.upper():
            return self._parse_join(sql)
        
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
    
    def _parse_join(self, sql: str) -> Dict:
        """Parse JOIN statement"""
        # Match: SELECT * FROM table1 INNER JOIN table2 ON table1.id = table2.user_id
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
    
    def _parse_update(self, sql: str) -> Dict:
        """Parse UPDATE statement"""
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
    
    def _parse_delete(self, sql: str) -> Dict:
        """Parse DELETE statement"""
        pattern = r'DELETE FROM (\w+)(?: WHERE (.+))?'
        match = re.match(pattern, sql, re.IGNORECASE)
        
        if not match:
            return {"type": "ERROR", "error": "Invalid DELETE syntax"}
        
        table_name = match.group(1).strip()
        where_clause = match.group(2)
        
        # Parse WHERE clause
        conditions = {}
        if where_clause:
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
    
    def _parse_drop_table(self, sql: str) -> Dict:
        """Parse DROP TABLE statement"""
        pattern = r'DROP TABLE (\w+)'
        match = re.match(pattern, sql, re.IGNORECASE)
        
        if not match:
            return {"type": "ERROR", "error": "Invalid DROP TABLE syntax"}
        
        table_name = match.group(1).strip()
        
        return {
            "type": "DROP_TABLE",
            "table_name": table_name
        }
    
    def _parse_ledger_command(self, sql: str) -> Dict:
        """Parse ledger-specific commands"""
        parts = sql.split()
        
        if len(parts) >= 3 and parts[0].upper() == 'LEDGER':
            
            if parts[1].upper() == 'CREATE':
                table_name = parts[2]
                return {'type': 'LEDGER_CREATE', 'table': table_name}
                
            elif parts[1].upper() == 'APPEND' and len(parts) >= 4:
                table_name = parts[2]
                # Join the remaining parts
                rest = ' '.join(parts[3:])
                params = self._parse_key_value_pairs(rest)
                
                return {
                    'type': 'LEDGER_APPEND',
                    'table': table_name,
                    'params': params
                }
                
            elif parts[1].upper() == 'VERIFY':
                table_name = parts[2]
                return {'type': 'LEDGER_VERIFY', 'table': table_name}
                
            elif parts[1].upper() == 'AUDIT':
                table_name = parts[2]
                # Join the remaining parts
                rest = ' '.join(parts[3:]) if len(parts) > 3 else ''
                params = self._parse_key_value_pairs(rest)
                
                return {
                    'type': 'LEDGER_AUDIT',
                    'table': table_name,
                    'params': params
                }
        
        return {"type": "ERROR", "error": f"Unknown syntax: {sql}"}
    
    def _parse_key_value_pairs(self, text: str) -> Dict:
        """Parse key=value pairs from text, handling quoted values"""
        params = {}
        
        if not text:
            return params
        
        # Use shlex to properly handle quoted strings
        try:
            lexer = shlex.shlex(text, posix=True)
            lexer.whitespace = ' '
            lexer.whitespace_split = True
            tokens = list(lexer)
            
            for token in tokens:
                if '=' in token:
                    key, value = token.split('=', 1)
                    # Remove quotes if present
                    if (value.startswith("'") and value.endswith("'")) or \
                       (value.startswith('"') and value.endswith('"')):
                        value = value[1:-1]
                    params[key.lower()] = value
                    
        except Exception:
            # Fallback: simple split
            for part in text.split():
                if '=' in part:
                    key, value = part.split('=', 1)
                    # Remove quotes if present
                    if (value.startswith("'") and value.endswith("'")) or \
                       (value.startswith('"') and value.endswith('"')):
                        value = value[1:-1]
                    params[key.lower()] = value
        
        return params