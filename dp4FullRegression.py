# -*- coding: UTF-8 -*-
# DP-4 test module for OES 1.0
# Requirements:
# Selenium Driver: https://www.selenium.dev/downloads/
# Chrome Driver: https://chromedriver.chromium.org/downloads
# The dateutil libraries for Python 3: https://pypi.org/project/python-dateutil/
# The pytz libraries for Python 3: https://pypi.org/project/pytz/
# The openpyxl libraries for Python 3: https://pypi.org/project/openpyxl/
# The pdfminer libraries for Python 3: https://pypi.org/project/pdfminer/
# For default credentials and S3 upload, boto3: https://boto3.amazonaws.com/v1/documentation/api/latest/guide/quickstart.html
# Usage: python dp4Regression.py [-h] [-r] [-e] [-d] [-l] [-u]
# Arguments:
# -h, --headless:       Specifies headless or display mode for browser (default False)
# -r, --random:         Specifies random or set response mode for assessment (default False)
# -e, --env:            Specifies the environment to login and perform actions (default "uat")
# -d, --directory:      Specifies the directory to save any downloaded PDFs (default current working directory)
# -l, --log-to-file:    Specifies whether to log to the terminal output or to a text file in --directory (default False)
# --username:           Specifies a username to use for logging in; default credentials require S3, so required if S3 not available
# --password:           Specifies a password to use for logging in; default credentials require S3, so required if S3 not available

import sys

from oesLibrary import *
from dateutil.relativedelta import *
from datetime import date
# from productExcelToModuleData import * >> These are now packaged in oesLibrary
# from pdf_process import * >> These are now packaged in oesLibrary
import getopt, csv, os, re, mimetypes
import pprint, platform, shutil
import pytz, boto3, json
from contextlib import redirect_stdout, redirect_stderr

todaysDate = date.today()
uploadBucket = 'wps-qa-automation'


def runTestModule(kwargs):
    try:
        username = kwargs.pop('username')
    except:
        username = None
    
    try:
        password = kwargs.pop('password')
    except:
        password = None
    
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
        randomResponse = kwargs.pop('random')
    except:
        randomResponse = None
    
    try:
        uploadToS3 = bool(kwargs.pop('uploadToS3')) and 'boto3' in sys.modules
    except:
        uploadToS3 = False
    
    try:
        logName = kwargs.pop('logName')
    except:
        logName = None
    
    # if logName is None:
        # logName = str(os.path.splitext(os.path.basename(str(sys.argv[0])))[0] + (time.strftime("_%F_%T", time.gmtime())).replace(":", "-"))
    
    if logName is None:
        logName = str(os.path.splitext(os.path.basename(str(__file__)))[0])
            
    logNameStamped = str(logName) + (time.strftime("_%F_%T", time.gmtime())).replace(":", "-")
    
    try:
        directory = kwargs.pop('directory')
    except:
        directory = None
    
    if directory is None or directory == 'None' or directory == '':
        directory = str(os.getcwd())
    
    # try:
        # if not os.path.isdir(os.path.join(str(directory), str(logName))):
            # os.mkdir(os.path.join(str(directory), str(logName)))
        # directory = os.path.join(str(directory), str(logName))
    # except:
        # loggingPrint("Unable to create sub-directory for all tests! Outputting to specified directory instead")
    
    try:
        if not os.path.isdir(os.path.join(str(directory), str(logNameStamped))):
            os.mkdir(os.path.join(str(directory), str(logNameStamped)))
    except:
        logging.exception("Unable to create sub-directory for test suite " + str(logNameStamped) + "! Outputting to specified directory instead")
    
    # try:
        # # there should be a symlink to the X: drive with the updated spreadsheet
        # # use it to copy the latest version of the test spreadsheet into the Git directory
        # shutil.copy2(os.path.join(str("DP4 Sample Testcases_" + platform.system()), "DP4_Samples_Testcases_FINAL_With_DateControl.xlsx"), os.getcwd())
    # finally:
        # inputFile = "DP4_Samples_Testcases_FINAL_With_DateControl.xlsx"
    inputFile = "DP4_Samples_Testcases_FINAL_With_DateControl.xlsx"
    
    sheets, directionTextList, questionTextList, reports = convertXls(input=inputFile)
    
    if uploadToS3:
        s3 = boto3.resource('s3', region_name='us-west-2')
        bucket = s3.Bucket(uploadBucket)
        bucket.put_object(Key=str("output/oes-1.0-automation/" + str(env) + "/" + os.path.basename(directory) + "/"))
    
    referencePDFs = {}
    logging.warning("Generating listing of reference PDFs for later comparison...")
    for subdir, dirs, files in os.walk(str("DP-4 REPORT PDF")):
        for file in files:
            referencePDFs[file] = os.path.join(subdir, file)
    
    dataInputs = [[env, headless, randomResponse, str(directory), logToFile, logName, uploadToS3, username, password, [sheet]+sheets[sheet], directionTextList[sheets[sheet][0]['assessmentform']], questionTextList[sheets[sheet][0]['assessmentform']], referencePDFs] for sheet in sheets.keys()]
    
    return_val = None
    
    try:
        with multiprocessing.Pool(processes=4) as pool:
            return_val = pool.starmap(runTestSheet, dataInputs)
    except:
        logging.error("Some tests encountered error!!! Further tests may be compromised, investigate logs!!!")
    
    for sheet, formid in return_val:
        sheets[str(sheet)][0]['formid'] = str(formid)
    
    # Start running Reports
    
    try:
        if not os.path.isdir(os.path.join(str(directory), "Reports")):
            os.mkdir(os.path.join(str(directory), "Reports"))
    except:
        logging.error("Unable to create sub-directory for all reports! Outputting to specified directory instead")
    
    for type in set([report['report type'] for report in reports]):
        try:
            if not os.path.isdir(os.path.join(str(directory), str(type).replace('/', '-').replace('\\', '-').replace('_', '-'))):
                os.mkdir(os.path.join(str(directory), "Reports", str(type).replace('/', '-').replace('\\', '-').replace('_', '-')))
        except:
            logging.exception("Unable to create sub-directory for test group " + str(type) + "! Outputting to current directory " + str(directory) + " instead")
    
    
    dataInputs = [[env, headless, str(directory), logToFile, None, uploadToS3, username, password, report, sheets[report['forms'][0][0]][0], referencePDFs] for report in reports]
    
    with multiprocessing.Pool(processes=4) as pool:
        pool.starmap(runReportsModule, dataInputs)

def runTestSheet(env="uat", headless=False, randomResponse=False, directory=None, logToFile=False, logName=None, uploadToS3=False, username=None, password=None, sheet=None, directionsTexts=None, questionsText=None, referencePDFs=None):

    return_val = None
    try:
        if directory is None:
            directory = str(os.getcwd())

        # if logName is None:
            # logName = str(report['reference']).replace('.pdf','')
        
        if logName is None:
            logName = str(sheet[0])
            try:
                if not os.path.isdir(os.path.join(str(directory), str(logName))):
                    os.mkdir(os.path.join(str(directory), str(logName)))
            except:
                logging.error("Unable to create sub-directory for test case " + str(logName) + "! Outputting to specified directory instead")
        
        logNameStamped = str(logName) + (time.strftime("_%F_%T", time.gmtime())).replace(":", "-")
        
        # if logToFile:
            # with open(os.path.join(os.path.join(str(directory), str(logName)), str(logName + (time.strftime("_%F_%T", time.gmtime())).replace(":", "-") + ".txt")), 'w', encoding='utf-8') as f:
                # with redirect_stdout(f), redirect_stderr(f):
                    # logging.info("Current output directory is: " + str(directory))
        
                    # try:
                        # if not os.path.isdir(os.path.join(str(directory), str(logName))):
                            # os.mkdir(os.path.join(str(directory), str(logName)))
                    # except:
                        # logging.exception("Unable to create sub-directory for test case " + str(logName) + "! Outputting to current directory instead")
                    
                    # return_val = runTest(env=env, headless=headless, randomResponse=randomResponse, directory=os.path.join(str(directory), str(logName)), username=username, password=password, sheet=sheet, directionsTexts=directionsTexts, questionsText=questionsText, referencePDFs=referencePDFs)
        # else:
            # logging.info("Current output directory is: " + str(directory))
        
            # try:
                # if not os.path.isdir(os.path.join(str(directory), str(logName))):
                    # os.mkdir(os.path.join(str(directory), str(logName)))
            # except:
                # logging.exception("Unable to create sub-directory for test case " + str(logName) + "! Outputting to current directory instead")
        if logToFile:
            logging.warning("Setting up logfile at " + os.path.join(str(directory), str(logName), str(logNameStamped)+'.log'))
            loggingSetup(output=os.path.join(str(directory), str(logName), str(logNameStamped)+'.log'))
        else:
            loggingSetup()
            
        logger = logging.getLogger(str(logNameStamped))
        
        logger.info("Specified output directory is: " + os.path.join(str(directory), str(logName)))
        
        return_val = runTest(env=env, headless=headless, randomResponse=randomResponse, directory=str(os.path.join(str(directory), str(logName))), logName=logger, username=username, password=password, sheet=sheet, directionsTexts=directionsTexts, questionsText=questionsText, referencePDFs=referencePDFs)
    except:
        try:
            logger.exception("Failed to run test case!!!")
        except:
            logging.exception("Failed to run test case!!!")
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
                        uploadKey = str("output/oes-1.0-automation/" + str(env) + "/" + todaysDate.strftime("%m-%d-%Y") + "/" + os.path.basename(directory) + "/" + str(logName) + "/" + file)
                        bucket.put_object(Key=uploadKey, Body=data, ContentType=contentType)
                        logger.warning("Files uploaded to S3 at: s3://" + uploadBucket + "/" + uploadKey)
                        
        return return_val
    

    
def runTest(env="uat", headless=False, randomResponse=False, directory=None, logName=None, username=None, password=None, sheet=None, directionsTexts=None, questionsText=None, referencePDFs=None):
    #for sheet in sheets:
    logging.info("Beginning test case '" + str(sheet[0]) + "'")
    # testInfo = sheet[1]
    # argsListAssessment = sheet[2]
    # argsListValidation = sheet[3]
    # argsListAssessment.extend(argsListValidation)
    # questionList = sheet[4]
    # scoreTable = sheet[5]
    # scaleComparison = sheet[6]
    return_val = None    
    
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
    
    Prac = oesPractitioner(loginUrl, username=username, password=password, logName=logName)
    logger = Prac.logger
    Prac.headless = headless
    if directory is None:
        Prac.download_dir = str(os.getcwd())
    else:
        Prac.download_dir = str(directory)
    
    Prac.setUp()

    try:
        Prac.login()
        completedFormGUID = completeAssessmentForm(env, headless, randomResponse, directory, Prac, sheet, directionsTexts, questionsText)
        completedFormID = Prac.getFormIdFromAdministrationFormGUID(administrationFormGUID=completedFormGUID)
        return_val = (str(sheet[0]), str(completedFormID))
        # # adding a 5s sleep to ensure all the files are completely generated properly
        # time.sleep(5)
    except:
        try:
            logger.exception("Regression failed!!!")
            Prac.browser.save_screenshot(os.path.join(str(directory), "regression_failed_" + (time.strftime("_%F_%T", time.gmtime())).replace(":", "-") + ".png"))
        except:
            logging.exception("Saving screenshot failed!!!")
        finally:
            raise
    finally:
        try:
            try:
                referencePDF = referencePDFs[str(sheet[1]['reference'])]
            except:
                referencePDF = None
            
            if referencePDF is not None and referencePDF != '':
                pdfDownload = None
                logger.info("Confirming successful PDF download...")
                for subdir, dir, files in os.walk(str(str(directory))):
                    for file in files:
                        if os.path.splitext(file)[1].lower()=='.pdf':
                            pdfDownload = os.path.join(subdir, file)
                            break
                            
                if pdfDownload is not None and pdfDownload != '':
                    logger.info("Download successful, performing PDF comparison...")
                    logger.info("Reference PDF: " + referencePDF)
                    logger.info("Generated PDF: " + os.path.basename(pdfDownload))
                    pdfCompare = oesPDFObject(logName=logName, directory=directory)
                    pdfResult = pdfCompare.scorePdfCompare(referencePDF, pdfDownload)
                    if pdfResult == []:
                        logger.info("PDFs match")
                    else:
                        hasDiffs = True
                        mse = None
                        logger.warning("Text compare found differences, generating diff screenshots...")
                        try:
                            # The 47.85 Mean Squared Error threshold was determined through trial-and-error to account only for different Report ID and dates
                            hasDiffs, mse = pdfCompare.pdfImageCompare(referencePDF, pdfDownload, mseThreshold=47.85)
                        except:
                            logger.exception("Failed to generate diff screenshots!!!")

                        if hasDiffs or mse is None:
                            filename = str("pdf_compare" + (time.strftime("_%F_%T", time.gmtime())).replace(":", "-") + ".txt")
                            logger.warning("PDFs DO NOT MATCH!!! Generating diff file " + filename)
                            with open(os.path.join(str(str(directory)), filename), 'a', encoding='utf-8') as f:
                                with redirect_stdout(f), redirect_stderr(f):
                                    for line in pdfResult:
                                        print(line)
                                    
                                    # print("Reference PDF: " + referencePDF)
                                    # print("Generated PDF: " + os.path.basename(pdfDownload))
                                    # print('')
                                    # for i in range(len(pdfResult)):
                                        # print(pdfResult[i])
                                        # print(pdfResult[i+1])
                                        # print()
                                        # i+=2
                        else:
                            logger.warning("Image compare passed, Mean Squared Error " + str(mse) + " below 47.85 threshold")
                            try:
                                shutil.rmtree(os.path.join(str(str(directory)), "diffs"))
                            except:
                                pass
                            
                            
                else:
                    logger.warning("No PDF was generated to compare to reference!")
                    logger.warning("Attempting to score or re-download...")
                    Prac.selectByAdministrationFormGUID(administrationFormGUID=completedFormGUID)
                    Prac.scoreForm(shouldSucceed=scoreForm, expectedResponse=validateFormMessage, demoResponses=argsListValidation)
            else:
                logger.info("No reference PDF provided, skipping PDF comparison check...")
        except:
            logger.error("Encountered an error attempting to perform PDF comparison!!!")
            logging.exception("PDF Compare Failed")
        
        try:
            Prac.logout()   
            Prac.tearDown()
        except:
            pass
        
        
        try:
            if return_val is None:
                return_val = (str(sheet[0]), '')
        except:
            return_val = (str(sheet[0]), '')
        
        return return_val

def completeAssessmentForm(env="uat", headless=False, randomResponse=False, directory=None, Prac=None, sheet=None, directionsTexts=None, questionsText=None):
# def runTest(env="uat", headless=False, randomResponse=False, directory=None, input=None, waitTime=None):
    testInfo = sheet[1]
    argsListAssessment = sheet[2]
    argsListValidation = sheet[3]
    # argsListAssessment.extend(argsListValidation)
    questionList = sheet[4]
    scoreTable = sheet[5]
    scaleComparison = sheet[6]
    
    logger = Prac.logger
    
    if headless:
        logger.info("Running in headless mode")
    else:
        logger.info("Running in display mode")
    
    if randomResponse:
        logger.info("Running in random response mode")
    else:
        logger.info("Running in set response mode")
    
    try:
        # The "calculation of client birthdate from their age" logic has been shifted from calculation in Excel to within the test module
        # This is due to an issue where Excel only updates dynamic values upon save, so any formula using a value such as "TODAY()" is unreliable
        
        try:
            if testInfo['administrationdate'] is None or testInfo['administrationdate'] == '' or testInfo['administrationdate'] == 'None':
                logger.warning("Provided Administration Date is empty string, setting to current date in Pacific timezone!!!")
                administrationDate = pytz.utc.localize(dt=datetime.utcnow()).astimezone(pytz.timezone("America/Los_Angeles")).strftime("%m/%d/%Y")
            else:
                administrationDate = testInfo['administrationdate'].split(' ')
                for x in range(len(administrationDate)):
                    if administrationDate[x] in ['year', 'years', 'años', 'año']:
                        adminYears = administrationDate[x-1]
                    elif administrationDate[x] in ['months', 'month', 'meses', 'mes']:
                        adminMonths = administrationDate[x-1]
                    elif administrationDate[x] in ['days', 'day', 'dia', 'dias']:
                        adminDays = administrationDate[x-1]
                
                try:
                    administrationDate = '{d.month}/{d.day}/{d.year}'.format(d=adjustedDateCalculator(yearsAdjust=int(adminYears), monthsAdjust=int(adminMonths), daysAdjust=int(adminDays)))
                except:
                    administrationDate = '{d.month}/{d.day}/{d.year}'.format(d=adjustedDateCalculator(yearsAdjust=adminYears, monthsAdjust=adminMonths, daysAdjust=adminDays))
        except:
            logger.warning("Provided Administration Date is , setting to current date in Pacific timezone!!!")
            administrationDate = pytz.utc.localize(dt=datetime.utcnow()).astimezone(pytz.timezone("America/Los_Angeles")).strftime("%m/%d/%Y")

        logger.info("Administration date has been specified as " + str(administrationDate))
        
        try:
            clientAge = adjustedDateCalculator(yearsAdjust=int(int(testInfo['clientageyears'])+int(adminYears)), monthsAdjust=int(int(testInfo['clientagemonths'])+int(adminMonths)), daysAdjust=int(int(testInfo['clientagedays'])+int(adminDays)))
        except:
            logger.exception("Error getting client age!")
            try:
                logger.error("Client Years: " + testInfo['clientageyears'])
            except:
                logger.exception("Error with Client Years!!!")

            try:
                logger.error("Client Months: " + testInfo['clientagemonths'])
            except:
                logger.exception("Error with Client Months!!!")

            try:
                logger.error("Client Days: " + testInfo['clientagedays'])
            except:
                logger.exception("Error with Client Days!!!")
                
            logger.error(testInfo)
            
            raise
        
        try:
            clientYear = str(clientAge.year)
        except:
            clientYear = None
            
        try:           
            clientMonth = str(clientAge.month)
        except:
            clientMonth = None
            
        try:
            clientDay = str(clientAge.day)
        except:
            clientDay = None
        
        try:
            if testInfo['clientfirstname'] != '':
                clientFirstName = testInfo['clientfirstname']
            else:
                clientFirstName = randomString()
        except:
            clientFirstName = randomString()
            
        try:
            if testInfo['clientlastname'] != '':
                clientLastName = testInfo['clientlastname']
            else:
                clientLastName = randomString()
        except:
            clientLastName = randomString()
        
        # Technically, this should be "None", but until the new PDF checking logic is implemented, lock it
        try:
            if testInfo['clientcaseid'] != '':
                clientCaseID = testInfo['clientcaseid']
            else:
                # clientCaseID = None
                clientCaseID = 'ugGSvu'
        except:
            # clientCaseID = None
            clientCaseID = 'ugGSvu'
        
        try:
            if testInfo['clientgender'] != '':
                clientGender = (testInfo['clientgender'][0]).upper() + (testInfo['clientgender'][1:]).lower()
                if clientGender not in ["Female", "Male"]:
                    logger.warning("Invalid client gender option provided! Using random instead")
                    clientGender = None
            else:
                clientGender = None
        except:
            clientGender = None
            
        try:
            if testInfo['clientemail'] != '':
                regex = '^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'
                if(re.search(regex, testInfo['clientemail'])):  
                    clientEmail = testInfo['clientemail']
                else:  
                    logger.warning("Invalid client email provided! Using random instead")
                    clientEmail = None
            else:
                clientEmail = None
        except:
            clientEmail = None
            
        
        try:    
            Prac.navigateToClient(str(clientFirstName + " " + clientLastName))
            Prac.updateClient(
            clientFirstName=clientFirstName,
            clientLastName=clientLastName,
            clientMonth=clientMonth, 
            clientDay=clientDay, 
            clientYear=clientYear,
            clientCaseID=clientCaseID,
            clientEmail=clientEmail,
            clientGender=clientGender
            )
        except:
            Prac.createNewClient(
            clientFirstName=clientFirstName,
            clientLastName=clientLastName,
            clientMonth=clientMonth, 
            clientDay=clientDay, 
            clientYear=clientYear,
            clientCaseID=clientCaseID,
            clientEmail=clientEmail,
            clientGender=clientGender
            )
        
        try:
            assessmentType = str(testInfo['assessmenttype']).lower()
            # assessmentType = str(re.sub('[^0-9a-zA-Z]+', ' ', testInfo['assessmenttype'])).lower()
            # if assessmentType != '':
                # if assessmentType not in ['dp3', 'abas3', 'spm', 'spmp', 'ppascale', 'srs2', 'smalsi', 'casl2', 'opus', 'scq', 'arizona4', 'rcmas2', 'dbc2', 'piersharris3', 'rise', 'caps', 'dp4']:
                    # loggingPrint("Invalid assessment type provided! Using random instead")
                    # assessmentType = None
            # else:
                # assessmentType = None
        except:
            assessmentType = None
        logger.info("Assessment type has been specified as " + str(assessmentType))        
        
        try:
            assessmentForm = testInfo['assessmentform']
            if assessmentForm == '':
                assessmentForm = None
        except:
            assessmentForm = None
        
        logger.info("Assessment form has been specified as " + str(assessmentForm))        
        
        try:
            respondentName = testInfo['respondentname']
            if respondentName == '':
                respondentName = None
            else:
                respondentName = respondentName  + " " + pytz.utc.localize(dt=datetime.utcnow()).astimezone(pytz.timezone("America/Los_Angeles")).strftime("%I-%M-%S%p")
        except:
            respondentName = None
        
        logger.info("Assessment respondent has been specified as " + str(respondentName))    
        
        Prac.administerAssessment(assessmentType=assessmentType, assessmentForm=assessmentForm, respondentName=respondentName, administrationDate=administrationDate)
        Prac.switchToRespondent()
        
        if assessmentType is None:
            dp4Resp = oesRespondent(browser=Prac.browser, logName=Prac.logger)
        else:
            dp4Resp = oesRespondent(browser=Prac.browser, assessment=assessmentType, scoreOnly=Prac.scoreOnly, logName=Prac.logger)

        directionsText = ''
        try:
            directionsText = directionsTexts['Directions']
        except:
            try:
                # This is for the backwards-compatibility case if it's just a string and not bundled with the legend
                directionsText = directionsTexts
            except:
                directionsText = ''

        if directionsText is not None and directionsText != '':
            dp4Resp.verifyDirectionsText(directionsText=str(directionsText), directory=str(directory))
        
        for section in argsListAssessment.keys():
            for field in argsListAssessment[section].keys():
                if field.lower() in ["administration date", "fecha de la administración", 'fecha de hoy']:
                    # administrationDate = argsListAssessment[section][field].split(' ')
                    # for x in range(len(administrationDate)):
                        # if administrationDate[x] in ['year', 'years', 'años', 'año']:
                            # adminYears = administrationDate[x-1]
                        # elif administrationDate[x] in ['months', 'month', 'meses', 'mes']:
                            # adminMonths = administrationDate[x-1]
                        # elif administrationDate[x] in ['days', 'day', 'dia', 'dias']:
                            # adminDays = administrationDate[x-1]
                    
                    #argsListAssessment[section][field] = adjustedDateCalculator(yearsAdjust=adminYears, monthsAdjust=adminMonths, daysAdjust=adminDays).strftime("%m/%d/%Y")
                    try:
                        adminDate = adjustedDateCalculator(yearsAdjust=int(adminYears), monthsAdjust=int(adminMonths), daysAdjust=int(adminDays))
                    except:
                        adminDate = adjustedDateCalculator(yearsAdjust=adminYears, monthsAdjust=adminMonths, daysAdjust=adminDays)
                    
                    if adminDate > todaysDate:
                        argsListAssessment[section][field] = '{d.month}/{d.day}/{d.year}'.format(d=todaysDate)
                    else:
                        argsListAssessment[section][field] = '{d.month}/{d.day}/{d.year}'.format(d=adminDate)
                elif field.lower() in ["date of birth", "fecha de nacimiento"]:
                    #argsListAssessment[section][field] = clientAge.strftime("%m/%d/%Y")
                    argsListAssessment[section][field] = '{d.month}/{d.day}/{d.year}'.format(d=clientAge)
                elif field.lower() in ["child's name", "name", "nombre del niño o de la niña", "nombre", "name of child being evaluated", "name of student being evaluated", "name of individual being evaluated", 'nombre del/de la niño/a que está siendo evaluado/a', 'nombre del/de la estudiante que está siendo evaluado/a', 'nombre del individuo que está siendo evaluado/a']:
                    argsListAssessment[section][field] = str(clientFirstName + " " + clientLastName)
        
        logger.info("Populating assessment form fields: " + str(argsListAssessment))
        dp4Resp.navigateToQuestions(demoResponses=argsListAssessment, directory=str(directory))
        
        try:
            waitTime = testInfo['waittime']
            if waitTime == '':
                waitTime = 0.2
        except:
            waitTime = 0.2
        
        if randomResponse:
            dp4Resp.completeAssessmentRandomly(waitTime=float(waitTime))
        else:
            if dp4Resp.singleView:
                submitFound = False
                
                while not submitFound:
                    section = dp4Resp.getCurrentSection()
                    try:
                        qNum = int(dp4Resp.browser.execute_script("return singleSectionList[sectionCounter].ItemAndResponseList[sectionItemCounter].ItemNo;"))
                    except:
                        qNum = 0
                        
                    if qNum > 0:
                        sectionQuestions = questionList[section]
                        try:
                            questionResponseVals = questionList[section][str('q' + str(qNum))]
                            for questionResponseVal in questionResponseVals:
                                logger.info("Answering question number " + str(qNum) + " in section " + str(section) + " with response of " + str(questionResponseVal))
                                if str(questionResponseVal).lower() not in ["skip", "randomanswer"]:
                                    answerSuccess = dp4Resp.answerQuestion(questionNumber=qNum, questionResponse=str(questionResponseVal))
                                    time.sleep(float(waitTime))
                                    if not answerSuccess:
                                        logger.warning("Failed to successfully confirm question response! Trying a second time...")
                                        time.sleep(float(waitTime))
                                        answerSuccess = dp4Resp.answerQuestion(questionNumber=qNum, questionResponse=str(questionResponseVal))
                                        if not answerSuccess:
                                            logger.warning("Failed to successfully confirm question response! Trying one more time...")
                                            time.sleep(float(waitTime))
                                            answerSuccess = dp4Resp.answerQuestion(questionNumber=qNum, questionResponse=str(questionResponseVal))
                                            if not answerSuccess:
                                                try:
                                                    logger.error("Failed to successfully confirm question response three times!!! Attempting to save screenshot...")
                                                    Prac.browser.save_screenshot(os.path.join(str(directory), "response_failed_" + str(qNum) + (time.strftime("_%F_%T", time.gmtime())).replace(":", "-") + ".png"))
                                                except:
                                                    logging.exception("Saving screenshot failed!!!")
                                elif questionResponseVal == "randomAnswer":
                                    dp4Resp.answerQuestion(questionNumber=qNum)
                                    time.sleep(float(waitTime))
                        except:
                            logger.exception("Question/response is missing or invalid; answering question randomly instead!")
                            dp4Resp.answerQuestion(questionNumber=qNum)
                            time.sleep(float(waitTime))

                    try:
                        pageNavButton = dp4Resp.getPageNavButton("next")
                        if pageNavButton.get_attribute("value") in dp4Resp.submitTranslations:
                            logger.info("Submit button found! Disregarding any remaining responses...")
                            submitFound = True
                        else:
                            logger.info("Navigating to next page...")
                            dp4Resp.nextPage()
                    except:
                        if Prac.scoreOnly:
                            logger.info("Reached end of assessment! Disregarding any remaining responses...")
                            submitFound = True
                        else:
                            logger.warning("Error checking assessment form navigation; may not have loaded correctly!")

            else:
                for b in questionList.keys(): 
                    section = dp4Resp.getCurrentSection()
                    logger.info("Answering questions in section: " + str(section))
                    
                    questions = sorted({int(k[1:]):v for k,v in questionList[section].items() if any (regex_match(k) for regex_match in [re.compile("^q[0-9]+$").match])}.keys())
                    q = 0
                    # submitFound = False
                    
                    while q < len(questions):
                        numQuestions = len(dp4Resp.getQuestionsInPage())
                        logger.info("Number of questions in page: " + str(numQuestions))
                        if int(numQuestions) > 0:
                            for i in range(1, numQuestions+1):
                                q += 1
                                try:
                                    questionResponseVals = questionList[section][str('q' + str(questions[q-1]))]
                                    for questionResponseVal in questionResponseVals:
                                        logger.info("Answering question number " + str(q) + " with response of " + str(questionResponseVal))
                                        if str(questionResponseVal).lower() not in ["skip", "randomanswer"]:
                                            answerSuccess = dp4Resp.answerQuestion(questionNumber=i, questionResponse=str(questionResponseVal))
                                            time.sleep(float(waitTime))
                                            if not answerSuccess:
                                                logger.warning("Failed to successfully confirm question response! Trying a second time...")
                                                time.sleep(float(waitTime))
                                                answerSuccess = dp4Resp.answerQuestion(questionNumber=i, questionResponse=str(questionResponseVal))
                                                if not answerSuccess:
                                                    logger.warning("Failed to successfully confirm question response! Trying one more time...")
                                                    time.sleep(float(waitTime))
                                                    answerSuccess = dp4Resp.answerQuestion(questionNumber=i, questionResponse=str(questionResponseVal))
                                                    if not answerSuccess:
                                                        try:
                                                            logger.error("Failed to successfully confirm question response three times!!! Attempting to save screenshot...")
                                                            Prac.browser.save_screenshot(os.path.join(str(directory), "response_failed_" + str(i) + (time.strftime("_%F_%T", time.gmtime())).replace(":", "-") + ".png"))
                                                        except:
                                                            logging.exception("Saving screenshot failed!!!")
                                        elif questionResponseVal == "randomAnswer":
                                            dp4Resp.answerQuestion(questionNumber=i)
                                            time.sleep(float(waitTime))
                                except:
                                    logger.exception("Question/response is missing or invalid; answering question randomly instead!")
                                    dp4Resp.answerQuestion(questionNumber=i)
                                    time.sleep(float(waitTime))
                        else:
                            logger.info("No questions found on page")
                        
                        try:
                            pageNavButton = dp4Resp.getPageNavButton("next")
                            if pageNavButton.get_attribute("value") in dp4Resp.submitTranslations:
                                logger.info("Submit button found! Disregarding any remaining responses...")
                                # submitFound = True
                            else:
                                logger.info("Navigating to next page...")
                                dp4Resp.nextPage()
                        except:
                            if Prac.scoreOnly:
                                logger.info("Reached end of assessment! Disregarding any remaining responses...")
                                # submitFound = True
                            else:
                                logger.warning("Error checking assessment form navigation; may not have loaded correctly!")
                        finally:
                            q += len(questions)
                                
        # This is the basal/ceiling check section
        
        # Check for if we even need to do basal/ceiling checks
        basalCeilingChecks = []
        for section in questionList.keys():
            try:
                basalVal = questionList[section]['basal']
                if basalVal == '' or basalVal is None:
                    basalVal = None
            except:
                basalVal = None
                
            try:
                ceilingVal = questionList[section]['ceiling']
                if ceilingVal == '' or ceilingVal is None:
                    ceilingVal = None
            except:
                ceilingVal = None
            if basalVal is not None or ceilingVal is not None:
                basalCeilingChecks.append((section, basalVal, ceilingVal))
                

        if basalCeilingChecks is not None and basalCeilingChecks != []:
            # We have to jump out of the questions because if you're in a section it doesn't show basal/ceiling
            # Might as well be the very first section since that's easiest to detect and guaranteed usable
            dp4Resp.jumpToSection(dp4Resp.getFirstSection())
            
            for section, basalVal, ceilingVal in basalCeilingChecks:
                dp4Resp.basalCeilingCheck(section=section, basal=basalVal, ceiling=ceilingVal, directory=str(directory))
                
            nextSectionButtonXPath = "//*/input[@type='button' and @class='next' and not(contains(@class, 'beforeComplete'))]"
            nextSectionButton = WebDriverWait(dp4Resp.browser, 10).until(EC.presence_of_element_located((By.XPATH, nextSectionButtonXPath)))
            counter = 0
            
            # We're setting the counter at 20 to account for errors and to avoid an infinite loop
            # We would jump straight to the last section, but sometimes it's disabled if you're in demographics sections
            while nextSectionButton.get_attribute("value") not in dp4Resp.submitTranslations and counter<20:
                dp4Resp.nextPage()
                nextSectionButton = WebDriverWait(dp4Resp.browser, 10).until(EC.presence_of_element_located((By.XPATH, nextSectionButtonXPath)))
                counter += 1
        
        if not Prac.scoreOnly:
            try:
                expectedResponse = testInfo['submitformmessage']
                if expectedResponse == '' or expectedResponse is None:
                    expectedResponse = None
            except:
                expectedResponse = None
            dp4Resp.submit(expectedResponse=expectedResponse, directory=str(directory))
            
        dp4Resp.browser.close()
        
        Prac.switchToPractitioner()
        Prac.browser.refresh()
        
        try:
            try:
                validateForm = bool(testInfo['validateform'])
                if validateForm == '' or validateForm is None:
                    validateForm = True
            except:
                validateForm = True
                
            if validateForm:
                try:
                    validateFormMessage = testInfo['validateformmessage']
                    if validateFormMessage == '':
                        validateFormMessage = None
                except:
                    validateFormMessage = None
                    
                Prac.selectByAdministrationFormGUID(administrationFormGUID=dp4Resp.administrationFormGUID)
                
                Prac.validateForm(expectedResponse=validateFormMessage, demoResponses=argsListValidation)
        except:
            logger.warning("Validation encountered an error, refreshing page and attempting one more time...")
            try:
                Prac.browser.refresh()
                
                Prac.selectByAdministrationFormGUID(administrationFormGUID=dp4Resp.administrationFormGUID)
                        
                if validateForm:
                    Prac.validateForm(expectedResponse=validateFormMessage, demoResponses=argsListValidation)
            except:                      
                try:
                    logger.error("Validation failed!!!")
                    Prac.browser.save_screenshot(os.path.join(str(directory), "dp4_" + str(sheet[0]) + "_validation_failed_" + (time.strftime("_%F_%T", time.gmtime())).replace(":", "-") + ".png"))
                except:
                    logging.exception("Saving screenshot failed!!!")
            
        try:
            try:
                scoreForm = bool(testInfo['scoreform'])
                if scoreForm == '' or scoreForm is None:
                    scoreForm = False
            except:
                scoreForm = False
                
            Prac.scoreForm(shouldSucceed=scoreForm, expectedResponse=validateFormMessage, demoResponses=argsListValidation)
        except:
            logger.warning("Scoring encountered an error, refreshing page and attempting one more time...")
            try:
                Prac.browser.refresh()
                
                sleepInt = random.randint(5, 10)
                logger.warning("Randomizing sleep to avoid deadlock, num. seconds: " + str(sleepInt))
                time.sleep(int(sleepInt))
                
                Prac.selectByAdministrationFormGUID(administrationFormGUID=dp4Resp.administrationFormGUID)

                # Trying to randomize the wait time a bit to avoid another possible deadlock...
                sleepInt = random.randint(5, 10)
                logger.warning("Randomizing sleep to avoid deadlock, num. seconds: " + str(sleepInt))
                time.sleep(int(sleepInt))
                Prac.scoreForm(shouldSucceed=scoreForm, expectedResponse=validateFormMessage, demoResponses=argsListValidation)
            except:
                try:
                    logger.error("Scoring failed!!!")
                    Prac.browser.save_screenshot(os.path.join(str(directory), "dp4_" + str(sheet[0]) + "_regression_failed_save_" + (time.strftime("_%F_%T", time.gmtime())).replace(":", "-") + ".png"))
                except:
                    logging.exception("Saving screenshot failed!!!")
                
                try:
                    form = Prac.browser.find_element(By.XPATH, "//*[@class='cannotScoreErrorMsg']")
                except:
                    form = None
                
                if form is not None:
                    logger.error("Licensing message has appeared! Please add licenses for this form and re-run!")
                    raise

        try:
            try:
                isDeleteClient = testInfo['deleteclient']
                if isDeleteClient == '' or isDeleteClient is None:
                    isDeleteClient = False
            except:
                isDeleteClient = False
                
            if isDeleteClient:
                Prac.deleteClient(clientFirstName + " " + clientLastName)
        except:
            logger.warning("Deleting client failed!!!")
        
        return dp4Resp.administrationFormGUID
        
    except Exception as err:
        logger.exception(sys.exc_info()[2])
        Prac.browser.save_screenshot(os.path.join(str(directory), "dp4_" + str(sheet[0]) + "_regression_exception_" + (time.strftime("_%F_%T", time.gmtime())).replace(":", "-") + ".png"))
        Prac.logout()
        Prac.tearDown()
        raise
    
    # loggingPrint("Test completed!\r\n")
    
def runReportsModule(env="uat", headless=False, directory=None, logToFile=False, logName=None, uploadToS3=False, username=None, password=None, report=None, testInfo=None, referencePDFs=None):
    try:
        if directory is None:
            directory = str(os.getcwd())
        
        if logName is None:
            logName = str(report['reference']).replace('.pdf','')
        
        # if logName is None:
            # logName = ''
            # try:
                # for x in sheet:
                    # if logName == '':
                        # logName = str(x[0]).lower()
                    # else:
                        # logName = logName + "+" + str(x[0]).lower()
            # except:
                # logName = str(report['reference']).replace('.pdf','')
                    
        logNameStamped = str(logName) + (time.strftime("_%F_%T", time.gmtime())).replace(":", "-")
        
        try:
            if not os.path.isdir(os.path.join(str(directory), "Reports", str(report['report type']).replace('/', '-').replace('\\', '-').replace('_', '-'), str(logName))):
                os.mkdir(os.path.join(str(directory), "Reports", str(report['report type']).replace('/', '-').replace('\\', '-').replace('_', '-'), str(logName)))
        except:
            logging.exception("Unable to create sub-directory for test case " + str(logName) + "! Outputting to current directory instead")
        
        if logToFile:
            logging.warning("Setting up logfile at " + os.path.join(str(directory), "Reports", str(report['report type']).replace('/', '-').replace('\\', '-').replace('_', '-'), str(logName), str(logNameStamped)+'.log'))
            loggingSetup(output=os.path.join(str(directory), "Reports", str(report['report type']).replace('/', '-').replace('\\', '-').replace('_', '-'), str(logName), str(logNameStamped)+'.log'))
        else:
            loggingSetup()
            
        logger = logging.getLogger(str(logNameStamped))
        
        logger.info("Specified output directory is: " + str(directory))
        
        # runReport(env=env, headless=headless, directory=os.path.join(str(directory), "Reports", str(report['report type']).replace('/', '-').replace('\\', '-').replace('_', '-'), str(logName)), username=username, password=password, report=report, logName=logger, sheet=sheet)
        
        
        # if logToFile:
            # with open(os.path.join(os.path.join(str(directory), "Reports", str(report['report type']).replace('/', '-').replace('\\', '-').replace('_', '-'), str(logName)), str(logName + (time.strftime("_%F_%T", time.gmtime())).replace(":", "-") + ".txt")), 'w', encoding='utf-8') as f:
                # with redirect_stdout(f), redirect_stderr(f):
                    # # runTest(env=env, headless=headless, randomResponse=randomResponse, directory=str(os.path.join(str(directory), str(logName))), input=input, waitTime=waitTime)
                    # runReport(env=env, headless=headless, directory=os.path.join(str(directory), "Reports", str(report['report type']).replace('/', '-').replace('\\', '-').replace('_', '-'), str(logName)), username=username, password=password, report=report, testInfo=testInfo, referencePDFs=referencePDFs)
        # else:
        runReport(env=env, headless=headless, directory=os.path.join(str(directory), "Reports", str(report['report type']).replace('/', '-').replace('\\', '-').replace('_', '-'), str(logName)), username=username, password=password, report=report, testInfo=testInfo, logName=logger, referencePDFs=referencePDFs)
    # except:
        # loggingPrint("Regression failed!!!")
        # Prac.browser.save_screenshot(os.path.join(str(directory), "regression_failed_" + (time.strftime("_%F_%T", time.gmtime())).replace(":", "-") + ".png"))
    finally:    
        if uploadToS3:
            uploadBucket = 'wps-qa-automation'
            s3 = boto3.resource('s3', region_name='us-west-2')
            bucket = s3.Bucket(uploadBucket)
            
        for subdir, dirs, files in os.walk(str(os.path.join(str(directory), "Reports", str(report['report type']).replace('/', '-').replace('\\', '-').replace('_', '-'), str(logName)))):
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
                        # we're explicitly writing all of our text files in UTF-8, so we're confident in this
                        if 'text' in contentType:
                            contentType = contentType + '; charset=utf-8'
                        uploadKey = str("output/oes-1.0-automation/" + str(env) + "/" + todaysDate.strftime("%m-%d-%Y") + "/" + os.path.basename(directory) + "/" + "Reports" + "/" + str(report['report type']).replace('/', '-').replace('\\', '-').replace('_', '-') + "/" + str(logName) + "/" + file)
                        bucket.put_object(Key=uploadKey, Body=data, ContentType=contentType)
                        logger.warning("Files uploaded to S3 at: s3://" + uploadBucket + "/" + uploadKey)
                        

def runReport(env="uat", headless=False, directory=None, username=None, password=None, report=None, testInfo=None, logName=None, referencePDFs=None):
    try:
        
        # we're letting the test info from the first form drive data like login and client
        try:
            # testInfo = sheets[report['forms'][0][0]][0]
            if testInfo is None or testInfo=='' or testInfo==[] or testInfo=={}:
                raise
        except:
            logging.exception("Invalid test case!!! Please ensure that the test entry is correct!!!")
            raise
        
        if logName is None:
            logName = os.path.join(str(directory), os.path.basename(str(directory)), ".log")
        
        try:
            if username is not None and username == '':
                username = None
        except:
            username = None
        
        try:
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
        
        Prac = oesPractitioner(loginUrl, username=username, password=password, logName=logName)
        logger = Prac.logger
        Prac.headless = headless
        if directory is None:
            Prac.download_dir = str(os.getcwd())
        else:
            Prac.download_dir = str(directory)
        Prac.setUp()
        Prac.login()
        
        Prac.navigateToClient(str(testInfo['clientfirstname'] + " " + testInfo['clientlastname']))
        
        Prac.navigateToAssessment(assessmentType=testInfo['assessmenttype'])
        
        logger.info("Compiling list of forms for report...")
        formIDs = []
        for form, formid in report['forms']:
            try:
                logger.info('Adding test case: ' + str(form) + ", Form ID: " + str(formid))
                if formid is not None and formid != '':
                    formIDs.append(str(formid))
                else:
                    logger.warning('Form ID is missing!!!')
            except:
                logger.error('Failed to grab Form ID!!!')
        
        report['forms'] = formIDs
        
        logger.info("Compiled Form IDs: " + str(report['forms']))
        
        try:
            reportTitle = str(report['title'])
        except:
            logger.warning("Unable to determine report title! Randomizing!")
            reportTitle = randomString()
            
        try:
            reportDescription = str(report['description'])
        except:
            logger.warning("Unable to determine report description! Randomizing!")
            reportDescription = randomString()
        
        reportInformation = {'title': reportTitle, 'description': reportDescription}
        
        try:
            reportInformation['formType'] = str(report['form type'])
        except:
            pass
            
        try:
            reportInformation['questions'] = report['questions']
        except:
            pass
        
        try:
            Prac.generateReport(reportType=str(report['report type']), formIds=report['forms'], reportInformation=reportInformation)
        except:
            logger.exception("Failed to generate report!!!")
            raise
        
        # # adding a 5s sleep to ensure all the files are completely generated properly
        # time.sleep(5)
    except:
        try:
            logger.exception("Reports Regression failed!!!")
            Prac.browser.save_screenshot(os.path.join(str(directory), "regression_failed_reports_" + (time.strftime("_%F_%T", time.gmtime())).replace(":", "-") + ".png"))
        except:
            logging.exception("Saving screenshot failed!!!")
        finally:
            raise
            
    finally: 
        try:
            try:
                referencePDF = referencePDFs[report['reference']]
            except:
                referencePDF = None
            
            if referencePDF is not None and referencePDF != '':
                pdfDownload = None
                logger.info("Confirming successful PDF download...")
                for subdir, dir, files in os.walk(str(directory)):
                    for file in files:
                        if os.path.splitext(file)[1].lower()=='.pdf':
                            pdfDownload = os.path.join(subdir, file)
                            break
                            
                if pdfDownload is not None and pdfDownload != '':
                    logger.info("Download successful, performing PDF comparison...")
                    logger.info("Reference PDF: " + referencePDF)
                    logger.info("Generated PDF: " + os.path.basename(pdfDownload))
                    pdfCompare = oesPDFObject(logName=logName, directory=directory)
                    pdfResult = pdfCompare.scorePdfCompare(referencePDF, pdfDownload)
                    if pdfResult == []:
                        logger.info("PDFs match")
                    else:
                        hasDiffs = True
                        mse = None
                        logger.warning("Text compare found differences, generating diff screenshots...")
                        try:
                            hasDiffs, mse = pdfCompare.pdfImageCompare(referencePDF, pdfDownload, mseThreshold=0.0)
                        except:
                            logger.exception("Failed to generate diff screenshots!!!")

                        if hasDiffs or mse is None:
                            filename = str("pdf_compare" + (time.strftime("_%F_%T", time.gmtime())).replace(":", "-") + ".txt")
                            logger.warning("PDFs DO NOT MATCH!!! Generating diff file " + filename)
                            with open(os.path.join(str(str(directory)), filename), 'a', encoding='utf-8') as f:
                                with redirect_stdout(f), redirect_stderr(f):
                                    for line in pdfResult:
                                        print(line)
                                    
                                    # print("Reference PDF: " + referencePDF)
                                    # print("Generated PDF: " + os.path.basename(pdfDownload))
                                    # print('')
                                    # for i in range(len(pdfResult)):
                                        # print(pdfResult[i])
                                        # print(pdfResult[i+1])
                                        # print()
                                        # i+=2
                        else:
                            logger.warning("Image compare passed, Mean Squared Error " + str(mse) + " below 0.0 threshold")
                            try:
                                shutil.rmtree(os.path.join(str(str(directory)), "diffs"))
                            except:
                                pass
                else:
                    logger.warning("No PDF was generated to compare to reference!")
            else:
                logger.info("No reference PDF provided, skipping PDF comparison check...")
        except Exception as e:
            logging.error("Encountered an error attempting to perform PDF comparison!!!")
            logging.exception("PDF Compare Failed")
            with open(os.path.join(str(str(directory)), str("pdf_compare_exception" + (time.strftime("_%F_%T", time.gmtime())).replace(":", "-") + ".txt")), 'a', encoding='utf-8') as f:
                print(str(e), file=f)
        try:
            Prac.logout()
            Prac.tearDown()
        except:
            pass

    
if __name__ == "__main__":
    
    short_options = "he:rd:lu"
    long_options = ["headless", "env=", "random", "directory=", "log-to-file", "upload", "username=", "password="]
    # short_options = "he:rd:i:lw:"
    # long_options = ["headless", "env=", "random", "directory=", "input=", "log-to-file", "wait-time="]
    # "output=",
    
    # Get full command-line arguments
    full_cmd_arguments = sys.argv
    argument_list = full_cmd_arguments[1:]

    env = "uat"
    headless = False
    randomResponse = False
    directory = None
    logToFile = False
    logName = None
    uploadToS3 = False
    username = None
    password = None
    # waitTime = None
    
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
        # elif current_argument in ("-w", "--wait-time"):
            # waitTime = current_value
        elif current_argument in ("-r", "--random"):
            randomResponse = True
        elif current_argument in ("-l", "--log-to-file"):
            logToFile = True
        elif current_argument in ("-u", "--upload") and 'boto3' in sys.modules:
            uploadToS3 = True
        elif current_argument in ("--username"):
            username = str(current_value)
        elif current_argument in ("--password"):
            password = str(current_value)
            #print (("Enabling special output mode (%s)") % (current_value))

    if directory is None or directory == 'None' or directory == '':
        directory = str(os.getcwd())
    
    try:
        directory = str(os.path.join(str(directory), str(os.path.splitext(os.path.basename(str(sys.argv[0])))[0] + (time.strftime("_%F_%T", time.gmtime())).replace(":", "-"))))
        os.mkdir(directory)
    except:
        logging.error("Unable to create sub-directory for all tests! Outputting to specified directory instead")
    
    logging.warning("Current output directory is: " + str(directory))
     
    # try:
        # # there should be a symlink to the X: drive with the updated spreadsheet
        # # use it to copy the latest version of the test spreadsheet into the Git directory
        # shutil.copy2(os.path.join(str("DP4 Sample Testcases_" + platform.system()), "DP4_Samples_Testcases_FINAL_With_DateControl.xlsx"), os.getcwd())
    # except:
        # pass
    # finally:
        # inputFile = "DP4_Samples_Testcases_FINAL_With_DateControl.xlsx"
    inputFile = "DP4_Samples_Testcases_FINAL_With_DateControl.xlsx"
    
    sheets, directionTextList, questionTextList, reports = convertXls(input=inputFile)
    
    # dataInputs = []
    # for sheet in sheets.keys():
        # sheets[sheet][0]['username'] = username
        # sheets[sheet][0]['password'] = password
        # dataInputs.append([env, headless, randomResponse, str(directory), logToFile, logName, uploadToS3, username, password, [sheet]+sheets[sheet]])
     
    if uploadToS3:
        logging.error("S3 upload is currently enabled")
        s3 = boto3.resource('s3', region_name='us-west-2')
        bucket = s3.Bucket(uploadBucket)
        bucket.put_object(Key=str("output/oes-1.0-automation/" + str(env) + "/" + os.path.basename(directory) + "/"))
    
    if logToFile:
        logging.error("Logging to file is enabled; each test case will log to file instead of console")
    
    if headless:
        logging.error("Headless mode is enabled; browser sessions will not be displayed!")
    
    referencePDFs = {}
    logging.warning("Generating listing of reference PDFs for later comparison...")
    for subdir, dirs, files in os.walk(os.path.join(os.path.dirname(os.path.realpath(__file__)), str("DP-4 REPORT PDF"))):
        for file in files:
            referencePDFs[file] = os.path.join(subdir, file)
    
    dataInputs = [[env, headless, randomResponse, str(directory), logToFile, logName, uploadToS3, username, password, [sheet]+sheets[sheet], directionTextList[sheets[sheet][0]['assessmentform']], questionTextList[sheets[sheet][0]['assessmentform']], referencePDFs] for sheet in sheets.keys()]
    
    # Start running Sheets
    logging.warning("Running " + str(len(sheets)) + " test cases...")
    
    return_val = None
    
    with multiprocessing.Pool(processes=4) as pool:
        return_val = pool.starmap(runTestSheet, dataInputs)
    
    # Have to do it this way, between function scoping and sharing state between processes
    
    for sheet, formid in return_val:
        sheets[str(sheet)][0]['formid'] = str(formid)
    
    for report in range(len(reports)):
        formIDs = []
        for form in reports[report]['forms']:
             formIDs.append((str(form), sheets[str(form)][0]['formid']))
        reports[report]['forms'] = formIDs
    
    # with open(os.path.join(str(directory),  "testDataPre.txt"), 'w', encoding='utf-8') as f:
                # with redirect_stdout(f), redirect_stderr(f):
                    # pp = pprint.PrettyPrinter(indent=4)
                    # print("sheets = ", end = '')
                    # pp.pprint(sheets)
                    # print()
                    # print("questionTextList = ", end = '')
                    # pp.pprint(questionTextList)
                    # print()
                    # print("reports = ", end = '')
                    # pp.pprint(reports)
                    # print()
    
    
    # Start running Reports
    logging.warning("Running " + str(len(reports)) + " report cases...")
      
    try:
        if not os.path.isdir(os.path.join(str(directory), "Reports")):
            os.mkdir(os.path.join(str(directory), "Reports"))
    except:
        logging.error("Unable to create sub-directory for all reports! Outputting to specified directory instead")
    
    for type in set([report['report type'] for report in reports]):
        try:
            if not os.path.isdir(os.path.join(str(directory), str(type).replace('/', '-').replace('\\', '-').replace('_', '-'))):
                os.mkdir(os.path.join(str(directory), "Reports", str(type).replace('/', '-').replace('\\', '-').replace('_', '-')))
        except:
            logging.error("Unable to create sub-directory for test group " + str(type) + "! Outputting to current directory " + str(directory) + " instead")
    
    dataInputs = [[env, headless, str(directory), logToFile, None, uploadToS3, username, password, report, sheets[report['forms'][0][0]][0], referencePDFs] for report in reports]
    
    with multiprocessing.Pool(processes=4) as pool:
        pool.starmap(runReportsModule, dataInputs)
    
    # with open(os.path.join(str(directory),  "testDataPost.txt"), 'w', encoding='utf-8') as f:
                # with redirect_stdout(f), redirect_stderr(f):
                    # pp = pprint.PrettyPrinter(indent=4)
                    # print("sheets = ", end = '')
                    # pp.pprint(sheets)
                    # print()
                    # print("questionTextList = ", end = '')
                    # pp.pprint(questionTextList)
                    # print()
                    # print("reports = ", end = '')
                    # pp.pprint(reports)
                    # print()