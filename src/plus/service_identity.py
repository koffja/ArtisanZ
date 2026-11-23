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


# Wordings that all refer to the service, each with the text that replaces it in
# translated strings. Upstream reworded its strings in v5 ("artisan platform",
# "artisan account"); the Chinese entries are the renderings upstream's
# artisan_zh_CN.ts uses for the same terms. Articles are part of the needle so
# the English result stays grammatical ("with the artisan platform" -> "with Cotrix").
def brand_substitutions() -> tuple[tuple[str, str], ...]:
    name = DISPLAY_NAME
    return (
        ('An artisan account', f'A {name} account'),
        ('an artisan account', f'a {name} account'),
        ('the artisan platform', name),
        ('artisan.plus', name),
        ('artisan platform', name),
        ('artisan account', f'{name} account'),
        ('工匠平台', name),
        ('手工艺平台', name),
        ('工匠账户', f'{name}账户'),
    )


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
