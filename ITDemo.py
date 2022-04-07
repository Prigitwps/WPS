# Parallelized PDF generation runner for OES 1.0
# Requirements: Selenium and Chrome Drivers
# Selenium Driver: https://www.selenium.dev/downloads/
# Chrome Driver: https://chromedriver.chromium.org/downloads
# Usage: python generalRegression.py [-h] [-r] [-e] [-o] [-i] [-l]
# Arguments:
# -h, --headless:       Specifies headless or display mode for browser (default False)
# -r, --random:         Specifies random or set response mode for assessment (default False)
# -e, --env:            Specifies the environment to login and perform actions (default "uat")
# -d, --directory:      Specifies the directory to save any downloaded PDFs (default current working directory)
# -i, --input:          Specifies the path to the input Python script modules to be run (default none)
# -l, --log-to-file:    Specifies whether to log to the terminal output or to a text file in --directory (default False)
# -p, --log-prefix:     Specifies the prefix to add to all generated log files (default '')


import sys, getopt, importlib, inspect
from oesLibrary import *

todaysDate = date.today()
uploadBucket = 'wps-qa-automation'

class testModule(object):
    def __init__(self, moduleName, modulePath):
        self.modulePath = modulePath
        self.moduleName = moduleName

    #def moduleFunction(self, env, headless, randomResponse, output, logToFile):
    def moduleFunction(self, **kwargs):
        spec = importlib.util.spec_from_file_location(self.moduleName, self.modulePath)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        module.runTestModule(kwargs)
        #module.runTestModule(env, headless, randomResponse, str(output), logToFile)

def worker(testModule, kwargs):
    #testModule = kwargs.pop('testModule')
    testModule.moduleFunction(**kwargs)
    
    # env="uat", headless=False, directory=None, logToFile=False, logName=None, uploadToS3=False, username=None, password=None
    # env="uat", headless=False, randomResponse=False, directory=None, logToFile=False, logName=None, uploadToS3=False, username=None, password=None
    # env="uat", headless=False, randomResponse=False, directory=None, logToFile=False, logName=None, uploadToS3=False, username=None, password=None, sheet=None
    # kwargs['testModule'].moduleFunction(args[1], args[2], args[3], str(args[4]), args[5])



if __name__ == "__main__":
    
    short_options = "he:ro:d:i:lp:u"
    long_options = ["headless", "env=", "random", "output=", "directory=", "input=", "log-to-file", "log-prefix", "upload", "username=", "password=", "admin-username=", "admin-password=", "admin-env="]
    
    # Get full command-line arguments
    full_cmd_arguments = sys.argv
    argument_list = full_cmd_arguments[1:]

    env = "staging"
    headless = False
    randomResponse = True
    directory = None
    input = None
    logToFile = False
    uploadToS3 = False
    username = None
    password = None
    adminUsername = None
    adminPassword = None
    
    prefix = ''

    try:
        arguments, values = getopt.getopt(argument_list, short_options, long_options)
    except getopt.error as err:
        # Output error, and return with an error code
        print (str(err))
        sys.exit(2)
    
    for current_argument, current_value in arguments:
        if current_argument in ("-h", "--headless"):
            headless = True
        elif current_argument in ("-e", "--env"):
            env = current_value
        elif current_argument in ("-d", "--directory", "-o", "--output"):
            directory = current_value
        elif current_argument in ("-i", "--input"):
            input = current_value
        elif current_argument in ("-r", "--random"):
            randomResponse = True
        elif current_argument in ("-l", "--log-to-file"):
            logToFile = True
        elif current_argument in ("-u", "--upload") and 'boto3' in sys.modules:
            uploadToS3 = True
        elif current_argument in ("-p", "--log-prefix"):
            prefix = str(current_value)
        elif current_argument in ("--username"):
            username = str(current_value)
        elif current_argument in ("--password"):
            password = str(current_value)
        elif current_argument in ("--admin-username"):
            adminUsername = str(current_value)
        elif current_argument in ("--admin-password"):
            adminPassword = str(current_value)
        elif current_argument in ("--admin-env"):
            adminEnv = str(current_value)
            #print (("Enabling special output mode (%s)") % (current_value))
    
    if headless:
        logging.warning("Running full regression in headless mode")
    else:
        logging.warning("Running full regression in display mode")
    
    if randomResponse:
        logging.warning("Running full regression in random response mode")
    else:
        logging.warning("Running full regression in set response mode")
    
    # if env=="staging":
        # loginUrl = "https://platform.stage.wpspublish.com"
    # elif env=="uat":
        # loginUrl = "https://practitioner-uat.wpspublish.io"
    # elif env=="qa":
        # loginUrl = "https://practitioner-qa.wpspublish.io"
    # elif env=="prod":
        # loginUrl = "https://platform.wpspublish.com"
    # elif env="dev":
        # loginUrl = "https://practitioner-dev.wpspublish.io"

    if input is None or input == 'None' or input == '':
        # input = str(os.getcwd())
        input = os.path.join(os.path.dirname(os.path.realpath(__file__)), str("ITDemo"))
        
    if directory is None or directory == 'None' or directory == '':
        directory = str(os.getcwd())
    
    try:
        os.mkdir(os.path.join(str(directory), str(os.path.splitext(os.path.basename(str(sys.argv[0])))[0] + (time.strftime("_%F_%T", time.gmtime())).replace(":", "-"))))
        directory = str(os.path.join(str(directory), str(os.path.splitext(os.path.basename(str(sys.argv[0])))[0] + (time.strftime("_%F_%T", time.gmtime())).replace(":", "-"))))
    except:
        logging.exception("Unable to create sub-directory for all tests! Outputting to specified directory instead")
    
    if uploadToS3 and 'boto3' in sys.modules:
        logging.warning("S3 upload is currently enabled")
        s3 = boto3.resource('s3', region_name='us-west-2')
        bucket = s3.Bucket(uploadBucket)
        bucket.put_object(Key=urllib.parse.quote(str("output/oes-1.0-automation/" + str(env) + "/" + todaysDate.strftime("%m-%d-%Y") + "/" + os.path.basename(directory) + "/")))
    else:
        uploadToS3 = False
    
    testModuleArgs = {'env': env, 'headless': headless, 'random': randomResponse, 'directory': str(directory), 'logToFile': logToFile, 'uploadToS3': uploadToS3, 'username': username, 'password': password, 'adminUsername': adminUsername, 'adminPassword': adminPassword, 'uploadParentDirectory': uploadToS3}
    inputModules = []
    for f in os.listdir(input):
        if os.path.isfile(os.path.join(input, f)) and os.path.splitext(os.path.basename(str(f)))[1]=='.py' and str(f)!='__init__.py':
            moduleName=str(f)
            modulePath=os.path.join(str(input), str(f))
            workerInput = {'logName': str(prefix+os.path.splitext(moduleName)[0])}
            workerInput.update(testModuleArgs)
            inputModules.append([testModule(moduleName=moduleName, modulePath=modulePath), workerInput])
    
    
    
    # inputModules = [[[testModule(str(f), os.path.join(str(input), str(f)), str(prefix+os.path.splitext(os.path.basename(os.path.join(input, f)))[0]))]+[env, headless, random, str(output), logToFile, uploadToS3, username, password]] for f in os.listdir(input) if os.path.isfile(os.path.join(input, f)) and os.path.splitext(os.path.basename(str(f)))[1]=='.py' and str(f)!='__init__.py']
    
    logging.warning("Running " + str(len(inputModules)) + " test modules...")
    
    if logToFile:
        logging.warning("Logging to file is enabled; each test module will log to file instead of console")
    
    if headless:
        logging.warning("Headless mode is enabled; browser sessions will not be displayed!")
    
    logging.warning("Outputting all results to: " + str(directory))
    
    with multiprocessing.Pool(processes=4) as pool:
        pool.starmap(worker, inputModules)
    
    # for subdir, dirs, files in os.walk(output):
        # for file in files:
            # full_path = os.path.join(subdir, file)
            # with open(full_path, 'rb') as data:
                # bucket.put_object(Key=str("output/oes-1.0-automation/" + os.path.basename(output) + "/" + str(subdir[len(output)+1:]) + "/" + file), Body=data)
    