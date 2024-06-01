from setuptools import setup, find_packages

setup(
    name="entoli",
    version="0.1.2",
    author="Your Name",
    author_email="cwahn0904@gmail.com",
    description="A Python functional programming library",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/cwahn/entoli",  # Update this URL to your project's repository
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.12",
    install_requires=[],
    extras_require={
        "dev": open("requirements_dev.txt").read().splitlines(),
    },
    entry_points={
        "console_scripts": [
            # Add any CLI scripts here
        ],
    },
)
