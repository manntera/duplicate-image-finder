from PyInstaller.utils.hooks import copy_metadata, collect_dynamic_libs, collect_data_files

# Copy metadata
datas = copy_metadata('cupy')

# Collect dynamic libraries
binaries = collect_dynamic_libs('cupy')

# Collect data files
datas += collect_data_files('cupy')
