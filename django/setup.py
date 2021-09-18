import setuptools

setuptools.setup(
    name="datatable-examples",
    version="0.0.1",
    author="Ian Jones",
    description="Datatable examples",
    include_package_data = True,
    packages=['examples'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
