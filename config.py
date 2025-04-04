"""
Configuration settings for the Backdoor AI Learning Server

This module handles configuration for various deployment platforms:
- Render.com
- Koyeb.com
- Local development
"""
import os
import logging
import tempfile

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Determine deployment environment
IS_RENDER = os.getenv("RENDER", "").lower() in ["true", "1", "yes"]
IS_KOYEB = os.getenv("KOYEB_DEPLOYMENT", "").lower() in ["true", "1", "yes"]

# Detect platform and set appropriate base paths
if IS_RENDER:
    logger.info("Running on Render.com platform")
    BASE_DIR = os.getenv("RENDER_DISK_PATH", "/opt/render/project")
    PLATFORM = "render"
elif IS_KOYEB:
    logger.info("Running on Koyeb.com platform")
    BASE_DIR = "/tmp"  # Koyeb uses ephemeral storage
    PLATFORM = "koyeb"
else:
    logger.info("Running in local/custom environment")
    BASE_DIR = os.getenv("BASE_DIR", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    PLATFORM = "local"

# Server settings
PORT = int(os.getenv("PORT", 10000))

# Storage paths - ensure they exist
DATA_DIR = os.path.join(BASE_DIR, "data")
MODEL_DIR = os.path.join(BASE_DIR, "models")
NLTK_DATA_PATH = os.path.join(BASE_DIR, "nltk_data")
UPLOADED_MODELS_DIR = os.path.join(MODEL_DIR, "uploaded")

# Ensure directories exist
for directory in [DATA_DIR, MODEL_DIR, NLTK_DATA_PATH, UPLOADED_MODELS_DIR]:
    os.makedirs(directory, exist_ok=True)

# Database path
DB_PATH = os.path.join(DATA_DIR, "interactions.db")

# NLTK Resources
NLTK_RESOURCES = ['punkt', 'stopwords', 'wordnet']

# Model training settings
MIN_TRAINING_DATA = int(os.getenv("MIN_TRAINING_DATA", "50"))
MAX_MODELS_TO_KEEP = int(os.getenv("MAX_MODELS_TO_KEEP", "5"))  # Keep only the most recent N models

# Training thresholds - can be tuned via environment variables
RETRAINING_THRESHOLDS = {
    'pending_models': int(os.getenv("THRESHOLD_PENDING_MODELS", "3")),
    'hours_since_last_training': int(os.getenv("THRESHOLD_HOURS", "12")),
    'new_interactions': int(os.getenv("THRESHOLD_INTERACTIONS", "100"))
}

# Text processing settings
MAX_FEATURES = int(os.getenv("MAX_FEATURES", "5000"))
NGRAM_RANGE = (1, 2)  # Bigram features

# Ensemble model settings
BASE_MODEL_WEIGHT = float(os.getenv("BASE_MODEL_WEIGHT", "2.0"))
USER_MODEL_WEIGHT = float(os.getenv("USER_MODEL_WEIGHT", "1.0"))

# Database lock timeout (seconds)
DB_LOCK_TIMEOUT = int(os.getenv("DB_LOCK_TIMEOUT", "60"))

# Model naming
MODEL_VERSION_PREFIX = os.getenv("MODEL_VERSION_PREFIX", "1.0.")

# Storage mode configuration
STORAGE_MODE = os.getenv("STORAGE_MODE", "dropbox")

# Dropbox Integration Settings
DROPBOX_ENABLED = os.getenv("DROPBOX_ENABLED", "True").lower() in ["true", "1", "yes"]
DROPBOX_API_KEY = os.getenv("DROPBOX_API_KEY", "")  # Should be set as environment variable
DROPBOX_DB_FILENAME = os.getenv("DROPBOX_DB_FILENAME", "backdoor_ai_db.db")
DROPBOX_MODELS_FOLDER = os.getenv("DROPBOX_MODELS_FOLDER", "backdoor_models")

# Dropbox Sync Settings
DROPBOX_DB_SYNC_INTERVAL = int(os.getenv("DROPBOX_DB_SYNC_INTERVAL", "60"))  # Seconds
DROPBOX_MODELS_SYNC_INTERVAL = int(os.getenv("DROPBOX_MODELS_SYNC_INTERVAL", "300"))  # Seconds

# Google Drive Integration Settings (optional)
GOOGLE_DRIVE_ENABLED = os.getenv("GOOGLE_DRIVE_ENABLED", "False").lower() in ["true", "1", "yes"]
GOOGLE_CREDENTIALS_PATH = os.getenv("GOOGLE_CREDENTIALS_PATH", "google_credentials.json")
GOOGLE_DRIVE_DB_FILENAME = os.getenv("GOOGLE_DRIVE_DB_FILENAME", "backdoor_ai_db.db")
GOOGLE_DRIVE_MODELS_FOLDER = os.getenv("GOOGLE_DRIVE_MODELS_FOLDER", "backdoor_models")

# Base model name (used to identify the model in storage)
BASE_MODEL_NAME = os.getenv("BASE_MODEL_NAME", "model_1.0.0.mlmodel")

# Memory management settings
# For platforms with memory constraints, tune these settings
MEMORY_OPTIMIZED = os.getenv("MEMORY_OPTIMIZED", "True").lower() in ["true", "1", "yes"]
MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "50"))  # Maximum file upload size in MB
CONCURRENT_TRAINING_ENABLED = os.getenv("CONCURRENT_TRAINING_ENABLED", "True").lower() in ["true", "1", "yes"]

# Temporary directory for processing
TMP_DIR = tempfile.gettempdir()

# Check for necessary credentials
if DROPBOX_ENABLED and not DROPBOX_API_KEY:
    logger.warning("Dropbox is enabled but no API key provided. Set DROPBOX_API_KEY environment variable.")
    DROPBOX_ENABLED = False

if GOOGLE_DRIVE_ENABLED and not os.path.exists(GOOGLE_CREDENTIALS_PATH):
    logger.warning(f"Google Drive is enabled but credentials file not found at {GOOGLE_CREDENTIALS_PATH}")
    GOOGLE_DRIVE_ENABLED = False

# Determine final storage mode
if STORAGE_MODE == "dropbox" and not DROPBOX_ENABLED:
    logger.warning("Dropbox storage requested but not enabled. Falling back to local storage.")
    STORAGE_MODE = "local"
elif STORAGE_MODE == "google_drive" and not GOOGLE_DRIVE_ENABLED:
    logger.warning("Google Drive storage requested but not enabled. Falling back to local storage.")
    STORAGE_MODE = "local"

logger.info(f"Using {STORAGE_MODE} storage mode")
logger.info(f"Base directory: {BASE_DIR}")
logger.info(f"Database path: {DB_PATH}")
