def sumTo(n, acc):
    if n == 0:
        return acc
    else:
        return sumTo(n - 1, acc + n)


def sum_to(n):
    if n == 0:
        return 0
    else:
        return n + sum_to(n - 1)
