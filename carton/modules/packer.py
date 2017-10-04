import collections as co
import json
import os
from carton.core import hook, Module, proc
from carton.util import path, strings as s

class PackerModule(Module):
    @hook
    @hook('enable')
    def on_load(self):
        self.acquire('links.json')
        self.locked = True

        self.links = self.state / 'links.json'
        try:
            with self.links.open() as f:
                self.database = json.load(f)
        except FileNotFoundError:
            self.database = {}
        except json.decoder.JSONDecodeError:
            print(s.CORRUPT_FILE.format(file=self.links))
            self.acquire('links.json.bak')
            self.links.rename(self.links.with_suffix('.json.bak'))
            self.database = {}

    @hook
    @hook('disable')
    def on_unload(self):
        if getattr(self, 'locked', False):
            data = json.dumps(self.database, indent=2)
            with self.links.open('w') as f:
                f.write(data)

            self.locked = False
            self.release('links.json')
            try:
                self.release('links.json.bak')
            except ValueError:
                pass

    @proc
    def unpack(self):
        files = self.proc('get', 'install') or {}
        if not isinstance(files, co.Mapping):
            raise TypeError(s.INVALID_CONFIGURATION.format(element='install'))

        for file, reference in files.items():
            self.proc('can_link', reference, file)

        for file, reference in files.items():
            self.proc('link', reference, file)
            self.database[file] = reference

        # We cleanup dead shortcuts and invalid ones
        for file in self.database.keys():
            if file not in files:
                self.proc('unlink', file)

    @proc
    def can_link(self, reference, file):
        file = path.clean(file, resolve=False)
        origin = self.repository / 'refs' / reference
        source = file.resolve()
        if not origin.exists():
            raise FileNotFoundError(s.FILE_NOT_FOUND.format(path=origin))
        elif file.exists() and (self.repository / 'refs') not in source.parents:
            raise FileExistsError(s.FILE_EXISTS.format(path=file))
        elif file.parent.exists() and not file.parent.is_dir():
            raise NotADirectoryError(s.NOT_A_DIRECTORY.format(path=file.parent))
        elif file.parent.exists() and not os.access(file.parent, os.W_OK):
            raise PermissionError(s.PERMISSION_ERROR.format(path=file.parent))

    @proc
    def link(self, reference, file):
        file = path.clean(file, resolve=False)
        origin = self.repository / 'refs' / reference

        if not file.parent.exists():
            file.parent.mkdir(parents=True)
        if file.exists():
            file.unlink()
        file.symlink_to(origin, target_is_directory=origin.is_dir())

    @proc
    def unlink(self, file):
        file = path.clean(file, resolve=False)
        source = file.resolve()
        if not file.exists():
            raise FileNotFoundError(s.FILE_NOT_FOUND.format(path=file))
        elif not os.access(file.parent, os.W_OK):
            raise PermissionError(s.PERMISSION_ERROR.format(path=file.parent))
        elif (self.repository / 'refs') not in source.parents:
            raise FileExistsError(s.FILE_NOT_TRACKED.format(path=file))
        else:
            file.unlink()
