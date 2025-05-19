from setuptools import find_packages, setup

with open("README.md", "r") as f:
    long_description = f.read()

setup(
    name="snowbird",
    version="0.3.9",
    description=("Snowbird helps configure Snowflake resources for dataproducts"),
    # package_dir={"": "inbound"},
    packages=find_packages(include=("snowbird/*,")),
    author="NAV IT Virksomhetsdatalaget",
    author_email="virksomhetsdatalaget@nav.no",
    url="https://github.com/navikt/snowbird",
    license="MIT",
    long_description=long_description,
    long_description_content_type="text/markdown",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.10",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        "pyyaml",
        "click",
        "snowflake-connector-python[secure-local-storage]",
        "jinja2",
        "alive-progress",
    ],
    extras_require={
        "dev": [
            "pytest",
            "black",
            "isort",
        ],
    },
    python_requires=">=3.10",
    entry_points="""
        [console_scripts]
        snowbird=snowbird.main:cli
    """,
)
