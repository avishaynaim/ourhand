from setuptools import setup, find_packages

def read_requirements():
    """Read requirements.txt with proper encoding"""
    with open('requirements.txt', encoding='utf-8') as f:
        return [
            line.strip()
            for line in f.readlines()
            if line.strip() and not line.startswith('#')
        ]

setup(
    name='yad2-monitor',
    version='2.1.0',
    packages=find_packages(),
    include_package_data=True,
    package_data={
        '': ['templates/*.html', 'static/**/*', 'static/*'],
    },
    install_requires=read_requirements(),
)
