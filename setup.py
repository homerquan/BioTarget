from setuptools import setup, find_packages
from setuptools.command.install import install
import subprocess
import sys


class CustomInstallCommand(install):
    def run(self):
        # Check for NVIDIA GPU / nvcc
        has_gpu = False
        try:
            subprocess.check_output(["nvcc", "--version"])
            has_gpu = True
        except (FileNotFoundError, subprocess.CalledProcessError):
            try:
                subprocess.check_output(["nvidia-smi"])
                has_gpu = True
            except (FileNotFoundError, subprocess.CalledProcessError):
                pass

        if not has_gpu:
            sys.stderr.write(
                "Error: you need nvidia GPU, support nvcc... (gnina requires an NVIDIA GPU)\n"
            )
            sys.exit(1)

        # Ensure Docker is installed
        try:
            subprocess.check_output(["docker", "--version"])
        except (FileNotFoundError, subprocess.CalledProcessError):
            sys.stderr.write("Error: docker is required to run the gnina container.\n")
            sys.exit(1)

        # Pull gnina docker image
        print("Pulling gnina docker image...")
        try:
            import platform

            if platform.machine().lower() in ["aarch64", "arm64"]:
                subprocess.check_call(
                    ["docker", "pull", "--platform", "linux/amd64", "gnina/gnina"]
                )
            else:
                subprocess.check_call(["docker", "pull", "gnina/gnina"])
        except subprocess.CalledProcessError:
            print(
                "Warning: could not pull gnina/gnina docker image. It will be pulled on first run."
            )

        install.run(self)


with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="biotarget",
    version="0.1.5",
    description="BioTarget: AI Drug Discovery Pipeline. Requires NVIDIA GPU and Docker for GNINA docking. Run ./scripts/install_gnina_docker.sh before use.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="BioTarget Contributors",
    packages=find_packages(),
    install_requires=[
        "drugclip>=0.1.2",
        "torch>=2.0",
        "torch_geometric>=2.3",
        "pandas",
        "tqdm",
        "rdkit",
    ],
    cmdclass={
        "install": CustomInstallCommand,
    },
    entry_points={
        "console_scripts": [
            "biotarget=biotarget.cli:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Environment :: GPU :: NVIDIA CUDA",
    ],
    python_requires=">=3.9",
)
