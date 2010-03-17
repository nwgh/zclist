#!/usr/bin/env python
#
# Copyright (c) 2006 Nicholas W. Hurley <hurley@todesschaf.org>
#
# $Id: zclist.py 5 2006-08-24 03:23:06Z hurley $

"""Zero-copy list module

Implements a list that returns slices that are not made by copying the
elements of the list (ever, even if the elements are, say, ints)
"""

__author__ = 'Nicholas W. Hurley <hurley@todesschaf.org>'
__copyright__ = 'Copyright (c) 2006 Nicholas W. Hurley'
__license__ = 'BSD'
__url__ = 'https://svn.todesschaf.org/zclist/'
__version__ = '0.1'

import unittest

class ZeroCopySlice(object):
    """Implement a slice of a list that does NOT make a copy of the elements
    being sliced out of the list. This is useful when you want to pass a
    slice of a list to a function that may modify the slice, and you want
    the parent list of the slice to be modified if the slice is.
    """
    def __readjust_bounds(self):
        """Readjust self.__low and self.__high in case the list has changed
        """
        if self.__low >= len(self.__list):
            # Eep! the whole range is outside what exists. Empty the range
            self.__low = self.__high = 0
        else:
            # Just make sure the high point isn't outside what exists
            self.__high = min(self.__high, len(self.__list))

    def __verify_bounds(self, low, high):
        """Make sure low and high are within the range of the slice
        """
        if not (self.__low <= low < self.__high):
            # Low MUST be within the range
            raise IndexError, 'list index out of range'
        if not (self.__low <= high <= self.__high):
            # High can be one more than the highest index
            raise IndexError, 'list index out of range'

    def __verify_index(self, idx):
        """Make sure idx is within the range of the slice
        """
        if not (self.__low <= idx < self.__high):
            raise IndexError, 'list index out of range'
    
    def __init__(self, l, i, j):
        """Create a zero-copy 'slice' of list l, starting at location i
        and going up to (but not including) location j
        """
        if not isinstance(l, list):
            raise TypeError, 'l must be a list'
        if not isinstance(i, (int, long)) or not isinstance(j, (int, long)):
            raise TypeError, 'list index must be an int or long'
        
        self.__list = l
        
        if i < 0:
            # Normalize to a non-negative number
            idx = len(self.__list) + i
        else:
            idx = i
        if idx >= len(self.__list) and idx != 0:
            # If idx is 0, we don't care if the list is empty, otherwise
            # throw an error
            raise IndexError, 'list index out of range'
        self.__low = idx
        
        if j < 0:
            # Normalize to a non-negative number
            idx = len(self.__list) + j
        else:
            idx = j
        if idx > len(self.__list):
            # High idx can be one more than the last index in the list,
            # just like in a regular list slice
            raise IndexError, 'list index out of range'
        self.__high = idx

    def __repr__(self):
        """s.__repr__() <==> repr(s)
        """
        self.__readjust_bounds()
        if self.__low >= self.__high:
            # Empty list
            return '[]'
        s = '[' + repr(self.__list[self.__low])
        for i in range(self.__low + 1, self.__high):
            s += ', %s' % repr(self.__list[i])
        s += ']'
        return s

    def __str__(self):
        """s.__str__() <==> str(s)
        """
        # repr == str
        # don't bother readjusting bounds, since repr() does it
        return repr(self)

    def __contains__(self, x):
        """s.__contains__(x) <==> x in s
        """
        self.__readjust_bounds()
        for i in range(self.__low, self.__high):
            if self.__list[i] == x:
                return True
        return False

    def __getitem__(self, i):
        """s.__getitem__(i) <==> s[i]
        """
        self.__readjust_bounds()
        if i < 0:
            # Normalize to a non-negative number
            idx = self.__high + i
        else:
            idx = self.__low + i
            
        self.__verify_index(idx)

        return self.__list[idx]

    def __getslice__(self, i, j):
        """s.__getslice__(i, j) <==> s[i:j] (NOTE: this creates another
        zero-copy slice)
        """
        self.__readjust_bounds()
        
        if i < 0:
            # Normalize to a non-negative number
            low = self.__high + i
        else:
            low = self.__low + i

        if j < 0:
            # Normalize to a non-negative number
            high = self.__high + j
        else:
            high = self.__low + j
            
        self.__verify_bounds(low, high)
        
        return ZeroCopySlice(self.__list, low, high)

    def __len__(self):
        """s.__len__() <==> len(s)
        """
        self.__readjust_bounds()
        return self.__high - self.__low

    def __setitem__(self, i, x):
        """s.__setitem__(i, x) <==> s[i]=x
        """
        self.__readjust_bounds()
        
        if i < 0:
            # Normalize to a non-negative number
            idx = self.__high + i
        else:
            idx = self.__low + i

        self.__verify_index(idx)

        self.__list[idx] = x

    def count(self, x):
        """s.count(x) -> integer -- return number of occurrences of x
        """
        self.__readjust_bounds()
        count = 0

        # This doesn't use list slicing because, to stay true to the name,
        # ZeroCopySlice NEVER copies anything within the parent list
        for i in range(self.__low, self.__high):
            if self.__list[i] == x:
                count += 1
                
        return count

    def index(self, x, start=None, stop=None):
        """s.index(x, [start, [stop]]) -> integer -- return first index of x
        """
        self.__readjust_bounds()
        
        if start is None:
            # Start from the first position in the slice
            begin = self.__low
        elif start < 0:
            # Normalize to a non-negative number
            begin = self.__high + start
        else:
            begin = self.__low + start

        if stop is None:
            # End at the end of the slice
            end = self.__high
        elif stop < 0:
            # Normalize to a non-negative number
            end = self.__high + stop
        else:
            end = self.__low + stop

        self.__verify_bounds(begin, end)

        for i in range(begin, end):
            if self.__list[i] == x:
                return i - begin

        raise ValueError, '%s not in list' % x

class ZeroCopyList(list):
    """Like a list, but all slices returned are ZeroCopySlices
    """
    def __init__(self, l=None):
        """l = list to initialize this list from. Does NOT turn l into
        a ZeroCopyList.
        """
        if l is None:
            # Ensure we're trying to init the list from an iterable,
            # and avoid having a mutable default argument
            lst = []
        elif not isinstance(l, (list, tuple)):
            raise TypeError, 'list must be a list or tuple'
        else:
            lst = l
        return super(ZeroCopyList, self).__init__(lst)
    
    def __getslice__(self, i, j):
        """l.__getslice__(i, j) <==> l[i:j]
        """
        # Override the builtin list's __getslice__ to return a ZeroCopySlice
        return ZeroCopySlice(self, i, j)

# def make_zerocopy(l):
#     """Turn l into a ZeroCopyList
#     """
#     l = ZeroCopyList(l)

# class TestGlobal_make_zerocopy(unittest.TestCase):
#     def runTest(self):
#         l = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
#         make_zerocopy(l)
#         assert isinstance(l, ZeroCopyList), 'make_zerocopy(l) != ZCL'
#         m = []
#         make_zerocopy(m)
#         assert isinstance(m, ZeroCopyList), 'make_zerocopy(m) != ZCL'
#         try:
#             n = 0
#             make_zerocopy(n)
#             assert False, 'make_zerocopy(n) did not fail'
#         except:
#             pass

class TestZCL__init__(unittest.TestCase):
    def runTest(self):
        l = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
        t = (0, 1, 2, 3, 4, 5, 6, 7, 8, 9)
        e = []
        f = ()
        z1 = ZeroCopyList(l)
        z2 = ZeroCopyList(t)
        z3 = ZeroCopyList(e)
        z4 = ZeroCopyList(f)
        assert isinstance(z1, ZeroCopyList), 'ZCL(l) != ZCL'
        assert len(z1) == 10, 'len(ZCL(l)) != 10'
        assert isinstance(z2, ZeroCopyList), 'ZCL(t) != ZCL'
        assert len(z2) == 10, 'len(ZCL(t)) != 10'
        assert isinstance(z3, ZeroCopyList), 'ZCL(e) != ZCL'
        assert len(z3) == 0, 'len(ZCL(e)) != 0'
        assert isinstance(z4, ZeroCopyList), 'ZCL(f) != ZCL'
        assert len(z4) == 0, 'len(ZCL(f)) != 0'
        try:
            z5 = ZeroCopyList(0)
            assert False, 'ZCL(0) did not fail'
        except:
            pass

class TestZCL__getslice__(unittest.TestCase):
    def runTest(self):
        l = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
        z = ZeroCopyList(l)
        s = z[4:7]
        assert isinstance(s, ZeroCopySlice), 'ZCL[4:7] != ZCS'

class TestZCS__getslice__(unittest.TestCase):
    def runTest(self):
        l = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
        s1 = ZeroCopySlice(l, 1, 9)
        s2 = s1[2:6]
        assert isinstance(s2, ZeroCopySlice), 'ZCS[2:6] != ZCS'
        try:
            s3 = s1[2:10]
            assert False, 'ZCS[2:10] did not fail'
        except:
            pass

class TestZCS__contains__(unittest.TestCase):
    def runTest(self):
        l = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
        s = ZeroCopySlice(l, 4, 7)
        assert 4 in s, '4 not in s'
        assert 8 not in s, '8 in s'

class TestZCS__getitem__(unittest.TestCase):
    def runTest(self):
        l = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
        s = ZeroCopySlice(l, 4, 7)
        assert s[0] == 4, 's[0] != 4'
        assert s[1] == 5, 's[1] != 5'
        assert s[-1] == 6, 's[-1] != 6'
        try:
            s[10]
            assert False, 's[10] did not fail'
        except:
            pass

class TestZCS__len__(unittest.TestCase):
    def runTest(self):
        l = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
        m = []
        s1 = ZeroCopySlice(l, 4, 7)
        s2 = ZeroCopySlice(m, 0, 0)
        assert len(s1) == 3, 'len(s1) != 3'
        assert len(s2) == 0, 'len(s2) != 0'

class TestZCS__repr__(unittest.TestCase):
    def runTest(self):
        l = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
        s1 = ZeroCopySlice(l, 4, 7)
        s2 = ZeroCopySlice(l, 4, 5)
        s3 = ZeroCopySlice(l, 4, 4)
        assert repr(s1) == '[4, 5, 6]', 'repr(s1) != [4, 5, 6]'
        assert repr(s2) == '[4]', 'repr(s2) != [4]'
        assert repr(s3) == '[]', 'repr(s3) != []'

class TestZCS__setitem__(unittest.TestCase):
    def runTest(self):
        l = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
        s = ZeroCopySlice(l, 4, 7)
        s[1] = 23
        assert s[1] == 23, 's[1] != 23'
        assert l[5] == 23, 'l[5] != 23'
        try:
            s[10] = 23
            assert False, 's[10] = 23 did not fail'
        except:
            pass

class TestZCS__str__(unittest.TestCase):
    def runTest(self):
        l = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
        s1 = ZeroCopySlice(l, 4, 7)
        s2 = ZeroCopySlice(l, 4, 5)
        s3 = ZeroCopySlice(l, 4, 4)
        assert str(s1) == '[4, 5, 6]', 'str(s1) != [4, 5, 6]'
        assert str(s2) == '[4]', 'str(s2) != [4]'
        assert str(s3) == '[]', 'str(s3) != []'

class TestZCS_count(unittest.TestCase):
    def runTest(self):
        l = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
        s = ZeroCopySlice(l, 4, 7)
        assert s.count(4) == 1, 's.count(4) != 1'
        assert s.count(8) == 0, 's.count(8) != 0'

class TestZCS_index(unittest.TestCase):
    def runTest(self):
        l = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
        s = ZeroCopySlice(l, 4, 7)
        assert s.index(5) == 1, 's.index(5) != 1'
        try:
            s.index(8)
            assert False, 's.index(8) did not fail'
        except:
            pass

if __name__ == '__main__':
    unittest.main()
