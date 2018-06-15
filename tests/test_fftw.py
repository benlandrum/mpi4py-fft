from __future__ import print_function
from copy import copy
import six
import numpy as np
import scipy
import pyfftw
from mpi4py_fft import fftw
from time import time

abstol = dict(f=5e-4, d=1e-12, g=1e-14)

kinds = {'dst4': fftw.FFTW_RODFT11, # no scipy to compare with
         'dct4': fftw.FFTW_REDFT11, # no scipy to compare with
         'dst3': fftw.FFTW_RODFT01,
         'dct3': fftw.FFTW_REDFT01,
         'dct2': fftw.FFTW_REDFT10,
         'dst2': fftw.FFTW_RODFT10,
         'dct1': fftw.FFTW_REDFT00,
         'dst1': fftw.FFTW_RODFT00}

inv = {
    fftw.FFTW_RODFT11: fftw.FFTW_RODFT11,
    fftw.FFTW_REDFT11: fftw.FFTW_REDFT11,
    fftw.FFTW_RODFT01: fftw.FFTW_RODFT10,
    fftw.FFTW_REDFT01: fftw.FFTW_REDFT10,
    fftw.FFTW_RODFT10: fftw.FFTW_RODFT01,
    fftw.FFTW_REDFT10: fftw.FFTW_REDFT01,
    fftw.FFTW_RODFT00: fftw.FFTW_RODFT00,
    fftw.FFTW_REDFT00: fftw.FFTW_REDFT00
}

ds = {val: key for key, val in six.iteritems(kinds)}

def allclose(a, b):
    atol = abstol[a.dtype.char.lower()]
    return np.allclose(a, b, rtol=0, atol=atol)

def test_fftw():
    from itertools import product

    dims = (1, 2, 3)
    sizes = (7, 8, 9)
    types = 'fdg'
    fflags = (fftw.FFTW_MEASURE, fftw.FFTW_DESTROY_INPUT)
    iflags = (fftw.FFTW_MEASURE, fftw.FFTW_DESTROY_INPUT)

    for threads in (1, 2):
        for typecode in types:
            for dim in dims:
                for shape in product(*([sizes]*dim)):
                    allaxes = tuple(reversed(range(dim)))
                    for i in range(dim):
                        for j in range(i+1, dim):
                            axes = allaxes[i:j]
                            #print(shape, axes, typecode, threads)
                            # r2c - c2r
                            A = np.random.random(shape).astype(typecode)
                            outshape = list(copy(shape))
                            outshape[axes[-1]] = shape[axes[-1]]//2+1
                            input_array = np.zeros_like(A)
                            output_array = np.zeros(outshape, dtype=typecode.upper())
                            rfftn = fftw.rfftn(input_array, output_array, axes, threads, fflags)
                            B = rfftn(A)
                            BC = B.copy()
                            B2 = pyfftw.interfaces.numpy_fft.rfftn(A, axes=axes)
                            assert allclose(B, B2), np.linalg.norm(B-B2)
                            irfftn = fftw.irfftn(output_array.copy(), input_array.copy(), axes, threads, iflags)
                            A2 = irfftn(B, normalize_idft=True)
                            assert allclose(A, A2), np.linalg.norm(A-A2)
                            # Note that irfftn destroys input for
                            # multidimensional transform. Can be avoided using
                            # instead A2 = irfftn(B, implicit=False, normalize_idft=True)
                            hfftn = fftw.hfftn(output_array, input_array, axes, threads, fflags)
                            AC = hfftn(BC, implicit=False)
                            ihfftn = fftw.ihfftn(input_array.copy(), output_array.copy(), axes, threads, iflags)
                            A2 = ihfftn(AC, normalize_idft=True, implicit=False)
                            assert allclose(A2, BC), print(np.linalg.norm(A2-BC))

                            # c2c
                            C = np.random.random(shape).astype(typecode.upper())
                            input_array = np.zeros_like(C)
                            output_array = np.zeros_like(C)
                            fftn = fftw.fftn(input_array, output_array, axes, threads, fflags)
                            D = fftn(C)
                            ifftn = fftw.ifftn(output_array.copy(), input_array.copy(), axes, threads, iflags)
                            C2 = ifftn(D, normalize_idft=True)
                            assert allclose(C, C2), np.linalg.norm(C-C2)
                            D2 = pyfftw.interfaces.numpy_fft.fftn(C, axes=axes)
                            assert allclose(D, D2), np.linalg.norm(D-D2)

                            # r2r
                            input_array = np.zeros_like(A)
                            output_array = np.zeros_like(A)
                            for type in (1, 2, 3, 4):
                                dct = fftw.dct(input_array, output_array, axes, type, threads, fflags)
                                B = dct(A)
                                idct = fftw.idct(output_array.copy(), input_array.copy(), axes, type, threads, iflags)
                                A2 = idct(B, normalize_idft=True)
                                assert allclose(A, A2), np.linalg.norm(A-A2)
                                if typecode is not 'g' and not type is 4:
                                    B2 = scipy.fftpack.dctn(A, axes=axes, type=type)
                                    assert allclose(B, B2), np.linalg.norm(B-B2)

                                dst = fftw.dst(input_array, output_array, axes, type, threads, fflags)
                                B = dst(A)
                                idst = fftw.idst(output_array.copy(), input_array.copy(), axes, type, threads, iflags)
                                A2 = idst(B, normalize_idft=True)
                                assert allclose(A, A2), np.linalg.norm(A-A2)
                                if typecode is not 'g' and not type is 4:
                                    B2 = scipy.fftpack.dstn(A, axes=axes, type=type)
                                    assert allclose(B, B2), np.linalg.norm(B-B2)

                            # Different r2r transforms along all axes. Just pick
                            # any naxes transforms and compare with scipy
                            naxes = len(axes)
                            kds = np.random.randint(3, 11, size=naxes) # get naxes transforms
                            tsf = [ds[k] for k in kds]
                            T = fftw.FFT(input_array, output_array, axes=axes,
                                         kind=kds, threads=threads, flags=fflags)
                            C = T(A)
                            TI = fftw.FFT(output_array.copy(), input_array.copy(), axes=axes,
                                          kind=list([inv[kd] for kd in kds]),
                                          threads=threads, flags=iflags)

                            C2 = TI(C)
                            M = 1.0
                            for l, dd in enumerate(tsf):
                                if dd == 'dct1':
                                    M *= 2*(C.shape[axes[l]]-1)
                                elif dd == 'dst1':
                                    M *= 2*(C.shape[axes[l]]+1)
                                else:
                                    M *= 2*C.shape[axes[l]]
                            assert allclose(C2/M, A)
                            if typecode is not 'g' and not any(f in kds for f in (fftw.FFTW_RODFT11, fftw.FFTW_REDFT11)):
                                for m, ts in enumerate(tsf):
                                    A = eval('scipy.fftpack.'+ts[:-1])(A, axis=axes[m], type=int(ts[-1]))
                                assert allclose(C, A), np.linalg.norm(C-A)

    fftw.xfftn.export_wisdom('wisdom.dat')
    fftw.xfftn.import_wisdom('wisdom.dat')

if __name__ == '__main__':
    test_fftw()