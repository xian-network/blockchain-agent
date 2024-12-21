from setuptools import setup, find_packages


setup(
    name='Xian Blockchain Agent',
    version='1.0.0',
    author='crosschainer',
    packages=find_packages(),
    python_requires='>=3.11',
    install_requires=[
        'python-dotenv', 'aiohttp'
    ],
)
