"""
Admin models package.
"""

from core.models.admin.admin_audit import AdminAuditLog
from core.models.admin.admin_onetimepass import AdminOneTimePass

__all__ = ["AdminAuditLog", "AdminOneTimePass"]
