__version__ = '4.2.1'
__revision__ = ''
__build__ = '0'
import platform as _platform
__artisan_os__ = 'Darwin' if _platform.system() == 'Darwin' else ('Windows' if _platform.system() == 'Windows' else 'Linux')

# Keep in sync with plus.service_identity.DISPLAY_NAME and WEB_BASE_URL.
# We cannot import from plus.* here because plus.connection imports
# __version__ from this module (circular import). If service_identity
# values change, update these literals too.
__release_sponsor_name__ = 'Cotrix'
__release_sponsor_domain__ = 'tastermatrix.com'
__release_sponsor_url__ = 'https://tastermatrix.com/'
__signature__ = 'e9ca9f1c44ee9e5d4a651dd8938943e410847f5506fa1578b67408f1e91822e089c0be38c78eeb4ba14f8448d1ba1a3f27828e25133cb8da5ca84f01eae6860f'

import sys as _sys
from pathlib import Path as _Path

def resource_path(relative_path: str) -> _Path:
    """Return the absolute path to a bundled resource, working both in dev and PyInstaller frozen mode."""
    if getattr(_sys, 'frozen', False) and hasattr(_sys, '_MEIPASS'):
        return _Path(_sys._MEIPASS) / relative_path
    return _Path(__file__).parent.parent / relative_path  # dev: go up from artisanlib/ to src/
