from taichi.core.util import ti_core as _ti_core
from taichi.lang.impl import expr_init

import taichi as ti


@ti.func
def polar_decompose2d(a, dt):
    x, y = a(0, 0) + a(1, 1), a(1, 0) - a(0, 1)
    scale = (1.0 / ti.sqrt(x * x + y * y))
    c = x * scale
    s = y * scale
    r = ti.Matrix([[c, -s], [s, c]])
    return r, r.transpose() @ a


@ti.func
def polar_decompose3d(A, dt):
    U, sig, V = ti.svd(A, dt)
    return U @ V.transpose(), V @ sig @ V.transpose()


# https://www.seas.upenn.edu/~cffjiang/research/svd/svd.pdf
@ti.func
def svd2d(A, dt):
    R, S = polar_decompose2d(A, dt)
    c, s = ti.cast(0.0, dt), ti.cast(0.0, dt)
    s1, s2 = ti.cast(0.0, dt), ti.cast(0.0, dt)
    if abs(S[0, 1]) < 1e-5:
        c, s = 1, 0
        s1, s2 = S[0, 0], S[1, 1]
    else:
        tao = ti.cast(0.5, dt) * (S[0, 0] - S[1, 1])
        w = ti.sqrt(tao**2 + S[0, 1]**2)
        t = ti.cast(0.0, dt)
        if tao > 0:
            t = S[0, 1] / (tao + w)
        else:
            t = S[0, 1] / (tao - w)
        c = 1 / ti.sqrt(t**2 + 1)
        s = -t * c
        s1 = c**2 * S[0, 0] - 2 * c * s * S[0, 1] + s**2 * S[1, 1]
        s2 = s**2 * S[0, 0] + 2 * c * s * S[0, 1] + c**2 * S[1, 1]
    V = ti.Matrix.zero(dt, 2, 2)
    if s1 < s2:
        tmp = s1
        s1 = s2
        s2 = tmp
        V = [[-s, c], [-c, -s]]
    else:
        V = [[c, s], [-s, c]]
    U = R @ V
    return U, ti.Matrix([[s1, ti.cast(0, dt)], [ti.cast(0, dt), s2]]), V


def svd3d(A, dt, iters=None):
    assert A.n == 3 and A.m == 3
    inputs = tuple([e.ptr for e in A.entries])
    assert dt in [ti.f32, ti.f64]
    if iters is None:
        if dt == ti.f32:
            iters = 5
        else:
            iters = 8
    if dt == ti.f32:
        rets = _ti_core.sifakis_svd_f32(*inputs, iters)
    else:
        rets = _ti_core.sifakis_svd_f64(*inputs, iters)
    assert len(rets) == 21
    U_entries = rets[:9]
    V_entries = rets[9:18]
    sig_entries = rets[18:]
    U = expr_init(ti.Matrix.zero(dt, 3, 3))
    V = expr_init(ti.Matrix.zero(dt, 3, 3))
    sigma = expr_init(ti.Matrix.zero(dt, 3, 3))
    for i in range(3):
        for j in range(3):
            U(i, j).assign(U_entries[i * 3 + j])
            V(i, j).assign(V_entries[i * 3 + j])
        sigma(i, i).assign(sig_entries[i])
    return U, sigma, V


@ti.func
def svd(A, dt):
    if ti.static(A.n == 2):
        ret = svd2d(A, dt)
        return ret
    elif ti.static(A.n == 3):
        return svd3d(A, dt)
    else:
        raise Exception("SVD only supports 2D and 3D matrices.")


@ti.func
def polar_decompose(A, dt):
    if ti.static(A.n == 2):
        ret = polar_decompose2d(A, dt)
        return ret
    elif ti.static(A.n == 3):
        return polar_decompose3d(A, dt)
    else:
        raise Exception(
            "Polar decomposition only supports 2D and 3D matrices.")
