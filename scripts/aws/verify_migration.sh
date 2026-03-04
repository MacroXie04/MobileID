#!/usr/bin/env bash
exec "$(dirname "$0")/../../infra/aws/$(basename "$0")" "$@"
