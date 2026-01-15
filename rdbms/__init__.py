"""
SimpleRDBMS - A minimal relational database management system
"""
from .database import Database
from .repl import RDBMS_REPL

__version__ = "0.1.0"
__all__ = ["Database", "RDBMS_REPL"]