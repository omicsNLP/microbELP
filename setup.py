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
'PySimpleGUI==4.60.5',
'alive_progress==2.1.0'
],
    python_requires='>=3.6'
)