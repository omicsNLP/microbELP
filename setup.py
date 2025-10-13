import setuptools
   
setuptools.setup(
    name="microbELP",
    version="0.2.0",
    author="Dhylan Patel, Antoine D. Lain, Joram M. Posma",
    author_email="adlain@ic.ac.uk, j.posma11@imperial.ac.uk",
    description="This projects is to build a pipeline for Microbiome NER and NEN.",
    packages=setuptools.find_packages(),
    classifiers=[
        "Intended Audience :: Science/Research",
        "Programming Language :: Python :: 3.6",
        "License :: OSI Approved :: MIT License",
        "Operating System :: WINDOWS/LINUX/MACOS",
    ],
    install_requires=[
    'PySimpleGUI',
    'alive_progress',
    'pillow==11.1.0',
    'ete3==3.1.3',
    'six==1.17.0',
    'PyQt5==5.15.11',
    'ipykernel==6.29.5',
    'numpy==1.26.4 ',
    'pandas==2.2.2',
    'matplotlib==3.8.4',
    'scipy==1.11.4',
    'statsmodels==0.14.1'
    ],
    python_requires='>=3.6'
)
