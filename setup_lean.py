import subprocess, sys, glob, os, shutil, logging, ctypes
from os.path import abspath, basename, dirname, join, normpath, relpath

here = normpath(abspath(dirname(__file__)))

required_packages = ['setuptools', 'wheel', 'twine']

for package in required_packages:
    try:
        __import__(package)
    except ImportError:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", package])
            __import__(package)
        except:
            print("Installation encountered an error!!! Attempting to install with --user flag...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", package, "--user"])
            __import__(package)

import setuptools, distutils.cmd
from distutils.command.install import install

class CleanCommand(distutils.cmd.Command):
    """Custom clean command to tidy up the project root."""
    CLEAN_FILES = './build ./dist ./*.pyc ./*.tgz ./*.egg-info'.split(' ')

    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        global here

        for path_spec in self.CLEAN_FILES:
            # Make paths absolute and relative to this path
            abs_paths = glob.glob(os.path.normpath(os.path.join(here, path_spec)))
            for path in [str(p) for p in abs_paths]:
                if not path.startswith(here):
                    # Die if path in CLEAN_FILES is absolute + outside this directory
                    raise ValueError("%s is not a path inside %s" % (path, here))
                print('removing %s' % os.path.relpath(path))
                shutil.rmtree(path)

class MyInstall(install):
    # Calls the default run command, then cleans up the temp files from build
    # (equivalent to "setup.py clean").
    def run(self):
        install.run(self)
        
        #c = CleanCommand(self.distribution)
        #c.run()


with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="oesLibrary",
    version="0.0.1",
    author="Brennan Jackson",
    author_email="bjackson@wpspublish.com",
    description="OES 1.0 Automation Library",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/wpspublish/testing-scripts/tree/master/oesLibraryPackage",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.9.1',
    install_requires=[
          # 'pytz',
          # 'python-dateutil',
          # 'pdfminer',
          # 'openpyxl',
          # 'lxml',
          # 'boto3',
          # 'pdfplumber',
          # 'geckodriver-autoinstaller',          
          # 'selenium',
          # 'chromedriver_autoinstaller',
      ],
    cmdclass={
        'clean': CleanCommand,
        # 'install': MyInstall,
    },
)

# print("Attempting to force chromedriver_autoinstaller to full installation...")

# try:
    # try:
        # subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", "--upgrade", '--force-reinstall', 'chromedriver_autoinstaller'])
    # except:
        # print("Installation encountered an error!!! Attempting to install without --user flag...")
        # subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", '--force-reinstall', 'chromedriver_autoinstaller'])
    # import chromedriver_autoinstaller
    # # chromedriver_filename = chromedriver_autoinstaller.utils.get_chromedriver_filename()
    # # src = str(normpath(chromedriver_autoinstaller.install()))
    # # pathList = []
    # # if sys.platform.startswith('win'):
        # # pathList = os.environ['PATH'].split(';')
    # # else:
        # # pathList = os.environ['PATH'].split(':')

    # # dst = ''
    # # for x in pathList:
        # # if x != '' and os.path.isdir(x) and os.access(x, os.W_OK) and os.access(x, os.R_OK):
            # # if x.endswith('Python'+str(sys.version_info.major)+str(sys.version_info.minor)):
                # # dst = x
                # # break

    # # if dst == '':
        # # for x in pathList:
            # # if x != '' and os.path.isdir(x) and os.access(x, os.W_OK) and os.access(x, os.R_OK):
                # # if x.endswith('bin'):
                    # # dst = x
                    # # break

    # # dst = os.path.join(dst, chromedriver_filename)
    # # print()
    # # isAdmin = False
    # # if sys.platform.startswith('win'):
        # # try:
            # # isAdmin = ctypes.windll.shell32.IsUserAnAdmin()
        # # except:
            # # isAdmin = False
    # # else:
        # # if os.geteuid() == 0:
            # # isAdmin = True
        # # else:
            # # isAdmin = False    

    # # if isAdmin and dst == '':
        # # if sys.platform.startswith('win'):
            # # dst = os.getenv('SystemRoot')
        # # else:
            # # dst = '/usr/local/bin'

    # # try:
        # # print("Attempting to add symlink to directory in system path for use outside Python...")
        # # try:
            # # os.symlink(src, dst)
            # # os.chmod(dst, 0o777)
        # # except OSError as e:
            # # try:
                # # os.remove(dst)
                # # os.symlink(src, dst)
                # # os.chmod(dst, 0o777)
            # # except:
                # # logging.exception("Was unable to add chromedriver to system path, likely due to user permissions!!! Please do so manually, or it will only be available in Python!!!")
                # # print()
                # # print("chromedriver location: " + src)
        # # print("Symlink added successfully at " + str(dst) + " pointing to " + str(src))
    # # except:
        # # print("Failed to add symlink!!!")

    # # if os.path.exists(dst):
        # # print("The chromedriver binary is currently available outside of Python at '" + str(dst) + "'", end = '')
        # # if not chromedriver_autoinstaller.utils.check_version(dst, chromedriver_autoinstaller.utils.get_matched_chromedriver_version(chromedriver_autoinstaller.utils.get_chrome_version())):
            # # print(", but appears outdated. Please ensure it is pointing to the correct location for the latest chromedriver.")
        # # else:
            # # print()
    # # else:
        # # print("The chromedriver binary is currently only available within Python by importing chromedriver_autoinstaller")
        # # print("If you would like chromedriver available elsewhere, please try to run again with elevated permissions to create a symlink in the system path, or do so yourself")
    # # print("chromedriver location: " + src)
# except:
    # logging.exception("Failed to ensure proper chromedriver installation!!! Please confirm install for proper function!!!")

# print()
# print("Attempting to force selenium to full installation...")

# try:
    # try:
        # subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", '--force-reinstall', 'selenium', '--user'])
    # except:
        # print("Installation encountered an error!!! Attempting to install without --user flag...")
        # subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", '--force-reinstall', 'selenium'])
    # import selenium
# except:
    # logging.exception("Failed to ensure proper selenium installation!!! Please confirm install for proper function!!!")
    