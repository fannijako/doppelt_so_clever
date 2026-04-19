from setuptools import setup, find_packages

BUILD = [
    "matplotlib",
    "pygame>=2.5.0",
]

TEST = [
    "pytest==8.4.1",
    "pytest-cov==5.0.0",
    "pylint==3.0.2",
    "flake8==6.1.0",
]

with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="repo_template",
    version="0.1.0",
    description="Repository template for my Python projects",
    long_description=long_description,
    long_description_content_type="text/markdown",

    author="Fanni Jako",
    author_email="fannijako@gmail.com",

    url="https://github.com/fannijako/repo_template",

    packages=find_packages(),
    include_package_data=True,

    install_requires=BUILD,

    extras_require={
        "test": TEST,
        "build": BUILD,
    },

    python_requires=">=3.10",
)
