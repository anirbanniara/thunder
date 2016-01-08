import pytest
import os
import glob
import json
from numpy import arange, allclose

from thunder.images.readers import fromlist, fromarray, frompng, fromtif, frombinary, fromexample

pytestmark = pytest.mark.usefixtures("eng")

resources = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'resources')


def test_from_list(eng):
    a = arange(8).reshape((2, 4))
    data = fromlist([a], engine=eng)
    assert allclose(data.shape, (1,) + a.shape)
    assert allclose(data.dims, a.shape)
    assert allclose(data.toarray(), a)


def test_from_array(eng):
    a = arange(8).reshape((1, 2, 4))
    data = fromarray(a, engine=eng)
    assert allclose(data.shape, a.shape)
    assert allclose(data.dims, a.shape[1:])
    assert allclose(data.toarray(), a)


def test_from_png(eng):
    path = os.path.join(resources, 'singlelayer_png', 'dot1_grey.png')
    data = frompng(path, engine=eng)
    assert allclose(data.shape, (1, 70, 75))
    assert allclose(data.toarray().shape, (70, 75))
    assert allclose(data.toarray().max(), 239)
    assert allclose(data.toarray().min(), 1)


def test_from_tif():
    path = os.path.join(resources, "singlelayer_tif", "dot1_grey_lzw.tif")
    data = fromtif(path)
    assert allclose(data.shape, (1, 70, 75))
    assert allclose(data.toarray().shape, (70, 75))
    assert allclose(data.toarray().max(), 239)
    assert allclose(data.toarray().min(), 1)


def test_from_tif_many():
    path = os.path.join(resources, "singlelayer_tif", "dot*_grey_lzw.tif")
    data = fromtif(path)
    assert allclose(data.shape, (3, 70, 75))
    assert allclose(data.toarray().shape, (3, 70, 75))
    assert [x.sum() for x in data.toarray()] == [1233881, 1212169, 1191300]


def test_from_tif_multi_lzw():
    path = os.path.join(resources, 'multilayer_tif', 'dotdotdot_lzw.tif')
    data = fromtif(path)
    val = data.toarray()
    assert allclose(data.shape, (1, 70, 75, 3))
    assert allclose(data.toarray().shape, (70, 75, 3))
    assert [val[:, :, i].sum() for i in range(3)] == [1140006, 1119161, 1098917]


def test_from_tif_multi_float():
    path = os.path.join(resources, 'multilayer_tif', 'dotdotdot_float32.tif')
    data = fromtif(path)
    val = data.toarray()
    assert allclose(data.shape, (1, 70, 75, 3))
    assert allclose(data.toarray().shape, (70, 75, 3))
    assert [val[:, :, i].sum() for i in range(3)] == [1140006, 1119161, 1098917]


def test_from_tif_multi_planes():
    path = os.path.join(resources, 'multilayer_tif', 'dotdotdot_lzw.tif')
    data = fromtif(path, nplanes=3)
    assert data.shape[0] == 1
    data = fromtif(path, nplanes=1)
    assert data.shape[0] == 3
    assert allclose(data.toarray().shape, (3, 70, 75))
    assert [x.sum() for x in data.toarray()] == [1140006, 1119161, 1098917]


def test_from_tif_multi_planes_many():
    path = os.path.join(resources, 'multilayer_tif', 'dotdotdot_lzw*.tif')
    data = fromtif(path, nplanes=3)
    assert data.shape[0] == 2
    assert allclose(data.shape, (2, 70, 75, 3))
    assert allclose(data.toarray().shape, (2, 70, 75, 3))
    data = fromtif(path, nplanes=1)
    assert data.shape[0] == 6
    assert allclose(data.shape, (6, 70, 75))
    assert allclose(data.toarray().shape, (6, 70, 75))
    assert [x.sum() for x in data.toarray()] == [1140006, 1119161, 1098917, 1140006, 1119161, 1098917]


def test_from_tif_signed():
    path = os.path.join(resources, 'multilayer_tif', 'test_signed.tif')
    data = fromtif(path, nplanes=1)
    assert data.dtype == 'int16'
    assert allclose(data.toarray().shape, (2, 120, 120))
    assert [x.sum() for x in data.toarray()] == [1973201, 2254767]


def test_from_binary(tmpdir):
    a = arange(8, dtype='int16').reshape((2, 4))
    a.tofile(os.path.join(str(tmpdir), 'test.bin'))
    data = frombinary(str(tmpdir), dims=(2, 4), dtype='int16')
    assert data.dtype == 'int16'
    assert allclose(data.shape, (1, 2, 4))
    assert allclose(data.toarray(), a)


def test_from_binary_many(tmpdir):
    a = [arange(8, dtype='int16').reshape((2, 4)), arange(8, 16, dtype='int16').reshape((2, 4))]
    a[0].tofile(os.path.join(str(tmpdir), 'test0.bin'))
    a[1].tofile(os.path.join(str(tmpdir), 'test1.bin'))
    data = frombinary(str(tmpdir), dims=(2, 4), dtype='int16')
    assert data.dtype == 'int16'
    assert allclose(data.shape, (2, 2, 4))
    assert allclose(data.toarray(), a)


def test_from_binary_conf(tmpdir):
    a = [arange(8, dtype='int32').reshape((2, 4)), arange(8, 16, dtype='int32').reshape((2, 4))]
    a[0].tofile(os.path.join(str(tmpdir), 'test0.bin'))
    a[1].tofile(os.path.join(str(tmpdir), 'test1.bin'))
    with open(os.path.join(str(tmpdir), 'conf.json'), 'w') as f:
        json.dump({'dims': [2, 4], 'dtype': 'int32'}, f)
    data = frombinary(str(tmpdir))
    assert data.dtype == 'int32'
    assert allclose(data.shape, (2, 2, 4))
    assert allclose(data.toarray(), a)


def test_from_binary_multi(tmpdir):
    a = arange(24, dtype='int16').reshape((2, 3, 4))
    a.tofile(os.path.join(str(tmpdir), 'test.bin'))
    data = frombinary(str(tmpdir), dims=(2, 3, 4), dtype='int16')
    assert data.dtype == 'int16'
    assert allclose(data.shape, (1, 2, 3, 4))
    assert allclose(data.toarray(), a)


def test_from_binary_multi_planes_many(tmpdir):
    a = [arange(16, dtype='int16').reshape((4, 2, 2)), arange(16, 32, dtype='int16').reshape((4, 2, 2))]
    a[0].tofile(os.path.join(str(tmpdir), 'test0.bin'))
    a[1].tofile(os.path.join(str(tmpdir), 'test1.bin'))
    data = frombinary(str(tmpdir), dims=(4, 2, 2), dtype='int16', nplanes=2)
    assert allclose(data.shape, (2, 4, 2, 2))
    assert allclose(data.toarray().shape, (2, 4, 2, 2))
    data = frombinary(str(tmpdir), dims=(4, 2, 2), dtype='int16', nplanes=1)
    assert allclose(data.shape, (4, 4, 2))
    assert allclose(data.toarray().shape, (4, 4, 2))


def test_to_binary(tmpdir):
    a = [arange(8, dtype='int16').reshape((4, 2)), arange(8, 16, dtype='int16').reshape((4, 2))]
    fromlist(a).tobinary(os.path.join(str(tmpdir), 'binary'), prefix='image')
    files = [os.path.basename(f) for f in glob.glob(str(tmpdir) + '/binary/image*')]
    f = open(str(tmpdir) + '/binary/conf.json', 'r')
    conf = json.load(f)
    f.close()
    assert sorted(files) == ['image-00000.bin', 'image-00001.bin']
    assert conf['dims'] == [4, 2]
    assert conf['dtype'] == 'int16'


def test_to_binary_roundtrip(tmpdir):
    a = [arange(8).reshape((4, 2)), arange(8, 16).reshape((4, 2))]
    data = fromlist(a)
    data.tobinary(os.path.join(str(tmpdir), 'images'))
    loaded = frombinary(os.path.join(str(tmpdir), 'images'))
    assert allclose(data.toarray(), loaded.toarray())


def test_to_binary_roundtrip_3d(tmpdir):
    a = [arange(24).reshape((2, 3, 4)), arange(24, 48).reshape((2, 3, 4))]
    data = fromlist(a)
    data.tobinary(os.path.join(str(tmpdir), 'images'))
    loaded = frombinary(os.path.join(str(tmpdir), 'images'))
    assert allclose(data.toarray(), loaded.toarray())


def test_to_png(tmpdir, eng):
    a = [arange(8, dtype='int16').reshape((4, 2)), arange(8, 16, dtype='int16').reshape((4, 2))]
    fromlist(a, engine=eng).topng(os.path.join(str(tmpdir), 'images'), prefix='image')
    files = [os.path.basename(f) for f in glob.glob(str(tmpdir) + '/images/image*')]
    assert sorted(files) == ['image-00000.png', 'image-00001.png']


def test_to_png_roundtrip(tmpdir, eng):
    a = [arange(8, dtype='uint8').reshape((4, 2))]
    data = fromlist(a, engine=eng)
    data.topng(os.path.join(str(tmpdir), 'images'), prefix='image')
    loaded = frompng(os.path.join(str(tmpdir), 'images'))
    assert allclose(data.toarray(), loaded.toarray())


def test_to_tif(tmpdir, eng):
    a = [arange(8, dtype='int16').reshape((4, 2)), arange(8, 16, dtype='int16').reshape((4, 2))]
    fromlist(a, engine=eng).totif(os.path.join(str(tmpdir), 'images'), prefix='image')
    files = [os.path.basename(f) for f in glob.glob(str(tmpdir) + '/images/image*')]
    assert sorted(files) == ['image-00000.tif', 'image-00001.tif']


def test_to_tif_roundtrip(tmpdir, eng):
    a = [arange(8, dtype='uint8').reshape((4, 2))]
    data = fromlist(a, engine=eng)
    data.totif(os.path.join(str(tmpdir), 'images'), prefix='image')
    loaded = fromtif(os.path.join(str(tmpdir), 'images'))
    assert allclose(data.toarray(), loaded.toarray())


def test_fromexample(eng):
    data = fromexample('fish', engine=eng)
    assert allclose(data.shape, (20, 76, 87, 2))
    data = fromexample('mouse', engine=eng)
    assert allclose(data.shape, (20, 64, 64))