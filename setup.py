import setuptools

setuptools.setup(
    name="dragon_inference",
    version="0.1",
    author="Jeremy Ng",
    author_email="jeremy.ng@yale.edu",
    description="The DRAGON Inference provides a Streamlit app that"
                " runs CNN analysis based on our custom algorithm.",
    python_requires=">=3.0",
    packages=setuptools.find_packages(),
)