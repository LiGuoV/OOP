MISSING = object()


class Base:
    def __init__(self, cls, attrs):
        self.cls = cls
        self.attrs = attrs

    def write_attr(self, fieldname, value):
        meth = self.cls._read_from_class('__setattr__')
        return meth(self, fieldname, value)

    def read_attr(self, field_name):
        result = self.attrs.get(field_name, MISSING)
        if result is not MISSING:
            return result
        result = self.cls._read_from_class(field_name)
        # if callable(result):
        if hasattr(result,'__get__'):
            return _make_boundmathod(result, self)
        if result is not MISSING:
            return result
        meth = self.cls._read_from_class('__getattr__')
        if meth is not MISSING:
            return meth(self, field_name)
        raise AttributeError(field_name)

    def isinstance(self, cls):
        return self.cls.issubclass(cls)

    def callmethod(self, methname, *args):
        # meth = self.cls._read_from_class(methname)
        meth = self.read_attr(methname)
        return meth(*args)


class Class(Base):
    def __init__(self, name, base_class, fields, metaclass):
        Base.__init__(self, cls=metaclass, attrs=fields)
        self.name = name
        self.base_class = base_class

    def method_resolution_order(self):
        if self.base_class is None:
            return [self]
        return [self] + self.base_class.method_resolution_order()

    def issubclass(self, cls):
        return cls in self.method_resolution_order()

    def _read_from_class(self, methname):
        for cls in self.method_resolution_order():
            if methname in cls.attrs:
                return cls.attrs[methname]
        return MISSING



class Instance(Base):
    def __init__(self, cls):
        Base.__init__(self, cls, {})
        # 优化
        self.map = EMPTY_MAP
        self.storage = []

    def _read_dict(self,fieldname):
        idx = self.map.get_index(fieldname)
        if idx == -1:
            return MISSING
        return self.storage[idx]

    def _write_dict(self,fieldname,value):
        idx = self.map.get_index(fieldname)
        if idx != -1:
            self.storage[idx] = value
        else:
            self.map = self.map.next_map(fieldname)
            self.storage.append(value)


def OBJECT__setattr__(self, fieldname, value):
    # self.attrs[fieldname] = value
    self._write_dict(fieldname, value)


OBJECT = Class(name='object', base_class=None, fields={'__setattr__': OBJECT__setattr__}, metaclass=None)
TYPE = Class(name='type', base_class=OBJECT, fields={}, metaclass=None)
OBJECT.cls = TYPE
TYPE.cls = TYPE


def _make_boundmathod(meth, self):
    # def bound(*args):
    #     return meth(self, *args)
    # return bound
    """

    :param meth: 'fahrenheit'
    :param self: 'OBJECT'
    :return:
    """
    return meth.__get__(self,None)


"""
优化
"""
class Map:
    def __init__(self,attrs):
        self.attrs = attrs
        self.next_maps = {}

    def get_index(self,fieldname):
        return self.attrs.get(fieldname,-1)

    def next_map(self, fieldname):
        assert fieldname not in self.attrs
        if fieldname in self.next_maps:
            return self.next_maps[fieldname]
        attrs = self.attrs.copy()
        attrs[fieldname] = len(attrs)
        result = self.next_maps[fieldname] = Map(attrs)
        return result

EMPTY_MAP = Map({})