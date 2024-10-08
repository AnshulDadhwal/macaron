#!/usr/bin/env bash

# Copyright (c) 2024 - 2024, Oracle and/or its affiliates. All rights reserved.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/.

# This script checks the Verification Summary Attestation generated by Macaron.

# Strict bash options.
#
# -e:          exit immediately if a command fails (with non-zero return code),
#              or if a function returns non-zero.
#
# -u:          treat unset variables and parameters as error when performing
#              parameter expansion.
#              In case a variable ${VAR} is unset but we still need to expand,
#              use the syntax ${VAR:-} to expand it to an empty string.
#
# -o pipefail: set the return value of a pipeline to the value of the last
#              (rightmost) command to exit with a non-zero status, or zero
#              if all commands in the pipeline exit successfully.
#
# Reference: https://www.gnu.org/software/bash/manual/html_node/The-Set-Builtin.html.
set -euo pipefail

# Log error (to stderr).
log_err() {
    echo "[ERROR]: $*" >&2
}

# Print usage message.
print_help() {
    cat << EOF
Usage: $(basename "$0") [OPTIONS]

This script checks the Verification Summary Attestation (VSA) generated by Macaron.

Options:
  --artifact-path PATH   Path to the artifact file.
  --vsa-path PATH        Path to the Verification Summary Attestation (VSA) file.
  --purl URL             Package URL to match against the VSA.
  --help, -h             Display this help message and exit.

Examples:
  $(basename "$0") --artifact-path /path/to/artifact --vsa-path /path/to/vsa --purl "package-url"

EOF
}

# Assert that a file exists.
#
# Arguments:
#   $1: The path to the file.
#   $2: The argument from which the file is passed into this script.
#
# With the `set -e` option turned on, this function exits the script with
# return code 1 if the file does not exist.
function assert_file_exists() {
    if [[ ! -f "$1" ]]; then
        log_err "File $1 does not exist."
        return 1
    fi
}

# Parse main arguments.
while [[ $# -gt 0 ]]; do
    case $1 in
        --artifact-path)
            arg_artifact_path="$2"
            shift
            ;;
        --vsa-path)
            arg_vsa_path="$2"
            shift
            ;;
        --purl)
            purl="$2"
            shift
            ;;
        -h | --help)
            print_help
            exit 0
            ;;
        *)
            log_err "Unknown option: $1"
            print_help
            exit 1
            ;;
    esac
    shift
done


# Check the artifact path and compute the checksum of the artifact.
if [[ -n "${arg_artifact_path:-}" ]]; then
    assert_file_exists "$arg_artifact_path"
    artifact_checksum=$(shasum -a 256 "$arg_artifact_path" | awk '{print $1}')
else
    log_err "Please provide the artifact path."
    print_help
    exit 1
fi

# Check the VSA path.
if [[ -n "${arg_vsa_path:-}" ]]; then
    assert_file_exists "$arg_vsa_path"
else
    log_err "Please provide the VSA path."
    print_help
    exit 1
fi

# Check the purl and obtain the matching subject.
if [[ -n "${purl:-}" ]]; then
    subject_digest=$(cat "$arg_vsa_path" | jq -r ".payload" | base64 -d | jq -r ".subject[] | select(.uri == \"$purl\") | .digest.sha256")
else
    log_err "Please provide the package URL."
    print_help
    exit 1
fi

verify_result=$(cat "$arg_vsa_path" | jq -r ".payload" | base64 -d | jq -r ".predicate.verificationResult")
verifier=$(cat "$arg_vsa_path" | jq -r ".payload" | base64 -d | jq -r ".predicate.verifier.id")


# Check if the subject and artifact digests match.
if [ "$subject_digest" != "$artifact_checksum" ]; then
    echo "The subject checksum \"$subject_digest\" does not match the expected value \"$artifact_checksum\"."
    exit 1
fi

# Check if verifier is Macaron.
if [ "$verifier" != "https://github.com/oracle/macaron" ]; then
    echo "The VSA has not been verified by Macaron."
    exit 1
fi

# Check whether the verification has passed.
if [ "$verify_result" = "PASSED" ]; then
    echo "PASSED"
else
    echo "The verification has failed."
    exit 1
fi
