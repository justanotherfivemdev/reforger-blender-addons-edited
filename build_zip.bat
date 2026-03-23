@echo off
:: Builds installable zips for all multi-file plugins and the all-in-one release.
:: Run from the repo root: build_zip.bat
:: Requires Python to be installed and available on PATH.

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%plugins"

python -c "
import sys, zipfile, os

def build_zip(name):
    zip_path = name + '.zip'
    if os.path.exists(zip_path):
        os.remove(zip_path)
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(name):
            dirs[:] = [d for d in dirs if d != '__pycache__']
            for f in files:
                if not f.endswith('.pyc'):
                    p = os.path.join(root, f)
                    zf.write(p, p.replace(os.sep, '/'))
    print('Built plugins/' + zip_path)

build_zip('bk_arma_tools')
build_zip('bk_weight_gradient')
build_zip('bk_nla_automation')
build_zip('bk_weapon_rig_replacer')
build_zip('bk_fbx_exporter')
build_zip('bk_animation_export_profile')
build_zip('bk_crater_generator')
build_zip('bk_character_gear')
"

cd /d "%SCRIPT_DIR%"

python -c "
import zipfile, os
src = 'release/bk_reforger_addons'
out = 'release/bk_reforger_addons.zip'
with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as zf:
    for root, dirs, files in os.walk(src):
        dirs[:] = [d for d in dirs if d != '__pycache__']
        for f in sorted(files):
            if not f.endswith('.pyc'):
                p = os.path.join(root, f)
                arcname = os.path.relpath(p, 'release').replace(os.sep, '/')
                zf.write(p, arcname)
print('Built release/bk_reforger_addons.zip')
"
