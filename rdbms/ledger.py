import hashlib
import json
from datetime import datetime
from typing import Dict, List, Any, Optional

class LedgerTable:
    """
    A special table type that maintains an immutable, verifiable log
    """
    
    def __init__(self, name: str):
        self.name = name
        self.events = []  # List of event dictionaries
        self.current_hash = "0" * 64  # Starting hash
        self.index = {}  # For quick lookup
        
    def append_event(self, event_type: str, data: Dict, aggregate_id: str = None):
        """
        Append an immutable event to the ledger
        """
        event = {
            'id': len(self.events),
            'event_type': event_type,
            'aggregate_id': aggregate_id or 'global',
            'data': json.dumps(data, sort_keys=True),
            'timestamp': datetime.utcnow().isoformat(),
            'previous_hash': self.current_hash,
            'signature': None  # Could add cryptographic signatures
        }
        
        # Calculate hash for this event
        event_string = f"{event['id']}{event['event_type']}{event['data']}{event['previous_hash']}"
        event['current_hash'] = hashlib.sha256(event_string.encode()).hexdigest()
        
        # Update chain
        self.current_hash = event['current_hash']
        self.events.append(event)
        
        # Index by aggregate_id for faster queries
        if aggregate_id:
            if aggregate_id not in self.index:
                self.index[aggregate_id] = []
            self.index[aggregate_id].append(len(self.events) - 1)
        
        return event['id'], event['current_hash']
    
    def get_events(self, aggregate_id: str = None) -> List[Dict]:
        """Get events, optionally filtered by aggregate_id"""
        if aggregate_id and aggregate_id in self.index:
            return [self.events[i] for i in self.index[aggregate_id]]
        return self.events.copy()
    
    def verify_chain(self) -> Dict:
        """Verify the integrity of the hash chain"""
        previous_hash = "0" * 64
        is_valid = True
        invalid_events = []
        
        for i, event in enumerate(self.events):
            event_string = f"{event['id']}{event['event_type']}{event['data']}{previous_hash}"
            expected_hash = hashlib.sha256(event_string.encode()).hexdigest()
            
            if expected_hash != event['current_hash']:
                is_valid = False
                invalid_events.append({
                    'event_id': i,
                    'expected': expected_hash,
                    'actual': event['current_hash']
                })
            
            previous_hash = event['current_hash']
        
        return {
            'valid': is_valid,
            'total_events': len(self.events),
            'invalid_events': invalid_events
        }
    
    def replay_events(self, aggregate_id: str) -> List[Any]:
        """
        Replay events to reconstruct state
        Useful for Event Sourcing pattern
        """
        events = self.get_events(aggregate_id)
        state = {}
        
        for event in events:
            data = json.loads(event['data'])
            # Apply event to state (simplified example)
            if event['event_type'] == 'PAYMENT_RECEIVED':
                state['balance'] = state.get('balance', 0) + data.get('amount', 0)
            elif event['event_type'] == 'PAYMENT_SENT':
                state['balance'] = state.get('balance', 0) - data.get('amount', 0)
            # Add more event handlers as needed
        
        return state


class LedgerDB:
    """
    Main ledger database that manages multiple ledger tables
    """
    
    def __init__(self):
        self.tables = {}  # name -> LedgerTable
        
    def create_table(self, name: str) -> LedgerTable:
        """Create a new ledger table"""
        if name in self.tables:
            raise ValueError(f"Table {name} already exists")
        
        table = LedgerTable(name)
        self.tables[name] = table
        return table
    
    def get_table(self, name: str) -> Optional[LedgerTable]:
        """Get a ledger table by name"""
        return self.tables.get(name)
    
    def list_tables(self) -> List[str]:
        """List all ledger tables"""
        return list(self.tables.keys())


# Global ledger instance
ledger_db = LedgerDB()