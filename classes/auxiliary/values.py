class SymbolicValue:
    def __init__(self, value):
        self.value = value

    def __eq__(self, other):
        return self.value == other.value if isinstance(other, SymbolicValue) else False

    def __lt__(self, other):
        assert isinstance(other, SymbolicValue)
        return self.value < other.value

    def __contains__(self, v):
        return v == self.value

    def __repr__(self):
        return str(self.value)


class IntegerEntity:
    def smallest(self):
        pass

    def greatest(self):
        pass

    def width(self):
        pass


class IntegerValue(IntegerEntity):
    def __init__(self, value):
        self.value = value

    def smallest(self):
        return self.value

    def greatest(self):
        return self.value

    def width(self):
        return 1

    def to_list(self):
        return [self.value]

    def __eq__(self, other):
        return self.value == other.value if isinstance(other, IntegerValue) else False

    def __lt__(self, other):
        assert isinstance(other, IntegerValue)
        return self.value < other.value

    def __contains__(self, v):
        return v == self.value

    def __repr__(self):
        return str(self.value)


class IntegerInterval(IntegerEntity):
    def __init__(self, inf, sup):
        assert inf < sup
        self.inf = inf
        self.sup = sup
        self.width = float('inf') if inf == float('-inf') or sup == float('inf') else sup + 1 - inf

    def smallest(self):
        return self.inf

    def greatest(self):
        return self.sup

    def width(self):
        return self.width

    def to_list(self):
        return [v for v in range(self.inf, self.sup + 1)]

    def is_binary(self):
        return self.inf == 0 and self.sup == 1

    def __iter__(self):
        return self.to_list().__iter__()

    def __getitem__(self, item):
        return self.to_list().__getitem__(item)

    def __eq__(self, other):
        return self.inf == other.inf and self.sup == other.sup if isinstance(other, IntegerInterval) else False

    def __lt__(self, other):
        assert isinstance(other, IntegerInterval)
        return self.sup <= other.inf

    def __contains__(self, v):
        return self.inf <= v <= self.sup

    def __repr__(self):
        return str(self.inf) + ".." + str(self.sup)
