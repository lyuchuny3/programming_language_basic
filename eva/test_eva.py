from env import Environment
from evai import Eva
import operator

global_env = Environment(
    {"version": 1.0, "None": None, "true": True, "print": print, "+": operator.add}
)
eva = Eva(global_env)


def test_self_eval(eva):
    assert eva.eval(1) == 1
    assert eva.eval('"hello"') == "hello"


def test_math(eva):
    assert eva.eval(["+", 1, 2]) == 3
    assert eva.eval(["*", 3, 2]) == 6
    assert eva.eval(["+", ["*", 2, 3], 2]) == 8


def test_variable(eva):
    # define
    assert eva.eval(["var", "x", 1]) == 1
    # lookup
    assert eva.eval("x") == 1
    # eva.eval('y')   not defined

    # lookup defined var in global_env
    assert eva.eval("version") == 1.0
    # assign value should be eval
    assert eva.eval(["var", "is_chun", "true"]) == True
    assert eva.eval(["var", "y", ["+", 1, 2]]) == 3
    # update
    eva.eval(["set", "x", 2023])  # update var value
    assert eva.eval("x") == 2023


def test_block(eva):
    # test for sequence of expressions[block]
    """
    x=10
    y=20
    x*y+30 ->230
    """
    assert (
        eva.eval(
            ["begin", ["var", "x", 10], ["var", "y", 20], ["+", ["*", "x", "y"], 30]]
        )
        == 230
    )
    # test for block scope,
    """
    var x=0
    {
      var x=20 /set x=20
    }
    x 
    """
    assert eva.eval(["begin", ["var", "x", 0], ["begin", ["var", "x", 20]], "x"]) == 0
    assert eva.eval(["begin", ["var", "x", 0], ["begin", ["set", "x", 20]], "x"]) == 20

    # resolve the name in cur_env,global_env
    """
    x = 10
    {
    y = x+10
    }
    """
    assert (
        eva.eval(["begin", ["var", "x", 10], ["begin", ["var", "y", ["+", "x", 10]]]])
        == 20
    )
    """
    sum=0
    {
      sum = sum+1
    }
    sum ???
    """


def test_if(eva):
    assert (
        eva.eval(
            [
                "begin",
                ["var", "x", 10],
                ["var", "y", 20],
                ["if", [">", "x", 5], ["set", "y", 600], ["set", "y", 100]],
                "y",
            ]
        )
        == 600
    )


def test_while(eva):
    assert (
        eva.eval(
            [
                "begin",
                ["var", "x", 0],
                ["var", "sum", 0],
                [
                    "while",
                    ["<", "x", 10],
                    [
                        "begin",
                        ["set", "sum", ["+", "sum", 100]],
                        ["set", "x", ["+", "x", 1]],
                    ],
                ],
                "sum",
            ]
        )
        == 1000
    )


def test_built_in_functions(eva):
    assert eva.eval(["begin", ["print", '"hello world"'], ["+", 10, 20],]) == 30


def test_user_defined_functions(eva):
    """
    (begin
       (def square (x)
          (* x x))
        (square 2)
    }
    """
    assert (
        eva.eval(["begin", ["def", "square", "x", ["*", "x", "x"]], ["square", 3]]) == 9
    )
    assert (
        eva.eval(
            [
                "begin",
                [
                    "def",
                    "calc",
                    ["x", "y"],
                    ["begin", ["var", "z", 30], ["+", ["*", "x", "y"], "z"]],
                ],
                ["calc", 10, 20],
            ]
        )
        == 230
    )
    # closure
    """
    value=100
    def calc(x,y):
        z=x+y          30
        def inner(foo):    30
           return foo+z+value
        return inner
    fn = calc(10,20)
    fn(30) = 160
    """
    assert (
        eva.eval(
            [
                "begin",
                ["var", "value", 100],
                [
                    "def",
                    "calc",
                    ["x", "y"],
                    [
                        "begin",
                        ["var", "z", ["+", "x", "y"]],
                        ["def", "inner", "foo", ["+", ["+", "foo", "z"], "value"]],
                        "inner",
                    ],
                ],
                ["var", "fn", ["calc", 10, 20]],
                ["fn", 30],
            ]
        )
        == 160
    )


def test_lambda_function(eva):
    # immediately-invoked lambda expression IILE
    assert eva.eval([["lambda", "x", ["+", "x", "x"]], 10]) == 20
    # callback function
    assert (
        eva.eval(
            [
                "begin",
                [
                    "def",
                    "onClick",
                    "callback",
                    [
                        "begin",
                        ["var", "x", 10],
                        ["var", "y", 20],
                        ["callback", ["+", "x", "y"]],
                    ],
                ],
                ["onClick", ["lambda", "data", ["*", "data", 10]]],
            ]
        )
        == 300
    )
    # save lambda function in var
    assert (
        eva.eval(
            [
                "begin",
                ["var", "add", ["lambda", ["x", "y"], ["+", "x", "y"]]],
                ["add", 10, 20],  # func call of multi params
            ]
        )
        == 30
    )


def test_recursive_function(eva):
    assert (
        eva.eval(
            [
                "begin",
                [
                    "def",
                    "factorial",
                    "x",
                    ["if", ["=", "x", 1], 1, ["*", "x", ["factorial", ["-", "x", 1]]]],
                ],
                ["factorial", 5],
            ]
        )
        == 120
    )


def test_switch(eva):
    assert (
        eva.eval(
            [
                "begin",
                ["var", "x", 1],
                ["switch", [["=", "x", 1], 100], [[">", "x", 1], 200], ["else", 0],],
            ]
        )
        == 100
    )


def test_inc(eva):
    assert eva.eval(["begin", ["var", "x", 10], ["++", "x"]]) == 11


def test_for(eva):
    assert (
        eva.eval(
            [
                "begin",
                ["var", "sum", 0],
                [
                    "for",
                    ["var", "i", 0],
                    ["<", "i", 10],
                    ["++", "i"],
                    ["+=", "sum", "i"]
                    # ['print','i']
                ],
                "sum",
            ]
        )
        == 45
    )


def test_class(eva):
    assert (
        eva.evalGlobal(
            [
                "class",
                "Point",
                "None",
                [
                    "begin",
                    [
                        "def",
                        "constructor",
                        ["self", "x", "y"],
                        [
                            "begin",
                            ["set", ["prop", "self", "x"], "x"],
                            ["set", ["prop", "self", "y"], "y"],
                        ],
                    ],
                    [
                        "def",
                        "calc",
                        "self",
                        ["+", ["prop", "self", "x"], ["prop", "self", "y"]],
                    ],
                ],
            ],
            ["var", "p", ["new", "Point", 10, 20]],
            [["prop", "p", "calc"], "p"],
        )
        == 30
    )


def test_super_class(eva):
    assert (
        eva.evalGlobal(
            [
                "class",
                "Point",
                "None",
                [
                    "begin",
                    [
                        "def",
                        "constructor",
                        ["self", "x", "y"],
                        [
                            "begin",
                            ["set", ["prop", "self", "x"], "x"],
                            ["set", ["prop", "self", "y"], "y"],
                        ],
                    ],
                    [
                        "def",
                        "calc",
                        "self",
                        ["+", ["prop", "self", "x"], ["prop", "self", "y"]],
                    ],
                ],
            ],
            [
                "class",
                "Point3D",
                "Point",
                [
                    "begin",
                    [
                        "def",
                        "constructor",
                        ["self", "x", "y", "z"],
                        [
                            "begin",
                            [
                                ["prop", ["super", "Point3D"], "constructor"],
                                "self",
                                "x",
                                "y",
                            ],
                            ["set", ["prop", "self", "z"], "z"],
                        ],
                    ],
                    [
                        "def",
                        "calc",
                        "self",
                        [
                            "+",
                            [["prop", ["super", "Point3D"], "calc"], "self"],
                            ["prop", "self", "z"],
                        ],
                    ],
                ],
            ],
            ["var", "p", ["new", "Point3D", 10, 20, 30]],
            [["prop", "p", "calc"], "p"],
        )
        == 60
    )


def test_module(eva):
    eva.evalGlobal(
        [
            "module",
            "Math",
            [
                "begin",
                ["def", "abs", "x", ["if", ["<", "x", 0], ["-", "x"], "x"]],
                ["def", "square", "x", ["*", "x", "x"]],
                ["var", "MAX_VALUE", 1000],
            ],
        ]
    )
    assert eva.eval(["prop", "Math", "MAX_VALUE"]) == 1000
    assert eva.eval([["prop", "Math", "abs"], -10]) == 10
    assert eva.eval([["prop", "Math", "square"], 10]) == 100


def test_import(eva):
    eva.eval(["import", "Math"])
    assert eva.eval(["prop", "Math", "MAX_VALUE"]) == 1000
    assert eva.eval([["prop", "Math", "abs"], -10]) == 10
    assert eva.eval([["prop", "Math", "square"], 10]) == 100


if __name__ == "__main__":
    test_self_eval(eva)
    test_math(eva)
    test_variable(eva)
    test_block(eva)
    test_if(eva)
    test_while(eva)
    test_built_in_functions(eva)
    test_user_defined_functions(eva)
    test_lambda_function(eva)
    test_recursive_function(eva)
    test_switch(eva)
    test_inc(eva)
    test_for(eva)
    test_class(eva)
    test_super_class(eva)
    test_module(eva)
    test_import(eva)
    print("all tests passed!")
