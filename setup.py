"""
Setup script for Premium Content Bot
"""
from setuptools import setup, find_packages

setup(
    name="premium-content-bot",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        'python-telegram-bot==20.7',
    ],
    entry_points={
        'console_scripts': [
            'premium-bot=main:main',
        ],
    },
)
