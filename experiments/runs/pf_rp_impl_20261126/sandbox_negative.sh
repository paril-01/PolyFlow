#!/bin/sh
# Actual WSL/Linux namespace and filesystem checks, no agent/model invocation.
set -eu
trial_root=$(mktemp -d /tmp/rcir-isolation-XXXXXX)
mkdir "$trial_root/work" "$trial_root/oracle"
printf 'PRIVATE_ORACLE_SENTINEL\n' > "$trial_root/oracle/answer.txt"
printf 'public source\n' > "$trial_root/work/source.txt"
export RCIR_HOST_SECRET=should_not_be_visible
bwrap --unshare-all --die-with-parent --new-session --clearenv \
  --setenv PATH /usr/bin:/bin --setenv HOME /tmp \
  --ro-bind /usr /usr --ro-bind /bin /bin --ro-bind /lib /lib --ro-bind /lib64 /lib64 \
  --proc /proc --dev /dev --tmpfs /tmp --bind "$trial_root/work" /work --chdir /work \
  -- /bin/sh -ec '
    test -f /work/source.txt
    test ! -e /oracle/answer.txt
    test ! -e /mnt/c
    test ! -e /home
    test ! -e /work/.git
    test -z "${RCIR_HOST_SECRET:-}"
    test "$(ls /sys/class/net 2>/dev/null | wc -l)" -eq 0
    printf "agent output\n" > /work/patch.txt
    printf "SANDBOX_AGENT_NEGATIVE_CONTROLS_PASSED\n"
  '
test -f "$trial_root/work/patch.txt"
# The trusted evaluator may mount the oracle in its separate sandbox.
bwrap --unshare-all --die-with-parent --new-session --clearenv \
  --ro-bind /usr /usr --ro-bind /bin /bin --ro-bind /lib /lib --ro-bind /lib64 /lib64 \
  --proc /proc --dev /dev --tmpfs /tmp --ro-bind "$trial_root/work" /work \
  --ro-bind "$trial_root/oracle" /oracle --chdir /work \
  -- /bin/sh -ec 'test -f /oracle/answer.txt; test -f /work/patch.txt; printf "SEPARATE_EVALUATOR_MOUNT_PASSED\n"'
printf 'Actual disposable trial directory: %s\n' "$trial_root"
