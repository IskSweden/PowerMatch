from setuptools import setup, find_packages

setup(
    name="powermatch",
    version="1.0.0",
    description="PowerMatch — Real-Time Precision Energy Game Backend",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="Isak Skoog",
    author_email="skoog.isak@gmail.com",
    url="https://github.com/IskSweden/PowerMatch",
    license="MIT",
    packages=find_packages(include=["powermatch", "powermatch.*"]),
    include_package_data=True,
    package_data={
        "powermatch": ["frontend/dist/index.html", "frontend/dist/assets/*"],
    },
    install_requires=[
        "fastapi~=0.110",
        "uvicorn~=0.22",
        "paho-mqtt~=1.6",
        "python-dotenv~=1.0",
        "websockets~=12.0",
        "rich~=13.7",
        "sqlalchemy~=2.0",
    ],
    entry_points={
        "console_scripts": [
            "powermatch=powermatch.cli:main",
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Framework :: FastAPI",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Environment :: Console",
        "Topic :: Games/Entertainment :: Simulation",
    ],
    python_requires=">=3.7",
)
