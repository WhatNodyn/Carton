import collections
import functools
import pkgutil
import importlib
import types
from carton.util import path, strings as s

class Module:
    def __init__(self, core):
        self.carton = core

    def get_hook(self, _name):
        for name in dir(self):
            value = getattr(self, name)
            if _name in getattr(value, '_hooks', ()):
                return value

    def get_proc(self, _name):
        for name in dir(self):
            value = getattr(self, name)
            if _name in getattr(value, '_procs', ()):
                return value

    def acquire(self, resource):
        return self.carton.acquire(self, resource)

    def release(self, resource):
        return self.carton.release(self, resource)

    def __getattr__(self, key):
        return getattr(self.carton, key, None)

def hook(value, name=None):
    if isinstance(value, str):
        return functools.partial(hook, name=value)
    elif not callable(value):
        raise ValueError(s.DECORATED_NOT_CALLABLE)

    if name is None:
        name = value.__name__
    if name.startswith('on_'):
        name = name[3:]

    hooks = getattr(value, '_hooks', ())
    if name not in hooks:
        value._hooks = hooks + (name,)

    return value

def proc(value, name=None):
    if isinstance(value, str):
        return functools.partial(proc, name=value)
    elif not callable(value):
        raise ValueError(s.DECORATED_NOT_CALLABLE)

    if name is None:
        name = value.__name__
    if name.startswith('on_'):
        name = name[3:]

    procs = getattr(value, '_procs', ())
    if name not in procs:
        value._procs = procs + (name,)

    return value

class Core:
    def __init__(self, root=None):
        self.repository = path.repository(root)
        self.state = path.state(root)

        lock = self.state / 'carton.lock'
        if lock.exists():
            raise FileExistsError(s.FILE_EXISTS.format(path=lock))

        lock.touch()
        self._acquired = True

        self._locks = {}
        self._modules = collections.OrderedDict()

        # Load core modules
        modules = path.clean(__file__).parent / 'modules'
        for module in map(lambda m: m.name, pkgutil.iter_modules((modules,))):
            self.load_from('carton.modules.{name}'.format(name=module))

        # Load system modules
        for module in map(lambda m: m.name, pkgutil.iter_modules()):
            if module.startswith('carton_'):
                self.load_from(module)

        # TODO: Load repository modules

    # NOTE: This returns a tuple of (name, instance) for a given module
    def _get_module(self, module):
        is_instance = isinstance(module, Module)
        is_subclass = isinstance(module, type) and issubclass(module, Module)

        if not (is_instance or is_subclass or isinstance(module, str)):
            type_name = type(module).__name__
            raise ValueError(s.MODULE_EXPECTED.format(bad_type=type_name))

        if isinstance(module, str):
            loaded = self._modules.get(module, None)
            if None is loaded:
                loaded = self._modules.get('#' + module, None)
                if None is loaded:
                    raise ValueError(s.MODULE_OFFLINE.format(module=module))

            return (module, loaded)

        else:
            for name, loaded in self._modules.items():
                if is_instance and module is loaded:
                    return (name.lstrip('#'), loaded)
                elif is_subclass and isinstance(loaded, module):
                    return (name.lstrip('#'), loaded)

            name = getattr(module, '__name__', module.__class__.__name__)
            raise ValueError(s.MODULE_OFFLINE.format(module=name))


    # Resource loading and unloading
    def load_from(self, module):
        if isinstance(module, str):
            name = module
            module = importlib.import_module(module)
        elif not isinstance(module, types.ModuleType):
            type_name = type(m).__name__
            message = s.PYTHON_MODULE_EXPECTED.format(bad_type=type_name)
            raise TypeError(message)
        else:
            name = module.__name__

        if name.startswith('carton.modules.'):
            name = name[15:]
        elif name.startswith('carton') and name[6] in '._':
            name = name[7:]

        setup = getattr(module, 'setup', None)
        if callable(setup):
            setup(self, name)
        else:
            for identifier in dir(module):
                value = getattr(module, identifier, None)
                if value is Module:
                    continue
                try:
                    self.load(value, name)
                except TypeError as e:
                    type_name = type(value).__name__
                    message = s.MODULE_EXPECTED.format(bad_type=type_name)
                    if e.args[0] != message:
                        raise e

    def load(self, module, parent=None):
        is_instance = isinstance(module, Module)
        is_subclass = isinstance(module, type) and issubclass(module, Module)

        if not (is_instance or is_subclass):
            type_name = type(module).__name__
            raise TypeError(s.MODULE_EXPECTED.format(bad_type=type_name))

        name = getattr(module, '__name__', module.__class__.__name__)
        if parent is not None:
            name = '{parent}.{name}'.format(parent=parent, name=name)

        if name in self._modules or ('#' + name) in self._modules:
            raise ValueError(s.MODULE_LOADED.format(module=name))

        self._modules[name] = module if is_instance else module(self)
        self.hook('load', _restrict=(name,))

    def loaded(self, module=None):
        if module is None:
            return list(map(lambda s: s.lstrip('#'), self._modules))
        else:
            try:
                name, loaded = self._get_module(module)
                return True
            except ValueError as e:
                name = getattr(module, '__name__', module.__class__.__name__)
                if e.args[0] != s.MODULE_OFFLINE.format(module=name):
                    raise e

            return False

    def unload(self, module):
        name, loaded = self._get_module(module)

        # We can just check the presence of name, because its absence means
        # that #name is in the list, which means the module is disabled.
        if name not in self._modules:
            self.enable(name)

        self.hook('unload', _restrict=(name,))

        if name in self._modules:
            del self._modules[name]
        elif ('#' + name) in self._modules:
            del self._modules['#' + name]


    # Enabling and disabling of modules, useful for longer-lived processes
    def enable(self, module):
        name, loaded = self._get_module(module)
        # We can just check the presence of name, because its absence means
        # that #name is in the list, which means the module is disabled.
        if ('#' + name) in self._modules:
            self._modules[name] = loaded
            del self._modules['#' + name]
            self.hook('enable', _restrict=(name,))

    def enabled(self, module=None):
        if module is None:
            return list(filter(lambda s: not s.startswith('#'), self._modules))
        else:
            # We can just check the presence of name, because its absence means
            # that #name is in the list, which means the module is disabled.
            name, loaded = self._get_module(module)
            return name in self._modules

    def disable(self, module):
        name, loaded = self._get_module(module)
        # We can just check the presence of name, because its absence means
        # that #name is in the list, which means the module is disabled.
        if name in self._modules:
            self.hook('disable', _restrict=(name,))
            self._modules['#' + name] = loaded
            del self._modules[name]


    # Resource ownership, speaking in terms of files in repository
    # When a resource is acquired, it is in both the repository and the state
    def acquire(self, requester, resource):
        name, loaded = self._get_module(requester)

        owner = self._locks.setdefault(resource, name)
        if owner != name:
            message = s.RESOURCE_LOCKED.format(resource=resource, owner=owner)
            raise ValueError(message)

    def release(self, requester, resource):
        name, loaded = self._get_module(requester)

        owner = self._locks.get(resource, None)
        if None is owner:
            raise ValueError(s.RESOURCE_FREE.format(resource=resource))
        elif owner != name:
            message = s.RESOURCE_LOCKED.format(resource=resource, owner=owner)
            raise ValueError(message)
        else:
            del self._locks[resource]


    # Module queries
    def hook(self, _name, *args, _filter='latest', _restrict=None, **kwargs):
        results = collections.OrderedDict()
        modules = filter(lambda s: not s.startswith('#'), self._modules)
        if _restrict is not None:
            modules = filter(lambda s: s in _restrict, modules)

        for name in modules:
            f = self._modules[name].get_hook(_name)
            if callable(f):
                results[name] = f(*args, **kwargs)
            else:
                results[name] = f

        if callable(_filter):
            return _filter(results)
        elif _filter == 'all':
            return results
        else:
            index = 0 if _filter in ('earliest', 'first') else -1
            results = tuple(filter(lambda v: v is not None, results.values()))
            return results[index] if len(results) > 0 else None

    def proc(self, _name, *args, **kwargs):
        modules = tuple(filter(lambda s: not s.startswith('#'), self._modules))
        for name in reversed(modules):
            f = self._modules[name].get_proc(_name)
            if callable(f):
                return f(*args, **kwargs)

        raise NameError(s.COMMAND_NOT_FOUND.format(command=_name))


    # Exiting Carton
    def shutdown(self):
        for name, module in self._modules.copy().items():
            self.unload(name.lstrip('#'))

        lock = self.state / 'carton.lock'
        if self._acquired and lock.exists():
            lock.unlink()

    def __del__(self):
        if getattr(self, '_acquired', False):
            self.shutdown()
