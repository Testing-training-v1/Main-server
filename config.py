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

# Use environment variables if set, otherwise use platform-specific defaults
DATA_DIR = os.getenv("DATA_DIR", None)
MODEL_DIR = os.getenv("MODELS_DIR", None)
NLTK_DATA_PATH = os.getenv("NLTK_DATA_DIR", None)

# Detect platform and set appropriate base paths if not set by environment variables
if IS_RENDER:
    logger.info("Running on Render.com platform")
    PLATFORM = "render"
    # Use /tmp for Render.com if not set in environment
    if not DATA_DIR:
        DATA_DIR = "/tmp/data"
    if not MODEL_DIR:
        MODEL_DIR = "/tmp/models"
    if not NLTK_DATA_PATH:
        NLTK_DATA_PATH = "/tmp/nltk_data"
elif IS_KOYEB:
    logger.info("Running on Koyeb.com platform")
    PLATFORM = "koyeb"
    # Use /tmp for Koyeb if not set in environment
    if not DATA_DIR:
        DATA_DIR = "/tmp/data"
    if not MODEL_DIR:
        MODEL_DIR = "/tmp/models"
    if not NLTK_DATA_PATH:
        NLTK_DATA_PATH = "/tmp/nltk_data"
else:
    logger.info("Running in local/custom environment")
    PLATFORM = "local"
    # Use local paths if not set in environment
    BASE_DIR = os.getenv("BASE_DIR", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if not DATA_DIR:
        DATA_DIR = os.path.join(BASE_DIR, "data")
    if not MODEL_DIR:
        MODEL_DIR = os.path.join(BASE_DIR, "models")
    if not NLTK_DATA_PATH:
        NLTK_DATA_PATH = os.path.join(BASE_DIR, "nltk_data")

# Log the paths being used
logger.info(f"Using DATA_DIR: {DATA_DIR}")
logger.info(f"Using MODEL_DIR: {MODEL_DIR}")
logger.info(f"Using NLTK_DATA_PATH: {NLTK_DATA_PATH}")

# Server settings
PORT = int(os.getenv("PORT", 10000))

# Storage paths - ensure they exist with error handling
UPLOADED_MODELS_DIR = os.path.join(MODEL_DIR, "uploaded")

# Ensure directories exist with error handling
for directory in [DATA_DIR, MODEL_DIR, NLTK_DATA_PATH, UPLOADED_MODELS_DIR]:
    try:
        os.makedirs(directory, exist_ok=True)
        logger.info(f"Created directory: {directory}")
    except PermissionError:
        logger.warning(f"Permission denied creating directory: {directory}")
        # If this is a critical directory, we need to handle the error
        if directory == DATA_DIR:
            # Fallback to a temporary directory
            DATA_DIR = tempfile.mkdtemp()
            logger.info(f"Using temporary directory instead: {DATA_DIR}")
        elif directory == MODEL_DIR:
            MODEL_DIR = tempfile.mkdtemp()
            UPLOADED_MODELS_DIR = os.path.join(MODEL_DIR, "uploaded")
            os.makedirs(UPLOADED_MODELS_DIR, exist_ok=True)
            logger.info(f"Using temporary directory instead: {MODEL_DIR}")
    except Exception as e:
        logger.error(f"Error creating directory {directory}: {e}")

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
DROPBOX_API_KEY = os.getenv("DROPBOX_API_KEY", "sl.u.AFq4bB6QLwGkFBnEjGlZUaNV4LLlz9VNhsgHBOk5gF-XjlqEW51vkc5FieOD-K8OJ2NCBPtpMvVzQ089oWXlZh_v1v_GzsiXeiWwZ3zVCzJJDc4i0xO2xaYDKyN5fVenr6_hnMsqX__nD2djGteMl-JCc-0r0hrsLYemibNUBKPu7zCZR450hn71ljeXqVSkP22lNLjmBZwqmHHkDXJE_LeSCeoeqVdoV0-WbjCe1oHjz3EcwhLKk0oyNY_mAXM4H9VRI7_Mz0tjCTsVwe5pWFuXKB8m8j6WmMzR3htkLevsGdN46xTCimt2I70ejVsvXkbq8d6c1o2Onu1z4y777Bnw83Q1kVeS3q3OvU4Xzzq7gaOD4t4Rj3Sbz1ox4ssCXyJQxKDzZ6uqrE6N_nYJ-fkXyWwBZGddySX-XkKyX9TMtD1BNEN6c9ZnDfnfdOjGcenyPnClrc2E0mtEDvzmURrcCm0KmtRyH_gEU6xbkQk4ZbkE0Dj94kIER32aWDn1arwC1Ur8T4WP5GzhVayXARggjqu_-JKiCYnH_HbQvSzBFcCVfdeErFA7caeRvNo6JSR2lkLjVJysWLwdaiwbTYFw9iKgjZAH-cpny6gh3yhsk0HyfP51HUqFCA7vmc4pQwCb4IASGOmtfr_FsVE3E6UdvQHgZY1-twKIehZXFdHyweWK4O5bm_IHVur1Eh0IQySf5dNTuEm1BoRbyVEPtlRw_l3qNHpvJ5Bm_qnL4py1N9Q3DhnuuznVsh-Yh42Q305mHC9qyXO-25-Covn9G3KYvxN4oU4GVjZodjTePcNloK5gdv1ZKAM2Zfh4OALowTy4fijXJIEyWqZc5DeHf8F3xZLr702INz78yAht2gth8P9MP2mpfrCajUshUOdMXvJS6niQ5XzTJ_HNX3CqqOu62NQcVfiK449pLpanhES_Cn8WHmpdPXVaA2DTpS_V-xeqsPB6GKzlL8AJBigR8wKsa85JWtg4iQ7nCaaXGUjkmSJN0oykNFndxzEqzu8rNStFvmBiiGen0gbxwM-j-gNT7FjPGfuWyZK3wrUMwyIyVC59Pp72NoCZ8DEbfoAHF5N3bk7ts7-mFprp5_jpjKOc9CX_g41patE0ylQoReZ3QdVJegWS-rxQwCx0-2cz44fUoAkPzDm6NwiZIXp5c-9wG-4vj_NOBgQdQ0quXXJ8JKyoRcnjW4Kc1B20J0gewpNZYitWC_B3bGHeANwTrKlZY_HfLbF32MZiClJ-vN74EnwNcgVSI15_9uN8h2OhvO93GEc5zl7lo2-HooinGQoPTlloIn1XxdY2AbVHxIcrppv2pDY9dctTKLXtmPekCwzIuwsA0In1zNH0o1L5pMzo3_tzm2jF6ORcWRhRoXyWD6IcTKvVjp37giytLUAF4uZKV6rQ38J8XOA_qpVXQT8wA-wyIX-QOtOJrVl_tNGmtg")  # Should be set as environment variable
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
