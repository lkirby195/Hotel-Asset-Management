"""Tests for the User model role hierarchy."""

from tests.conftest import make_user


class TestUserRoleHierarchy:
    """Test User.has_role() role hierarchy logic."""

    def test_admin_has_all_roles(self):
        user = make_user(role="admin")
        assert user.has_role("admin")
        assert user.has_role("executive")
        assert user.has_role("operator")
        assert user.has_role("manager")

    def test_executive_has_exec_and_below(self):
        user = make_user(role="executive")
        assert not user.has_role("admin")
        assert user.has_role("executive")
        assert user.has_role("operator")
        assert user.has_role("manager")

    def test_operator_has_operator_and_below(self):
        user = make_user(role="operator")
        assert not user.has_role("admin")
        assert not user.has_role("executive")
        assert user.has_role("operator")
        assert user.has_role("manager")

    def test_manager_has_only_manager(self):
        user = make_user(role="manager")
        assert not user.has_role("admin")
        assert not user.has_role("executive")
        assert not user.has_role("operator")
        assert user.has_role("manager")

    def test_unknown_role_has_nothing(self):
        user = make_user(role="unknown")
        assert not user.has_role("admin")
        assert not user.has_role("executive")
        assert not user.has_role("operator")
        assert not user.has_role("manager")
