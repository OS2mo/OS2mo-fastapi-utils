# SPDX-FileCopyrightText: Magenta ApS
#
# SPDX-License-Identifier: MPL-2.0

import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="os2mo-fastapi-utils",
    version="0.0.2",
    author="Magenta ApS",
    author_email="info@magenta.dk",
    description="Utility library with various reusable FastAPI components",
    license="MPL 2.0",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://git.magenta.dk/rammearkitektur/os2mo-data-import-and-export",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        "fastapi",
        "pydantic",
        "opentelemetry-api",
        "opentelemetry-sdk",
        "opentelemetry-exporter-jaeger",
        "opentelemetry-instrumentation-aiohttp-client",
        "opentelemetry-instrumentation-requests",
        "opentelemetry-instrumentation-fastapi",
        "structlog",
    ],
    extras_require={
        'lint': [
            'mypy',
            'black',
            'isort',
        ],
        'test': [
            'pytest',
            'pytest-cov',
        ],
        'dist': [
            'build',
            'twine',
        ],
    },
    packages=setuptools.find_packages(),
    python_requires='>=3.7',
)
