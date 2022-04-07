# Assessment load testing harness for OES 1.0
# Requirements: Selenium, Google Chrome
# Selenium Driver: https://www.selenium.dev/downloads/
# For default credentials and S3 upload, boto3: https://boto3.amazonaws.com/v1/documentation/api/latest/guide/quickstart.html
# Usage: python loadTest.py [-h] [-e] [-l] [-d] [-t] [-i] [-u] [-w]
# Arguments:
# -h, --headless:       Specifies headless or display mode for browser (default False)
# -e, --env:            Specifies the environment to login and perform actions (default "uat")
# -l, --log-to-file:    Specifies whether to log to the terminal output or to a text file in --output (default False)
# -d, --directory:      Specifies the directory to save any downloaded PDFs (default current working directory)
# -u, --upload:         Specifies whether to upload all generated files to S3 (default False)
# -w, --wait-time:      Specifies how long to wait between responses on a form in seconds (default 0.1)
# -t, --threads:        Specifies the number of parallel threads to run; generally limited by CPU cores (default 1)
# -i, --iterations:     Specifes the number of iterations (repetitions of a loop) to perform in each thread (default 1)
# --username:           Specifies a username to use for logging in; default credentials require S3, so required if S3 not available
# --password:           Specifies a password to use for logging in; default credentials require S3, so required if S3 not available

import sys
from oesLibrary import *
from dateutil.relativedelta import *
from datetime import date
import getopt, csv, os, re, mimetypes, glob, requests
import pprint, pytz, boto3, json, hashlib, time
from contextlib import redirect_stdout, redirect_stderr

todaysDate = date.today()
uploadBucket = 'wps-qa-automation'

testInfo = {'password': '',
            'username': ''}

def runTestModule(kwargs):
    try:
        try:
            username = kwargs.pop('username')
        except:
            username = None
        
        if username is not None:
            testInfo['username'] = username
        
        try:
            password = kwargs.pop('password')
        except:
            password = None
        
        if password is not None:
            testInfo['password'] = password
        
        try:
            uploadToS3 = bool(kwargs.pop('uploadToS3')) and 'boto3' in sys.modules
        except:
            uploadToS3 = False
        
        try:
            logName = kwargs.pop('logName')
        except:
            logName = None
        
        if logName is None:
            logName = str(os.path.splitext(os.path.basename(str(__file__)))[0])
                
        logNameStamped = str(logName) + (time.strftime("_%F_%T", time.gmtime())).replace(":", "-")
        
        try:
            directory = kwargs.pop('directory')
        except:
            directory = None
        
        if directory is None or directory == 'None' or directory == '':
            directory = str(os.getcwd())

        try:
            if not os.path.isdir(os.path.join(str(directory), str(logNameStamped))):
                os.mkdir(os.path.join(str(directory), str(logNameStamped)))
        except:
            logging.exception("Unable to create sub-directory for test " + str(logNameStamped) + "! Outputting to specified directory instead")
        
        if uploadToS3:
            s3 = boto3.resource('s3', region_name='us-west-2')
            bucket = s3.Bucket(uploadBucket)
            bucket.put_object(Key=urllib.parse.quote(str("output/oes-1.0-automation/" + str(env) + "/" + os.path.basename(directory) + "/")))
        
        try:
            logToFile = bool(kwargs.pop('logToFile'))
        except:
            logToFile = False
        
        try:
            env = kwargs.pop('env')
        except:
            env = "uat"
        
        try:
            headless = kwargs.pop('headless')
        except:
            headless = None

        try:
            threads = kwargs.pop('threads')
        except:
            threads = None
        
        try:
            scoreForm = kwargs.pop('scoreForm')
        except:
            scoreForm = True
        
        try:
            waitTime = kwargs.pop('waitTime')
        except:
            waitTime = None

        try:
            iterations = kwargs.pop('iterations')
        except:
            iterations = None

        try:
            randomResponse = kwargs.pop('random')
        except:
            randomResponse = None

        testModuleArgs = [[env, headless, str(directory), logToFile, logName, uploadToS3, username, password, scoreForm, float(waitTime), int(iterations)] for x in range(int(iterations))]
    
        logging.warning("Current wait time between anwswering questions on form is: " + str(waitTime) + "s")
        logging.warning("Specified number of simultaneous threads is: " + str(threads))
        
        if int(multiprocessing.cpu_count())<int(threads):
            logging.warning("WARNING!!! " + str(threads) + " have been requested, but this machine only has " + str(multiprocessing.cpu_count()) + " cores available! This will likely be the upper limit for simultaneous operations.")
        
        logging.warning("Specified number of iterations per thread is: " + str(iterations))

        try:
            with multiprocessing.Pool(processes=int(threads)) as pool:
                pool.starmap(runTestThread, testModuleArgs)
        except:
            logging.exception("Some tests encountered error!!! Further tests may be compromised, investigate logs!!!")
        
        logging.warning("Test completed!\r\n")

def runTestThread(env="uat", headless=False, directory=None, logToFile=False, logName=None, uploadToS3=False, username=None, password=None, scoreForm=True, waitTime=0.1, iterations=1):
    try:
        if directory is None:
            directory = str(os.getcwd())

        
        
        if logName is None:
            logName = str(multiprocessing.current_process().name)
            try:
                if not os.path.isdir(os.path.join(str(directory), str(logName))):
                    os.mkdir(os.path.join(str(directory), str(logName)))
            except:
                logging.error("Unable to create sub-directory for test case " + str(logName) + "! Outputting to specified directory instead")
        
        logNameStamped = str(logName) + (time.strftime("_%F_%T", time.gmtime())).replace(":", "-")
        
        if logToFile:
            logging.warning("Setting up logfile at " + os.path.join(str(directory), str(logName), str(logNameStamped)+'.log'))
            loggingSetup(output=os.path.join(str(directory), str(logName), str(logNameStamped)+'.log'))
        else:
            loggingSetup()
            
        logger = logging.getLogger(str(logNameStamped))
        
        logger.info("Specified output directory is: " + os.path.join(str(directory), str(logName)))

        runTestIterations(env=env, headless=headless, directory=os.path.join(str(directory), str(logName)), logName=logger, username=username, password=password, scoreForm=scoreForm, waitTime=waitTime, iterations=iterations)
        
    finally:
        if uploadToS3:
            s3 = boto3.resource('s3', region_name='us-west-2')
            bucket = s3.Bucket(uploadBucket)
            
        for subdir, dirs, files in os.walk(str(os.path.join(str(directory), str(logName)))):
            for file in files:
                full_path = os.path.join(subdir, file)
                # sometimes downloading a file takes long enough that Chrome doesn't get to rename
                # so we'll clean that up manually
                if os.path.splitext(str(file))[1] == '.crdownload':
                    os.rename(full_path, os.path.splitext(full_path)[0])
                if uploadToS3:
                    with open(full_path, 'rb') as data:
                        mimetypes.add_type('text/plain', '.log')
                        contentType = mimetypes.guess_type(full_path)[0]
                        if 'text' in contentType:
                            # we're explicitly writing all of our text files in UTF-8, so we're confident in this
                            contentType = contentType + '; charset=utf-8'
                        # bucket.put_object(Key=str("output/oes-1.0-automation/" + str(env) + "/" + os.path.basename(directory) + "/" + str(logName) + "/" + file), Body=data, ContentType=contentType)
                        uploadKey = str("output/oes-1.0-automation/" + str(env) + "/" + os.path.basename(directory) + "/" + str(logName) + "/" + file)
                        bucket.put_object(Key=urllib.parse.quote(uploadKey), Body=data, ContentType=contentType)
                        logger.warning("Files uploaded to S3 at: s3://" + uploadBucket + "/" + uploadKey)

def runTestIterations(env="uat", headless=False, directory=None, logName=None, username=None, password=None, scoreForm=True, waitTime=0.1, iterations=1):
    try:
        if logName is None:
            logName = os.path.join(str(directory), os.path.basename(str(directory)), ".log")
        
        try:
            # username = testInfo['username']
            if username is not None and username == '':
                username = None
        except:
            username = None
        
        try:
            # password = testInfo['password']
            if password is not None and password == '':
                password = None
        except:
            password = None
    
        if env=="staging":
            loginUrl = "https://platform.stage.wpspublish.com"
        elif env=="uat":
            loginUrl = "https://practitioner-uat.wpspublish.io"
        elif env=="qa":
            loginUrl = "https://practitioner-qa.wpspublish.io"
        elif env=="prod":
            loginUrl = "https://platform.wpspublish.com"
        elif env=="dev":
            loginUrl = "https://practitioner-dev.wpspublish.io"
        elif env=="dev2":
            loginUrl = "https://practitioner-dev2.wpspublish.io"
        elif env=="dev1":
            loginUrl = "https://practitioner-dev1.wpspublish.io"
        elif env=="qa1":
            loginUrl = "https://practitioner-qa1.wpspublish.io"
        elif env=="uat1":
            loginUrl = "https://practitioner-uat1.wpspublish.io"
        elif env=="perf":
            loginUrl = "https://platform.perf.wpspublish.com"
        else:
            loginUrl = env
                
        clientDate = adjustedDateCalculator(yearsAdjust=9, monthsAdjust=6, daysAdjust=3)
        clientYear = str(clientDate.year)
        clientMonth = str(clientDate.month)
        clientDay = str(clientDate.day)
        
        
        assessmentType = 'spm'
        assessmentForm = 'Art Class (ART) Form'
        respondentName = None
        administrationDate = None
        
        Prac = oesPractitioner(loginUrl, username=username, password=password, logName=logName)
        logger = Prac.logger
        Prac.headless = headless
        if directory is None:
            Prac.download_dir = str(os.getcwd())
        else:
            Prac.download_dir = str(directory)
        
        Prac.setUp()
        Prac.login()        
        
        for x in range(iterations):
            logger.warning("Starting iteration "+str(x+1))

            Prac.createNewClient(
            clientMonth=clientMonth, 
            clientDay=clientDay, 
            clientYear=clientYear
            )
            
            Prac.administerAssessment(assessmentType=assessmentType, assessmentForm=assessmentForm, respondentName=respondentName, administrationDate=administrationDate)
            Prac.switchToRespondent()
            Resp = oesRespondent(browser=Prac.browser, assessment=assessmentType, scoreOnly=Prac.scoreOnly, logName=Prac.logger)
            Resp.navigateToQuestions(argsList='random', directory=Prac.download_dir)
            Resp.completeAssessmentRandomly(waitTime=waitTime)
            Resp.submit()

            Prac.switchToPractitioner()
            Prac.browser.refresh()
            
            Prac.selectByAdministrationFormGUID(administrationFormGUID=Resp.administrationFormGUID)
            Prac.validateForm(argsList='random')
            
            if scoreForm:
                Prac.scoreForm()
            
            # Mostly just sets the stage for the next iteration if you're not scoring for whatever reason
            Prac.browser.get(Prac.loginUrl + "/case")
    except:
        try:
            try:
                logger.exception("Iteration failed!!!")
            except:
                logging.exception("Iteration failed!!!")
            errShotName = str("failed_" + str(multiprocessing.current_process().name) + "_" + str(multiprocessing.Process().name).replace(":", "-") + (time.strftime("_%F_%T", time.gmtime())).replace(":", "-") + ".png")
            try:
                logger.exception("Saving error screenshot '" + str(errShotName) + "'...")
            except:
                logging.exception("Saving error screenshot '" + str(errShotName) + "'...")
            Prac.browser.save_screenshot(os.path.join(str(directory), str(errShotName)))
        except:
            try:
                logger.exception("Saving screenshot failed!!!")
            except:
                logging.exception("Saving screenshot failed!!!")
        finally:
            raise
    finally:
        try:
            Prac.switchToPractitioner()
        except:
            pass
        
        try:
            Prac.logout()
            Prac.tearDown()
        except:
            pass

def gen_chunks(reader, chunksize=100):
    # not being used right now but you never know...
    chunk = []
    for row, line in enumerate(reader):
        if (row % chunksize == 0 and row > 0):
            yield chunk
            del chunk[:]
        chunk.append(line[0])
    yield chunk

if __name__ == "__main__":
    
    short_options = "he:d:lusw:t:i:"
    long_options = ["headless", "env=", "directory=", "log-to-file", "upload", "username=", "password=", "skip-scoring", "wait-time=", "threads=", "iterations="]
    
    # Get full command-line arguments
    full_cmd_arguments = sys.argv
    argument_list = full_cmd_arguments[1:]

    env = "uat"
    headless = False
    
    # This is being kept for compatibility purposes; it doesn't do anything
    random = False
    
    directory = None
    logToFile = False
    logName = None
    uploadToS3 = False
    username = None
    password = None
    scoreForm = True
    waitTime = 0.1
    threads = 1
    iterations = 1
    
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
        elif current_argument in ("-d", "--directory"):
            directory = current_value
        elif current_argument in ("-w", "--wait-time"):
            waitTime = float(current_value)
        elif current_argument in ("-t", "--threads"):
            threads = int(current_value)
        elif current_argument in ("-i", "--iterations"):
            iterations = int(current_value)
        elif current_argument in ("-l", "--log-to-file"):
            logToFile = True
        elif current_argument in ("-s", "--skip-scoring"):
            scoreForm = False
        elif current_argument in ("-u", "--upload") and 'boto3' in sys.modules:
            uploadToS3= True
        elif current_argument in ("--username"):
            username = str(current_value)
        elif current_argument in ("--password"):
            password = str(current_value)

    if directory is None or directory == 'None' or directory == '':
        directory = str(os.getcwd())
    
    # try:
        # directory = str(os.path.join(str(directory), str(os.path.splitext(os.path.basename(str(sys.argv[0])))[0] + (time.strftime("_%F_%T", time.gmtime())).replace(":", "-"))))
        # os.mkdir(directory)
    # except:
        # logging.exception("Unable to create sub-directory for all tests! Outputting to specified directory instead")
    
    # logging.warning("Current output directory is: " + str(directory))
        
    testModuleArgs = [[env, headless, str(directory), logToFile, logName, uploadToS3, username, password, scoreForm, float(waitTime), int(iterations)] for x in range(int(threads))]
    
    if uploadToS3:
        logging.warning("S3 upload is currently enabled")
    
    if logToFile:
        logging.warning("Logging to file is enabled; each test case will log to file instead of console")
    
    if headless:
        logging.warning("Headless mode is enabled; browser sessions will not be displayed!")
    
    logging.warning("Current wait time between anwswering questions on form is: " + str(waitTime) + "s")
    logging.warning("Specified number of simultaneous threads is: " + str(threads))
    
    if int(multiprocessing.cpu_count())<int(threads):
        logging.warning("WARNING!!! " + str(threads) + " have been requested, but this machine only has " + str(multiprocessing.cpu_count()) + " cores available! This will likely be the upper limit for simultaneous operations.")
    
    logging.warning("Specified number of iterations per thread is: " + str(iterations))

    try:
        with multiprocessing.Pool(processes=int(threads)) as pool:
            pool.starmap(runTestThread, testModuleArgs)
    except:
        logging.exception("Some tests encountered error!!! Further tests may be compromised, investigate logs!!!")
    
    logging.warning("Test completed!\r\n")
