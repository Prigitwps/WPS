import sys
from oesLibrary import *
from dateutil.relativedelta import *
from dateutil.parser import parse
from datetime import date, datetime
import getopt, csv, os, re, mimetypes, requests
import pprint, pytz, time, glob, hashlib, itertools
from contextlib import redirect_stdout, redirect_stderr


def getDocumentHashes(assessment='dp3', audio=False, Prac=None):
    if Prac is None or Prac == '':
        logging.warning("No oesPractitioner object provided!!!")
        raise
    
    directory = str(Prac.download_dir)
    logger = Prac.logger
    
    assessmentDocuments = {}
    assessmentDir = os.path.join(str(directory), str(assessment))
    
    try:
        os.mkdir(assessmentDir)
    except:
        logger.exception("Directory already exists, just using that...")
    
    if audio:
        Prac.navigateToAssessmentTab(assessmentType=assessment, tab='audio')
    else:
        Prac.navigateToAssessmentTab(assessmentType=assessment, tab='documents')
    
    documentsEntryXPath = "//*[contains(@class, 'List')]//tr[contains(@class, 'Row')]"
    
    if audio:
        logger.info("Verifying that audio has loaded...")
    else:
        logger.info("Verifying that documents have loaded...")
        
    # we're waiting to make sure the page is properly loaded with the documents
    documents = WebDriverWait(Prac.browser, 20).until(EC.presence_of_element_located((By.XPATH, documentsEntryXPath)))
    
    if audio:
        logger.info("Audio has loaded successfully")
    else:
        logger.info("Documents have loaded successfully")

    documents = Prac.browser.find_elements(By.XPATH, documentsEntryXPath + "//*[contains(@class, 'Title')]")
    documentsOrder = []

    for document in documents:
        documentTitle = str(document.get_attribute('innerText'))
        documentsOrder.append(documentTitle)
        xpathList = []
        if documentTitle is not None and str(documentTitle).lower().strip() != '':
            try:
                xpathStr = documentsEntryXPath + "//*[contains(@class, 'Title') and "
                for argPart in documentTitle.split():
                    xpathStr += 'contains(text(), "' + argPart + '") and '
                xpathStr = xpathStr[:-5] + ']//..//..//following-sibling::input'
            except:
                logger.exception("Error parsing document title!:" + str(documentTitle))
                raise

        documentFile = WebDriverWait(Prac.browser, 20).until(EC.presence_of_element_located((By.XPATH, xpathStr)))
        filesBeforeDownload = [filename for filename in glob.glob(os.path.join(str(directory), '*.*')) if not filename.endswith('crdownload') and not filename.endswith('tmp')]
        start = time.time()
        elapsed = 0
        Prac.browser.execute_script("arguments[0].click();", documentFile)
        while elapsed < 45:
            filesAfterDownload = [filename for filename in glob.glob(os.path.join(str(directory), '*.*')) if not filename.endswith('crdownload') and not filename.endswith('tmp')]
            done = time.time()
            elapsed = done - start
            filesAfterDownload = [filename for filename in glob.glob(os.path.join(str(directory), '*.*')) if not filename.endswith('crdownload') and not filename.endswith('tmp')]
            newfile = list(set(filesAfterDownload).difference(filesBeforeDownload))
            if len(newfile):
                break
        
        
        try:
            with open(os.path.normpath(newfile[0]), "rb") as f:
                data = f.read()
                assessmentDocuments[documentTitle] = (os.path.basename(newfile[0]), hashlib.sha256(data).hexdigest())
        except:
            logger.exception("Failed to read document, randomizing sleep and retrying...")
            sleepInt = random.randint(5, 10)
            with open(os.path.normpath(newfile[0]), "rb") as f:
                data = f.read()
                assessmentDocuments[documentTitle] = (os.path.basename(newfile[0]), hashlib.sha256(data).hexdigest())
    
        os.rename(os.path.join(str(directory), os.path.basename(newfile[0])), os.path.join(str(assessmentDir), os.path.basename(newfile[0])))
    
    assessmentDocuments['Ordered Content Listing'] = documentsOrder
    
    logger.info("assessmentDocuments = " + pprint.pformat(assessmentDocuments, indent=4))

    return assessmentDocuments


def getManualHashes(assessment='dp3', easels=False, Prac=None):
    if Prac is None or Prac == '':
        logging.warning("No oesPractitioner object provided!!!")
        raise
    
    directory = str(Prac.download_dir)
    logger = Prac.logger

    assessmentHashes = {}
    assessmentDir = os.path.join(str(directory), str(assessment))
    
    try:
        os.mkdir(assessmentDir)
    except:
        logger.exception("Directory already exists, just using that...")
    
    if easels:
        Prac.navigateToAssessmentEasels(assessmentType=assessment)
    else:
        Prac.navigateToAssessmentManuals(assessmentType=assessment)
    
    manualsEntryXPath = "//*//input[contains(@class, 'redButn') and not(contains(@class, 'Resend'))]"
    
    if easels:
        logger.info("Verifying that easels have loaded...")
    else:
        logger.info("Verifying that manuals have loaded...")
        
    manuals = WebDriverWait(Prac.browser, 20).until(EC.presence_of_element_located((By.XPATH, manualsEntryXPath)))
    
    if easels:
        logger.info("Easels have loaded successfully")
    else:
        logger.info("Manuals have loaded successfully")
    
    manuals = Prac.browser.find_elements(By.XPATH, manualsEntryXPath)

    for manual in manuals:
        manualName = "Undetermined"
        try:
            manualHashes = {}
            manualName = str(manual.get_attribute('onclick')).split("'")[3]
            manualName = manualName.replace(":", " - ")
            
            try:
                os.mkdir(os.path.join(assessmentDir, manualName.replace("/", "-").replace("\\", "-")))
            except:
                logger.exception("Directory already exists, just using that...")
                
            Prac.browser.execute_script("arguments[0].click();", manual)
            Prac.switchToRespondent()
            loaded = WebDriverWait(Prac.browser, 40).until(AnyEc(EC.visibility_of_element_located((By.XPATH, "//*//img[@id='rightpage']")), EC.visibility_of_element_located((By.XPATH, "//*//img[@id='leftpage']"))))
            leftPage = WebDriverWait(Prac.browser, 20).until(EC.presence_of_element_located((By.XPATH, "//*//img[@id='leftpage']")))
            rightPage = WebDriverWait(Prac.browser, 20).until(EC.presence_of_element_located((By.XPATH, "//*//img[@id='rightpage']")))
            
            nextPage = Prac.browser.find_element(By.XPATH, "//*//img[@id='btnNextPage']")
            prevPage = Prac.browser.find_element(By.XPATH, "//*//img[@id='btnPrevPage']")
            lastPage = Prac.browser.find_element(By.XPATH, "//*//img[@id='btnLastPage']")
            firstPage = Prac.browser.find_element(By.XPATH, "//*//img[@id='btnFirstPage']")
            currPage = Prac.browser.find_element(By.XPATH, "//*//input[@id='tbPage']")
            
            leftPageImage = leftPage.get_attribute('src')
            rightPageImage = rightPage.get_attribute('src')
            
            # We either display two-page mode or in single-page mode (Easels, Quick-Tips Manual, etc.)
            # Single-page mode only uses the left page, so that's the only time the left page would be populated here
            doublePage = leftPageImage == ''
            
            if rightPage is not None and rightPage == '' and leftPage is not None and leftPage == '':
                # For some reason, sometimes navigating using the 'First Page' button clears the src attribute
                # This is fixed on refreshing the page, though, so just do that first
                Prac.browser.refresh()
                loaded = WebDriverWait(Prac.browser, 40).until(AnyEc(EC.visibility_of_element_located((By.XPATH, "//*//img[@id='rightpage']")), EC.visibility_of_element_located((By.XPATH, "//*//img[@id='leftpage']"))))
                leftPage = WebDriverWait(Prac.browser, 20).until(EC.presence_of_element_located((By.XPATH, "//*//img[@id='leftpage']")))
                rightPage = WebDriverWait(Prac.browser, 20).until(EC.presence_of_element_located((By.XPATH, "//*//img[@id='rightpage']")))
                nextPage = Prac.browser.find_element(By.XPATH, "//*//img[@id='btnNextPage']")
                prevPage = Prac.browser.find_element(By.XPATH, "//*//img[@id='btnPrevPage']")
                lastPage = Prac.browser.find_element(By.XPATH, "//*//img[@id='btnLastPage']")
                firstPage = Prac.browser.find_element(By.XPATH, "//*//img[@id='btnFirstPage']")
                currPage = Prac.browser.find_element(By.XPATH, "//*//input[@id='tbPage']")
                leftPageImage = leftPage.get_attribute('src')
                rightPageImage = rightPage.get_attribute('src')


            cookies = {
                'CloudFront-Key-Pair-Id': Prac.browser.get_cookie('CloudFront-Key-Pair-Id')['value'],
                'CloudFront-Policy': Prac.browser.get_cookie('CloudFront-Policy')['value'],
                'CloudFront-Signature': Prac.browser.get_cookie('CloudFront-Signature')['value'],
                    }
            
            if rightPageImage is not None and rightPageImage != '':
                pageImage = requests.get(rightPageImage, cookies=cookies, stream=True, allow_redirects=True)
                filePath = os.path.join(assessmentDir, str(manualName.replace("/", "-").replace("\\", "-")), assessment+'_'+rightPageImage.rsplit('/', 1)[-1])
                with open(filePath, 'wb') as f:
                    f.write(pageImage.content)
                    
                with open(filePath, "rb") as f:
                    data = f.read()
                    downloadHash = hashlib.sha256(data).hexdigest()
                
                manualHashes[assessment+'_'+rightPageImage.rsplit('/', 1)[-1]] = downloadHash
                
                logger.info(str(manualName + ": " + assessment+'_'+rightPageImage.rsplit('/', 1)[-1]))
                logger.info(str(downloadHash))
            
            if leftPageImage is not None and leftPageImage != '':
                pageImage = requests.get(leftPageImage, cookies=cookies, stream=True, allow_redirects=True)
                filePath = os.path.join(assessmentDir, str(manualName.replace("/", "-").replace("\\", "-")), assessment+'_'+leftPageImage.rsplit('/', 1)[-1])
                with open(filePath, 'wb') as f:
                    f.write(pageImage.content)
                    
                with open(filePath, "rb") as f:
                    data = f.read()
                    downloadHash = hashlib.sha256(data).hexdigest()
                
                manualHashes[assessment+'_'+leftPageImage.rsplit('/', 1)[-1]] = downloadHash
                
                logger.info(str(manualName + ": " + assessment+'_'+leftPageImage.rsplit('/', 1)[-1]))
                logger.info(str(downloadHash))
            
            Prac.browser.execute_script("arguments[0].click();", lastPage)
            if doublePage:
                #loaded = WebDriverWait(Prac.browser, 20).until(AnyEc(EC.visibility_of_element_located((By.XPATH, "//*//img[@id='rightpage']")), EC.visibility_of_element_located((By.XPATH, "//*//img[@id='leftpage']"))))
                loaded = WebDriverWait(Prac.browser, 20).until(AnyEc(wait_for_not_attribute_value((By.XPATH, "//*//img[@id='rightpage']"), 'src', ''), wait_for_not_attribute_value((By.XPATH, "//*//img[@id='leftpage']"), 'src', '')))
            else:
                # Single-page manuals sometimes get the src attribute cleared as above; just do a quick navigate to fix
                logger.info("Prev Page Nav...")
                Prac.browser.execute_script("arguments[0].click();", prevPage)
                loaded = WebDriverWait(Prac.browser, 20).until(AnyEc(wait_for_not_attribute_value((By.XPATH, "//*//img[@id='rightpage']"), 'src', ''), wait_for_not_attribute_value((By.XPATH, "//*//img[@id='leftpage']"), 'src', '')))
                logger.info("Left Page: " + leftPage.get_attribute('src'))
                logger.info("Right Page: " + rightPage.get_attribute('src'))
                leftPageImage = leftPage.get_attribute('src')
                rightPageImage = rightPage.get_attribute('src')
                logger.info("Next Page Nav...")
                Prac.browser.execute_script("arguments[0].click();", nextPage)
            
            loaded = WebDriverWait(Prac.browser, 20).until(AnyEc(wait_for_not_attribute_value((By.XPATH, "//*//img[@id='rightpage']"), 'src', rightPageImage), wait_for_not_attribute_value((By.XPATH, "//*//img[@id='leftpage']"), 'src', leftPageImage)))
            loaded = WebDriverWait(Prac.browser, 20).until(AnyEc(wait_for_not_attribute_value((By.XPATH, "//*//img[@id='rightpage']"), 'src', ''), wait_for_not_attribute_value((By.XPATH, "//*//img[@id='leftpage']"), 'src', '')))
            
            nextPage = Prac.browser.find_element(By.XPATH, "//*//img[@id='btnNextPage']")
            prevPage = Prac.browser.find_element(By.XPATH, "//*//img[@id='btnPrevPage']")
            lastPage = Prac.browser.find_element(By.XPATH, "//*//img[@id='btnLastPage']")
            firstPage = Prac.browser.find_element(By.XPATH, "//*//img[@id='btnFirstPage']")
            currPage = Prac.browser.find_element(By.XPATH, "//*//input[@id='tbPage']")
            leftPage = WebDriverWait(Prac.browser, 20).until(EC.presence_of_element_located((By.XPATH, "//*//img[@id='leftpage']")))
            rightPage = WebDriverWait(Prac.browser, 20).until(EC.presence_of_element_located((By.XPATH, "//*//img[@id='rightpage']")))
            leftPageImage = leftPage.get_attribute('src')
            rightPageImage = rightPage.get_attribute('src')
            logger.info("Left Page: " + leftPage.get_attribute('src'))
            logger.info("Right Page: " + rightPage.get_attribute('src'))
            logger.info("Beginning download...")
            
            if rightPageImage is not None and rightPageImage != '':
                pageImage = requests.get(rightPageImage, cookies=cookies, stream=True, allow_redirects=True)
                filePath = os.path.join(assessmentDir, str(manualName.replace("/", "-").replace("\\", "-")), assessment+'_'+rightPageImage.rsplit('/', 1)[-1])
                with open(filePath, 'wb') as f:
                    f.write(pageImage.content)
                    
                with open(filePath, "rb") as f:
                    data = f.read()
                    downloadHash = hashlib.sha256(data).hexdigest()
                
                manualHashes[assessment+'_'+rightPageImage.rsplit('/', 1)[-1]] = downloadHash

                logger.info(str(manualName + ": " + assessment+'_'+rightPageImage.rsplit('/', 1)[-1]))
                logger.info(str(downloadHash))
            
            if leftPageImage is not None and leftPageImage != '':
                pageImage = requests.get(leftPageImage, cookies=cookies, stream=True, allow_redirects=True)
                filePath = os.path.join(assessmentDir, str(manualName.replace("/", "-").replace("\\", "-")), assessment+'_'+leftPageImage.rsplit('/', 1)[-1])
                with open(filePath, 'wb') as f:
                    f.write(pageImage.content)
                    
                with open(filePath, "rb") as f:
                    data = f.read()
                    downloadHash = hashlib.sha256(data).hexdigest()
                
                manualHashes[assessment+'_'+leftPageImage.rsplit('/', 1)[-1]] = downloadHash
                
                logger.info(str(manualName + ": " + assessment+'_'+leftPageImage.rsplit('/', 1)[-1]))
                logger.info(str(downloadHash))

                
            logger.info("Jumping to page 11")
            currPage.send_keys('11')
            currPage.send_keys(Keys.ENTER)
            if doublePage:
                #loaded = WebDriverWait(Prac.browser, 20).until(AnyEc(EC.visibility_of_element_located((By.XPATH, "//*//img[@id='rightpage']")), EC.visibility_of_element_located((By.XPATH, "//*//img[@id='leftpage']"))))
                loaded = WebDriverWait(Prac.browser, 20).until(AnyEc(wait_for_not_attribute_value((By.XPATH, "//*//img[@id='rightpage']"), 'src', ''), wait_for_not_attribute_value((By.XPATH, "//*//img[@id='leftpage']"), 'src', '')))
            else:
                # Single-page manuals sometimes get the src attribute cleared as above; just do a quick navigate to fix
                logger.info("Single page issue! Navigating to and from...")
                logger.info("Prev Page Nav...")
                Prac.browser.execute_script("arguments[0].click();", prevPage)
                loaded = WebDriverWait(Prac.browser, 20).until(AnyEc(wait_for_not_attribute_value((By.XPATH, "//*//img[@id='rightpage']"), 'src', ''), wait_for_not_attribute_value((By.XPATH, "//*//img[@id='leftpage']"), 'src', '')))
                logger.info("Left Page: " + leftPage.get_attribute('src'))
                logger.info("Right Page: " + rightPage.get_attribute('src'))
                leftPageImage = leftPage.get_attribute('src')
                rightPageImage = rightPage.get_attribute('src')
                logger.info("Next Page Nav...")
                Prac.browser.execute_script("arguments[0].click();", nextPage)
            
            loaded = WebDriverWait(Prac.browser, 20).until(AnyEc(wait_for_not_attribute_value((By.XPATH, "//*//img[@id='rightpage']"), 'src', rightPageImage), wait_for_not_attribute_value((By.XPATH, "//*//img[@id='leftpage']"), 'src', leftPageImage)))
            loaded = WebDriverWait(Prac.browser, 20).until(AnyEc(wait_for_not_attribute_value((By.XPATH, "//*//img[@id='rightpage']"), 'src', ''), wait_for_not_attribute_value((By.XPATH, "//*//img[@id='leftpage']"), 'src', '')))
            
            nextPage = Prac.browser.find_element(By.XPATH, "//*//img[@id='btnNextPage']")
            prevPage = Prac.browser.find_element(By.XPATH, "//*//img[@id='btnPrevPage']")
            lastPage = Prac.browser.find_element(By.XPATH, "//*//img[@id='btnLastPage']")
            firstPage = Prac.browser.find_element(By.XPATH, "//*//img[@id='btnFirstPage']")
            currPage = Prac.browser.find_element(By.XPATH, "//*//input[@id='tbPage']")
            leftPage = WebDriverWait(Prac.browser, 20).until(EC.presence_of_element_located((By.XPATH, "//*//img[@id='leftpage']")))
            rightPage = WebDriverWait(Prac.browser, 20).until(EC.presence_of_element_located((By.XPATH, "//*//img[@id='rightpage']")))
            leftPageImage = leftPage.get_attribute('src')
            rightPageImage = rightPage.get_attribute('src')
            logger.info("Left Page: " + leftPage.get_attribute('src'))
            logger.info("Right Page: " + rightPage.get_attribute('src'))
            logger.info("Beginning download...")
            
            if rightPageImage is not None and rightPageImage != '':
                pageImage = requests.get(rightPageImage, cookies=cookies, stream=True, allow_redirects=True)
                filePath = os.path.join(assessmentDir, str(manualName.replace("/", "-").replace("\\", "-")), assessment+'_'+rightPageImage.rsplit('/', 1)[-1])
                with open(filePath, 'wb') as f:
                    f.write(pageImage.content)
                    
                with open(filePath, "rb") as f:
                    data = f.read()
                    downloadHash = hashlib.sha256(data).hexdigest()
                
                manualHashes[assessment+'_'+rightPageImage.rsplit('/', 1)[-1]] = downloadHash
                
                logger.info(str(manualName + ": " + assessment+'_'+rightPageImage.rsplit('/', 1)[-1]))
                logger.info(str(downloadHash))
            
            if leftPageImage is not None and leftPageImage != '':
                pageImage = requests.get(leftPageImage, cookies=cookies, stream=True, allow_redirects=True)
                filePath = os.path.join(assessmentDir, str(manualName.replace("/", "-").replace("\\", "-")), assessment+'_'+leftPageImage.rsplit('/', 1)[-1])
                with open(filePath, 'wb') as f:
                    f.write(pageImage.content)
                    
                with open(filePath, "rb") as f:
                    data = f.read()
                    downloadHash = hashlib.sha256(data).hexdigest()
                
                manualHashes[assessment+'_'+leftPageImage.rsplit('/', 1)[-1]] = downloadHash

                logger.info(str(manualName + ": " + assessment+'_'+leftPageImage.rsplit('/', 1)[-1]))
                logger.info(str(downloadHash))
        except:
            if easels:
                logger.exception("Failed to check easel " + str(manualName) + " !!!")
            else:
                logger.exception("Failed to check manual " + str(manualName) + " !!!")
            
        Prac.browser.close()
        Prac.switchToPractitioner()
        
        assessmentHashes[str(manualName)] = manualHashes
    
    return assessmentHashes




if __name__ == "__main__":
    short_options = "he:d:l"
    long_options = ["headless", "env=", "directory=", "log-to-file", "username=", "password="]
    # short_options = "he:rd:i:lw:"
    # long_options = ["headless", "env=", "random", "directory=", "input=", "log-to-file", "wait-time="]
    # "output=",
    
    # Get full command-line arguments
    full_cmd_arguments = sys.argv
    argument_list = full_cmd_arguments[1:]

    env = "prod"
    headless = False
    directory = None
    username = None
    password = None
    logToFile = False
    
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
        elif current_argument in ("-l", "--log-to-file"):
            logToFile = True
        elif current_argument in ("--username"):
            username = str(current_value)
        elif current_argument in ("--password"):
            password = str(current_value)

            #print (("Enabling special output mode (%s)") % (current_value))
    
    if directory is None or directory == 'None' or directory == '':
        # directory = r"C:\Users\bjackson\Desktop\Test Scripts\documentsDownload\Manuals"
        loggingPrint("Directory does not exist! Using current working directory: " + str(os.getcwd()))
        directory = str(os.getcwd())
    
    logName = str(os.path.splitext(os.path.basename(str(__file__)))[0])
            
    logNameStamped = str(logName) + (time.strftime("_%F_%T", time.gmtime())).replace(":", "-")
    
    try:
        if not os.path.isdir(os.path.join(str(directory), str(logNameStamped))):
            os.mkdir(os.path.join(str(directory), str(logNameStamped)))
        
        outputDirectory = os.path.join(str(directory), str(logNameStamped))    
    except:
        logging.exception("Unable to create sub-directory " + str(logNameStamped) + " for generated hash values! Outputting to specified directory instead")
        outputDirectory = str(directory)
    
    if logToFile:
        logging.warning("Setting up logfile at " + os.path.join(str(outputDirectory), str(logNameStamped)+'.log'))
        loggingSetup(output=os.path.join(str(outputDirectory), str(logNameStamped)+'.log'))
    else:
        loggingSetup()
        
    logger = logging.getLogger(str(logNameStamped))
    
    try:
        if username == '':
            username = None
    except:
        username = None
    
    try:
        if password == '':
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

        
    Prac = oesPractitioner(loginUrl, username=username, password=password, logName=logger)
    logger = Prac.logger
    Prac.headless = headless
    Prac.download_dir = str(outputDirectory)
    Prac.setUp()
    Prac.login()
    #unreleasedAssessments = ['spm2']
    manualAssessments = ['owlsii', 'spm2', 'opus', 'dp3', 'casl2', 'ppascale', 'abas3', 'spm', 'spmp', 'srs2', 'smalsi', 'scq', 'arizona4', 'rcmas2', 'dbc2', 'piersharris3', 'rise', 'caps', 'dp4', 'adir', 'ados2', 'cars2', 'goal', 'migdas2']
    easelAssessments = ['owlsii', 'casl2', 'ppascale', 'opus', 'arizona4']
    documentsAssessments = ['opus', 'spm2', 'dp3', 'abas3', 'spm', 'spmp', 'srs2', 'smalsi', 'casl2', 'scq', 'arizona4', 'rcmas2', 'dbc2', 'piersharris3', 'rise', 'caps', 'dp4']
    audioAssessments = ['opus', 'rcmas2', 'smalsi']
    fileHashes = {}

    try:
        manualsEasels = (manualAssessments + list(set(easelAssessments) - set(manualAssessments)))
        documentsAudio = (documentsAssessments + list(set(audioAssessments) - set(documentsAssessments)))
        allAssessments = (manualsEasels + list(set(documentsAudio) - set(manualsEasels)))
        
        for assessment in allAssessments:
            assessmentHashes = {}
            
            if assessment in manualAssessments:
                assessmentHashes['manuals'] = getManualHashes(assessment, False, Prac)
            
            if assessment in easelAssessments:
                assessmentHashes['easels'] = getManualHashes(assessment, True, Prac)
            
            if assessment in documentsAssessments:
                assessmentHashes['documents'] = getDocumentHashes(assessment, False, Prac)
                
            if assessment in audioAssessments:
                assessmentHashes['audio'] = getDocumentHashes(assessment, True, Prac)
            
            fileHashes[str(assessment)] = assessmentHashes
            
            logger.info(str(assessment) + " = " + pprint.pformat(assessmentHashes, indent=4))
            
    except:
        try:
            try:
                logger.exception("Regression failed!!!")
            except:
                logging.exception("Regression failed!!!")
            Prac.browser.save_screenshot(os.path.join(str(Prac.download_dir), "regression_failed" + (time.strftime("_%F_%T", time.gmtime())).replace(":", "-") + ".png"))
        except:
            try:
                logging.exception("Saving screenshot failed!!!")
            except:
                logger.exception("Saving screenshot failed!!!")
    finally:
        try:
            Prac.logout() 
            Prac.tearDown()
        except:
            pass
        
        try:
            with open(os.path.join(str(outputDirectory), "fileHashes.txt"), 'w', encoding='utf-8') as f:
                with redirect_stdout(f), redirect_stderr(f):
                    pp = pprint.PrettyPrinter(indent=4)
                    print("fileHashes = ", end = '')
                    pp.pprint(fileHashes)
        except:
            pass
                
                    
