#!/bin/bash
set -e

echo "================================================="
echo "  BioTarget: GNINA Docker Setup Script"
echo "================================================="

# 1. Check for docker
if ! command -v docker &> /dev/null; then
    echo "[!] Error: 'docker' is not installed or not in PATH."
    echo "    Please install Docker first: https://docs.docker.com/get-docker/"
    exit 1
fi

# 2. Check docker daemon is running
if ! docker info &> /dev/null; then
    echo "[!] Error: Docker daemon is not running or current user does not have permissions (try running with sudo or add user to docker group)."
    exit 1
fi

ARCH=$(uname -m)
echo "[*] Detected Architecture: $ARCH"

if [[ "$ARCH" == "aarch64" || "$ARCH" == "arm64" ]]; then
    echo "[*] ARM architecture detected. GNINA does not have a native ARM image."
    echo "[*] BioTarget will use Docker's x86_64 (amd64) emulation via QEMU."
    echo "[!] Note: GPU pass-through is NOT supported during emulation across architectures. GNINA will run on CPU."
    
    echo "[*] Ensuring QEMU multi-architecture support is registered..."
    # The '|| true' ensures the script doesn't fail if the user already has binfmt set up or lacks privileged rights
    docker run --rm --privileged tonistiigi/binfmt --install all || true
    
    echo "[*] Pulling linux/amd64 gnina image..."
    docker pull --platform linux/amd64 gnina/gnina:latest
    
elif [[ "$ARCH" == "x86_64" || "$ARCH" == "amd64" ]]; then
    echo "[*] x86_64 architecture detected."
    
    if command -v nvidia-smi &> /dev/null; then
        echo "[*] NVIDIA GPU detected!"
        echo "[*] Pulling gnina image..."
        docker pull gnina/gnina:latest
        
        echo "[*] Testing NVIDIA Container Toolkit (GPU Pass-through)..."
        # We test with a lightweight CUDA base image instead of gnina itself to isolate toolkit errors
        if docker run --rm --gpus all nvidia/cuda:12.2.0-base-ubuntu22.04 nvidia-smi &> /dev/null; then
            echo "[+] GPU Pass-through is working correctly!"
        else
            echo "[-] Warning: NVIDIA Container Toolkit might not be configured correctly for Docker."
            echo "    Docker could not access the GPU."
            echo "    Please ensure you have installed and configured 'nvidia-container-toolkit'."
            echo "    Guide: https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html"
        fi
    else
        echo "[-] No NVIDIA GPU detected (nvidia-smi not found)."
        echo "[*] GNINA will still be pulled, but will run in CPU-only mode."
        docker pull gnina/gnina:latest
    fi
else
    echo "[-] Unknown architecture: $ARCH. Attempting default pull..."
    docker pull gnina/gnina:latest
fi

echo "================================================="
echo "[+] Setup Complete! GNINA Docker image is ready."
echo "================================================="
