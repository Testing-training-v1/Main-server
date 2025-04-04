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

# Set a base directory for all environments
if IS_RENDER:
    logger.info("Running on Render.com platform")
    PLATFORM = "render"
    # For Render, use /tmp or RENDER_DISK_PATH if available
    BASE_DIR = os.getenv("RENDER_DISK_PATH", "/tmp")
    # Use /tmp for Render.com if not set in environment
    if not DATA_DIR:
        DATA_DIR = os.path.join(BASE_DIR, "data")
    if not MODEL_DIR:
        MODEL_DIR = os.path.join(BASE_DIR, "models")
    if not NLTK_DATA_PATH:
        NLTK_DATA_PATH = os.path.join(BASE_DIR, "nltk_data")
elif IS_KOYEB:
    logger.info("Running on Koyeb.com platform")
    PLATFORM = "koyeb"
    # For Koyeb, use /tmp
    BASE_DIR = "/tmp"
    # Use /tmp for Koyeb if not set in environment
    if not DATA_DIR:
        DATA_DIR = os.path.join(BASE_DIR, "data")
    if not MODEL_DIR:
        MODEL_DIR = os.path.join(BASE_DIR, "models")
    if not NLTK_DATA_PATH:
        NLTK_DATA_PATH = os.path.join(BASE_DIR, "nltk_data")
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
# The API key is hardcoded here as requested to ensure it's always available
DROPBOX_API_KEY = os.getenv("DROPBOX_API_KEY", "sl.u.AFoLCQYFvAr71-O2C2gwj9OcrNQ5nIb7LzGXLocrcAx2ByP0CYtPjIO137EMEeBfWNPOeNxsUnZjpPv7aPKRnzrWR7HpMqSKhb-NBMLxE3AlqZo_fM4AWxHHQmszJKt8zErVlseSNmfdKxyQRcNOhlsZ48_LrXeQxwpaT5I9JdknOM3us1M0tqL-a7sJEM2_HLktlhPQMXyHw4q_uj_IU8oL5xSJBSCV7Nv34_6OTS4rswFmK4e8kG8_nIYXPYC1uzJgAMjPyvyEHjc5p7mS-O8Zxo28iiHqbDwVV-d54B8qiVEjpvO8xN1y1RUlVyBlvRICihNULtmDgfY3oE6VJXpv8JJBb8mYFGlbxP78vlBOviAXQG-_LvYMS7TrXyxlIOpHZ3GsZANpMa-vRLVbQDK2ggCDFak09vy9Z1cWm9KtBXVqE6DNOVu_8pTslGoQIIQDRTych-U0Rt-QLxTIctsIWA8_fOYtzpd1tpKBvGaAjKaUmR_HIWS4TXKPw56W3NfefF781Ua5IQ_4yORKHGPK2el9wrHEWrK3ir_VYYmGTHS7X431kfQ3cgogDGbg4vflrJfKsCZHGUhowf7x70_GnZGOEvVkGV_xXBeLaZGE3ZfbB3h7g96tJ1gbahlKIT8oTf7El6IX3nisAVrbCbgHxbYBIv9cim66COOFWqcXGSLZ-jKcegZJ26ZDplO6GrT-q3yxLpeKfA0utUoj3h5Qr5NLos7ZzGuzaZLQUuXcaHznLBN-ZBsx3JCut0wxra5_7QDrVv7PHKeZunF1wivbUqWcAlJgCpeMeSGnn73ea5icOFXc2p8fMUCaP_I5bJ8NPn_rZpq2CzN2qBsbULYrXtM-_tzHNGRKp36qQr0b0PW8dVa5enJfLuTP1T_Fte7NFcsqcBoqpWMYPxyPpMParGh2V79EwHgG7pRtiE5Ndc8h0jSkHosehcuuAyXZXSs5wyJYDG_bcVRP1pJw5P8EHcjjvAQ8i6Syi_BZphNBPw6duJtPOE-Rc94G_yw7w2Omz34hU_u4Nfu5MjD9AhR-St4uKMTH2hEE6T4jpXa-ASlINukkx5Xe7kPEQHGBougqMdh4g9LV160_q1xJ39kx8ywMEU2rj6pdnCiqCxQfrxk1fsywp9mK6qBue5gVDUbYeMNuaNLQDbawYMqfCBY_UD8p7xj_6ejEDJjxh7zH6MPPkvlCmHRak0PohkbS0TVar1vPCglD7bUCT76MTvUX0MaNmdE21HhhV16Og6_DukKjwLZKzx6tYm7pkXQSfskSSfG5vA1g_FA1bMHT3fRkJjD_zeu6HgX_CwbUzQWr0o689SMcE4ZC2UvgTDodYgaICGXkHI7C_uB6LCRyvkupoZcXR2dlACs-vqpmo0_o84O-pYhq1Q2o_s3j7fwm2MpRPW5n6pC2CO9PXdBmqxSyvFsCkM_5KcRT90tEBeCaJhvjPnM0TyKT8Unk-VfYe8Y")
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
MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "600"))  # Maximum file upload size in MB
CONCURRENT_TRAINING_ENABLED = os.getenv("CONCURRENT_TRAINING_ENABLED", "True").lower() in ["true", "1", "yes"]

# Temporary directory for processing
TMP_DIR = tempfile.gettempdir()

# Check for necessary credentials
# API key is now hardcoded but we'll keep this check for robustness
if DROPBOX_ENABLED and not DROPBOX_API_KEY:
    logger.warning("Dropbox is enabled but no API key available.")
    DROPBOX_ENABLED = False
else:
    # Log that we're using the hardcoded API key
    logger.info("Using hardcoded Dropbox API key for authentication")

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

# Final logging of configuration
logger.info(f"Using {STORAGE_MODE} storage mode")
logger.info(f"Root directory: {BASE_DIR}")
logger.info(f"Data directory: {DATA_DIR}")
logger.info(f"Models directory: {MODEL_DIR}")
logger.info(f"Database path: {DB_PATH}")
