"""
Optional JSON persistence layer
"""
import json
import os
import pickle
from typing import Dict, List, Any

class StorageEngine:
    """Handles file persistence for the database"""
    
    def __init__(self, db_name: str):
        self.db_name = db_name
        self.data_dir = f"data/{db_name}"
        os.makedirs(self.data_dir, exist_ok=True)
    
    def save_metadata(self, metadata: Dict):
        """Save database metadata"""
        with open(f"{self.data_dir}/metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)
    
    def load_metadata(self) -> Dict:
        """Load database metadata"""
        metadata_file = f"{self.data_dir}/metadata.json"
        if os.path.exists(metadata_file):
            with open(metadata_file, 'r') as f:
                return json.load(f)
        return {}
    
    def save_table(self, table_name: str, data: List[Dict], indexes: Dict):
        """Save table data and indexes"""
        table_file = f"{self.data_dir}/{table_name}.json"
        with open(table_file, 'w') as f:
            json.dump({
                "data": data,
                "indexes": indexes
            }, f, indent=2)
    
    def load_table_data(self, table_name: str) -> List[Dict]:
        """Load table data"""
        table_file = f"{self.data_dir}/{table_name}.json"
        if os.path.exists(table_file):
            with open(table_file, 'r') as f:
                content = json.load(f)
                return content.get("data", [])
        return []
    
    def delete_table(self, table_name: str):
        """Delete table file"""
        table_file = f"{self.data_dir}/{table_name}.json"
        if os.path.exists(table_file):
            os.remove(table_file)