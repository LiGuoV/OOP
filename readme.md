实现 [简单对象模型](https://aosabook.org/en/500L/a-simple-object-model.html)

> 一切都是对象 两种对象:`类`和 类的`实例(不再是类)`
```python
class Class:pass
class Instance:pass
```

> - 将属性读取和写入`对象(类和实例)`的能力
```python
class BASE:
  # 存储对象的 cls attr
  ...

class Class(BASE):
    # 类是其元类的实例
    def __init__(self, name, base_class, fields, metaclass):
          Base.__init__(self, metaclass, fields)
          self.name = name
          self.base_class = base_class
        
class Instance(BASE):
    def __init__(self, cls):
        assert isinstance(cls, Class)
        Base.__init__(self, cls, {})
```

> - 调用对象方法的能力
> - 一个类作为另一个类的子类的能力

```python
# test1
A = Class(name="A", base_class=OBJECT, fields={"a": 1}, metaclass=TYPE)
assert A.read_attr("a") == 1
A.write_attr("a", 5)
assert A.read_attr("a") == 5
    
obj = Instance(A)
obj.write_attr("a", 1)
assert obj.read_attr("a") == 1
```

> 类的两个特殊实例
- `OBJECT` 是继承层次结构的最终基类 因此
  - OBJECT没有基类
  - TYPE是 OBJECT的 子类
- (默认)所有的类是`TYPE`的实例 
  - 注意：TYPE是 OBJECT 和自身的实例
  - 可以 子类化`TYPE`创建新的元类
  
```python
OBJECT = Class(name='object',base_class=None,fields={},metaclass=None)
TYPE = Class(name='type',base_class=OBJECT, fields={},metaclass=None)
OBJECT.cls = TYPE
TYPE.cls = TYPE
```

# 测试:对象具有类
```python
A = Class(name="A", base_class=OBJECT, fields={}, metaclass=TYPE)
B = Class(name="B", base_class=A, fields={}, metaclass=TYPE)
b = Instance(B)
assert b.isinstance(B)
assert b.isinstance(A)
assert b.isinstance(OBJECT)
assert not b.isinstance(TYPE)
```
检查obj是不是cls的实例 通过遍历超类链查找
```python
class BASE:
  def isinstance(self, cls):
      return self.cls.issubclass(cls)

class Class(Base):
    def method_resolution_order(self):
        if self.base_class is None:
            return [self]
        return [self] + self.base_class.method_resolution_order()

    def issubclass(self,cls):
        return cls in self.method_resolution_order()
```

# 调用对象方法的能力
```python
def test_callmethod_subclassing_and_arguments():

    def g_A(self, arg):
        return self.read_attr("x") + arg
    
    A = Class(name="A", base_class=OBJECT, fields={"g": g_A}, metaclass=TYPE)
    obj = Instance(A)
    obj.write_attr("x", 1)
    assert obj.callmethod("g", 4) == 5

    def g_B(self, arg):
        return self.read_attr("x") + arg * 2
    
    B = Class(name="B", base_class=A, fields={"g": g_B}, metaclass=TYPE)
    obj = Instance(B)
    obj.write_attr("x", 4)
    assert obj.callmethod("g", 4) == 12
```
对象的方法来自类
```python
class BASE:
    def callmethod(self, methname, *args):
        """ call method 'methname' with arguments 'args' on object """
        meth = self.cls._read_from_class(methname)
        return meth(self, *args)

class Class:
    ...
    def _read_from_class(self, methname):
        for cls in self.method_resolution_order():
            if methname in cls._fields:
                return cls._fields[methname]
        return MISSING

```
# 基于属性的模型
基于方法的模型将方法调用作为程序执行的`原语(不可分割)`  
`result = obj.f(arg1, arg2)`

基于属性的模型将方法调用分为两步 查找到属性 再调用
```python
# 查找到的结果是绑定方法 一个封装对象以及类中找到的函数的对象
method = obj.f
# 调用该绑定方法
result = method(arg1, arg2)
```


这是Smalltalk、Ruby 和 JavaScript 与另一方面的 Python 和 Lua 之间的核心区别之一

```python
def test_bound_method():
    def f_A(self, a):
        return self.read_attr("x") + a + 1
    A = Class(name="A", base_class=OBJECT, fields={"f": f_A}, metaclass=TYPE)
    obj = Instance(A)
    obj.write_attr("x", 2)
    m = obj.read_attr("f")
    assert m(4) == 7

    B = Class(name="B", base_class=A, fields={}, metaclass=TYPE)
    obj = Instance(B)
    obj.write_attr("x", 1)
    m = obj.read_attr("f")
    assert m(10) == 12
```
实现此行为需要更改`BASE.read_attr`的实现  
如果字典中没有找到该属性 从类中找 找到且是可调用的
转换为绑定方法
```python
def _make_boundmathod(meth,self):
    def bound(*args):
        return meth(self,*args)
    return bound

class BASE:
    ...
    def read_attr(self, field_name):
        result = self.attrs.get(field_name, MISSING)
        if result is not MISSING:
            return result
        result = self.cls._read_from_class(field_name)
        if result is not MISSING and callable(result):
            return _make_boundmathod(result,self)
        if result is not MISSING:
            return result
        raise AttributeError(field_name)

    def callmethod(self,methname,*args):
        # meth = self.cls._read_from_class(methname)
        # meth被包装过了
        meth = self.read_attr(methname)
        # return meth(self,*args)
        return meth(*args)
```

# 元对象协议
使用`特殊方法`来覆盖原始操作并为它们提供自定义行为。
因此，它们是钩子，告诉对象模型机器如何做某些事情
添加三个这样的元钩子，用于微调读取和写入属性时究竟发生了什么。
- `__getattr__` 通过正常方式查不到属性时，对象模型将调用该方法；即，既不在实例上也不在类上
- `__setattr__`

```python
def test_getattr():
    def __getattr__(self, name):
        if name == "fahrenheit":
            return self.read_attr("celsius") * 9. / 5. + 32
        raise AttributeError(name)
    def __setattr__(self, name, value):
        if name == "fahrenheit":
            self.write_attr("celsius", (value - 32) * 5. / 9.)
        else:
            # call the base implementation
            OBJECT.read_attr("__setattr__")(self, name, value)

    A = Class(name="A", base_class=OBJECT,
              fields={"__getattr__": __getattr__, "__setattr__": __setattr__},
              metaclass=TYPE)
    obj = Instance(A)
    obj.write_attr("celsius", 30)
    assert obj.read_attr("fahrenheit") == 86 # test __getattr__
    obj.write_attr("celsius", 40)
    assert obj.read_attr("fahrenheit") == 104
    obj.write_attr("fahrenheit", 86) # test __setattr__
    assert obj.read_attr("celsius") == 30
    assert obj.read_attr("fahrenheit") == 86
```
需要更改`Base.read_attr`和`Base.write_attr`
```python
class BASE:
    
    def read_attr(self, fieldname):
        """ read field 'fieldname' out of the object """
        result = self._read_dict(fieldname)
        if result is not MISSING:
            return result
        result = self.cls._read_from_class(fieldname)
        if _is_bindable(result):
            return _make_boundmethod(result, self)
        if result is not MISSING:
            return result
        meth = self.cls._read_from_class("__getattr__")
        if meth is not MISSING:
            return meth(self, fieldname)
        raise AttributeError(fieldname)

    def write_attr(self, fieldname, value):
        """ write field 'fieldname' into the object """
        meth = self.cls._read_from_class("__setattr__")
        return meth(self, fieldname, value)
# 属性的写入完全推迟到__setattr__方法。
# 为了使这个工作，OBJECT需要有一个__setattr__调用默认行为的方法

def OBJECT__setattr__(self, fieldname, value):
    self._write_dict(fieldname, value)
OBJECT = Class("object", None, {"__setattr__": OBJECT__setattr__}, None)
```
