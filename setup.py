from setuptools import setup

with open("README.md","r") as fh:
    long_description = fh.read()

setup(
    name = "paralg",
    author = "PALAT Labs",
    version="0.0.1",
    url="https://github.com/rcgale/compare-transcripts",
    description="For two directories containing ELAN .eaf files, compare the transcripts in those files "
                "which have matching file names.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    python_requires=">=3.7",
    install_requires=[
        "pympi-ling",
        "pandas",
        "openpyxl",
    ],
    entry_points={
        'console_scripts': [
            "elan-compare=elancompare:main"
        ]
    }
)