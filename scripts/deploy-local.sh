#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source_dir="${repo_root}/custom_components/pool_assistant"
target_config_dir="${1:-${HA_CONFIG_DIR:-../ha-config}}"
target_dir="${repo_root}/${target_config_dir}/custom_components/pool_assistant"

if [[ ! -d "${source_dir}" ]]; then
  echo "Source directory not found: ${source_dir}" >&2
  exit 1
fi

mkdir -p "$(dirname "${target_dir}")"
rm -rf "${target_dir}"
mkdir -p "${target_dir}"

tar \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  -C "${source_dir}" \
  -cf - . | tar -C "${target_dir}" -xf -

echo "Deployed Pool Assistant to ${target_dir}"
