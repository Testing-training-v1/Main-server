"""
In-memory database utilities for Backdoor AI Learning Server.

This module provides utilities for working with SQLite in-memory databases
with Dropbox synchronization.
"""

import io
import sqlite3
import threading
import time
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Import Dropbox storage
try:
    from utils.dropbox_storage import get_dropbox_storage
    from config import DROPBOX_ENABLED, DROPBOX_DB_SYNC_INTERVAL
except ImportError:
    logger.warning("Could not import Dropbox storage, memory DB sync disabled")
    DROPBOX_ENABLED = False
    DROPBOX_DB_SYNC_INTERVAL = 60  # Default 60 seconds if not defined in config

# Global in-memory database connection
_in_memory_db = None
_in_memory_db_lock = threading.RLock()
_last_db_sync_time = 0

def init_memory_db() -> sqlite3.Connection:
    """
    Initialize the in-memory database and load from Dropbox if available.
    
    Returns:
        sqlite3.Connection: Connection to the in-memory database
    """
    global _in_memory_db, _last_db_sync_time
    
    with _in_memory_db_lock:
        if _in_memory_db is not None:
            return _in_memory_db
        
        logger.info("Initializing in-memory database")
        _in_memory_db = sqlite3.connect(':memory:', check_same_thread=False)
        
        # If Dropbox is enabled, load from Dropbox
        if DROPBOX_ENABLED:
            try:
                dropbox_storage = get_dropbox_storage()
                db_data = dropbox_storage.download_db_to_memory()
                
                if db_data and db_data.get('success'):
                    # Load database from buffer
                    buffer = db_data.get('db_buffer')
                    if buffer:
                        # Import the SQL dump into memory
                        buffer.seek(0)
                        script = buffer.read().decode('utf-8')
                        _in_memory_db.executescript(script)
                        logger.info("Successfully loaded database from Dropbox into memory")
                        _last_db_sync_time = time.time()
                    else:
                        logger.warning("Downloaded database buffer from Dropbox was empty")
                else:
                    logger.info("No existing database found in Dropbox, starting with fresh database")
            except Exception as e:
                logger.error(f"Error loading database from Dropbox: {e}")
                logger.info("Starting with fresh in-memory database")
        
        return _in_memory_db

def sync_memory_db_to_dropbox() -> bool:
    """
    Sync the in-memory database to Dropbox.
    
    Returns:
        bool: True if sync was successful, False otherwise
    """
    global _last_db_sync_time
    
    if not DROPBOX_ENABLED or _in_memory_db is None:
        return False
    
    # Only sync if enough time has passed since last sync
    current_time = time.time()
    if current_time - _last_db_sync_time < DROPBOX_DB_SYNC_INTERVAL:
        return False
    
    try:
        # Dump the database to a buffer
        buffer = io.BytesIO()
        for line in _in_memory_db.iterdump():
            buffer.write(f"{line}\n".encode('utf-8'))
        
        # Upload to Dropbox
        dropbox_storage = get_dropbox_storage()
        result = dropbox_storage.upload_db_from_memory(buffer)
        
        if result and result.get('success'):
            logger.info("Successfully synced in-memory database to Dropbox")
            _last_db_sync_time = current_time
            return True
        else:
            logger.error(f"Failed to sync database to Dropbox: {result.get('error', 'Unknown error')}")
            return False
    except Exception as e:
        logger.error(f"Error syncing database to Dropbox: {e}")
        return False

def get_memory_db() -> sqlite3.Connection:
    """
    Get the global in-memory database connection.
    
    Returns:
        sqlite3.Connection: Connection to the in-memory database
    """
    if _in_memory_db is None:
        return init_memory_db()
    return _in_memory_db

def create_memory_db_copy() -> sqlite3.Connection:
    """
    Create a new in-memory database with a copy of the data from the global database.
    
    This is useful for creating isolated connections for thread safety.
    
    Returns:
        sqlite3.Connection: New connection to a copy of the database
    """
    if _in_memory_db is None:
        init_memory_db()
    
    with _in_memory_db_lock:
        # Create a new in-memory database
        new_db = sqlite3.connect(':memory:')
        
        # Copy the schema and data from the global database
        _in_memory_db.backup(new_db)
        
        return new_db

def commit_memory_db_copy(conn: sqlite3.Connection) -> bool:
    """
    Commit changes from a database copy back to the global database.
    
    Args:
        conn: Connection to a database copy
        
    Returns:
        bool: True if commit was successful
    """
    if _in_memory_db is None or conn is None:
        return False
    
    with _in_memory_db_lock:
        # Backup from the copy to the global database
        conn.backup(_in_memory_db)
        
        # Sync to Dropbox if needed
        sync_memory_db_to_dropbox()
        
        return True

def close_memory_db_copy(conn: sqlite3.Connection) -> None:
    """
    Close a database copy connection.
    
    Args:
        conn: Connection to close
    """
    if conn is not None:
        conn.close()
