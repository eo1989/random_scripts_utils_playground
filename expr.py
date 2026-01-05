eg_string = "((1 + 2) * (3 - 4))"
eg_expr = ["Mul", ["Add", 1, 2], ["Sub", 3, 4]]


def evalExpr(expr):
    match expr:
        case int() as n:
            return n
        case ["Add", a, b]:
            return evalExpr(a) + evalExpr(b)
        case ["Sub", a, b]:
            return evalExpr(a) - evalExpr(b)
        case ["Mul", a, b]:
            return evalExpr(a) * evalExpr(b)
        case ["Div", a, b]:
            return evalExpr(a) / evalExpr(b)
    raise RuntimeError("whatchu doin man?!")
