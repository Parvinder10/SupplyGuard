# ============================================================================
# Apache Superset 3.0 Configuration for SupplyGuard
# ============================================================================

import os

ROW_LIMIT = 50000
SUPERSET_WEBSERVER_PORT = 8088

# Secret key for session cryptography
SECRET_KEY = os.getenv("SUPERSET_SECRET_KEY", "supplyguard_super_secure_enterprise_secret_key_2026")

# Metadata database (PostgreSQL backend)
SQLALCHEMY_DATABASE_URI = os.getenv(
    "SUPERSET_DATABASE_URI", 
    "postgresql://postgres:postgres@postgres:5432/supplyguard_db"
)

# Feature flags for interactive filters, alert reporting, and advanced analytics
FEATURE_FLAGS = {
    "DASHBOARD_NATIVE_FILTERS": True,
    "DASHBOARD_CROSS_FILTERS": True,
    "DASHBOARD_NATIVE_FILTERS_SET": True,
    "ENABLE_TEMPLATE_PROCESSING": True,
    "ALERT_REPORTS": True,
    "ALERTS_ATTACH_REPORTS": True,
    "ALLOW_FULL_CSV_EXPORT": True
}

# Allow iframe embedding for portal integration
ENABLE_EMBEDDED_SUPERSET = True
TALISMAN_ENABLED = False
WTF_CSRF_ENABLED = False

# Enable CORS for frontend integration
ENABLE_CORS = True
CORS_OPTIONS = {
    "supports_credentials": True,
    "allow_headers": ["*"],
    "resources": ["*"],
    "origins": ["*"]
}
