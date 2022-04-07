# -*- coding: UTF-8 -*-
# Licensing activation and verification test module for OES 1.0
# Requirements:
# Selenium Driver: https://www.selenium.dev/downloads/
# For default credentials and S3 upload, boto3: https://boto3.amazonaws.com/v1/documentation/api/latest/guide/quickstart.html
# Usage: python assessmentLicenseTesting.py [-h] [-e] [-d] [-l] [-u]
# Arguments:
# -h, --headless:       Specifies headless or display mode for browser (default False)
# -e, --env:            Specifies the environment/url to login and perform actions (default "uat")
# -d, --directory:      Specifies the directory to save any downloaded PDFs (default current working directory)
# -l, --log-to-file:    Specifies whether to log to the terminal output or to a text file in --directory (default False)
# -u, --upload:         Specifies whether to upload all generated files to S3 (default False)
# --username:           Specifies a username to use for logging in to the Practitioner site; default credentials require S3, so required if S3 not available
# --password:           Specifies a password to use for logging in to the Practitioner site; default credentials require S3, so required if S3 not available
# --admin-username:     Specifies a username to use for logging in to the Platform Admin site; default credentials require S3, so required if S3 not available
# --admin-password:     Specifies a password to use for logging in to the Platform Admin site; default credentials require S3, so required if S3 not available
# --admin-env:     Specifies the environment/url to login and perform actions on the Platform Admin site; default is to match "-e" value

import sys
from oesLibrary import *
from dateutil.relativedelta import *
from datetime import date
import getopt, csv, os, re, mimetypes
import pprint, pytz, boto3, json
from contextlib import redirect_stdout, redirect_stderr

todaysDate = date.today()
uploadBucket = 'wps-qa-automation'

# We're only activating one SKU per assessment; we mostly just want to check that we can generate and activate valid licenses for each one generally
testInfo = {   'licenses': {  
                              'DP-4': ['W-703AP25'],
                              'PPA Scale': ['W-612DP'],
                              'SPM': ['W-505PK'],
                              'SPM-P': ['W-497PK'],
                              'SPM-2': ['W-706CP25'],
                              'SCQ': ['W-381P'],
                              'SRS-2': ['W-608P'],
                              'SMALSI': ['W-398RP25'],
                              'RCMAS-2': ['W-467P'],
                              'RISE': ['W-695P'],
                              'CAPs': ['W-699P'],
                              'CARS-2': ['W-472DP'],
                              'GOAL': ['W-614MP'],
                              'MIGDAS-2': ['W-690MP'],
                              'ADI-R': ['W-382BP'],
                              'ADOS-2': ['W-605MP'],
                              'Piers-Harris 3': ['W-696P'],
                              'ABAS-3': ['W-620P'],
                              'OPUS': ['W-686UP'],
                              'DP-3': ['W-462P'],
                              'CASL-2': ['W-685UP'],
                              'Arizona-4': ['W-358UP'],
                              'OWLS-II': ['W-603BP'],
                              'DBC2': ['W-692P']
                              },
                              
    'password': '',
    'username': '',
    'adminUsername': '',
    'adminPassword': ''}

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
            adminUsername = kwargs.pop('adminUsername')
        except:
            adminUsername = None
        
        if adminUsername is not None:
            testInfo['adminUsername'] = adminUsername
        
        try:
            adminPassword = kwargs.pop('adminPassword')
        except:
            adminPassword = None
        
        if adminPassword is not None:
            testInfo['adminPassword'] = adminPassword
        try:
            adminEnv = kwargs.pop('adminEnv')
        except:
            adminEnv = None

        try:
            directory = kwargs.pop('directory')
        except:
            directory = None
        
        if directory is None or directory == 'None' or directory == '':
            directory = str(os.getcwd())
        
        try:
            logName = kwargs.pop('logName')
        except:
            logName = None
        
        if logName is None:
            logName = str(os.path.splitext(os.path.basename(str(__file__)))[0])
            
        logNameStamped = str(logName) + (time.strftime("_%F_%T", time.gmtime())).replace(":", "-")

        try:
            if not os.path.isdir(os.path.join(str(directory), str(logNameStamped))):
                os.mkdir(os.path.join(str(directory), str(logNameStamped)))
            
            outputDirectory = os.path.join(str(directory), str(logNameStamped))    
        except:
            logging.exception("Unable to create sub-directory for test case " + str(logNameStamped) + "! Outputting to specified directory instead")
            outputDirectory = str(directory)
        
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

        if logToFile:
            logging.warning("Setting up logfile at " + os.path.join(str(outputDirectory), str(logNameStamped)+'.log'))
            loggingSetup(output=os.path.join(str(outputDirectory), str(logNameStamped)+'.log'))
        else:
            loggingSetup()
            
        logger = logging.getLogger(str(logNameStamped))
        
        logger.info("Specified output directory is: " + str(outputDirectory))
        runTest(env=env, headless=headless, directory=str(outputDirectory), logName=logger, adminEnv=adminEnv)
        
        # if logToFile:
            # with open(os.path.join(os.path.join(str(directory), str(logName)), str(logName + (time.strftime("_%F_%T", time.gmtime())).replace(":", "-") + ".txt")), 'w', encoding='utf-8') as f:
                # with redirect_stdout(f), redirect_stderr(f):
                    # # runTest(env=env, headless=headless, random=random, directory=str(os.path.join(str(directory), str(logName))), input=input, waitTime=waitTime)
                    # loggingPrint("Specified output directory is: " + str(directory))
                    # runTest(env=env, headless=headless, directory=os.path.join(str(directory), str(logName)), adminEnv=adminEnv)
        # else:
            # loggingPrint("Specified output directory is: " + str(directory))
            # runTest(env=env, headless=headless, directory=os.path.join(str(directory), str(logName)), adminEnv=adminEnv)
    finally:
        try:
            uploadToS3 = bool(kwargs.pop('uploadToS3')) and 'boto3' in sys.modules
        except:
            uploadToS3 = False
        
        try:
            uploadParentDirectory = bool(kwargs.pop('uploadParentDirectory'))
        except:
            uploadParentDirectory = False
        
        if uploadToS3:
            s3 = boto3.resource('s3', region_name='us-west-2')
            bucket = s3.Bucket(uploadBucket)
            
        for subdir, dirs, files in os.walk(str(outputDirectory)):
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
                        # bucket.put_object(Key=str("output/oes-1.0-automation/" + str(env) + "/" + os.path.basename(directory) + "/" + str(logNameStamped) + "/" + file), Body=data, ContentType=contentType)
                        if uploadParentDirectory:
                            uploadKey = str("output/oes-1.0-automation/" + str(env) + "/" + todaysDate.strftime("%m-%d-%Y") + "/" + os.path.basename(directory) + "/" + str(logNameStamped) + "/" + file)
                        else:
                            uploadKey = str("output/oes-1.0-automation/" + str(env) + "/" + todaysDate.strftime("%m-%d-%Y") + "/" + str(logNameStamped) + "/" + file)
                        bucket.put_object(Key=urllib.parse.quote(uploadKey), Body=data, ContentType=contentType)
                        logger.warning("Files uploaded to S3 at: s3://" + uploadBucket + "/" + uploadKey)

def runTest(env="uat", headless=False, directory=None, adminEnv=None, logName=None):
    try:
        if logName is None:
            logName = os.path.join(str(directory), os.path.basename(str(directory)), ".log")
        
        try:
            username = testInfo['adminUsername']
            if username == '':
                username = None
        except:
            username = None
        
        try:
            password = testInfo['adminPassword']
            if password == '':
                password = None
        except:
            password = None
        
        if adminEnv is None or adminEnv == '':
            adminEnv = env
        
        if adminEnv=="staging":
            loginUrl = "https://platform-admin.stage.wpspublish.com"
        elif adminEnv=="uat":
            loginUrl = "https://platformmanager-uat.wpspublish.io"
        elif adminEnv=="qa":
            loginUrl = "https://platformmanager-qa.wpspublish.io"
        elif adminEnv=="prod":
            loginUrl = "https://platform-admin.wpspublish.com"
        elif adminEnv=="dev":
            loginUrl = "https://platformmanager-dev.wpspublish.io"
        elif adminEnv=="dev1":
            loginUrl = "https://platformmanager-dev1.wpspublish.io"
        elif adminEnv=="dev2":
            loginUrl = "https://platformmanager-dev2.wpspublish.io"
        elif adminEnv=="dev3":
            loginUrl = "https://platformmanager-dev3.wpspublish.io"
        elif adminEnv=="qa1":
            loginUrl = "https://platformmanager-qa1.wpspublish.io"
        elif adminEnv=="uat1":
            loginUrl = "https://platformmanager-uat1.wpspublish.io"
        elif adminEnv=="perf":
            loginUrl = "https://platform-admin.perf.wpspublish.com/"
        else:
            loginUrl = adminEnv
        
        Admin = oesPlatformAdmin(loginUrl, username=username, password=password, logName=logName)
        logger = Admin.logger
        Admin.headless = headless
        if directory is None:
            Admin.download_dir = str(os.getcwd())
        else:
            Admin.download_dir = str(directory)
        
        logger.info("Attempting to load Platform Admin...")
        
        # Open browser and login to Platform Admin
        Admin.setUp()
        Admin.login()
        Admin.changeTabs()
        
        newLicenses = {}
        
        for assessment in testInfo['licenses']:
            assessmentDir = os.path.join(str(Admin.download_dir), str(assessment))
            try:
                logger.info("Creating directory for assessment licenses...")
                os.mkdir(assessmentDir)
            except:
                logger.warning("Assessment directory already exists, just using that...")
            assessmentLicenses = []
            for i in range(len(testInfo['licenses'][assessment])):
                license = testInfo['licenses'][assessment][i]
                # Create the license key for each assessment and store the contents of what it activates
                try:
                    license = Admin.createLicenseKey(assessmentType=str(assessment), licenseType=str(license))
                    assessmentLicenses += [license]
                    logger.info(license)
                except:
                    logger.error('Unable to select license!!!')
                    logger.error('Attempting to save screenshot...')
                    try:
                        Admin.browser.save_screenshot(os.path.join(str(Admin.download_dir), "license_failed_" + str(license) + (time.strftime("_%F_%T", time.gmtime())).replace(":", "-") + ".png"))
                    except:
                        pass
                    logger.info('Refreshing page and moving on...')
                    Admin.browser.refresh()
            newLicenses[assessment] = assessmentLicenses
            logger.info("All licenses generated for assessment " + str(assessment) + ":")
            logger.info(newLicenses[assessment])
            logger.info("Moving generated license files to assessment directory...")
            downloadedLicenses = [filename for filename in glob.glob(os.path.join(str(Admin.download_dir), '*.*')) if filename.endswith('PDF') or filename.endswith('pdf')]
            for file in downloadedLicenses:
                os.rename(file, os.path.join(str(assessmentDir), os.path.basename(file)))
            logger.info("License files moved")

        Admin.logout()
        
        logger.info("Attempting to switch to Practitioner...")
        
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
        elif env=="dev3":
            loginUrl = "https://practitioner-dev3.wpspublish.io"        
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
        
        try:
            username = testInfo['username']
            if username == '':
                username = None
        except:
            username = None
        
        # if username is not None:
            # Prac.username = username
        
        try:
            password = testInfo['password']
            if password == '':
                password = None
        except:
            password = None
        
        # if password is not None:
            # Prac.password = password
        
        Prac = oesPractitioner(loginUrl, username=username, password=password, browser=Admin.browser, logName=Admin.logName)
        
        # Switch to OES Practitioner
        Prac.download_dir = Admin.download_dir
        Prac.browser.get(loginUrl)
        Prac.login()
        
        currentLicenses = {}
        
        logger.info("Confirming state of pooling...")
        Prac.browser.get(loginUrl + "/myaccount/orglicensemanagement")
        listingOnly = False
        try:
            if Prac.browser.current_url != str(loginUrl + "/myaccount/orglicensemanagement"):
                logger.info("Current user does not have access to Manage Licenses functionality, relying on assessment listing...")
                listingOnly = True
            else:
                inputElement = WebDriverWait(Prac.browser, 30).until(EC.element_to_be_clickable((By.XPATH, "//*//*[@id='orgLicPoolCTA']//input[contains(@value, 'Edit')]")))
        except:
            logger.error("License Management page did not load in time!!! Refreshing and trying again...")
            Prac.browser.refresh()
            inputElement = WebDriverWait(Prac.browser, 45).until(EC.element_to_be_clickable((By.XPATH, "//*//*[@id='orgLicPoolCTA']//input[contains(@value, 'Edit')]")))
            
        if not listingOnly:
            assessmentRows = Prac.browser.find_elements(By.XPATH, "//*//*[@id='testmetadatalist']//tbody//tr")
            
            for row in assessmentRows:
                #assessment = str(row.text).lower().replace(' ','').replace('&#160;', '').replace('-','')
                assessment = str(row.text)
                if assessment in testInfo['licenses']:
                    if listingOnly:
                        currentLicenses[assessment]['isPooled'] = 'listingOnly'
                    elif row.find_element(By.XPATH, ".//input").get_attribute('checked') == 'true':
                        logger.info("Pooling is enabled for " + str(assessment))
                        try:
                            currentLicenses[assessment]['isPooled'] = True
                        except KeyError:
                            currentLicenses[assessment] = {}
                            currentLicenses[assessment]['isPooled'] = True
                    else:
                        logger.info("Pooling is NOT enabled for " + str(assessment))
                        try:
                            currentLicenses[assessment]['isPooled'] = False
                        except KeyError:
                            currentLicenses[assessment] = {}
                            currentLicenses[assessment]['isPooled'] = False
        
        # Get the list of licenses currently active for each assessment before activating the licenses we just generated
        for assessment in testInfo['licenses']:
            try:
                Prac.navigateToAssessmentLicense(assessmentType=assessment)
                
                try:
                    isAssessmentPooled = currentLicenses[assessment]['isPooled']
                except:
                    try:
                        currentLicenses[assessment]['isPooled'] = False
                    except KeyError:
                        currentLicenses[assessment] = {}
                        currentLicenses[assessment]['isPooled'] = False
                
                if currentLicenses[assessment]['isPooled']:
                    try:
                        WebDriverWait(Prac.browser, 15).until(EC.visibility_of_element_located((By.XPATH, "//*//*[@class='licPoolMessage']")))
                        if currentLicenses[assessment]['isPooled'] == 'listingOnly':
                            logger.info("Pooling is enabled for " + str(assessment))
                            try:
                                currentLicenses[assessment]['isPooled'] = True
                            except KeyError:
                                currentLicenses[assessment] = {}
                                currentLicenses[assessment]['isPooled'] = True
                    except:
                        if currentLicenses[assessment]['isPooled'] == 'listingOnly':
                            logger.info("Pooling is NOT enabled for " + str(assessment))
                            try:
                                currentLicenses[assessment]['isPooled'] = False
                            except KeyError:
                                currentLicenses[assessment] = {}
                                currentLicenses[assessment]['isPooled'] = False
                        else:
                            logger.exception("Pooling is not accurately listed for " + str(assessment) + "!")
                            try:
                                Prac.browser.save_screenshot(os.path.join(str(directory), str(assessment) + "_pooling_incorrect" + (time.strftime("_%F_%T", time.gmtime())).replace(":", "-") + ".png"))
                            except:
                                logging.exception("Saving screenshot failed!!!")
                
                #We could try to merge the dicts with z = {**x, **y} but...it's just one value...
                if currentLicenses[assessment]['isPooled']:
                    currentLicenses[assessment] = Prac.getCurrentLicenses()
                    currentLicenses[assessment]['isPooled'] = True
                else:
                    currentLicenses[assessment] = Prac.getCurrentLicenses()
                    currentLicenses[assessment]['isPooled'] = False

                logger.info("List of current licenses for " + str(assessment) + ":")
                logger.info(currentLicenses[assessment])
            except:
                try:
                    logger.error("Ran into an error trying to get current licenses for " + str(assessment) + ", trying one more time...")
                    Prac.navigateToAssessmentLicense(assessmentType=assessment)
                    if currentLicenses[assessment]['isPooled']:
                        try:
                            WebDriverWait(Prac.browser, 15).until(EC.visibility_of_element_located((By.XPATH, "//*//*[@class='licPoolMessage']")))
                        except:
                            logger.exception("Pooling is not accurately listed for " + str(assessment) + "!")
                            try:
                                Prac.browser.save_screenshot(os.path.join(str(directory), str(assessment) + "_pooling_incorrect" + (time.strftime("_%F_%T", time.gmtime())).replace(":", "-") + ".png"))
                            except:
                                logging.exception("Saving screenshot failed!!!")
                    
                    #We could try to merge the dicts with z = {**x, **y} but...it's just one value...
                    if currentLicenses[assessment]['isPooled']:
                        currentLicenses[assessment] = Prac.getCurrentLicenses()
                        currentLicenses[assessment]['isPooled'] = True
                    else:
                        currentLicenses[assessment] = Prac.getCurrentLicenses()
                        currentLicenses[assessment]['isPooled'] = False

                    logger.info("List of current licenses for " + str(assessment) + ":")
                    logger.info(currentLicenses[assessment])
                except:
                    logger.exception("Ran into an error trying to get current licenses for " + str(assessment) + "!")
        
        # loggingPrint("Navigating to license activation...")
        Prac.navigateToLicenseActivation()
        
        logger.info("Starting activation of licenses...")
        
        for assessment in testInfo['licenses']:
            for i in range(len(newLicenses[assessment])):
                logger.info("Activating License: " + str(newLicenses[assessment][i]))
                # Update our current licenses to account for what we're activating, so we can verify it updated correctly
                for j in range(1, len(newLicenses[assessment][i])):    
                    # Just because we have a license stored as being for an assessment, doesn't mean it only contains licenses for that assessment
                    # So we grab the assessment from the license item, to account for combo licenses like SPM/SPM-P
                    licenseAssessment = newLicenses[assessment][i][j][0]
                    licenseType = newLicenses[assessment][i][j][1]
                    licenseName = newLicenses[assessment][i][j][2]
                    licenseQuantity = newLicenses[assessment][i][j][3]
                    
                     # If this is a newly-activated feature, there's not going to be an entry for the license; in this case, catch the error and set it as 0
                    try:
                        currentLicense = currentLicenses[licenseAssessment][licenseName]
                    except:
                        logger.warning("Item was not previously present, adding new entry...")
                        try:
                            currentLicense = currentLicenses[licenseAssessment]
                        except:
                            currentLicenses[licenseAssessment] = {}
                        
                        try:
                            currentLicense = currentLicenses[licenseAssessment]['isPooled']
                        except:
                            logger.warning('Pooling status for assessment unclear! Setting as "Unknown"...')
                            currentLicenses[licenseAssessment]['isPooled'] = 'Unknown'
                            
                        currentLicenses[licenseAssessment][licenseName] = {}
                        currentLicenses[licenseAssessment][licenseName]['type'] = licenseType
                        currentLicenses[licenseAssessment][licenseName]['available'] = 0
                        currentLicenses[licenseAssessment][licenseName]['purchased'] = 0
                        currentLicenses[licenseAssessment][licenseName]['used'] = 0
                        
                    
                    if currentLicenses[assessment]['isPooled'] and currentLicenses[assessment]['isPooled'] != 'Unknown' and licenseType in ['Scoring Only', 'Standard']:
                        newLicenses[assessment][i][j][1] = 'Pooled / ' + newLicenses[assessment][i][j][1]
                        licenseType = newLicenses[assessment][i][j][1]

                    if currentLicenses[licenseAssessment][licenseName]['purchased'] != "Unlimited":
                        if licenseQuantity == 'Unlimited':
                            currentLicenses[licenseAssessment][licenseName]['purchased'] = 'Unlimited'
                        else:
                            currentLicenses[licenseAssessment][licenseName]['purchased'] = str(int(currentLicenses[licenseAssessment][licenseName]['purchased'])+int(licenseQuantity))
                    
                    if currentLicenses[licenseAssessment][licenseName]['available'] != "Unlimited":                    
                        if licenseQuantity == 'Unlimited':
                            currentLicenses[licenseAssessment][licenseName]['available'] = 'Unlimited'
                        else:
                            currentLicenses[licenseAssessment][licenseName]['available'] = str(int(currentLicenses[licenseAssessment][licenseName]['available'])+int(licenseQuantity))
                    
                # Validate and activate the license; function compares to what Platform Admin says it should include
                #try:
                try:
                    Prac.activateLicense(licenseKey=newLicenses[assessment][i])
                except:
                    try:
                        logger.exception("License activation failed for: " + str(newLicenses[assessment][i]))
                        Prac.browser.save_screenshot(os.path.join(str(directory), str(newLicenses[assessment][i][j][1]).lower().replace(' ', '_').replace('-', '_') + "_activation_failed_" + (time.strftime("_%F_%T", time.gmtime())).replace(":", "-") + ".png"))
                    except:
                        logging.exception("Saving screenshot failed!!!")
                #except:
                    #input("Encountered an error!!! Waiting to continue...")
        
        updatedLicenses = {}
        
        logger.info("Attempting to refresh session with new licenses...")
        Prac.logout()

        Prac.login()
        
        # Get the list of licenses currently active for each assessment after activating the licenses we just generated
        foundError = False
        errorAssessments = []
        for assessment in testInfo['licenses']:
            assessmentDir = os.path.join(str(Prac.download_dir), str(assessment))
            try:
                Prac.navigateToAssessmentLicense(assessmentType=assessment)
                
                # We're only gonna wait for the thing to load if we expect it to be there, to save time
                if currentLicenses[assessment]['isPooled'] == True:
                    try:
                        WebDriverWait(Prac.browser, 5).until(EC.visibility_of_element_located((By.XPATH, "//*//*[@class='licPoolMessage']")))
                        try:
                            updatedLicenses[assessment]['isPooled'] = True
                        except KeyError:
                            updatedLicenses[assessment] = {}
                            updatedLicenses[assessment]['isPooled'] = True
                    except:
                        logger.info("Pooling is NOT enabled for " + str(assessment))
                        try:
                            updatedLicenses[assessment]['isPooled'] = False
                        except KeyError:
                            updatedLicenses[assessment] = {}
                            updatedLicenses[assessment]['isPooled'] = False
                else:
                    try:
                        Prac.browser.find_element(By.XPATH, "//*//*[@class='licPoolMessage']")
                        try:
                            updatedLicenses[assessment]['isPooled'] = True
                        except KeyError:
                            updatedLicenses[assessment] = {}
                            updatedLicenses[assessment]['isPooled'] = True
                    except:
                        logger.info("Pooling is NOT enabled for " + str(assessment))
                        try:
                            updatedLicenses[assessment]['isPooled'] = False
                        except KeyError:
                            updatedLicenses[assessment] = {}
                            updatedLicenses[assessment]['isPooled'] = False
                
                #We could try to merge the dicts with z = {**x, **y} but...it's just one value...
                if updatedLicenses[assessment]['isPooled']:
                    updatedLicenses[assessment] = Prac.getCurrentLicenses()
                    updatedLicenses[assessment]['isPooled'] = True
                else:
                    updatedLicenses[assessment] = Prac.getCurrentLicenses()
                    updatedLicenses[assessment]['isPooled'] = False
                
                logger.info("List of updated licenses for " + str(assessment) + ":")
                logger.info(updatedLicenses[assessment])
            except:
                logger.exception("Ran into an error trying to get updated licenses for " + str(assessment) + "!")
                
        #for assessment in testInfo['licenses']:
            differences = {}
            if currentLicenses[assessment] is None:
                logging.error(str(assessment) + " data is invalid!!!")
            else:
                if currentLicenses[assessment]['isPooled'] == 'Unknown':
                    logging.info("Unable to determine previous pooling status for " + str(assessment) + ", skipping this check...")
                    currentLicenses[assessment]['isPooled'] = 'Skipped'
                    updatedLicenses[assessment]['isPooled'] = 'Skipped'
                if updatedLicenses[assessment] != currentLicenses[assessment]:
                    for key in set(currentLicenses[assessment].keys()).intersection(set(updatedLicenses.keys())):
                        if set(currentLicenses[assessment][key].items()) ^ set(updatedLicenses[assessment][key].items()) != set():
                            differences[key] = {'previous': currentLicenses[assessment][key], 'updated': updatedLicenses[assessment][key]}
                                
                    for key in set(currentLicenses[assessment].keys()) ^ set(updatedLicenses[assessment].keys()):
                    #for prevKey, updKey in itertools.zip_longest(currentLicenses[assessment].keys(), updatedLicenses[assessment].keys()):
                        prevLicense = {}
                        updLicense = {}
                        
                        try:
                            prevLicense = currentLicenses[assessment][key]
                        except:
                            prevLicense = {}
                        
                        try:
                            updLicense = updatedLicenses[assessment][key]
                        except:
                            updLicense = {}
                            
                        differences[key] = {'previous': prevLicense, 'updated': updLicense}
                    
                if differences != {}:
                    foundError = True
                    errorAssessments.append(assessment)
                    logger.error("Licenses did not update as expected for " + assessment + "!!!")
                    logger.error("Differences: " + str(differences))
                else:
                    logger.info("Licenses updated successfully")
                    try:
                        logger.info("Removing license directory...")
                        shutil.rmtree(assessmentDir)
                    except:
                        logger.exception("Error encountered attempting to clean up assessment!!!")
        
        if foundError:
            logger.error("ERRORS ENCOUNTERED!!! List of assessments encountering errors:")
            logger.error(errorAssessments)
            raise
        
    except:
        try:
            logger.exception("Fatal error attempting to complete assessment!!!")
        except:
            logging.exception("Fatal error attempting to complete assessment!!!")
        Admin.browser.save_screenshot(os.path.join(str(Admin.download_dir), "regression_failed_" + (time.strftime("_%F_%T", time.gmtime())).replace(":", "-") + ".png"))
    finally:
        try:
            Prac.logout()
            Prac.tearDown()
        except:
            Admin.logout()
            Admin.tearDown()
    
if __name__ == "__main__":
    
    short_options = "he:d:lu"
    long_options = ["headless", "env=", "directory=", "log-to-file", "upload", "username=", "password=", "admin-username=", "admin-password=", "admin-env="]
    # short_options = "he:rd:i:lw:"
    # long_options = ["headless", "env=", "random", "directory=", "input=", "log-to-file", "wait-time="]
    # "output=",
    
    # Get full command-line arguments
    full_cmd_arguments = sys.argv
    argument_list = full_cmd_arguments[1:]

    env = "uat"
    headless = False
    
    # This is being kept for compatibility purposes; it doesn't do anything
    random = False
    
    directory = None
    logToFile = False
    uploadToS3 = False
    username = None
    password = None
    adminUsername = None
    adminPassword = None
    adminEnv = None
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
        elif current_argument in ("-l", "--log-to-file"):
            logToFile = True
        elif current_argument in ("-u", "--upload") and 'boto3' in sys.modules:
            uploadToS3= True
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
    if directory is None or directory == 'None' or directory == '':
        directory = str(os.getcwd())
        
    testModuleArgs = {'env': env, 'headless': headless, 'directory': str(directory), 'logToFile': logToFile, 'uploadToS3': uploadToS3, 'username': username, 'password': password, 'adminUsername': adminUsername, 'adminPassword': adminPassword, 'adminEnv': adminEnv}
    
    if uploadToS3:
        loggingPrint("S3 upload is currently enabled")
        # s3 = boto3.resource('s3', region_name='us-west-2')
        # bucket = s3.Bucket('wps-qa-automation')
        # bucket.put_object(Key=str("output/oes-1.0-automation/" + str(env) + "/" + os.path.basename(directory) + "/"))
    
    if logToFile:
        loggingPrint("Logging to file is enabled; each test case will log to file instead of console")
    
    if headless:
        loggingPrint("Headless mode is enabled; browser sessions will not be displayed!")
    
    runTestModule(testModuleArgs)
    # runTestModule(env=env, headless=headless, directory=directory, logToFile=logToFile, uploadToS3=uploadToS3, username=username, password=password)
