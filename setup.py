import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(

    name="ICSVGDesigner",
    version="1.0.0",
    author="AdamantLife",
    author_email="contact.adamantmedia@gmail.com",
    description="A simply GUI for creating basic SVGs of IC's for use in design software.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/AdamantLife/ICSVGDesigner",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8',

    install_requires = [
        ],
    entry_points={
        "console_scripts": [
            "icsvgdesigner=ICSVGDesigner.__main__:cli",
            ]
    }
)
