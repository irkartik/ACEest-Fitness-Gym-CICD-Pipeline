#!/usr/bin/env bash
# rollback.sh — Kubernetes rollback helpers for ACEest Fitness & Gym
# Used by Jenkins post { failure { ... } } hook and manual recovery.
#
# Usage:
#   ./k8s/rollback.sh rolling          — undo last rolling update
#   ./k8s/rollback.sh blue-green blue  — switch traffic back to blue slot
#   ./k8s/rollback.sh canary           — scale canary to 0 (abort canary)
#   ./k8s/rollback.sh status           — show rollout status for all deployments

set -euo pipefail

STRATEGY="${1:-help}"

print_usage() {
  echo ""
  echo "Usage: $0 <strategy> [options]"
  echo ""
  echo "  rolling                   Undo the last rolling update"
  echo "  blue-green <blue|green>   Switch service selector to the given slot"
  echo "  canary                    Abort canary by scaling it to 0 replicas"
  echo "  status                    Show rollout status for all deployments"
  echo ""
}

rolling_rollback() {
  echo ">>> Rolling back: aceest-fitness deployment"
  kubectl rollout undo deployment/aceest-fitness
  echo ">>> Waiting for rollback to complete..."
  kubectl rollout status deployment/aceest-fitness --timeout=120s
  echo ">>> Current image after rollback:"
  kubectl get deployment aceest-fitness -o jsonpath='{.spec.template.spec.containers[0].image}'
  echo ""
}

blue_green_rollback() {
  SLOT="${2:-blue}"
  if [[ "$SLOT" != "blue" && "$SLOT" != "green" ]]; then
    echo "ERROR: slot must be 'blue' or 'green'" >&2
    exit 1
  fi
  echo ">>> Switching aceest-fitness-svc selector to slot: $SLOT"
  kubectl patch service aceest-fitness-svc \
    --namespace default \
    -p "{\"spec\":{\"selector\":{\"app\":\"aceest-fitness\",\"slot\":\"$SLOT\"}}}"
  echo ">>> Service now routing to: $SLOT"
  kubectl get service aceest-fitness-svc -o jsonpath='{.spec.selector}'
  echo ""
}

canary_abort() {
  echo ">>> Aborting canary: scaling aceest-fitness-canary to 0"
  kubectl scale deployment aceest-fitness-canary --replicas=0
  echo ">>> Canary pods:"
  kubectl get pods -l track=canary
  echo ">>> All traffic now served by stable deployment"
}

show_status() {
  echo "=== Deployment Rollout Status ==="
  for dep in aceest-fitness aceest-fitness-blue aceest-fitness-green \
             aceest-fitness-stable aceest-fitness-canary \
             aceest-fitness-production aceest-fitness-shadow \
             aceest-fitness-version-a aceest-fitness-version-b; do
    if kubectl get deployment "$dep" &>/dev/null 2>&1; then
      echo ""
      echo "--- $dep ---"
      kubectl rollout status deployment/"$dep" --timeout=10s || true
      kubectl get deployment "$dep" -o wide
    fi
  done
}

case "$STRATEGY" in
  rolling)
    rolling_rollback
    ;;
  blue-green)
    blue_green_rollback "$@"
    ;;
  canary)
    canary_abort
    ;;
  status)
    show_status
    ;;
  help|*)
    print_usage
    exit 0
    ;;
esac
