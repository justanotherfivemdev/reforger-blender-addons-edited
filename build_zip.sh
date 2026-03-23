#!/bin/bash
# Builds installable zips for all multi-file plugins and the all-in-one release.
# Run from the repo root: ./build_zip.sh
# Uses 'zip' if available, otherwise falls back to Python (cross-platform).

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR/plugins"

build_zip() {
    local name="$1"
    rm -f "${name}.zip"
    if command -v zip &>/dev/null; then
        zip -r "${name}.zip" "${name}/" -x "${name}/__pycache__/*" "${name}/**/__pycache__/*"
    else
        python3 -c "
import zipfile, os
src='${name}'
with zipfile.ZipFile('${name}.zip', 'w', zipfile.ZIP_DEFLATED) as zf:
    for root, dirs, files in os.walk(src):
        dirs[:] = [d for d in dirs if d != '__pycache__']
        for f in files:
            if not f.endswith('.pyc'):
                p = os.path.join(root, f)
                zf.write(p, p.replace(os.sep, '/'))
"
    fi
    echo "Built plugins/${name}.zip"
}

build_zip bk_arma_tools
build_zip bk_weight_gradient
build_zip bk_nla_automation
build_zip bk_weapon_rig_replacer
build_zip bk_fbx_exporter
build_zip bk_animation_export_profile
build_zip bk_crater_generator

# Build the all-in-one release zip from the release directory
cd "$SCRIPT_DIR"
python3 -c "
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
