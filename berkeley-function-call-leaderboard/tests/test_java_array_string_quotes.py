"""Regression tests for Java Array literal element normalization.

The Java checker passes each argument as a string of Java source. For a
parameter typed ``Array`` whose items are ``String`` (e.g. ``simple_java_35``
``RedissonConnection.bitOp(keys=...)``), a model that emits the *valid* Java
literal ``new String[]{"a", "b"}`` must be normalized to the bare Python
strings ``["a", "b"]`` that the answer key stores.

Previously ``parse_array`` delegated each element to ``java_type_converter``
without stripping the surrounding double quotes, while ``parse_arraylist``
did strip them. The result was that valid quoted String-array literals were
rejected (the quotes survived) and invalid unquoted ones were accepted.
"""

from bfcl_eval.eval_checker.ast_eval.type_convertor.java_type_converter import (
    java_type_converter,
)


def test_string_array_strips_element_quotes():
    # The valid Java literal from simple_java_35.
    out = java_type_converter(
        'new String[]{"user:online:today", "user:online:yesterday"}',
        "Array",
        nested_type="String",
    )
    assert out == ["user:online:today", "user:online:yesterday"]


def test_array_and_arraylist_normalize_the_same_strings():
    array_out = java_type_converter(
        'new String[]{"a", "b"}', "Array", nested_type="String"
    )
    arraylist_out = java_type_converter(
        'new ArrayList<>(Arrays.asList("a", "b"))',
        "ArrayList",
        nested_type="String",
    )
    assert array_out == arraylist_out == ["a", "b"]


def test_char_array_strips_element_quotes():
    out = java_type_converter(
        "new char[]{'a', 'b'}", "Array", nested_type="char"
    )
    assert out == ["a", "b"]
