from typing import Dict, List, Set, Optional

# ==============================================================================
# JobCatalyst AI - Standard Permission Matrix (RBAC Base Configuration)
# ==============================================================================
# Maps logical roles to standard granular permission boundaries.
DEFAULT_ROLE_PERMISSIONS_MATRIX: Dict[str, List[str]] = {
    "ADMIN": [
        "admin:all",
        "user:read",
        "user:write",
        "user:delete",
        "resumes:read",
        "resumes:write",
        "resumes:delete",
        "jobs:read",
        "jobs:create",
        "jobs:write",
        "jobs:delete",
        "coach:access",
        "coach:session",
    ],
    "USER": [
        "user:read",
        "resumes:read",
        "resumes:write",
        "resumes:delete",
        "jobs:read",
    ],
    "RECRUITER": [
        "user:read",
        "resumes:read",  # can inspect public/submitted resumes
        "jobs:read",
        "jobs:create",
        "jobs:write",
        "jobs:delete",
    ],
    "CAREER_COACH": [
        "user:read",
        "resumes:read",
        "coach:access",
        "coach:session",
    ]
}


class AuthorizationService:
    """
    Role-Based Access Control (RBAC) evaluation engine.
    Resolves permissions against active role lists and verifies access request grants.
    """

    def __init__(self, matrix: Optional[Dict[str, List[str]]] = None) -> None:
        self._matrix = matrix or DEFAULT_ROLE_PERMISSIONS_MATRIX

    def get_permissions_for_roles(self, roles: List[str]) -> Set[str]:
        """
        Aggregates and flattens all distinct permission grants associated with a set of roles.
        """
        permissions: Set[str] = set()
        for role in roles:
            role_upper = role.upper().strip()
            if role_upper in self._matrix:
                permissions.update(self._matrix[role_upper])
        return permissions

    def has_permission(self, user_roles: List[str], required_permission: str) -> bool:
        """
        Checks if the list of active user roles grants the required permission.
        Supports wildcard bypass ('admin:all') for ADMIN accounts.
        """
        user_permissions = self.get_permissions_for_roles(user_roles)
        
        # Admin wildcard escape-hatch check
        if "admin:all" in user_permissions:
            return True
            
        return required_permission in user_permissions

    def has_any_role(self, user_roles: List[str], allowed_roles: List[str]) -> bool:
        """
        Validates whether user carries at least one of the specified allowed roles.
        """
        user_roles_upper = {r.upper().strip() for r in user_roles}
        allowed_roles_upper = {r.upper().strip() for r in allowed_roles}
        return len(user_roles_upper.intersection(allowed_roles_upper)) > 0
