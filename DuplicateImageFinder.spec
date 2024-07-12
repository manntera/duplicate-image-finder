import os
import glob
from PyInstaller.utils.hooks import collect_dynamic_libs
from PyInstaller.building.build_main import Tree
import cupy

# CUDA パスを指定
cuda_path = os.environ.get('CUDA_PATH', r'C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.5')
# CuPy パッケージのパスを指定
cupy_path = os.path.dirname(cupy.__file__)
# CuPy _core パスを指定
cupy_core_path = os.path.join(cupy_path, '_core')

# CuPy _core パスが存在するか確認
if not os.path.exists(cupy_core_path):
    raise FileNotFoundError(f"CuPy core path does not exist: {cupy_core_path}")

# Collect all dynamic libraries related to cupy and CUDA
binary_files = [
    (os.path.join(cuda_path, 'bin', 'cudnn64_8.dll'), '.'),
    (os.path.join(cuda_path, 'bin', 'cuTENSOR.dll'), '.')
]

cupy_dlls = glob.glob(os.path.join(cupy_path, 'cupy_backends', 'cuda', 'libs', '*.dll'))
binary_files.extend([(dll, '.') for dll in cupy_dlls])

# Adding all dynamic libraries for cupy
binary_files.extend(collect_dynamic_libs('cupy'))

a = Analysis(
    ['src\\main.py'],
    pathex=[],
    binaries=binary_files,
    datas=[],
    hiddenimports=[
        'cupy_backends.cuda.stream',
        'fastrlock',
        'fastrlock.rlock',
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
        'cupy_backends.cuda.api.driver',
        'cupy_backends.cuda.api._driver_enum',
        'cupy.cuda.common',
        'cupy.cuda.cub',
        'cupy.cuda.memory',
        'cupy.cuda.stream',
        'cupy.cuda.graph',
        'cupy_backends.cuda._softlink',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# Add the necessary tree structure for CuPy core
if os.path.exists(cupy_core_path):
    a.datas += Tree(
        cupy_core_path,
        'cupy/_core',
        excludes=[
            '_accelerator.cp310-win_amd64.pyd',
            '_dtype.cp310-win_amd64.pyd',
            '_fusion_thread_local.cp310-win_amd64.pyd',
            '_kernel.cp310-win_amd64.pyd',
            '_memory_range.cp310-win_amd64.pyd',
            '_optimize_config.cp310-win_amd64.pyd',
            '_reduction.cp310-win_amd64.pyd',
            '_routines_binary.cp310-win_amd64.pyd',
            '_routines_indexing.cp310-win_amd64.pyd',
            '_routines_linalg.cp310-win_amd64.pyd',
            '_routines_logic.cp310-win_amd64.pyd',
            '_routines_manipulation.cp310-win_amd64.pyd',
            '_routines_math.cp310-win_amd64.pyd',
            '_routines_statistics.cp310-win_amd64.pyd',
            '_scalar.cp310-win_amd64.pyd',
            'core.cp310-win_amd64.pyd',
            'dlpack.cp310-win_amd64.pyd',
            'fusion.cp310-win_amd64.pyd',
            'internal.cp310-win_amd64.pyd',
            'raw.cp310-win_amd64.pyd'
        ]
    )
else:
    print(f"Error: The path {cupy_core_path} does not exist.")

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
