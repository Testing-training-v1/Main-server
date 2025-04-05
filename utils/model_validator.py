"""
Model validation utilities for the Backdoor AI server.

This module provides functionality to:
- Validate ML models by checking structure and metadata
- Test models with sample inputs
- Generate diagnostic information
- Store validation results in Dropbox
"""

import io
import os
import logging
import json
import time
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime

# Try to import coremltools safely
try:
    import coremltools as ct
except ImportError:
    ct = None

import config

logger = logging.getLogger(__name__)

class ModelValidationError(Exception):
    """Exception raised when model validation fails."""
    pass

def validate_base_model() -> Dict[str, Any]:
    """
    Validate the base model by loading it and checking its structure.
    
    This function:
    1. Attempts to load the base model
    2. Validates its structure
    3. Tests it with sample input
    4. Stores results in Dropbox
    
    Returns:
        Dict with validation results
    """
    logger.info("Starting base model validation")
    
    start_time = time.time()
    
    # Create results dictionary
    validation_results = {
        "timestamp": datetime.now().isoformat(),
        "model_name": config.BASE_MODEL_NAME,
        "success": False,
        "errors": [],
        "warnings": [],
        "metadata": {},
        "structure": {},
        "test_results": {}
    }
    
    # Step 1: Check if CoreML tools are available
    if ct is None:
        error = "CoreMLTools not installed - cannot validate model structure"
        validation_results["errors"].append(error)
        logger.error(error)
        return _store_validation_results(validation_results)
    
    # Step 2: Get the base model (either streamed or buffered)
    try:
        # First try using the streaming API to avoid loading the entire model
        try:
            from utils.model_streamer import get_base_model_stream
            logger.info("Attempting to stream model for validation")
            model_buffer = get_base_model_stream()
            if model_buffer:
                validation_results["model_found"] = True
                validation_results["streaming"] = True
                logger.info(f"Found base model {config.BASE_MODEL_NAME} using streaming API")
            else:
                # Fall back to regular buffer method
                from utils.model_download import get_base_model_buffer
                model_buffer = get_base_model_buffer()
                if model_buffer is None:
                    error = f"Base model {config.BASE_MODEL_NAME} not found"
                    validation_results["errors"].append(error)
                    logger.error(error)
                    return _store_validation_results(validation_results)
                    
                validation_results["model_found"] = True
                logger.info(f"Found base model {config.BASE_MODEL_NAME}")
        except ImportError:
            # Fall back to regular buffer method
            from utils.model_download import get_base_model_buffer
            model_buffer = get_base_model_buffer()
            
            if model_buffer is None:
                error = f"Base model {config.BASE_MODEL_NAME} not found"
                validation_results["errors"].append(error)
                logger.error(error)
                return _store_validation_results(validation_results)
                
            validation_results["model_found"] = True
            logger.info(f"Found base model {config.BASE_MODEL_NAME}")
        
    except Exception as e:
        error = f"Error loading base model: {str(e)}"
        validation_results["errors"].append(error)
        logger.error(error)
        return _store_validation_results(validation_results)
    
    # Step 3: Prepare model for CoreML validation
    try:
        # Check if we're in memory-only mode (set in entrypoint.sh)
        memory_only_mode = os.environ.get('MEMORY_ONLY_MODE') == 'True'
        if memory_only_mode:
            logger.info("Running in memory-only mode - avoiding temporary files")
        
        # Check if model_buffer is a streaming object or dict with streaming info
        is_streaming = hasattr(model_buffer, 'read') and hasattr(model_buffer, 'seek') and validation_results.get("streaming", False)
        is_streaming_dict = isinstance(model_buffer, dict) and model_buffer.get('streaming') and model_buffer.get('download_url')
        
        # Prepare memory buffer for validation
        import io
        memory_buffer = io.BytesIO()
        
        if is_streaming:
            # Stream from existing streaming object to memory buffer
            logger.info("Streaming model to memory buffer for validation")
            chunk_size = 1024 * 1024  # 1MB chunks
            while True:
                chunk = model_buffer.read(chunk_size)
                if not chunk:
                    break
                memory_buffer.write(chunk)
            # Reset positions
            model_buffer.seek(0)
            memory_buffer.seek(0)
            
        elif is_streaming_dict:
            # Stream from URL to memory buffer
            logger.info("Streaming model from URL to memory buffer")
            import requests
            
            url = model_buffer.get('download_url')
            
            # Use streaming requests to avoid loading the entire model at once
            with requests.get(url, stream=True) as response:
                if response.status_code == 200:
                    # Get total size for logging
                    total_size = int(response.headers.get('content-length', 0))
                    downloaded = 0
                    
                    # Use small chunks to avoid high memory usage
                    for chunk in response.iter_content(chunk_size=1024*1024):  # 1MB chunks
                        if chunk:
                            memory_buffer.write(chunk)
                            downloaded += len(chunk)
                            
                            # Log progress for large models
                            if total_size > 0 and downloaded % (20*1024*1024) == 0:  # Log every 20MB
                                logger.info(f"Downloaded {downloaded/(1024*1024):.1f}MB of {total_size/(1024*1024):.1f}MB")
                    
                    memory_buffer.seek(0)
                    logger.info(f"Successfully streamed {downloaded/(1024*1024):.1f}MB to memory")
                else:
                    error = f"Error downloading model: HTTP {response.status_code}"
                    validation_results["errors"].append(error)
                    logger.error(error)
                    return _store_validation_results(validation_results)
        else:
            # We have a regular buffer
            logger.info("Copying model buffer for validation")
            model_buffer.seek(0)
            memory_buffer.write(model_buffer.read())
            memory_buffer.seek(0)
            
        # Step 4: Load and validate model structure
        try:
            # Try to load directly from memory if possible
            try:
                logger.info("Attempting to load model directly from memory buffer")
                model = ct.models.MLModel(memory_buffer)
                logger.info("Successfully loaded model from memory buffer")
            except Exception as mem_error:
                # If direct memory loading fails, we need to use a temp file as fallback
                logger.warning(f"Could not load model directly from memory: {mem_error}")
                
                if memory_only_mode:
                    # In memory-only mode, create a virtual temp file or fail
                    try:
                        from utils.virtual_tempfile import NamedTemporaryFile
                        with NamedTemporaryFile(suffix=".mlmodel") as tmp:
                            tmp_path = tmp.name
                            memory_buffer.seek(0)
                            tmp.write(memory_buffer.read())
                            logger.info(f"Using virtual temp file: {tmp_path}")
                            model = ct.models.MLModel(tmp)
                    except Exception as vt_error:
                        error = f"Could not validate model in memory-only mode: {vt_error}"
                        validation_results["errors"].append(error)
                        logger.error(error)
                        return _store_validation_results(validation_results)
                else:
                    # In standard mode, fall back to a physical temp file
                    import tempfile
                    with tempfile.NamedTemporaryFile(suffix=".mlmodel", delete=False) as tmp:
                        tmp_path = tmp.name
                        memory_buffer.seek(0)
                        tmp.write(memory_buffer.read())
                    
                    logger.info(f"Loading model from temporary file: {tmp_path}")
                    model = ct.models.MLModel(tmp_path)
                    
                    # Add temp file info to results for cleanup later
                    validation_results["temp_file"] = tmp_path
            
            # Get the model specification
            spec = model.get_spec()
            
            # Check basic structure
            validation_results["structure"] = {
                "specification_version": str(spec.specificationVersion),
                "type": spec.WhichOneof('Type'),
                "input_count": len(spec.description.input),
                "output_count": len(spec.description.output),
                "inputs": [],
                "outputs": []
            }
            
            # Get input descriptions
            for input_desc in spec.description.input:
                input_info = {
                    "name": input_desc.name,
                    "type": str(input_desc.type)
                }
                validation_results["structure"]["inputs"].append(input_info)
            
            # Get output descriptions
            for output_desc in spec.description.output:
                output_info = {
                    "name": output_desc.name,
                    "type": str(output_desc.type)
                }
                validation_results["structure"]["outputs"].append(output_info)
            
            # Get metadata if available
            if model.user_defined_metadata:
                validation_results["metadata"] = {
                    k: v for k, v in model.user_defined_metadata.items()
                }
                
                # Get intents list if available
                if 'intents' in model.user_defined_metadata:
                    intents = model.user_defined_metadata['intents'].split(',')
                    validation_results["metadata"]["intent_count"] = len(intents)
                    validation_results["metadata"]["intents"] = intents
            
            logger.info(f"Successfully validated model structure")
            
            # Step 5: Test the model with sample input
            test_results = _test_model_with_samples(model)
            validation_results["test_results"] = test_results
            
            # Set success flag based on results
            validation_results["success"] = True
            if test_results.get("failed_count", 0) > 0:
                validation_results["warnings"].append(f"{test_results['failed_count']} model tests failed")
                logger.warning(f"Model validation: {test_results['failed_count']} tests failed")
            else:
                logger.info("All model tests passed successfully")
                
        except Exception as e:
            error = f"Error validating model structure: {str(e)}"
            validation_results["errors"].append(error)
            logger.error(error)
            
        # Clean up resources
        memory_only_mode = os.environ.get('MEMORY_ONLY_MODE') == 'True'
        
        # Clean up memory buffer
        try:
            if 'memory_buffer' in locals():
                memory_buffer.close()
        except Exception as e:
            logger.debug(f"Error closing memory buffer: {e}")
            
        # Clean up temp file if created and not in memory-only mode
        if not memory_only_mode and 'tmp_path' in locals() and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
                logger.debug(f"Deleted temporary file: {tmp_path}")
            except Exception as e:
                logger.warning(f"Could not delete temp file {tmp_path}: {e}")
            
    except Exception as e:
        error = f"Error preparing model for validation: {str(e)}"
        validation_results["errors"].append(error)
        logger.error(error)
    
    # Calculate validation duration
    validation_results["duration_seconds"] = time.time() - start_time
    
    # Store validation results
    return _store_validation_results(validation_results)

def _test_model_with_samples(model) -> Dict[str, Any]:
    """
    Test the model with sample inputs.
    
    Args:
        model: CoreML model instance
        
    Returns:
        Dict with test results
    """
    test_results = {
        "total_count": 0,
        "passed_count": 0,
        "failed_count": 0,
        "samples": []
    }
    
    # Sample texts to test with
    sample_texts = [
        "hello there",
        "what time is it",
        "help me with this",
        "thank you for your help",
        "goodbye"
    ]
    
    # Test each sample
    for text in sample_texts:
        test_result = {
            "input": text,
            "success": False,
            "error": None,
            "output": None,
            "confidence": None
        }
        
        try:
            # Make prediction
            prediction = model.predict({"text": text})
            
            # Extract result
            intent = None
            confidence = 0.0
            
            # Handle different output formats
            if isinstance(prediction, dict):
                # Extract intent and confidence based on available keys
                if 'intent' in prediction:
                    intent = prediction['intent']
                    
                    # Try to find confidence
                    if 'probabilities' in prediction:
                        probs = prediction['probabilities']
                        if isinstance(probs, dict) and intent in probs:
                            confidence = probs[intent]
                        elif isinstance(probs, list) and hasattr(model, 'classes_'):
                            try:
                                idx = model.classes_.index(intent)
                                confidence = probs[idx]
                            except (ValueError, IndexError):
                                pass
            
            test_result["success"] = True
            test_result["output"] = intent
            test_result["confidence"] = confidence
            test_results["passed_count"] += 1
            
        except Exception as e:
            test_result["error"] = str(e)
            test_results["failed_count"] += 1
        
        test_results["samples"].append(test_result)
        test_results["total_count"] += 1
    
    return test_results

def _store_validation_results(results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Store validation results in Dropbox.
    
    Args:
        results: Validation results dictionary
        
    Returns:
        Updated results with storage information
    """
    # Only store in Dropbox if enabled
    if not config.DROPBOX_ENABLED:
        results["storage"] = {
            "location": "local_only",
            "reason": "Dropbox storage not enabled"
        }
        return results
    
    try:
        # Import Dropbox storage
        from utils.dropbox_storage import get_dropbox_storage
        dropbox_storage = get_dropbox_storage()
        
        # Create validation folder if needed
        validation_folder = "model_validation"
        try:
            folder_path = f"/{validation_folder}"
            try:
                dropbox_storage.dbx.files_get_metadata(folder_path)
            except Exception:
                # Create folder if it doesn't exist
                logger.info(f"Creating validation folder: {folder_path}")
                dropbox_storage.dbx.files_create_folder_v2(folder_path)
        except Exception as e:
            logger.warning(f"Error ensuring validation folder exists: {e}")
            results["storage"] = {
                "location": "local_only",
                "reason": f"Dropbox folder creation failed: {str(e)}"
            }
            return results
        
        # Create a timestamped filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"validation_{timestamp}.json"
        
        # Convert results to JSON
        import io
        json_data = json.dumps(results, indent=2)
        buffer = io.BytesIO(json_data.encode('utf-8'))
        
        # Upload to Dropbox
        upload_result = dropbox_storage.upload_model(
            buffer,
            filename,
            validation_folder
        )
        
        if upload_result and upload_result.get('success'):
            # Add storage info to results
            results["storage"] = {
                "location": "dropbox",
                "path": upload_result.get('path'),
                "timestamp": datetime.now().isoformat()
            }
            
            # Try to get download URL
            try:
                model_info = dropbox_storage.get_model_stream(
                    filename,
                    folder=validation_folder
                )
                if model_info and model_info.get('success') and 'download_url' in model_info:
                    results["storage"]["download_url"] = model_info['download_url']
            except Exception as e:
                logger.warning(f"Error getting download URL: {e}")
                
            logger.info(f"Stored validation results in Dropbox: {validation_folder}/{filename}")
            
            # Also save as latest validation result
            try:
                latest_buffer = io.BytesIO(json_data.encode('utf-8'))
                latest_result = dropbox_storage.upload_model(
                    latest_buffer,
                    "latest_validation.json",
                    validation_folder
                )
                if latest_result and latest_result.get('success'):
                    logger.info("Updated latest validation results in Dropbox")
            except Exception as e:
                logger.warning(f"Error updating latest validation: {e}")
                
        else:
            # Handle upload failure
            error = upload_result.get('error', 'Unknown error')
            results["storage"] = {
                "location": "local_only",
                "reason": f"Dropbox upload failed: {error}"
            }
            logger.warning(f"Failed to upload validation results: {error}")
    
    except Exception as e:
        # Handle any exceptions
        results["storage"] = {
            "location": "local_only",
            "reason": f"Error: {str(e)}"
        }
        logger.error(f"Error storing validation results: {e}")
    
    return results

def get_latest_validation_results() -> Dict[str, Any]:
    """
    Get the latest validation results from Dropbox.
    
    Returns:
        Dict with validation results or empty dict if not found
    """
    if not config.DROPBOX_ENABLED:
        logger.warning("Dropbox not enabled - cannot get validation results")
        return {}
    
    try:
        # Import Dropbox storage
        from utils.dropbox_storage import get_dropbox_storage
        dropbox_storage = get_dropbox_storage()
        
        # Try to download latest validation results
        memory_download = dropbox_storage.download_model_to_memory(
            "latest_validation.json",
            folder="model_validation"
        )
        
        if memory_download and memory_download.get('success'):
            # Parse JSON
            model_buffer = memory_download.get('model_buffer')
            model_buffer.seek(0)
            json_data = model_buffer.read().decode('utf-8')
            
            # Parse the JSON data
            validation_results = json.loads(json_data)
            logger.info("Successfully loaded latest validation results from Dropbox")
            return validation_results
        
        logger.warning("Latest validation results not found in Dropbox")
        return {}
        
    except Exception as e:
        logger.error(f"Error getting latest validation results: {e}")
        return {}
