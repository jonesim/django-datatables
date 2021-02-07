import setuptools

with open("readme.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="django-filtered-datatables",
    version="0.0.9",
    author="Ian Jones",
    description="Django views with javascript filters using Datatables",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jonesim/django-datatables",
    include_package_data = True,
    packages=['django_datatables'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
