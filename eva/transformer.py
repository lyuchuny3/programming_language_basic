# AST Transformer


class Transformer:
    def __init__(self):
        pass

    def transformDefToVarLambda(self, def_exp):
        def_tag, fname, params, body = def_exp
        return ["var", fname, ["lambda", params, body]]

    def transformSwitchToIfexp(self, exp):
        switch_tag, *condtions = exp
        length = len(condtions)
        if_exp = ["if", None, None, None]
        current = if_exp
        for i in range(length - 1):
            curr_cond, curr_block = condtions[i]
            current[1] = curr_cond
            current[2] = curr_block

            next_cond, next_block = condtions[i + 1]
            if next_cond == "else":
                current[3] = next_block
            else:
                current[3] = ["if", None, None, None]
            current = current[3]
        return if_exp

    def transformForToWhile(self, for_exp):
        for_tag, init, end_cond, update, body = for_exp

        stmt = ["begin", init, ["while", end_cond, ["begin", body, update]]]
        return stmt

    def transformIncToSet(self, inc_exp):
        tag, var = inc_exp
        assert tag == "++"
        return ["set", var, ["+", var, 1]]

    def transformDecToSet(self, inc_exp):
        tag, var = inc_exp
        assert tag == "--"
        return ["set", var, ["-", var, 1]]

    def transformIncValToSet(self, inc_exp):
        tag, var, value = inc_exp
        assert tag == "+="
        return ["set", var, ["+", var, value]]

    def transformDecValToSet(self, inc_exp):
        tag, var, value = inc_exp
        assert tag == "-="
        return ["set", var, ["-", var, value]]

