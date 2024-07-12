import os
import site
import glob
from PyInstaller.utils.hooks import collect_dynamic_libs

cuda_path = os.environ.get('CUDA_PATH', r'C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.5')
site_packages = site.getsitepackages()[0]
cupy_backend_cuda_libs = os.path.join(site_packages, 'cupy_backends', 'cuda', 'libs')

# Collect all dynamic libraries related to cupy and CUDA
binary_files = [
    (os.path.join(cuda_path, 'bin', 'cudnn64_8.dll'), '.'),
    (os.path.join(cuda_path, 'bin', 'cuTENSOR.dll'), '.')
]

cupy_dlls = glob.glob(os.path.join(cupy_backend_cuda_libs, '*.dll'))
binary_files.extend([(dll, '.') for dll in cupy_dlls])

# Adding all dynamic libraries for cupy
binary_files.extend(collect_dynamic_libs('cupy'))

a = Analysis(
    ['src\\main.py'],
    pathex=[],
    binaries=binary_files,
    datas=[],
    hiddenimports=[
        'cupy',
        'cupy_backends.cuda._softlink',
        'cupy_backends.cuda.api._runtime_enum',
        'cupy._core._carray',
        'cupy._core._dtype',
        'cupy._core._scalar',
        'cupy._core._ufunc',
        'cupy._core._ufuncs',
        'cupy._core._kernel',
        'cupy._core._cub_reduction',
        'cupy._core._reduction',
        'cupy._core._routines_manipulation',
        'cupy._core._routines_math',
        'cupy._core._routines_sorting',
        'cupy.cuda.function',
        'cupy.cuda.device',
        'cupy.cuda.compiler',
        'fastrlock',
        'fastrlock.rlock',
        'cupy_backends.cuda.stream',
        'cupy_backends.cuda.api.driver',
        'cupy_backends.cuda.api._driver_enum',
        'cupy.cuda.common',
        'cupy.cuda.cub',
        'cupy.cuda.memory',
        'cupy.cuda.stream',
        'cupy.cuda.graph',
    ],
    hookspath=['hooks'],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='DuplicateImageFinder',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
