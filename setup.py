from setuptools import setup, find_packages

setup(
    name="powermatch",
    version="0.1.0",
    author="Isak Skoog",
    description="Real-time energy precision game backend",
    packages=["powermatch"],
    package_dir={"": "backend"},
    include_package_data=True,
    install_requires=[
        "fastapi~=0.110",
        "uvicorn~=0.22",
        "paho-mqtt~=1.6",
        "python-dotenv~=1.0",
        "websockets~=12.0",
        "rich~=13.7"
    ],
    entry_points={
        "console_scripts": [
            "powermatch = powermatch.cli:main"
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Framework :: FastAPI",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8',
)
