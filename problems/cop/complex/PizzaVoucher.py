"""
See Problem freepizza in MiniZinc

Example of Execution:
  python3 PizzaVoucher.py -data=PizzaVoucher_pizza6.json
"""

from pycsp3 import *

prices, vouchers = data
pay, free = zip(*vouchers)
nPizzas, nVouchers = len(prices), len(pay)

# v[i] is the voucher used for the ith pizza. 0 means that no voucher is used.
# A negative (resp., positive) value i means that the ith pizza contributes to the the pay (resp., free) part of voucher |i|.
v = VarArray(size=nPizzas, dom=range(-nVouchers, nVouchers + 1))

# p[i] is the number of paid pizzas wrt the ith voucher
p = VarArray(size=nVouchers, dom=lambda i: {0, pay[i]})

# f[i] is the number of free pizzas wrt the ith voucher
f = VarArray(size=nVouchers, dom=lambda i: range(free[i] + 1))

satisfy(
    # counting paid pizzas
    [Count(v, value=-i - 1) == p[i] for i in range(nVouchers)],

    # counting free pizzas
    [Count(v, value=i + 1) == f[i] for i in range(nVouchers)],

    # a voucher, if used, must contribute to have at least one free pizza.
    [(f[i] == 0) == (p[i] != pay[i]) for i in range(nVouchers)],

    # a free pizza obtained with a voucher must be cheaper than any pizza paid wrt this voucher
    [If(v[i] < 0, Then=v[i] != -v[j]) for i in range(nPizzas) for j in range(nPizzas) if prices[i] < prices[j]]
)

minimize(
    # minimizing summed up costs of pizzas
    Sum((v[i] <= 0) * prices[i] for i in range(nPizzas))
)

annotate(decision=v)

""" Comments
1) do you think that [(f[i] == 0) == (p[i] != vouchers[i].payPart) for i in range(nVouchers)] is clearer?
"""
