
MISSING = object()

class Base:
    def __init__(self,cls,fields:dict):
        self.cls = cls
        self._fields = fields

    def _read_dict(self, fieldname):
        """ read an field 'fieldname' out of the object's dict """
        return self._fields.get(fieldname, MISSING)

    def _write_dict(self,fieldname,value):
        self._fields[fieldname] = value

    def read_attr(self,fieldname):
        if (result := self._read_dict(fieldname)) is not MISSING:
            return result
        result = self.cls._read_from_class(fieldname)
        if _is_bindable(result):
            return _make_bundmethod(result,self)
        if result is not MISSING:
            return result
        meth = self.cls._read_from_class('__getattr__')
        if meth is not MISSING:
            return meth(self,fieldname)
        raise AttributeError(fieldname)

    def write_attr(self,fieldname,value):
        # self._write_dict(fieldname,value)
        meth = self.cls._read_from_class('__setattr__')
        return meth(self,fieldname,value)

    def isinstance(self,cls):
        return self.cls.issubclass(cls)

    def callmethod(self,methname,*args):
        meth = self.cls._read_from_class(methname)
        return meth(self,*args)


class Instance(Base):
    # 类也是对象 元类的实例
    def __init__(self,cls):
        assert isinstance(cls,Class)
        Base.__init__(self,cls,None)
        self.map = EMPTY_MAP
        self.storage = []

    def _read_dict(self, fieldname):
        index = self.map.get_index(fieldname)
        if index == -1:
            return MISSING
        return self.storage[index]

    def _write_dict(self,fieldname,value):
        index = self.map.get_index(fieldname)
        if index != -1:
            self.storage[index] = value
        else:
            new_map = self.map.next_map(fieldname)
            self.storage.append(value)
            self.map = new_map

class Class(Base):
    def __init__(self,name,base_class,fields,metaclass):
        Base.__init__(self,metaclass,fields)
        self.name = name
        self.base_class = base_class

    def method_resolution_order(self):
        """ compute the method resolution order of the class """
        if self.base_class is None:
            return [self]
        else:
            return [self] + self.base_class.method_resolution_order()

    def issubclass(self, cls):
        """ is self a subclass of cls? """
        return cls in self.method_resolution_order()

    def _read_from_class(self,methname):
        for cls in self.method_resolution_order():
            if methname in cls._fields:
                return cls._fields[methname]
        return MISSING


def OBJECT__setattr__(self,fieldname,value):
    self._write_dict(fieldname,value)

# object 是继承层次结构的最终基类 所以type是object的子类
OBJECT = Class(name='object',base_class=None,fields={'__setattr__':OBJECT__setattr__},metaclass=None)
# type 是所有类型的类型 所以是objcet的类型
# type 是type和object的实例
# type 子类化创建新的元类
TYPE = Class(name='type',base_class=OBJECT,fields={},metaclass=None)
TYPE.cls = TYPE
OBJECT.cls = TYPE

def _is_bindable(meth):
    # return callable(meth)
    return hasattr(meth,'__get__')

def _make_bundmethod(meth,self):
    # def bound(*args):
    #     return meth(self,*args)
    # return bound
    return meth.__get__(self,None)

class Map:
    def __init__(self,attrs:dict):
        self.attrs = attrs
        self.next_maps = {}

    def get_index(self,fieldname):
        # 在对象的存储中查找属性名称的索引
        return self.attrs.get(fieldname,-1)

    def next_map(self,fieldname):
        # 新属性添加到对象时使用 具有相同布局的对象也会使用相同Map对象
        assert fieldname not in self.attrs
        if fieldname in self.next_maps:
            return self.next_maps[fieldname]
        attrs = self.attrs.copy()
        attrs[fieldname] = len(attrs)
        result = self.next_maps[fieldname] = Map(attrs)
        return result

EMPTY_MAP = Map({})