from setuptools import setup

setup(
   name='Neighborhood',
   version='1.0',
   description='Social media platform',
   author='Abolo Samuel',
   author_email='ikabolo59@gmail.com',
   packages=['neighborhood'],  #same as name
   install_requires=['gunicorn', 'requests', 'flask', 'numpy', 'flask-cors', 'pandas', 'pymysql'], #external packages as dependencies
)
