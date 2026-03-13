class Sandbox(object):

    # language level sandboxed execute method
    def execute(self, code_string):
        import sys

        # minimal blacklist at the moment - can be expanded / chagned to a whitelist approach
        keyword_blacklist = ['file', 'quit', 'eval', 'exec']
        
        for keyword in keyword_blacklist:
            if keyword in code_string:
                raise ValueError("blacklisted")

        # make built-ins read only to prevent users from messing up the expected behaviour of python itself
        main = sys.modules["__main__"].__dict__
        orig_builtins = main["__builtins__"].__dict__

        safe_builtins = ReadOnlyBuiltins(orig_builtins)
        main["__builtins__"] = safe_builtins


        # libraries to modify the underlying CPython structure and allow us to delete attributes that can't otherwise be modified
        from ctypes import pythonapi, POINTER, py_object
        from types import FunctionType

        # don't expose base classes and subclasses (could be sensitive references)
        _get_dict = pythonapi._PyObject_GetDictPtr
        _get_dict.restype = POINTER(py_object)
        _get_dict.argtypes = [py_object]
        del pythonapi, POINTER, py_object

        def dictionary_of(ob):
            dptr = _get_dict(ob)
            return dptr.contents.value
        

        #these features work however pytorch and hugging face do need to use the base and sub classes as well as the code attribute. Disabling these language level protections for now
        type_dict = dictionary_of(type)
        # del type_dict["__bases__"] #prevents accessing base classes of an object
        # del type_dict["__subclasses__"] #prevents accessing sub classes of an object

        # don't expose import function attributes
        function_dict = dictionary_of(FunctionType)
        # del function_dict["__code__"] #prevents modifying the underlying function

        # execute the final code string with these limited features
        exec(code_string)


# Read-only version of a dictionary used for the builtins. Raises a ValueError whenever a modifiction of the built-ins is attempted
class ReadOnlyBuiltins(dict):
    def __delitem__(self, key):
        raise ValueError("Built-ins are read only")
    
    def pop(self, key, default=None):
        raise ValueError("Built-ins are read only")
    
    def popitem(self):
        raise ValueError("Built-ins are read only")
    
    def setdefault(self, key, value):
        raise ValueError("Built-ins are read only")
    
    def __setitem__(self, key, value):
        raise ValueError("Built-ins are read only")
    
    def update(self, dict, **kw):
        raise ValueError("Built-ins are read only")
    
