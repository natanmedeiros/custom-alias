#!/bin/bash
set -e

# Version
VERSION="0.1.0"
PACKAGE_NAME="dynamic-alias"
IDENTIFIER="com.natanmedeiros.dynamic-alias"

# Directories
BUILD_DIR="build_macos"
ROOT_DIR="$BUILD_DIR/root"
SCRIPTS_DIR="$BUILD_DIR/scripts"
OUTPUT_DIR="dist"

# Cleanup
rm -rf "$BUILD_DIR"
mkdir -p "$ROOT_DIR" "$SCRIPTS_DIR" "$OUTPUT_DIR"

# Build Wheel
echo "Building Python Wheel..."
python3 -m build

# Install to Root
echo "Installing to temporary root..."
pip3 install dist/*.whl --root "$ROOT_DIR" --ignore-installed --prefix=/usr/local

# Fix paths in scripts if necessary (e.g. #!/usr/bin/python3)
# Note: MacOS python location might vary.

# Create Component Package
echo "Creating Component Package..."
pkgbuild --root "$ROOT_DIR" \
    --identifier "$IDENTIFIER" \
    --version "$VERSION" \
    --install-location "/" \
    "$BUILD_DIR/extract.pkg"

# Create Distribution Package
echo "Creating Distribution Package..."
productbuild --distribution packaging/macos/scripts/distribution.xml \
    --resources packaging/macos/resources \
    --package-path "$BUILD_DIR" \
    "$OUTPUT_DIR/$PACKAGE_NAME-$VERSION.pkg"

echo "Done. Package is at $OUTPUT_DIR/$PACKAGE_NAME-$VERSION.pkg"
