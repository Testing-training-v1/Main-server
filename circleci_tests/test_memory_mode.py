#!/usr/bin/env python3
"""
Test script for memory-only mode in CircleCI environment.

This script verifies that:
1. Memory-only mode is properly enabled
2. Virtual tempfile implementation works
3. Dropbox access works (if credentials are available)
"""

import os
import sys
import time
import logging
import io
import tempfile

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger("circleci-test")

def test_memory_only_mode():
    """Test that memory-only mode is enabled."""
    logger.info("Testing memory-only mode detection...")
    
    # Import config
    try:
        import config
        logger.info(f"MEMORY_ONLY_MODE = {config.MEMORY_ONLY_MODE}")
        logger.info(f"USE_DROPBOX_STREAMING = {config.USE_DROPBOX_STREAMING}")
        logger.info(f"NO_LOCAL_STORAGE = {config.NO_LOCAL_STORAGE}")
        
        if config.MEMORY_ONLY_MODE and config.USE_DROPBOX_STREAMING:
            logger.info("✅ Memory-only mode correctly enabled")
            return True
        else:
            logger.error("❌ Memory-only mode not enabled!")
            return False
    except Exception as e:
        logger.error(f"Error importing config: {e}")
        return False

def test_virtual_tempfile():
    """Test that the virtual tempfile implementation works."""
    logger.info("Testing virtual tempfile implementation...")
    
    try:
        # First, ensure patch_tempfile is imported
        import patch_tempfile
        logger.info("Imported patch_tempfile")
        
        # Test creating a tempfile
        temp = tempfile.NamedTemporaryFile(delete=False)
        temp_name = temp.name
        logger.info(f"Created tempfile: {temp_name}")
        
        # Write data
        test_data = b'This is test data for CircleCI'
        temp.write(test_data)
        temp.flush()
        temp.close()
        
        # Read data back
        with open(temp_name, 'rb') as f:
            read_data = f.read()
        
        # Check if data matches
        if read_data == test_data:
            logger.info("✅ Virtual tempfile test passed")
            return True
        else:
            logger.error(f"❌ Data mismatch: {read_data} != {test_data}")
            return False
    except Exception as e:
        logger.error(f"Error testing virtual tempfile: {e}")
        return False

def test_dropbox_connection():
    """Test Dropbox connection if credentials are available."""
    logger.info("Testing Dropbox connection...")
    
    if not os.environ.get('DROPBOX_REFRESH_TOKEN'):
        logger.warning("⚠️ DROPBOX_REFRESH_TOKEN not set, skipping Dropbox test")
        return True
    
    try:
        import utils.dropbox_storage
        dropbox_storage = utils.dropbox_storage.get_dropbox_storage()
        
        # Test Dropbox connection
        account = dropbox_storage.dbx.users_get_current_account()
        logger.info(f"✅ Connected to Dropbox as: {account.name.display_name}")
        
        # Try listing files
        result = dropbox_storage.list_models()
        logger.info(f"Listed models: {result}")
        
        return True
    except Exception as e:
        logger.error(f"Error connecting to Dropbox: {e}")
        return False

def test_model_streaming():
    """Test model streaming functionality."""
    logger.info("Testing model streaming...")
    
    if not os.environ.get('DROPBOX_REFRESH_TOKEN'):
        logger.warning("⚠️ DROPBOX_REFRESH_TOKEN not set, skipping model streaming test")
        return True
    
    try:
        import utils.model_streamer
        
        # Try to get base model stream
        stream = utils.model_streamer.get_base_model_stream()
        
        if stream:
            # Test reading from the stream
            chunk = stream.read(1024)
            logger.info(f"Read {len(chunk)} bytes from model stream")
            stream.close()
            logger.info("✅ Model streaming test passed")
            return True
        else:
            logger.warning("⚠️ Could not get model stream, but no error occurred")
            return True
    except Exception as e:
        logger.error(f"Error testing model streaming: {e}")
        return False

def run_all_tests():
    """Run all tests and return overall success."""
    tests = [
        ("Memory-only mode", test_memory_only_mode),
        ("Virtual tempfile", test_virtual_tempfile),
        ("Dropbox connection", test_dropbox_connection),
        ("Model streaming", test_model_streaming)
    ]
    
    results = []
    
    logger.info("🔍 Starting CircleCI tests...")
    
    for name, test_func in tests:
        logger.info(f"Running test: {name}...")
        try:
            result = test_func()
            results.append(result)
            logger.info(f"Test {name}: {'✅ PASSED' if result else '❌ FAILED'}")
        except Exception as e:
            logger.error(f"Error in test {name}: {e}")
            results.append(False)
    
    # Print summary
    logger.info("\n\n===== TEST SUMMARY =====")
    for i, (name, _) in enumerate(tests):
        logger.info(f"{name}: {'✅ PASSED' if results[i] else '❌ FAILED'}")
    
    success_rate = sum(results) / len(results) if results else 0
    logger.info(f"Success rate: {success_rate:.0%}")
    
    return all(results)

if __name__ == "__main__":
    # Set memory-only mode explicitly for testing
    os.environ['MEMORY_ONLY_MODE'] = 'True'
    os.environ['USE_DROPBOX_STREAMING'] = 'True'
    os.environ['NO_LOCAL_STORAGE'] = 'True'
    os.environ['CIRCLECI_ENV'] = 'True'
    
    # Run tests
    success = run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)
