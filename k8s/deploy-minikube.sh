#!/usr/bin/env bash
# deploy-minikube.sh — Build image and deploy a chosen strategy to Minikube
#
# Prerequisites:
#   brew install minikube kubectl
#   minikube start --driver=docker --memory=4096 --cpus=2
#
# Usage:
#   ./k8s/deploy-minikube.sh rolling          — deploy rolling update strategy
#   ./k8s/deploy-minikube.sh blue-green        — deploy blue-green strategy
#   ./k8s/deploy-minikube.sh canary            — deploy canary strategy
#   ./k8s/deploy-minikube.sh ab-testing        — deploy A/B testing strategy
#   ./k8s/deploy-minikube.sh shadow            — deploy shadow strategy
#   ./k8s/deploy-minikube.sh all               — deploy all strategies
#   ./k8s/deploy-minikube.sh teardown          — delete all aceest-fitness resources

set -euo pipefail

STRATEGY="${1:-help}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

print_usage() {
  echo ""
  echo "Usage: $0 <strategy>"
  echo ""
  echo "  rolling      Rolling Update deployment"
  echo "  blue-green   Blue-Green deployment"
  echo "  canary       Canary Release deployment"
  echo "  ab-testing   A/B Testing deployment"
  echo "  shadow       Shadow deployment"
  echo "  all          Deploy all strategies"
  echo "  teardown     Delete all aceest-fitness resources from cluster"
  echo ""
}

build_images() {
  echo ">>> Pointing Docker CLI to Minikube's daemon (images built directly in cluster)"
  eval "$(minikube docker-env)"

  echo ">>> Building aceest-fitness:latest and aceest-fitness:v1.0"
  docker build -t aceest-fitness:latest -t aceest-fitness:v1.0 "$REPO_ROOT"

  echo ">>> Tagging aceest-fitness:v2.0 (same image — simulates a new version)"
  docker tag aceest-fitness:v1.0 aceest-fitness:v2.0

  echo ">>> Images available in Minikube:"
  docker images | grep aceest-fitness
}

deploy_rolling() {
  echo "=== Deploying: Rolling Update ==="
  kubectl apply -f "$SCRIPT_DIR/rolling-update/"
  kubectl rollout status deployment/aceest-fitness --timeout=120s
  echo ">>> Service URL:"
  minikube service aceest-fitness-svc --url 2>/dev/null || \
    echo "    Run: minikube service aceest-fitness-svc --url"
}

deploy_blue_green() {
  echo "=== Deploying: Blue-Green ==="
  kubectl apply -f "$SCRIPT_DIR/blue-green/"
  kubectl rollout status deployment/aceest-fitness-blue --timeout=120s
  kubectl rollout status deployment/aceest-fitness-green --timeout=120s
  echo ">>> Active slot: blue (green is on standby)"
  echo ">>> To cut over to green:"
  echo "    kubectl patch svc aceest-fitness-svc -p '{\"spec\":{\"selector\":{\"slot\":\"green\"}}}'"
}

deploy_canary() {
  echo "=== Deploying: Canary (80% stable / 20% canary) ==="
  kubectl apply -f "$SCRIPT_DIR/canary/"
  kubectl rollout status deployment/aceest-fitness-stable --timeout=120s
  kubectl rollout status deployment/aceest-fitness-canary --timeout=120s
  echo ">>> Pod distribution:"
  kubectl get pods -l app=aceest-fitness -o wide
}

deploy_ab_testing() {
  echo "=== Deploying: A/B Testing ==="
  echo ">>> Enabling Minikube ingress addon..."
  minikube addons enable ingress
  kubectl apply -f "$SCRIPT_DIR/ab-testing/"
  kubectl rollout status deployment/aceest-fitness-version-a --timeout=120s
  kubectl rollout status deployment/aceest-fitness-version-b --timeout=120s
  echo ">>> Add this to /etc/hosts for local resolution:"
  echo "    $(minikube ip)  aceest-fitness.local"
  echo ">>> Test Version A (default):  curl http://aceest-fitness.local/health"
  echo ">>> Test Version B (explicit): curl http://aceest-fitness.local/api/v2/health"
}

deploy_shadow() {
  echo "=== Deploying: Shadow ==="
  kubectl apply -f "$SCRIPT_DIR/shadow/"
  kubectl rollout status deployment/aceest-fitness-production --timeout=120s
  kubectl rollout status deployment/aceest-fitness-shadow --timeout=120s
  echo ">>> Production service URL:"
  minikube service aceest-fitness-production-svc --url 2>/dev/null || \
    echo "    Run: minikube service aceest-fitness-production-svc --url"
  echo ">>> Shadow service (internal only): aceest-fitness-shadow-svc"
}

teardown() {
  echo "=== Tearing down all aceest-fitness resources ==="
  kubectl delete -f "$SCRIPT_DIR/rolling-update/" --ignore-not-found=true
  kubectl delete -f "$SCRIPT_DIR/blue-green/" --ignore-not-found=true
  kubectl delete -f "$SCRIPT_DIR/canary/" --ignore-not-found=true
  kubectl delete -f "$SCRIPT_DIR/ab-testing/" --ignore-not-found=true
  kubectl delete -f "$SCRIPT_DIR/shadow/" --ignore-not-found=true
  echo ">>> All resources removed."
}

verify_minikube() {
  if ! kubectl cluster-info &>/dev/null; then
    echo "ERROR: Minikube cluster is not running."
    echo "Start it with: minikube start --driver=docker --memory=4096 --cpus=2"
    exit 1
  fi
  echo ">>> Cluster: $(kubectl config current-context)"
}

case "$STRATEGY" in
  rolling)
    verify_minikube
    build_images
    deploy_rolling
    ;;
  blue-green)
    verify_minikube
    build_images
    deploy_blue_green
    ;;
  canary)
    verify_minikube
    build_images
    deploy_canary
    ;;
  ab-testing)
    verify_minikube
    build_images
    deploy_ab_testing
    ;;
  shadow)
    verify_minikube
    build_images
    deploy_shadow
    ;;
  all)
    verify_minikube
    build_images
    deploy_rolling
    deploy_blue_green
    deploy_canary
    deploy_ab_testing
    deploy_shadow
    echo ""
    echo "=== All strategies deployed! ==="
    kubectl get deployments
    kubectl get services
    ;;
  teardown)
    teardown
    ;;
  help|*)
    print_usage
    exit 0
    ;;
esac
