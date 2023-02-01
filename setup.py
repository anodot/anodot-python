import pathlib
from setuptools import setup, find_packages


README = (pathlib.Path(__file__).parent / "README.md").read_text()

setup(
    name='python-anodot',
    description="Anodot API python package",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/anodot/anodot-python",
    author="Anodot",
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    packages=find_packages(),
    install_requires=["requests"],
    version='2.0.7'
)
