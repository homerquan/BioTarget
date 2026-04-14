from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="biotarget",
    version="0.1.1",
    description="End-to-End AI Drug Discovery Pipeline powered by DrugCLIP",
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
    entry_points={
        "console_scripts": [
            "biotarget=biotarget.cli:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.9",
)
