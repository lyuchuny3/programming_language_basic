# definition of environment
###############################
# environment is a repository of variables and functions defined in a scope.
# if someone ask you can you give me the value of x, you should ask in which scope/env?

# environment api
#######################
# - define a var                       (var x 10)
# - assign/update a new value to var   (set x 5)
# - loopup a var                       (x)

# environment structure
#######################
# record {var:value}
# parent (optional)


class Environment:
    def __init__(self, record={}, parent=None):
        self.record = record
        self.parent = parent

    def define(self, var, value):
        self.record[var] = value
        return value

    def assign(self, var, value):
        env = self.resolve(var)
        env.record[var] = value
        return value

    def lookup(self, var):
        # after resolve, may be curr_env/global_env
        env = self.resolve(var)
        return env.record[var]

    def resolve(self, var):
        #  return current_env /parant_env/NotDefined!
        if var in self.record:
            return self
        if self.parent is None:
            raise ValueError(f"Variable '{var}' is not defined.")
        return self.parent.resolve(var)
