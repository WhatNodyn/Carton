import collections as co
import copy
import json
from carton.core import hook, Module, proc
from carton.util import strings as s

class ConfigModule(Module):
    # TODO: Load environment from elsewhere.
    environment = {}

    def _patch(self, database, patch):
        if not isinstance(database, co.abc.MutableMapping):
            raise ValueError(s.WRONG_TYPE.format(
                expected="a mutable mapping",
                bad_type=type(database).__name__
            ))
        elif not isinstance(patch, co.Mapping):
            raise ValueError(s.WRONG_TYPE.format(
            	expected="a mapping",
            	bad_type=type(patch).__name__
            ))

        for key, value in patch.items():
            if isinstance(value, co.Mapping):
                database[key] = self._patch(database.get(key, {}), value)
            elif isinstance(value, co.Iterable) and not isinstance(value, str):
                orig = database.setdefault(key, [])
                if not isinstance(orig, co.MutableSequence):
                    database[key] = orig = [orig]
                orig.extend(value)
            else:
                database[key] = value

        return database
    
    def _reduce(self, database, environment):
        if not isinstance(database, co.abc.MutableMapping):
            return database

        condition = database.get('if', 'True')
        if not eval(condition, {'__builtins__': {}}, environment):
                return {}

        reduced = copy.deepcopy(database)
        reduced.pop('if', None)
        for patch in reduced.pop('patch', []):
            patch = self._reduce(patch, environment)
            reduced = self._patch(reduced, patch)

        return reduced

    @hook
    @hook('enable')
    def on_load(self):
        self.local = {}

        self.acquire('carton.json')
        self.locked = True

        self.config = self.repository / 'carton.json'
        try:
            with self.config.open() as f:
                self.database = json.load(f)
        except FileNotFoundError:
            self.database = {}
        except json.decoder.JSONDecodeError:
            print(s.CORRUPT_FILE.format(file=self.config))
            self.acquire('config.json.bak')
            self.config.rename(self.config.with_suffix('.json.bak'))

        self.local = self._reduce(self.database, self.environment)

    @hook
    @hook('disable')
    def on_unload(self):
        if self.locked:
            data = json.dumps(self.database, indent=2)
            with self.config.open('w') as f:
                f.write(data)

            self.locked = False
            self.release('carton.json')
            try:
                self.release('carton.json.bak')
            except ValueError:
                pass

    @proc
    def get(self, *keys, raw=False):
        result = self.database if raw else self.local
        for i, key in enumerate(keys):
            result = result.get(key, None)
            if not isinstance(result, co.Mapping) and i < len(keys) - 1:
                return None

        return copy.deepcopy(result)

    @proc
    def set(self, *keys, value, condition=None):
        if not isinstance(condition, co.Iterable) and condition is not None:
            return None
        elif isinstance(condition, str):
            condition = (condition,)

        database = self.database
        if condition:
            for c in condition:
                patches = database.setdefault('patch', [])
                patch = list(filter(lambda p: p.get('if', None) == c, patches))
                if len(patch) != 0:
                    database = patch[0]
                else:
                    database = {'if': c}
                    patches.append(database)

        for i, key in enumerate(keys[:-1]):
            database = database.setdefault(key, {})

        database[keys[-1]] = value
        self.local = self._reduce(self.database, self.environment)
