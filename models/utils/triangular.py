from functools import partial

import jax
import jax.numpy as jnp
from jax import Array, lax
from jax.typing import ArrayLike

from .continuousrv import ContinuousRV


class Triangular(ContinuousRV):

    def __init__(self, low: ArrayLike = 0, high: ArrayLike = 1, mode: ArrayLike = 0.5, name: str = None) -> None:
        self._low = low
        self._mode = mode
        self._high = high
        self.check_params()
        super().__init__(name)

    def check_params(self) -> None:
        assert jnp.all(self._low <= self._high), "low must be less than or equal to high"
        assert jnp.all(self._low <= self._mode), "low must be less than or equal to mid"
        assert jnp.all(self._mode <= self._high), "mid must be less than or equal to high"

    @partial(jax.jit, static_argnums=(0,))
    def logpdf(self, x: ArrayLike) -> ArrayLike:
        logpdf_val = jnp.where(x < self._low, -jnp.inf, x)
        logpdf_val = jnp.where(
            (self._low <= x) & (x < self._mode),
            jnp.log(2) + jnp.log(x - self._low) - jnp.log(self._high - self._low) - jnp.log(self._mode - self._low),
            logpdf_val)
        logpdf_val = jnp.where(x == self._mode, jnp.log(2) - jnp.log(self._high - self._low), logpdf_val)
        logpdf_val = jnp.where(
            (self._mode < x) & (x <= self._high),
            jnp.log(2) + jnp.log(self._high - x) - jnp.log(self._high - self._low) - jnp.log(self._high - self._mode),
            logpdf_val)
        logpdf_val = jnp.where(x > self._high, -jnp.inf, logpdf_val)
        return logpdf_val

    @partial(jax.jit, static_argnums=(0,))
    def logcdf(self, x: ArrayLike) -> ArrayLike:
        logcdf_val = jnp.where(x < self._low, -jnp.inf, x)
        logcdf_val = jnp.where(
            (self._low <= x) & (x < self._mode),
            2 * jnp.log(x - self._low) - jnp.log(self._high - self._low) - jnp.log(self._mode - self._low), logcdf_val)
        logcdf_val = jnp.where(
            x == self._mode,
            jnp.log(0.5),
            logcdf_val,
        )
        logcdf_val = jnp.where(
            (self._mode < x) & (x < self._high),
            jnp.log(1 - ((self._high - x)**2 / ((self._high - self._low) * (self._high - self._mode)))),
            logcdf_val,
        )
        logcdf_val = jnp.where(x >= self._high, jnp.log(1), logcdf_val)
        return logcdf_val

    @partial(jax.jit, static_argnums=(0,))
    def cdfinv(self, x: ArrayLike) -> ArrayLike:
        _Fc = self.cdf(self._mode)
        cdfinv_val = jnp.where(
            x < _Fc,
            self._low + lax.sqrt(x * (self._mode - self._low) * (self._high - self._low)),
            self._high - lax.sqrt((1 - x) * (self._high - self._low) * (self._high - self._mode)),
        )
        return cdfinv_val

    def rvs(self, N: int = 1) -> Array:
        return jax.random.triangular(self.get_key(), left=self._low, right=self._high, mode=self._mode, shape=(N,))

    def __repr__(self) -> str:
        string = f"Triangular(low={self._low}, mode={self._mode}, high={self._high}"
        if self._name is not None:
            string += f", name={self._name}"
        return string + ")"
