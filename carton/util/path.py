import os
import pathlib
import sys

from carton.util.strings import FILE_EXISTS

def _darwin_appsupport():
    try:
        import AppKit

        app_support = AppKit.NSSearchPathForDirectoriesInDomains(
            AppKit.NSApplicationSupportDirectory,
            AppKit.NSUserDomainMask,
            True)[0]

        app_support = clean(app_support) / 'Carton'
    except ModuleNotFoundError:
        app_support = clean('~/.carton')

    return app_support

def clean(path, *, resolve=True):
    path = pathlib.Path(path).expanduser()
    if resolve:
        return path.resolve()
    else:
        return path.absolute()

def repository(root=None):
    if root is not None:
        path = clean(root) / 'repository'
    elif 'CARTON_PATH' in os.environ:
        path = clean(os.getenv('CARTON_PATH')) / 'repository'
    elif sys.platform == 'win32':
        path = clean(os.getenv('APPDATA')) / 'Carton'
    elif sys.platform == 'darwin':
        path = _darwin_appsupport() / 'repository'
    elif sys.platform == 'linux':
        path = clean(os.getenv('XDG_DATA_HOME', '~/.local/share')) / 'carton' / 'repository'
    else:
        path = clean('~/.carton/repository')

    if not path.exists():
        path.mkdir(parents=True)
    elif not path.is_dir():
        raise FileExistsError(FILE_EXISTS.format(path=path))

    return path

def state(root=None):
    if root is not None:
        path = clean(root) / 'state'
    elif 'CARTON_PATH' in os.environ:
        path = clean(os.getenv('CARTON_PATH')) / 'state'
    elif sys.platform == 'win32':
        path = clean(os.getenv('LOCALAPPDATA')) / 'Carton'
    elif sys.platform == 'darwin':
        path = _darwin_appsupport() / 'state'
    elif sys.platform == 'linux':
        path = clean(os.getenv('XDG_DATA_HOME', '~/.local/share')) / 'carton' / 'state'
    else:
        path = clean('~/.carton/state')

    if not path.exists():
        path.mkdir(parents=True)
    elif not path.is_dir():
        raise FileExistsError(FILE_EXISTS.format(path=path))

    return path
