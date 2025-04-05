"""
Model orchestration module for Backdoor AI learning system.

This module handles the coordination between different model sources:
- Base model management
- User-uploaded model aggregation
- Model versioning and updates
"""

import os
import io
import logging
import json
import time
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

import config

logger = logging.getLogger(__name__)

def update_base_model(model_buffer: io.BytesIO, version: str) -> bool:
    """
    Update the base model in the dedicated base_model folder.
    
    This function:
    1. Copies the model to base_model/model_latest.mlmodel
    2. Also stores a versioned copy at base_model/model_{version}.mlmodel
    
    Args:
        model_buffer: BytesIO buffer containing the model data
        version: Version string for the model
        
    Returns:
        bool: True if update was successful
    """
    if not config.DROPBOX_ENABLED:
        logger.warning("Dropbox not enabled - cannot update base model")
        return False
        
    try:
        from utils.dropbox_storage import get_dropbox_storage
        dropbox_storage = get_dropbox_storage()
        
        # Reset buffer position
        model_buffer.seek(0)
        
        # Upload as latest model
        latest_result = dropbox_storage.upload_model(
            model_buffer, 
            "model_latest.mlmodel",
            config.DROPBOX_BASE_MODEL_FOLDER
        )
        
        if not latest_result.get('success'):
            logger.error(f"Failed to upload latest model: {latest_result.get('error')}")
            return False
            
        # Also upload as versioned model
        model_buffer.seek(0)
        versioned_name = f"model_{version}.mlmodel"
        versioned_result = dropbox_storage.upload_model(
            model_buffer,
            versioned_name,
            config.DROPBOX_BASE_MODEL_FOLDER
        )
        
        if not versioned_result.get('success'):
            logger.warning(f"Failed to upload versioned model: {versioned_result.get('error')}")
            # Continue anyway - the latest model was uploaded successfully
        
        logger.info(f"Successfully updated base model to version {version}")
        
        # Clear model cache to force reload with new version
        try:
            from utils.model_download import clear_model_cache
            clear_model_cache()
            logger.info("Cleared model cache to ensure latest base model is used")
        except Exception as e:
            logger.warning(f"Could not clear model cache: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error updating base model: {e}")
        return False

def get_uploaded_models() -> List[Dict[str, Any]]:
    """
    Get list of all user-uploaded models from backdoor_models/uploaded.
    
    Returns:
        List of dictionaries with model information
    """
    if not config.DROPBOX_ENABLED:
        logger.warning("Dropbox not enabled - cannot get uploaded models")
        return []
        
    try:
        from utils.dropbox_storage import get_dropbox_storage
        dropbox_storage = get_dropbox_storage()
        
        # First ensure the uploaded models directory exists
        try:
            uploaded_folder = f"/{config.DROPBOX_MODELS_FOLDER}/uploaded"
            try:
                dropbox_storage.dbx.files_get_metadata(uploaded_folder)
            except Exception:
                # Create folder if it doesn't exist
                logger.info(f"Creating uploaded models folder: {uploaded_folder}")
                dropbox_storage.dbx.files_create_folder_v2(uploaded_folder)
        except Exception as e:
            logger.error(f"Error ensuring uploaded folder exists: {e}")
            # Continue anyway
        
        # List all models
        all_models = dropbox_storage.list_models()
        
        # Filter to just uploaded models
        uploaded_models = []
        for model in all_models:
            path = model.get('path', '')
            if '/uploaded/' in path and path.endswith('.mlmodel'):
                # Extract device ID from filename if possible
                name = model.get('name', '')
                device_id = 'unknown'
                
                # Try to extract device ID from name (format: model_deviceXXXX.mlmodel)
                if name.startswith('model_device') and name.endswith('.mlmodel'):
                    device_id = name[len('model_device'):-len('.mlmodel')]
                
                # Add to result
                uploaded_models.append({
                    'id': name,
                    'device_id': device_id,
                    'path': path,
                    'file_path': f"dropbox:{path}",
                    'download_url': model.get('download_url'),
                    'size': model.get('size', 0),
                    'modified_date': model.get('modified_date', '')
                })
        
        logger.info(f"Found {len(uploaded_models)} uploaded models")
        return uploaded_models
        
    except Exception as e:
        logger.error(f"Error getting uploaded models: {e}")
        return []

def generate_model_version() -> str:
    """
    Generate a new model version string.
    
    Format: 1.0.YYYYMMDD.COUNTER
    
    Returns:
        str: New version string
    """
    # Get date part
    date_part = datetime.now().strftime("%Y%m%d")
    
    # Generate version with timestamp
    timestamp = int(time.time())
    version = f"{config.MODEL_VERSION_PREFIX}{date_part}.{timestamp}"
    
    return version

def create_training_summary(trained_model_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a summary of model training results.
    
    Args:
        trained_model_info: Dictionary with model training info
        
    Returns:
        Dict with JSON-serializable training summary
    """
    return {
        'version': trained_model_info.get('version', 'unknown'),
        'training_date': datetime.now().isoformat(),
        'accuracy': trained_model_info.get('accuracy', 0),
        'training_data_size': trained_model_info.get('training_data_size', 0),
        'is_ensemble': trained_model_info.get('is_ensemble', False),
        'component_models': trained_model_info.get('component_models', 0),
        'classes': trained_model_info.get('classes', [])
    }

def save_training_summary(summary: Dict[str, Any]) -> bool:
    """
    Save training summary to Dropbox.
    
    Args:
        summary: Dictionary with training summary
        
    Returns:
        bool: True if successfully saved
    """
    if not config.DROPBOX_ENABLED:
        logger.warning("Dropbox not enabled - cannot save training summary")
        return False
        
    try:
        from utils.dropbox_storage import get_dropbox_storage
        dropbox_storage = get_dropbox_storage()
        
        # Convert to JSON
        summary_json = json.dumps(summary, indent=2)
        buffer = io.BytesIO(summary_json.encode('utf-8'))
        
        # Save as latest summary
        latest_result = dropbox_storage.upload_model(
            buffer,
            "latest_model_info.json",
            config.DROPBOX_BASE_MODEL_FOLDER
        )
        
        if not latest_result.get('success'):
            logger.error(f"Failed to upload latest model info: {latest_result.get('error')}")
            return False
            
        # Also save as versioned summary
        buffer.seek(0)
        version = summary.get('version', 'unknown')
        versioned_result = dropbox_storage.upload_model(
            buffer,
            f"model_info_{version}.json",
            config.DROPBOX_BASE_MODEL_FOLDER
        )
        
        if not versioned_result.get('success'):
            logger.warning(f"Failed to upload versioned model info: {versioned_result.get('error')}")
            # Continue anyway - the latest summary was uploaded successfully
        
        logger.info(f"Successfully saved training summary for version {version}")
        return True
        
    except Exception as e:
        logger.error(f"Error saving training summary: {e}")
        return False