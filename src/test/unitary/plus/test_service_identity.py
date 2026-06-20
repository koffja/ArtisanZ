"""Focused tests for TM-ArtisanZ service identity configuration."""

from plus import config, service_identity


def test_tm_artisanz_service_identity_values() -> None:
    assert service_identity.service_id() == 'tm-artisanz'
    assert service_identity.display_name() == 'TM-ArtisanZ'
    assert service_identity.api_base_url() == 'https://tastermatrix.com/api/tm-artisanz/v1'
    assert service_identity.web_base_url() == 'https://tastermatrix.com'
    assert service_identity.shop_base_url() == 'https://tastermatrix.com'
    assert service_identity.keyring_service() == 'tm-artisanz'


def test_config_urls_are_derived_from_service_identity() -> None:
    assert config.app_name == service_identity.display_name()
    assert config.api_base_url == service_identity.api_base_url()
    assert config.web_base_url == service_identity.web_base_url()
    assert config.shop_base_url == service_identity.shop_base_url()
    assert config.auth_url == service_identity.endpoint('/accounts/users/authenticate')
    assert config.stock_url == service_identity.endpoint('/acoffees')
    assert config.roast_url == service_identity.endpoint('/aroast')
    assert config.lock_schedule_url == service_identity.endpoint('/aschedule/lock')
    assert config.notifications_url == service_identity.endpoint('/notifications')
