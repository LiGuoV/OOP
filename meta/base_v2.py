
MISSING = object()
class Base:
    def __init__(self,cls,attrs:dict):
        self.cls = cls
        self.attrs = attrs

    def write_attr(self, field_name, value):
        # self.attrs[field_name] = value
        meth = self.cls._read_from_class('__setattr__')
        meth(self,field_name,value)

    def read_attr(self, field_name):
        result = self.attrs.get(field_name, MISSING)
        if result is not MISSING:
            return result
        result = self.cls._read_from_class(field_name)
        if result is not MISSING and callable(result):
            return _make_boundmathod(result,self)

        meth = self.cls._read_from_class('__getattr__')
        if meth is not MISSING:
            return meth(self,field_name)

        raise AttributeError(field_name)

    def isinstance(self, cls):
        return self.cls.issubclass(cls)

    def callmethod(self,methname,*args):
        # meth = self.cls._read_from_class(methname)
        meth = self.read_attr(methname)
        return meth(*args)

class Class(Base):
    def __init__(self,name,base_class,fields,metaclass):
        Base.__init__(self,cls=metaclass,attrs=fields)
        self.name = name
        self.base_class = base_class

    def method_resolution_order(self):
        if self.base_class is None:
            return [self]
        return [self] + self.base_class.method_resolution_order()

    def issubclass(self,cls):
        return cls in self.method_resolution_order()

    def _read_from_class(self,methname):
        for cls in self.method_resolution_order():
            if methname in cls.attrs:
                return cls.attrs[methname]
        return MISSING


class Instance(Base):
    def __init__(self,base):
        Base.__init__(self,cls=base,attrs={})



OBJECT = Class(name='object',base_class=None,fields={},metaclass=None)
TYPE = Class(name='type',base_class=OBJECT, fields={},metaclass=None)
OBJECT.cls = TYPE
TYPE.cls = TYPE


def _make_boundmathod(meth,self):
    def bound(*args):
        return meth(self,*args)
    return bound
