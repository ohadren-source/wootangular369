from setuptools import setup, find_packages

setup(
    name="lilypod",
    version="1.0.0",
    description="The Wootangular Dev Framework. For Lilian. For Lily.",
    long_description=(
        "LILYPOD — Grow through the swamp. "
        "Built on BOOL++, NULL_Φ, Albert's Axiom, GI;WG?. VENIM.US."
    ),
    author="Ohad Phoenix Oren",
    packages=find_packages(include=["lilypod", "lilypod.*"]),
    include_package_data=True,
    package_data={
        "lilypod": [
            "templates/project/**/*",
            "templates/project/**/**/*",
        ]
    },
    entry_points={
        "console_scripts": [
            "lilypod=lilypod.cli:main",
        ],
    },
    install_requires=[
        "flask",
        "flask-cors",
        "psycopg2-binary",
    ],
    python_requires=">=3.9",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
    ],
)
