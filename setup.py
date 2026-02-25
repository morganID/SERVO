from setuptools import setup, find_packages

setup(
    name='colab-server',
    version='2.0.0',
    description='One-command background API server for Google Colab',
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
            'colab-server=colab_server.cli:main',
        ],
    },
    python_requires='>=3.7',
)