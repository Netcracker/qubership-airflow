import jwt
import os

from typing import TYPE_CHECKING

from airflow.providers.keycloak.auth_manager.keycloak_auth_manager import (
    KeycloakAuthManager,
)
from airflow.api_fastapi.common.types import MenuItem
from airflow.providers.keycloak.auth_manager.user import KeycloakAuthManagerUser
from airflow.providers.keycloak.auth_manager.resources import KeycloakResource

if TYPE_CHECKING:
    from airflow.api_fastapi.auth.managers.base_auth_manager import ResourceMethod

AIRFLOW_KEYCLOAK_ADMIN_ROLES = os.getenv("AIRFLOW_KEYCLOAK_ADMIN_ROLES", "airflow-role")
airflow_keycloak_admin_roles_list = AIRFLOW_KEYCLOAK_ADMIN_ROLES.split(",")


class QSRBACKeycloakAuthManager(KeycloakAuthManager):

    @staticmethod
    def _is_authorized_qs(user: KeycloakAuthManagerUser) -> bool:
        token = user.access_token
        me = jwt.decode(token, algorithms="RS256", options={"verify_signature": False})
        for airflow_role in airflow_keycloak_admin_roles_list:
            if airflow_role in me["realm_access"]["roles"]:
                return True
        return False

    def filter_authorized_menu_items(
        self, menu_items: list[MenuItem], *, user: KeycloakAuthManagerUser
    ) -> list[MenuItem]:
        if self._is_authorized_qs(user):
            return menu_items
        return []

    def _is_authorized(
        self,
        *,
        method: ResourceMethod | str,
        resource_type: KeycloakResource,
        user: KeycloakAuthManagerUser,
        resource_id: str | None = None,
        attributes: dict[str, str | None] | None = None,
    ) -> bool:
        return self._is_authorized_qs(user)
