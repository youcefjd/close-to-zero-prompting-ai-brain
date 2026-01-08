"""Setup script for ai-brain package."""

from setuptools import setup, find_packages
import os

# Read version from __init__.py
version = "0.1.0"

# Read README for long description
readme_path = os.path.join(os.path.dirname(__file__), "README.md")
if os.path.exists(readme_path):
    with open(readme_path, "r", encoding="utf-8") as f:
        long_description = f.read()
else:
    long_description = "Close-to-Zero Prompting AI Brain - Autonomous agent framework"

# Read requirements
requirements_path = os.path.join(os.path.dirname(__file__), "requirements.txt")
if os.path.exists(requirements_path):
    with open(requirements_path, "r", encoding="utf-8") as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]
else:
    requirements = [
        "langgraph>=0.2.0",
        "langchain>=0.1.0",
        "langchain-community>=0.0.20",
        "langchain-core>=0.1.0",
        "langchain-ollama>=1.0.0",
        "pydantic>=2.0.0",
        "typing-extensions>=4.8.0",
        "requests>=2.31.0",
    ]

setup(
    name="ai-brain",
    version=version,
    author="Youcef Djeddar",
    author_email="your.email@example.com",  # Update this
    description="Close-to-Zero Prompting AI Brain - Autonomous agent framework",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/youcefjd/close-to-zero-prompting-ai-brain",
    packages=find_packages(exclude=["tests", "tests.*", "*.tests", "*.tests.*"]),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
        "github": [
            "PyGithub>=2.0.0",
        ],
        "anthropic": [
            "langchain-anthropic>=0.1.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "ai-brain=autonomous_orchestrator:main",
            "ai-brain-approve=approve:main",
            "ai-engineer=autonomous_engineer_cli:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
