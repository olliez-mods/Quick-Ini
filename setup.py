from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="quick_ini",
    version="3.1.1",
    description="A library for reading from and writing to .ini formatted files",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="OllieZ-Mods",
    author_email="socksinthewash@gmail.com",
    url="https://github.com/olliez-mods/Quick-Ini",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.7",
    keywords="ini config configuration parser file",
    project_urls={
        "Bug Reports": "https://github.com/olliez-mods/Quick-Ini/issues",
        "Source": "https://github.com/olliez-mods/Quick-Ini",
    },
)