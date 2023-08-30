# Python test set -- part 1, grammar.
# This just tests whether the parser accepts them all.

# NOTE: When you run this test as a script from the command line, you
# get warnings about certain hex/oct constants.  Since those are
# issued by the parser, you can't suppress them by adding a
# filterwarnings() call to this module.  Therefore, to shut up the
# regression test, the filterwarnings() call has been added to
# regrtest.py.

import unittest

# testing import *
from sys import *
from test.support import check_syntax_error, run_unittest


class TokenTests(unittest.TestCase):
    def testBackslash(self):
        # Backslash means line continuation:
        x = 1 + 1
        assert x == 2

        # Backslash does not means continuation in comments :\
        x = 0
        assert x == 0

    def testPlainIntegers(self):
        assert int == int
        assert 255 == 255
        assert 255 == 255
        assert 2147483647 == 2147483647
        assert 9 == 9
        # "0x" is not a valid literal
        self.assertRaises(SyntaxError, eval, "0x")
        from sys import maxsize

        if maxsize == 2147483647:
            assert -2147483647 - 1 == -2147483648
            # XXX -2147483648
            assert 4294967295 > 0
            assert 4294967295 > 0
            assert 2147483647 > 0
            for s in (
                "2147483648",
                "0o40000000000",
                "0x100000000",
                "0b10000000000000000000000000000000",
            ):
                try:
                    eval(s)
                except OverflowError:
                    self.fail("OverflowError on huge integer literal %r" % s)
        elif maxsize == 9223372036854775807:
            assert -9223372036854775807 - 1 == -9223372036854775808
            assert 18446744073709551615 > 0
            assert 18446744073709551615 > 0
            assert 4611686018427387903 > 0
            for s in (
                "9223372036854775808",
                "0o2000000000000000000000",
                "0x10000000000000000",
                "0b100000000000000000000000000000000000000000000000000000000000000",
            ):
                try:
                    eval(s)
                except OverflowError:
                    self.fail("OverflowError on huge integer literal %r" % s)
        else:
            self.fail("Weird maxsize value %r" % maxsize)

    def testLongIntegers(self):
        pass

    def testUnderscoresInNumbers(self):
        # Integers
        pass

        # Floats

    def testFloats(self):
        pass
        # XXX x = 000.314

    def testEllipsis(self):
        x = ...
        assert x is Ellipsis
        self.assertRaises(SyntaxError, eval, ".. .")


class GrammarTests(unittest.TestCase):
    # single_input: NEWLINE | simple_stmt | compound_stmt NEWLINE
    # XXX can't test in a script -- this rule is only used when interactive

    # file_input: (NEWLINE | stmt)* ENDMARKER
    # Being tested as this very moment this very module

    # expr_input: testlist NEWLINE
    # XXX Hard to test -- used only in calls to input()

    def testEvalInput(self):
        # testlist ENDMARKER
        eval("1, 0 or 1")

    def testFuncdef(self):
        ### [decorators] 'def' NAME parameters ['->' test] ':' suite
        ### decorator: '@' dotted_name [ '(' [arglist] ')' ] NEWLINE
        ### decorators: decorator+
        ### parameters: '(' [typedargslist] ')'
        ### typedargslist: ((tfpdef ['=' test] ',')*
        ###                ('*' [tfpdef] (',' tfpdef ['=' test])* [',' '**' tfpdef] | '**' tfpdef)
        ###                | tfpdef ['=' test] (',' tfpdef ['=' test])* [','])
        ### tfpdef: NAME [':' test]
        ### varargslist: ((vfpdef ['=' test] ',')*
        ###              ('*' [vfpdef] (',' vfpdef ['=' test])*  [',' '**' vfpdef] | '**' vfpdef)
        ###              | vfpdef ['=' test] (',' vfpdef ['=' test])* [','])
        ### vfpdef: NAME
        def f1():
            pass

        f1()
        f1(*())
        f1(*(), **{})

        def f2(one_argument):
            pass

        def f3(two, arguments):
            pass

        assert f2.__code__.co_varnames == ("one_argument",)
        assert f3.__code__.co_varnames == ("two", "arguments")

        def a1(
            one_arg,
        ):
            pass

        def a2(
            two,
            args,
        ):
            pass

        def v0(*rest):
            pass

        def v1(a, *rest):
            pass

        def v2(a, b, *rest):
            pass

        f1()
        f2(1)
        f2(
            1,
        )
        f3(1, 2)
        f3(
            1,
            2,
        )
        v0()
        v0(1)
        v0(
            1,
        )
        v0(1, 2)
        v0(1, 2, 3, 4, 5, 6, 7, 8, 9, 0)
        v1(1)
        v1(
            1,
        )
        v1(1, 2)
        v1(1, 2, 3)
        v1(1, 2, 3, 4, 5, 6, 7, 8, 9, 0)
        v2(1, 2)
        v2(1, 2, 3)
        v2(1, 2, 3, 4)
        v2(1, 2, 3, 4, 5, 6, 7, 8, 9, 0)

        def d01(a=1):
            pass

        d01()
        d01(1)
        d01(*(1,))
        d01(**{"a": 2})

        def d11(a, b=1):
            pass

        d11(1)
        d11(1, 2)
        d11(1, **{"b": 2})

        def d21(a, b, c=1):
            pass

        d21(1, 2)
        d21(1, 2, 3)
        d21(*(1, 2, 3))
        d21(1, *(2, 3))
        d21(1, 2, *(3,))
        d21(1, 2, **{"c": 3})

        def d02(a=1, b=2):
            pass

        d02()
        d02(1)
        d02(1, 2)
        d02(*(1, 2))
        d02(1, *(2,))
        d02(1, **{"b": 2})
        d02(**{"a": 1, "b": 2})

        def d12(a, b=1, c=2):
            pass

        d12(1)
        d12(1, 2)
        d12(1, 2, 3)

        def d22(a, b, c=1, d=2):
            pass

        d22(1, 2)
        d22(1, 2, 3)
        d22(1, 2, 3, 4)

        def d01v(a=1, *rest):
            pass

        d01v()
        d01v(1)
        d01v(1, 2)
        d01v(*(1, 2, 3, 4))
        d01v(*(1,))
        d01v(**{"a": 2})

        def d11v(a, b=1, *rest):
            pass

        d11v(1)
        d11v(1, 2)
        d11v(1, 2, 3)

        def d21v(a, b, c=1, *rest):
            pass

        d21v(1, 2)
        d21v(1, 2, 3)
        d21v(1, 2, 3, 4)
        d21v(*(1, 2, 3, 4))
        d21v(1, 2, **{"c": 3})

        def d02v(a=1, b=2, *rest):
            pass

        d02v()
        d02v(1)
        d02v(1, 2)
        d02v(1, 2, 3)
        d02v(1, *(2, 3, 4))
        d02v(**{"a": 1, "b": 2})

        def d12v(a, b=1, c=2, *rest):
            pass

        d12v(1)
        d12v(1, 2)
        d12v(1, 2, 3)
        d12v(1, 2, 3, 4)
        d12v(*(1, 2, 3, 4))
        d12v(1, 2, *(3, 4, 5))
        d12v(1, *(2,), **{"c": 3})

        def d22v(a, b, c=1, d=2, *rest):
            pass

        d22v(1, 2)
        d22v(1, 2, 3)
        d22v(1, 2, 3, 4)
        d22v(1, 2, 3, 4, 5)
        d22v(*(1, 2, 3, 4))
        d22v(1, 2, *(3, 4, 5))
        d22v(1, *(2, 3), **{"d": 4})

        # keyword argument type tests
        try:
            str("x", **{b"foo": 1})
        except TypeError:
            pass
        else:
            self.fail("Bytes should not work as keyword argument names")

        # keyword only argument tests
        def pos0key1(*, key):
            return key

        pos0key1(key=100)

        def pos2key2(p1, p2, *, k1, k2=100):
            return p1, p2, k1, k2

        pos2key2(1, 2, k1=100)
        pos2key2(1, 2, k1=100, k2=200)
        pos2key2(1, 2, k2=100, k1=200)

        def pos2key2dict(p1, p2, *, k1=100, k2, **kwarg):
            return p1, p2, k1, k2, kwarg

        pos2key2dict(1, 2, k2=100, tokwarg1=100, tokwarg2=200)
        pos2key2dict(1, 2, tokwarg1=100, tokwarg2=200, k2=100)

        # keyword arguments after *arglist
        def f(*args, **kwargs):
            return args, kwargs

        assert f(1, *[3, 4], x=2, y=5) == ((1, 3, 4), {"x": 2, "y": 5})
        self.assertRaises(SyntaxError, eval, "f(1, *(2,3), 4)")
        self.assertRaises(SyntaxError, eval, "f(1, x=2, *(3,4), x=5)")

        # argument annotation tests
        def f(x) -> list:
            pass

        assert f.__annotations__ == {"return": list}

        def f(x: int):
            pass

        assert f.__annotations__ == {"x": int}

        def f(*x: str):
            pass

        assert f.__annotations__ == {"x": str}

        def f(**x: float):
            pass

        assert f.__annotations__ == {"x": float}

        def f(x, y: 1 + 2):
            pass

        assert f.__annotations__ == {"y": 3}

        def f(a, b: 1, c: 2, d):
            pass

        assert f.__annotations__ == {"b": 1, "c": 2}

        def f(a, b: 1, c: 2, d, e: 3 = 4, f=5, *g: 6):
            pass

        assert f.__annotations__ == {"b": 1, "c": 2, "e": 3, "g": 6}

        def f(
            a,
            b: 1,
            c: 2,
            d,
            e: 3 = 4,
            f=5,
            *g: 6,
            h: 7,
            i=8,
            j: 9 = 10,
            **k: 11,
        ) -> 12:
            pass

        assert f.__annotations__ == {
            "b": 1,
            "c": 2,
            "e": 3,
            "g": 6,
            "h": 7,
            "j": 9,
            "k": 11,
            "return": 12,
        }

        # Check for SF Bug #1697248 - mixing decorators and a return annotation
        def null(x):
            return x

        @null
        def f(x) -> list:
            pass

        assert f.__annotations__ == {"return": list}

        # test closures with a variety of oparg's
        closure = 1

        def f():
            return closure

        def f(x=1):
            return closure

        def f(*, k=1):
            return closure

        def f() -> int:
            return closure

        # Check ast errors in *args and *kwargs
        check_syntax_error(self, "f(*g(1=2))")
        check_syntax_error(self, "f(**g(1=2))")

    def testLambdef(self):
        ### lambdef: 'lambda' [varargslist] ':' test
        def l1():
            return 0

        assert l1() == 0

        def l2():
            return a[d]  # XXX just testing the expression

        def l3():
            return [(2 < x) for x in [-1, 3, 0]]

        assert l3() == [0, 1, 0]

        def l4(x=lambda y=lambda z=1: z: y()):
            return x()

        assert l4() == 1

        def l5(x, y, z=2):
            return x + y + z

        assert l5(1, 2) == 5
        assert l5(1, 2, 3) == 6
        check_syntax_error(self, "lambda x: x = 2")
        check_syntax_error(self, "lambda (None,): None")

        def l6(x, y, *, k=20):
            return x + y + k

        assert l6(1, 2) == 1 + 2 + 20
        assert l6(1, 2, k=10) == 1 + 2 + 10

    ### stmt: simple_stmt | compound_stmt
    # Tested below

    def testSimpleStmt(self):
        ### simple_stmt: small_stmt (';' small_stmt)* [';']
        x = 1
        del x

        def foo():
            # verify statements that end with semi-colons
            x = 1
            del x

        foo()

    ### small_stmt: expr_stmt | pass_stmt | del_stmt | flow_stmt | import_stmt | global_stmt | access_stmt
    # Tested below

    def testExprStmt(self):
        # (exprlist '=')* exprlist
        1
        1, 2, 3
        x = 1
        x = 1, 2, 3
        x = y = z = 1, 2, 3
        x, y, z = 1, 2, 3
        a, b, c = x, y, z = 1, 2, (3, 4)

        check_syntax_error(self, "x + 1 = 1")
        check_syntax_error(self, "a + 1 = b + 2")

    def testDelStmt(self):
        # 'del' exprlist
        abc = [1, 2, 3]
        x, y, z = abc
        xyz = x, y, z

        del abc
        del x, y, (z, xyz)

    def testPassStmt(self):
        # 'pass'
        pass

    # flow_stmt: break_stmt | continue_stmt | return_stmt | raise_stmt
    # Tested below

    def testBreakStmt(self):
        # 'break'
        while 1:
            break

    def testContinueStmt(self):
        # 'continue'
        i = 1
        while i:
            i = 0
            continue

        msg = ""
        while not msg:
            msg = "ok"
            try:
                continue
                msg = "continue failed to continue inside try"
            except:
                msg = "continue inside try called except block"
        if msg != "ok":
            self.fail(msg)

        msg = ""
        while not msg:
            msg = "finally block not called"
            try:
                continue
            finally:
                msg = "ok"
        if msg != "ok":
            self.fail(msg)

    def test_break_continue_loop(self):
        # This test warrants an explanation. It is a test specifically for SF bugs
        # #463359 and #462937. The bug is that a 'break' statement executed or
        # exception raised inside a try/except inside a loop, *after* a continue
        # statement has been executed in that loop, will cause the wrong number of
        # arguments to be popped off the stack and the instruction pointer reset to
        # a very small number (usually 0.) Because of this, the following test
        # *must* written as a function, and the tracking vars *must* be function
        # arguments with default values. Otherwise, the test will loop and loop.

        def test_inner(extra_burning_oil=1, count=0):
            big_hippo = 2
            while big_hippo:
                count += 1
                try:
                    if extra_burning_oil and big_hippo == 1:
                        extra_burning_oil -= 1
                        break
                    big_hippo -= 1
                    continue
                except:
                    raise
            if count > 2 or big_hippo != 1:
                self.fail("continue then break in try/except in loop broken!")

        test_inner()

    def testReturn(self):
        # 'return' [testlist]
        def g1():
            return

        def g2():
            return 1

        g1()
        g2()
        check_syntax_error(self, "class foo:return 1")

    def testYield(self):
        check_syntax_error(self, "class foo:yield 1")

    def testRaise(self):
        # 'raise' test [',' test]
        try:
            raise RuntimeError("just testing")
        except RuntimeError:
            pass
        try:
            raise KeyboardInterrupt
        except KeyboardInterrupt:
            pass

    def testImport(self):
        # 'import' dotted_as_names
        pass

        # 'from' dotted_name 'import' ('*' | '(' import_as_names ')' | import_as_names)

        # not testable inside a function, but already done at top of the module
        # from sys import *

    def testGlobal(self):
        # 'global' NAME (',' NAME)*
        global a
        global a, b
        global one, two, three, four, five, six, seven, eight, nine, ten

    def testNonlocal(self):
        # 'nonlocal' NAME (',' NAME)*
        x = 0
        y = 0

        def f():
            nonlocal x
            nonlocal x, y

    def testAssert(self):
        # assert_stmt: 'assert' test [',' test]
        assert 1
        assert 1, 1
        assert lambda x: x
        assert 1, lambda x: x + 1
        try:
            assert 0, "msg"
        except AssertionError as e:
            assert e.args[0] == "msg"
        else:
            if __debug__:
                self.fail("AssertionError not raised by assert 0")

    ### compound_stmt: if_stmt | while_stmt | for_stmt | try_stmt | funcdef | classdef
    # Tested below

    def testIf(self):
        # 'if' test ':' suite ('elif' test ':' suite)* ['else' ':' suite]
        if 1:
            pass
        if 1:
            pass
        else:
            pass
        if 0:
            pass
        elif 0:
            pass
        if 0:
            pass
        elif 0:
            pass
        elif 0:
            pass
        elif 0:
            pass
        else:
            pass

    def testWhile(self):
        # 'while' test ':' suite ['else' ':' suite]
        while 0:
            pass
        while 0:
            pass
        else:
            pass

        # Issue1920: "while 0" is optimized away,
        # ensure that the "else" clause is still present.
        x = 0
        while 0:
            x = 1
        else:
            x = 2
        assert x == 2

    def testFor(self):
        # 'for' exprlist 'in' exprlist ':' suite ['else' ':' suite]
        for _i in 1, 2, 3:
            pass
        for _i, _j, _k in ():
            pass
        else:
            pass

        class Squares:
            def __init__(self, max):
                self.max = max
                self.sofar = []

            def __len__(self):
                return len(self.sofar)

            def __getitem__(self, i):
                if not 0 <= i < self.max:
                    raise IndexError
                n = len(self.sofar)
                while n <= i:
                    self.sofar.append(n * n)
                    n = n + 1
                return self.sofar[i]

        n = 0
        for x in Squares(10):
            n = n + x
        if n != 285:
            self.fail("for over growing sequence")

        result = []
        for (x,) in [(1,), (2,), (3,)]:
            result.append(x)
        assert result == [1, 2, 3]

    def testTry(self):
        ### try_stmt: 'try' ':' suite (except_clause ':' suite)+ ['else' ':' suite]
        ###         | 'try' ':' suite 'finally' ':' suite
        ### except_clause: 'except' [expr ['as' expr]]
        try:
            1 / 0
        except ZeroDivisionError:
            pass
        else:
            pass
        try:
            1 / 0
        except EOFError:
            pass
        except TypeError:
            pass
        except RuntimeError:
            pass
        except:
            pass
        else:
            pass
        try:
            1 / 0
        except (EOFError, TypeError, ZeroDivisionError):
            pass
        try:
            1 / 0
        except (EOFError, TypeError, ZeroDivisionError):
            pass
        try:
            pass
        finally:
            pass

    def testSuite(self):
        # simple_stmt | NEWLINE INDENT NEWLINE* (stmt NEWLINE*)+ DEDENT
        if 1:
            pass
        if 1:
            pass
        if 1:
            #
            #
            #
            #
            pass
            #

    def testTest(self):
        ### and_test ('or' and_test)*
        ### and_test: not_test ('and' not_test)*
        ### not_test: 'not' not_test | comparison
        if not 1:
            pass
        if 1 and 1:
            pass
        if 1 or 1:
            pass
        if not not not 1:
            pass
        if not 1 and 1 and 1:
            pass
        if 1 and 1 or 1 and 1 and 1 or not 1 and 1:
            pass

    def testComparison(self):
        ### comparison: expr (comp_op expr)*
        ### comp_op: '<'|'>'|'=='|'>='|'<='|'!='|'in'|'not' 'in'|'is'|'is' 'not'
        if 1:
            pass
        if 1 == 1:
            pass
        if 1 != 1:
            pass
        if 1 < 1:
            pass
        if 1 > 1:
            pass
        if 1 <= 1:
            pass
        if 1 >= 1:
            pass
        if 1 == 1:
            pass
        if 1 != 1:
            pass
        if 1 in ():
            pass
        if 1 not in ():
            pass
        if 1 < 1 > 1 == 1 >= 1 <= 1 != 1 in 1 not in 1 == 1 != 1:
            pass

    def testBinaryMaskOps(self):
        pass

    def testShiftOps(self):
        pass

    def testAdditiveOps(self):
        pass

    def testMultiplicativeOps(self):
        pass

    def testUnaryOps(self):
        pass

    def testSelectors(self):
        ### trailer: '(' [testlist] ')' | '[' subscript ']' | '.' NAME
        ### subscript: expr | [expr] ':' [expr]

        import sys
        import time

        sys.path[0]
        time.time()
        sys.modules["time"].time()
        a = "01234"
        a[0]
        a[-1]
        a[0:5]
        a[:5]
        a[0:]
        a[:]
        a[-5:]
        a[:-1]
        a[-4:-3]
        # A rough test of SF bug 1333982.  http://python.org/sf/1333982
        # The testing here is fairly incomplete.
        # Test cases should include: commas with 1 and 2 colons
        d = {}
        d[1] = 1
        d[1,] = 2
        d[1, 2] = 3
        d[1, 2, 3] = 4
        L = list(d)
        L.sort(key=lambda x: x if isinstance(x, tuple) else ())
        assert str(L) == "[1, (1,), (1, 2), (1, 2, 3)]"

    def testAtoms(self):
        ### atom: '(' [testlist] ')' | '[' [testlist] ']' | '{' [dictsetmaker] '}' | NAME | NUMBER | STRING
        ### dictsetmaker: (test ':' test (',' test ':' test)* [',']) | (test (',' test)* [','])

        x = 1
        x = 1 or 2 or 3
        x = (1 or 2 or 3, 2, 3)

        x = []
        x = [1]
        x = [1 or 2 or 3]
        x = [1 or 2 or 3, 2, 3]
        x = []

        x = {}
        x = {"one": 1}
        x = {
            "one": 1,
        }
        x = {"one" or "two": 1 or 2}
        x = {"one": 1, "two": 2}
        x = {
            "one": 1,
            "two": 2,
        }
        x = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6}

        x = {"one"}
        x = {
            "one",
            1,
        }
        x = {"one", "two", "three"}
        x = {
            2,
            3,
            4,
        }

        x = x
        x = "x"
        x = 123

    ### exprlist: expr (',' expr)* [',']
    ### testlist: test (',' test)* [',']
    # These have been exercised enough above

    def testClassdef(self):
        # 'class' NAME ['(' [testlist] ')'] ':' suite
        class B:
            pass

        class B2:
            pass

        class C1(B):
            pass

        class C2(B):
            pass

        class D(C1, C2, B):
            pass

        class C:
            def meth1(self):
                pass

            def meth2(self, arg):
                pass

            def meth3(self, a1, a2):
                pass

        # decorator: '@' dotted_name [ '(' [arglist] ')' ] NEWLINE
        # decorators: decorator+
        # decorated: decorators (classdef | funcdef)
        def class_decorator(x):
            return x

        @class_decorator
        class G:
            pass

    def testDictcomps(self):
        # dictorsetmaker: ( (test ':' test (comp_for |
        #                                   (',' test ':' test)* [','])) |
        #                   (test (comp_for | (',' test)* [','])) )
        nums = [1, 2, 3]
        assert {i: (i + 1) for i in nums} == {1: 2, 2: 3, 3: 4}

    def testListcomps(self):
        # list comprehension tests
        nums = [1, 2, 3, 4, 5]
        strs = ["Apple", "Banana", "Coconut"]
        spcs = ["  Apple", " Banana ", "Coco  nut  "]

        assert [s.strip() for s in spcs] == ["Apple", "Banana", "Coco  nut"]
        assert [(3 * x) for x in nums] == [3, 6, 9, 12, 15]
        assert [x for x in nums if x > 2] == [3, 4, 5]
        assert [(i, s) for i in nums for s in strs] == [
            (1, "Apple"),
            (1, "Banana"),
            (1, "Coconut"),
            (2, "Apple"),
            (2, "Banana"),
            (2, "Coconut"),
            (3, "Apple"),
            (3, "Banana"),
            (3, "Coconut"),
            (4, "Apple"),
            (4, "Banana"),
            (4, "Coconut"),
            (5, "Apple"),
            (5, "Banana"),
            (5, "Coconut"),
        ]
        assert [
            (i, s) for i in nums for s in [f for f in strs if "n" in f]
        ] == [
            (1, "Banana"),
            (1, "Coconut"),
            (2, "Banana"),
            (2, "Coconut"),
            (3, "Banana"),
            (3, "Coconut"),
            (4, "Banana"),
            (4, "Coconut"),
            (5, "Banana"),
            (5, "Coconut"),
        ]
        assert [
            (lambda a: [(a**i) for i in range(a + 1)])(j) for j in range(5)
        ] == [[1], [1, 1], [1, 2, 4], [1, 3, 9, 27], [1, 4, 16, 64, 256]]

        def test_in_func(l):
            return [0 < x < 3 for x in l if x > 2]

        assert test_in_func(nums) == [False, False, False]

        def test_nested_front():
            assert [[x, x + 1] for x in [1, 3, 5]] == [[1, 2], [3, 4], [5, 6]]

        test_nested_front()

        check_syntax_error(self, "[i, s for i in nums for s in strs]")
        check_syntax_error(self, "[x if y]")

        suppliers = [(1, "Boeing"), (2, "Ford"), (3, "Macdonalds")]

        parts = [(10, "Airliner"), (20, "Engine"), (30, "Cheeseburger")]

        suppart = [(1, 10), (1, 20), (2, 20), (3, 30)]

        x = [
            (sname, pname)
            for (sno, sname) in suppliers
            for (pno, pname) in parts
            for (sp_sno, sp_pno) in suppart
            if sno == sp_sno and pno == sp_pno
        ]

        assert x == [
            ("Boeing", "Airliner"),
            ("Boeing", "Engine"),
            ("Ford", "Engine"),
            ("Macdonalds", "Cheeseburger"),
        ]

    def testGenexps(self):
        # generator expression tests
        g = (list(range(10)) for x in range(1))
        assert next(g) == list(range(10))
        try:
            next(g)
            self.fail("should produce StopIteration exception")
        except StopIteration:
            pass

        a = 1
        try:
            g = (a for d in a)
            next(g)
            self.fail("should produce TypeError")
        except TypeError:
            pass

        assert [(x, y) for x in "abcd" for y in "abcd"] == [
            (x, y) for x in "abcd" for y in "abcd"
        ]
        assert [(x, y) for x in "ab" for y in "xy"] == [
            (x, y) for x in "ab" for y in "xy"
        ]

        a = list(range(10))
        b = (x for x in (y for y in a))
        assert sum(b) == sum(list(range(10)))

        assert sum(x**2 for x in range(10)) == sum(
            [(x**2) for x in range(10)]
        )
        assert sum(x * x for x in range(10) if x % 2) == sum(
            [(x * x) for x in range(10) if x % 2]
        )
        assert sum(x for x in (y for y in range(10))) == sum(list(range(10)))
        assert sum(x for x in (y for y in (z for z in range(10)))) == sum(
            list(range(10))
        )
        assert sum(x for x in (list(range(10)))) == sum(list(range(10)))
        assert sum(
            x for x in (y for y in (z for z in range(10) if True)) if True
        ) == sum(list(range(10)))
        assert (
            sum(
                x
                for x in (y for y in (z for z in range(10) if True) if False)
                if True
            )
            == 0
        )
        check_syntax_error(self, "foo(x for x in range(10), 100)")
        check_syntax_error(self, "foo(100, x for x in range(10))")

    def testComprehensionSpecials(self):
        # test for outmost iterable precomputation
        x = 10
        g = (i for i in range(x))
        x = 5
        assert len(list(g)) == 10

        # This should hold, since we're only precomputing outmost iterable.
        x = 10
        t = False
        g = ((i, j) for i in range(x) if t for j in range(x))
        x = 5
        t = True
        assert [(i, j) for i in range(10) for j in range(5)] == list(g)

        # Grammar allows multiple adjacent 'if's in listcomps and genexps,
        # even though it's silly. Make sure it works (ifelse broke this.)
        assert [x for x in range(10) if x % 2 if x % 3] == [1, 5, 7]
        assert [x for x in range(10) if x % 2 if x % 3] == [1, 5, 7]

        # verify unpacking single element tuples in listcomp/genexp.
        assert [x for x, in [(4,), (5,), (6,)]] == [4, 5, 6]
        assert [x for x, in [(7,), (8,), (9,)]] == [7, 8, 9]

    def test_with_statement(self):
        class manager:
            def __enter__(self):
                return (1, 2)

            def __exit__(self, *args):
                pass

        with manager():
            pass
        with manager() as x:
            pass
        with manager() as (x, y):
            pass
        with manager(), manager():
            pass
        with manager(), manager():
            pass
        with manager(), manager():
            pass

    def testIfElseExpr(self):
        # Test ifelse expressions in various cases
        def _checkeval(msg, ret):
            "helper to check that evaluation of expressions is done correctly"
            print(x)
            return ret

        # the next line is not allowed anymore
        # self.assertEqual([ x() for x in lambda: True, lambda: False if x() ], [True])
        assert [x() for x in (lambda: True, lambda: False) if x()] == [True]
        assert [
            x(False)
            for x in (
                lambda x: False if x else True,
                lambda x: True if x else False,
            )
            if x(False)
        ] == [True]
        assert (5 if 1 else _checkeval("check 1", 0)) == 5
        assert (_checkeval("check 2", 0) if 0 else 5) == 5
        assert (5 and 6 if 0 else 1) == 1
        assert (5 and 6 if 0 else 1) == 1
        assert (5 and (6 if 1 else 1)) == 6
        assert (0 or _checkeval("check 3", 2) if 0 else 3) == 3
        assert (
            1 or _checkeval("check 4", 2) if 1 else _checkeval("check 5", 3)
        ) == 1
        assert (0 or 5 if 1 else _checkeval("check 6", 3)) == 5
        assert (not 5 if 1 else 1) is False
        assert (not 5 if 0 else 1) == 1
        assert (6 + 1 if 1 else 2) == 7
        assert (6 - 1 if 1 else 2) == 5
        assert (6 * 2 if 1 else 4) == 12
        assert (6 / 2 if 1 else 3) == 3
        assert (6 < 4 if 0 else 2) == 2

    def testStringLiterals(self):
        x = ""
        y = ""
        assert len(x) == 0 and x == y
        x = "'"
        y = "'"
        assert len(x) == 1 and x == y and ord(x) == 39
        x = '"'
        y = '"'
        assert len(x) == 1 and x == y and ord(x) == 34
        x = 'doesn\'t "shrink" does it'
        y = 'doesn\'t "shrink" does it'
        assert len(x) == 24 and x == y
        x = 'does "shrink" doesn\'t it'
        y = 'does "shrink" doesn\'t it'
        assert len(x) == 24 and x == y
        x = """
The "quick"
brown fox
jumps over
the 'lazy' dog.
"""
        y = "\nThe \"quick\"\nbrown fox\njumps over\nthe 'lazy' dog.\n"
        assert x == y
        y = """
The "quick"
brown fox
jumps over
the 'lazy' dog.
"""
        assert x == y
        y = "\n\
The \"quick\"\n\
brown fox\n\
jumps over\n\
the 'lazy' dog.\n\
"
        assert x == y
        y = "\n\
The \"quick\"\n\
brown fox\n\
jumps over\n\
the 'lazy' dog.\n\
"
        assert x == y


def test_main():
    run_unittest(TokenTests, GrammarTests)


if __name__ == "__main__":
    test_main()
