# Parallelized single-script runner for OES 1.0
# Requirements: Selenium and Chrome Drivers
# Selenium Driver: https://www.selenium.dev/downloads/
# Chrome Driver: https://chromedriver.chromium.org/downloads
# Usage: python parallelSingleScript.py [-h] [-r] [-n] [-e] [-o] [-i] [-l]
# Arguments:
# -h, --headless:       Specifies headless or display mode for browser (default False)
# -r, --random:         Specifies random or set response mode for assessment (default False)
# -n, --number:         Specifies the number of times to run the script (default 1)
# -e, --env:            Specifies the environment to login and perform actions (default "uat")
# -o, --output:         Specifies the directory to save any downloaded PDFs (default current working directory)
# -i, --input:          Specifies the path to the input Python script to be run (default none)
# -l, --log-to-file:    Specifies whether to log to the terminal output or to a text file in --output (default False)
# -p, --log-prefix:     Specifies the prefix to add to all generated log files (default '')
# --username:           Specifies a username to use for logging in; default credentials require boto3 configuration and S3 access, so required if not available
# --password:           Specifies a password to use for logging in; default credentials require boto3 configuration and S3 access, so required if not available

import sys, getopt, importlib, inspect
from oesLibrary import *

class testModule(object):
    def __init__(self, moduleName, modulePath):
        self.modulePath = modulePath
        self.moduleName = moduleName
    def moduleFunction(self, **kwargs):
        spec = importlib.util.spec_from_file_location(self.moduleName, self.modulePath)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        module.runTestModule(kwargs)

def worker(testModule, kwargs):
    testModule.moduleFunction(**kwargs)


if __name__ == "__main__":
    
    short_options = "he:ro:d:i:lp:un:"
    long_options = ["headless", "env=", "random", "output=", "directory=", "input=", "log-to-file", "log-prefix", "upload", "username=", "password=", "number="]
    
    # Get full command-line arguments
    full_cmd_arguments = sys.argv
    argument_list = full_cmd_arguments[1:]

    env = "uat"
    headless = False
    randomResponse = False
    output = None
    input = None
    logToFile = False
    uploadToS3 = False
    username = None
    password = None
    threadNum = 4
    number = 1
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
        elif current_argument in ("-o", "-d", "--output", "--directory"):
            output = current_value
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
        elif current_argument in ("-n", "--number"):
            number = int(current_value)
        elif current_argument in ("-t", "--threads"):
            threadNum = int(current_value)
        elif current_argument in ("--username"):
            username = str(current_value)
        elif current_argument in ("--password"):
            password = str(current_value)
        elif current_argument in ("--admin-username"):
            adminUsername = str(current_value)
        elif current_argument in ("--admin-password"):
            adminPassword = str(current_value)
            #print (("Enabling special output mode (%s)") % (current_value))
    
    if headless:
        logging.warning("Running parallel regression in headless mode")
    else:
        logging.warning("Running parallel regression in display mode")
    
    if randomResponse:
        logging.warning("Running parallel regression in random response mode")
    else:
        logging.warning("Running parallel regression in set response mode")
    
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
        input = str(os.getcwd())
        
    if output is None or output == 'None' or output == '':
        output = str(os.getcwd())
    
    try:
        os.mkdir(os.path.join(str(output), str(os.path.splitext(os.path.basename(str(sys.argv[0])))[0] + (time.strftime("_%F_%T", time.gmtime())).replace(":", "-"))))
        output = str(os.path.join(str(output), str(os.path.splitext(os.path.basename(str(sys.argv[0])))[0] + (time.strftime("_%F_%T", time.gmtime())).replace(":", "-"))))
    except:
        logging.exception("Unable to create sub-directory for all tests! Outputting to specified directory instead")
    
    if uploadToS3 and 'boto3' in sys.modules:
        logging.warning("S3 upload is currently enabled")
        s3 = boto3.resource('s3', region_name='us-west-2')
        bucket = s3.Bucket('testautomation-results.wpspublish.io')
        bucket.put_object(Key=urllib.parse.quote(str("output/oes-1.0-automation/" + str(env) + "/" + os.path.basename(output) + "/")))
    else:
        uploadToS3 = False
    
    testModuleArgs = {'env': env, 'headless': headless, 'random': randomResponse, 'directory': str(output), 'logToFile': logToFile, 'uploadToS3': uploadToS3, 'username': username, 'password': password, 'adminUsername': adminUsername, 'adminPassword': adminPassword, 'uploadParentDirectory': uploadToS3}
    inputModules = []
    if os.path.exists(input) and os.path.isfile(input) and os.path.splitext(os.path.basename(str(input)))[1]=='.py' and str(input)!='__init__.py':
        for i in range(number):
            moduleName=str(os.path.basename(input))
            modulePath=str(input)
            workerInput = {'logName': str(prefix+os.path.splitext(moduleName)[0]+"_"+str(i+1))}
            workerInput.update(testModuleArgs)
            inputModules.append([testModule(moduleName=moduleName, modulePath=modulePath), workerInput])

    
    
    # inputModules = [[[testModule(str(f), os.path.join(str(input), str(f)), str(prefix+os.path.splitext(os.path.basename(os.path.join(input, f)))[0]))]+[env, headless, random, str(output), logToFile, uploadToS3, username, password]] for f in os.listdir(input) if os.path.isfile(os.path.join(input, f)) and os.path.splitext(os.path.basename(str(f)))[1]=='.py' and str(f)!='__init__.py']
    
    logging.warning("Running " + str(len(inputModules)) + " instances of test module " + os.path.splitext(os.path.basename(str(input)))[0] + "across " + str(threadNum) + " thread(s)...")
    
    if logToFile:
        logging.warning("Logging to file is enabled; each test module will log to file instead of console")
    
    if headless:
        logging.warning("Headless mode is enabled; browser sessions will not be displayed!")
    
    logging.warning("Outputting all results to: " + output)
    
    with multiprocessing.Pool(processes=threadNum) as pool:
        pool.starmap(worker, inputModules)
    
    # for subdir, dirs, files in os.walk(output):
        # for file in files:
            # full_path = os.path.join(subdir, file)
            # with open(full_path, 'rb') as data:
                # bucket.put_object(Key=str("output/oes-1.0-automation/" + os.path.basename(output) + "/" + str(subdir[len(output)+1:]) + "/" + file), Body=data)
    