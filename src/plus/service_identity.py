#
# service_identity.py
#
# ABOUT
# Central identity for the configured cloud sync provider.

from typing import Final


SERVICE_ID: Final[str] = 'tm-artisanz'
DISPLAY_NAME: Final[str] = 'Cotrix'
API_BASE_URL: Final[str] = 'https://tastermatrix.com/api/tm-artisanz/v1'
WEB_BASE_URL: Final[str] = 'https://tastermatrix.com'
SHOP_BASE_URL: Final[str] = WEB_BASE_URL
KEYRING_SERVICE: Final[str] = SERVICE_ID
COTRIX_ROASTS_PATH: Final[str] = '/app/#/pages/cotrix/roasts'


def service_id() -> str:
    return SERVICE_ID


def display_name() -> str:
    return DISPLAY_NAME


def api_base_url() -> str:
    return API_BASE_URL


def web_base_url() -> str:
    return WEB_BASE_URL


def shop_base_url() -> str:
    return SHOP_BASE_URL


def cotrix_roasts_url() -> str:
    return f'{WEB_BASE_URL}{COTRIX_ROASTS_PATH}'


def keyring_service() -> str:
    return KEYRING_SERVICE


def endpoint(path: str) -> str:
    normalized_path = path if path.startswith('/') else f'/{path}'
    return f'{API_BASE_URL}{normalized_path}'
