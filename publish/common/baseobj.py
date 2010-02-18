#!/usr/local/bin/python25
"""
A recursive object-based JSON serializer/deserializer
See project.py and tests/data_objects.py for examples

Michael DeHaan <mdehaan@lulu.com>
"""

import simplejson
import exceptions

class BaseData:

    # ----------------------------------------------------------------------------

    def __init__(self, datastruct=None):
        """
        Base class of all projects.  Can optionally be constructed from a nested datastructure.
        """
        self._data = {}
        self._map = self.get_map()

        # initialize objects to stock values
        for (k, v) in self._map.iteritems():
            self._data[k] = v[0]

        # if a datastructure is supplied, set contents
        if datastruct is not None:
            self.from_datastruct(datastruct)

    # ----------------------------------------------------------------------------

    def get_map(self):
        """
        The map defines what the member variable names are, the default values, and their types.
        See any subclass for examples.
        """
        raise exceptions.NotImplementedError()

    # ----------------------------------------------------------------------------

    def from_json(self, json):
        """
        Given a json string as data, set the object state to reflect the datastructure contents.
        """
        self._data = {}
        self.from_datastruct(simplejson.loads(json))
        return self

    # ----------------------------------------------------------------------------

    def from_datastruct(self, data):
        """
        Given a nested datastructure, set the object state to reflect the datastructure contents.
        """
        for (k, v) in data.iteritems():
            if not self._map.has_key(k):
                raise exceptions.AttributeError("no such data member: %s" % k)
            self.set(k, v)
        return self

    # ----------------------------------------------------------------------------

    def __coerce_basic_type(self, key, value, typ, restrictions):
        """
        Supports type conversions in deserialization.
        """
        if typ == "string":
            return unicode(value)
        elif typ == "int":
            return int(value)
        elif typ == "list":
            assert type(value) == type([]), "%s is not a list (key: %s)" % (type(value), key) 
            return self.__coerce_list(key, value, typ, restrictions)
        elif typ == "boolean":
            return bool(value)
        elif typ == "currency":
            # we'll always loose precision but throw away any input not within the rounding range
            return round(float(value),2)
        elif typ == "float":
            return float(value)
        assert("internal error -- type not handled")

    # ----------------------------------------------------------------------------

    def __coerce_list(self, key, value, typ, restrictions):
        """
        Supports lists in deserialization.
        """
        assert type(value) == type([]), "%s is not a list" % type(value)   
        def mapper(list_value):
            if restrictions in [ "currency", "float", "int", "string", "list", "boolean" ]:
                return self.__coerce_basic_type(key,list_value,restrictions,None)
            else:
                if type(value) == type({}):
                    assert isinstance(typ, BaseData)
                    return typ().from_datastruct(list_value)
                else:
                    return list_value
        rc = map(mapper, value)
        return rc

    # ----------------------------------------------------------------------------

    def __coerce_type(self, key, value):
        """
        For validating set functions and also for deserialization, this method ensures 
        the arguments are of the right type according to the map.

        string      accepts only strings
        int         accepts ints or strings
        list        accepts lists of objects or basic types, container type is required
        choice      accepts only certain basic values
        booleans    accepts bools or attempts casting to bools 
        $className  accepts an object of a hash to initialize the class
 
        More types can be added later.
        """
        (default, typ, restrictions) = self._map[key]
        if value is None:
            return None
        if typ == "choice":
            assert value in restrictions, "Invalid choice %s for %s.  Valid choices include: %s" % (value, key, ", ".join(restrictions))
            return value
        elif typ in [ "string", "int", "currency", "float", "list", "boolean" ]:
            return self.__coerce_basic_type(key, value, typ, restrictions)
        elif typ == "list":
            return self.__coerce_list(key, value, typ, restrictions)
        else:
            # represents an object
            if type(value) == type({}):
                return typ().from_datastruct(value)
            else: 
                return value


    # ----------------------------------------------------------------------------

    def to_datastruct(self):
        """
        Return the object as serialized to a nested datastructure.
        """
        retval = {}
        for (k, v) in self._data.iteritems():
            if isinstance(v, BaseData):
                retval[k] = v.to_datastruct()
            elif type(v) == type([]):
                tmp = []
                for subitem in v:
                    if isinstance(subitem, BaseData):
                        tmp.append(subitem.to_datastruct())
                    else:
                        tmp.append(subitem)
                retval[k] = tmp 
            else:
                retval[k] = v
        return retval

    # ----------------------------------------------------------------------------

    def to_json(self):
        """
        Return the object serialized to JSON.
        """
        return simplejson.dumps(self.to_datastruct())

    # ----------------------------------------------------------------------------

    def set(self, key, value):
        """
        While __getattr__/__setattr__ leads to shiny code, it also leads to fun debugging.
        To set a field, call set (key, value)
        """
        assert self._map.has_key(key), "no such data member: %s" % key
        value = self.__coerce_type(key, value)
        self._data[key] = value

    # ----------------------------------------------------------------------------

    def get(self, key):
        """
        Retrieve the value of a field.
        """
        assert self._map.has_key(key), "no such data member: %s" % key
        return self._data[key]

    # ----------------------------------------------------------------------------

    def __str__(self):
        """
        If we print the object, just print the JSON.
        """ 
        return self.to_json()

    # ----------------------------------------------------------------------------

    def human_diff(self, other):
        """
        Print out the differences between two projects in nice, indented JSON.
        """
        data = self.diff(other)
        return simplejson.dumps(data, sort_keys=True, indent=4)

    # ----------------------------------------------------------------------------

    def diff(self, other):
        """
        Given two project instances, return the list of portions that are different
        between them as a hash.  The keys of the hash are the differing fields.
        The values are the explanations in how they differ as strings.
        """
        ds1 = self.to_flattened_datastruct()
        ds2 = other.to_flattened_datastruct()
        results = {}
        keys = ds1.keys()
        keys.extend(ds2.keys()) 
        keys = self._uniquify(keys)

        for k in keys:
            if not ds2.has_key(k) or (ds2[k] is None and ds1[k] is not None):
                results[k] = "key not in object 2"
            elif not ds1.has_key(k) or (ds1[k] is None and ds2[k] is not None):
                results[k] = "key not in object 1"
            elif type(ds1) != type(ds2):
                results[k] = "types differ: %s, %s" % (type(ds1[k]), type(ds2[k]))
            elif ds1[k] != ds2[k]:
                results[k] = "values differ: %s, %s" % (ds1[k], ds2[k])
        return results

    # ----------------------------------------------------------------------------

    def to_flattened_datastruct(self):
        """
        Returns the datastruct in a more human friendly structured format.
        """
        return self._flatten_ds(self.to_datastruct())

    # ----------------------------------------------------------------------------
    
    def _uniquify(self, lst):
        results = {}
        for x in lst:
            results[x] = 1
        results = results.keys()
        results.sort()
        return results

    # ----------------------------------------------------------------------------

    def _flatten_ds(self, ds, result=None, memo=""):
        """
        Flattens a nested hash into a more C-styled structure notation.
        Similar in purpose to Perl's Hash::Flatten
        """
        if result is None:
            result = {}
        assert type(ds) == type({})
        for (k,v) in ds.iteritems():
                if memo == "":
                    new_memo = k
                else:
                    new_memo = "%s.%s" % (memo,k)
                if type(v) == type({}):
                    self._flatten_ds(v, result=result, memo=new_memo)               
                else:
                    result[new_memo] = v 
        return result

