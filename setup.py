from setuptools import setup, find_packages

setup(
    name='moccha',
    version='2.0.0',
    description='just fun',
    packages=find_packages(),
    install_requires=[
        'flask',
        'flask-cors',
        'pyngrok',
        'psutil',
        'requests',
    ],
    entry_points={
        'console_scripts': [
            # Ini bikin command "colab-server" bisa dipanggil dari terminal
            'moccha=moccha.cli:main',
        ],
    },
    python_requires='>=3.7',
)