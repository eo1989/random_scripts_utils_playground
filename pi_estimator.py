import matplotlib.pyplot as plt
import numpy as np

rng = np.random.default_rng(42)


def pi_est(radius=1, num_iter: int = int(1e4)) -> None:
    """

    Parameters
    ----------
    radius : float
        distance from the center to the edge of the circle,
        default: 1
    num_iter : int
        number of iterations
        default: 1e4 = 10_000.

    """
    X = rng.uniform(-radius, radius, num_iter)
    Y = rng.uniform(-radius, radius, num_iter)
    R2 = X**2 + Y**2

    inside = R2 < radius**2
    outside = ~inside

    # samples = (2 * radius) * (2 * radius) * inside
    samples = (2 * radius) ** 2 * inside  # noqa
    I_hat = np.mean(samples)

    pi_hat = I_hat / radius**2  # <- Pi estimate
    pi_hat_se = np.std(samples) / np.sqrt(num_iter)  # <- Pi stdev

    print(f"Pi est: {pi_hat} ± {pi_hat_se:.5f}")

    plt.figure().sca
    plt.scatter(X[inside], Y[inside], c="b", alpha=0.5)
    plt.scatter(X[outside], Y[outside], c="r", alpha=0.5)
    plt.show()


if __name__ == "__main__":
    pi_est()
