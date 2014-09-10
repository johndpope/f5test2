'''
Created on Jun 11, 2011

@author: jono
'''
import types


def merge(dst, src, skip_prefix='$'):
    if isinstance(dst, dict) and isinstance(src, dict):
        for k, v in src.iteritems():
            if skip_prefix and isinstance(k, basestring) and k.startswith(skip_prefix):
                continue
            if k not in dst:
                dst[k] = v
            else:
                dst[k] = merge(dst[k], v, skip_prefix)
    else:
        return src
    return dst


def inverse(src, keys=None):
    """
    Reverts a dict of key:value into value:key.

    >>> src = dict(key1='val1', key2=['val2', 'val3'], key3='val3')
    >>> trans = dict(val3='gaga', val2='gaga')
    >>> invert_dict(src)
    {'val3': set(['key3', 'key2']), 'val2': set(['key2']), 'val1': set(['key1'])}
    >>> invert_dict(src, trans)
    {'val1': set(['key1']), 'gaga': set(['key3', 'key2'])}

    @param src: Source dict
    @type src: dict
    @param keys: Key transform dict
    @type keys: dict
    """
    outdict = {}
    if keys is None:
        keys = {}

    for k, lst in src.items():
        if type(lst) is types.StringType:
            lst = lst.split()
        for entry in lst:
            entry = keys.get(entry, entry)
            outdict.setdefault(entry, set())
            outdict[entry].add(k)

    return outdict
