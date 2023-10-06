import inspect
from env import Environment
from transformer import Transformer


def isVariableName(exp):
    if isinstance(exp, str):
        if exp[0].isalpha():
            return True
    return False


class Eva:
    # create a Eva instance with global environment
    def __init__(self, global_env=Environment()):
        self.global_env = global_env
        self._transformer = Transformer()

    def evalGlobal(self, *exp):
        return self._eval_block(["begin", *exp], self.global_env)

    def eval(self, exp, env=None):
        if env is None:
            env = self.global_env
        # self-evaluating
        # -----------------------
        if isinstance(exp, (int, float)):
            return exp
        if isinstance(exp, str) and exp[0] == '"' and exp[-1] == '"':
            return exp[1:-1]

        # var lookup/access
        if isVariableName(exp):
            return env.lookup(exp)

        # binary operator
        # --------------------------
        if exp[0] == "+":
            return self.eval(exp[1], env) + self.eval(exp[2], env)
        if exp[0] == "-":
            if len(exp) == 2:
                return -self.eval(exp[1], env)
            return self.eval(exp[1], env) - self.eval(exp[2], env)
        if exp[0] == "*":
            return self.eval(exp[1], env) * self.eval(exp[2], env)
        if exp[0] == ">":
            return self.eval(exp[1], env) > self.eval(exp[2], env)
        if exp[0] == "<":
            return self.eval(exp[1], env) < self.eval(exp[2], env)
        if exp[0] == "=":
            return self.eval(exp[1], env) == self.eval(exp[2], env)

        # inc
        # --------------------------
        if exp[0] == "++":
            set_exp = self._transformer.transformIncToSet(exp)
            return self.eval(set_exp, env)
        if exp[0] == "--":
            set_exp = self._transformer.transformDecToSet(exp)
            return self.eval(set_exp, env)
        if exp[0] == "+=":
            set_exp = self._transformer.transformIncValToSet(exp)
            return self.eval(set_exp, env)
        if exp[0] == "-=":
            set_exp = self._transformer.transformDecValToSet(exp)
            return self.eval(set_exp, env)

        # var declare: should eval value at define
        # ['var', var_name ,value]
        # --------------------------
        if exp[0] == "var":
            _, var, value = exp
            return env.define(var, self.eval(value, env))

        # var update/assign
        # ['set',var_name, value]
        # ['set',['prop','self','x'],10]
        if exp[0] == "set":
            _, ref, value = exp
            if ref[0] == "prop":
                _, instance, prop_name = ref
                # instance_env = env.lookup(instance) maybe instance is ['super','classname']
                instance_env = self.eval(instance, env)
                return instance_env.define(prop_name, self.eval(value, env))

            return env.assign(ref, self.eval(value, env))

        # block: group of exprs (stmt_seq)
        # block scope, new env on block enter
        # --------------------------
        if exp[0] == "begin":
            block_env = Environment({}, env)
            return self._eval_block(exp, block_env)

        # if
        # ['if', condition, stmt_then, stmt_else]
        # --------------------------
        if exp[0] == "if":
            _, cond, stmt1, stmt2 = exp
            if self.eval(cond, env):
                return self.eval(stmt1, env)
            return self.eval(stmt2, env)

        # switch
        # ['switch',[cond1, block1], [cond2, block2], ..., ['else', block]]
        # ---------------------------
        if exp[0] == "switch":
            if_exp = self._transformer.transformSwitchToIfexp(exp)
            return self.eval(if_exp, env)

        # while
        # ['while', cond, body]
        # --------------------------
        if exp[0] == "while":
            _, cond, body = exp
            ret = None
            while self.eval(cond, env):
                ret = self.eval(body, env)
            return ret

        # for
        # ['for', init, end_cond, update, body]
        # ---------------------------
        if exp[0] == "for":
            while_exp = self._transformer.transformForToWhile(exp)
            return self.eval(while_exp, env)
        # def
        # ['def',fname, params, body]
        # --------------------------
        # if exp[0] == "def":
        #     _, fname, params, body = exp
        #     func = [params, body, env]
        #     return env.define(fname, func)
        # syntax sugar:

        if exp[0] == "def":
            # JIT transpile to var decalration
            var_expr = self._transformer.transformDefToVarLambda(exp)
            return self.eval(var_expr, env)
        # lambda
        # ['lambda', params, body]
        # --------------------------
        """
        define function, param can be single, of multi params with list
        def func x [*,x,x]
        def func [x,y],[*,x,y]
        lambda x [*,x,x]
        lambda [x,y] [*,x,y]
        we transform into list at lambda parser
        func 2
        func 2 3
        call we will get args[ i for i in exp[1:]]
        """
        if exp[0] == "lambda":
            _, params, body = exp
            if not isinstance(params, list):
                params = [params]
            func = [params, body, env]
            return func

        # class
        # ['class', class_name, parent, body]
        # --------------------------
        if exp[0] == "class":
            _, class_name, parent, body = exp
            parent_env = self.eval(parent, env)
            parent_env = parent_env or env
            class_env = Environment({}, parent_env)
            self._eval_body(body, class_env)
            return env.define(class_name, class_env)

        # class instance
        # ['new', class_name, args]
        # when call constructor(self, x), the self is the instance_env
        # ============================
        if exp[0] == "new":
            _, class_name, *args = exp
            class_env = env.lookup(class_name)
            # class_env = self.eval(class_name, env)
            evaluated_args = [self.eval(i, env) for i in args]
            instance_env = Environment({}, class_env)
            self._callUserDefinedFunction(
                class_env.lookup("constructor"), [instance_env, *evaluated_args]
            )
            return instance_env

        # class prop access
        # ['prop', instante, var_name]
        if exp[0] == "prop":
            _, instance, var_name = exp
            instance_env = self.eval(instance, env)
            return instance_env.lookup(var_name)

        # super instance
        # ['prop',['super',Point3D],'constructor']
        # --------------------------
        if exp[0] == "super":
            _, class_name = exp
            return self.eval(class_name, env).parent

        # module
        # ['module', module_name, body]
        # ---------------------------
        if exp[0] == "module":
            _, module_name, body = exp
            module_env = Environment({}, env)
            self._eval_body(body, module_env)
            return env.define(module_name, module_env)

        # import
        # ['import','Math']
        if exp[0] == "import":
            _, module_name = exp
            with open(f"./import/{module_name}", "r") as file:
                body_str = file.read().replace("\n", "")
                body = eval("['begin'," + body_str + "]")
                module_exp = ["module", module_name, body]
                return self.eval(module_exp, env)

        # function call
        # --------------------------
        if isinstance(exp, list):
            fn = self.eval(exp[0], env)
            args = [self.eval(i, env) for i in exp[1:]]
            # built-in func
            if callable(fn):
                fn(*args)
                return
            # user defined func
            return self._callUserDefinedFunction(fn, args)

        print(f"not inplemented {exp}")

    def _eval_block(self, exp, env):
        ret = None
        for i in exp[1:]:
            ret = self.eval(i, env)
        return ret

    def _eval_body(self, body, env):
        if body[0] == "begin":
            return self._eval_block(body, env)
        return self.eval(body, env)

    def _callUserDefinedFunction(self, fn, args):
        params, body, fn_env = fn
        activation_record = {}
        for idx, param in enumerate(params):
            activation_record[param] = args[idx]
        activation_env = Environment(activation_record, fn_env)  # static scope
        return self._eval_body(body, activation_env)
