from setuptools import setup, find_packages
from setuptools.command.install import install
import subprocess
import sys
import os
import urllib.request
import stat


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

        # Download and install gnina
        bin_dir = os.path.join(sys.prefix, "bin")
        os.makedirs(bin_dir, exist_ok=True)
        gnina_path = os.path.join(bin_dir, "gnina")

        gnina_url = "https://github.com/gnina/gnina/releases/download/v1.0.3/gnina"
        print(f"Downloading gnina from {gnina_url} to {gnina_path}...")
        try:
            urllib.request.urlretrieve(gnina_url, gnina_path)
            st = os.stat(gnina_path)
            os.chmod(gnina_path, st.st_mode | stat.S_IEXEC)
            print("gnina downloaded and made executable.")
        except Exception as e:
            sys.stderr.write(f"Failed to download gnina: {e}\n")
            sys.exit(1)

        install.run(self)


with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="biotarget",
    version="0.1.3",
    description="BioTarget: AI Drug Discovery Pipeline. Requires NVIDIA GPU (nvcc) for GNINA docking.",
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
