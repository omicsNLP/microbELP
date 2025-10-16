import setuptools
   
setuptools.setup(
    name="microbELP",
    version="0.2.0",
    author="Dhylan Patel, Antoine D. Lain, Avish Vijayaraghavan, Joram M. Posma",
    author_email="adlain@ic.ac.uk, j.posma11@imperial.ac.uk",
    description="This projects is to build a pipeline for Microbiome NER and NEN.",
    packages=setuptools.find_packages(),
    classifiers=[
        "Intended Audience :: Science/Research",
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: MIT License",
        "Operating System :: WINDOWS/LINUX/MACOS",
    ],
    install_requires=[
    "PySimpleGUI",
    "alive-progress",
    "Pillow>=10.0.0",          
    "ete3>=3.1.3",
    "six>=1.16.0",
    "PyQt5>=5.15.0",
    "numpy>=1.25.0",
    "pandas>=2.2.0",
    "matplotlib>=3.8.0",
    "scipy>=1.11.0",
    "statsmodels>=0.14.0",
    "tqdm",
    "scikit-learn>=1.5.0",
    "torch>=2.1.0",
    "transformers>=4.40.0",
    "chardet"
    ],
    python_requires='>=3.9'
)
