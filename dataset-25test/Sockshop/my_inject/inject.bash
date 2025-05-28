#!/bin/bash
echo "Injecting fault at $(date -u)" > fault_start_time.log
kubectl apply -f user-abort.yaml
kubectl apply -f cleanup-user-abort.yaml
