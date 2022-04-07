# OES Automation Scripts
## PLEASE INSTALL the included oesLibraryPackage; nearly all of the scripts require it!!!

This repository is for automation scripts used for various OES 1.0 tasks, especially testing and verification.

The `testModules` directory includes currently-active test modules included as part of `fullRegression.py`.
Each one is used for running a regression test of some kind in OES, and can be run stand-alone as well.

## Currently Active Test Modules:
* abas3Regression.py
* arizona4Regression.py
* assessmentLicenseTesting.py
* capsRegression.py
* casl2Regression.py
* dbc2Regression.py
* dp3Regression.py
* opusRegression.py
* piersharris3Regression.py
* ppascaleRegression.py
* rcmas2Regression.py
* riseRegression.py
* scqRegression.py
* smalsiRegression.py
* spmpRegression.py
* spmRegression.py
* spmRegression_alt.py
* srs2Regression.py
* staticContentTesting.py


The `testModulesUnderDevelopment` directory includes test modules that are not quite completed for one reason or another, and not included as part of `generalRegression.py`;
often, they can still be run, but may be less reliable or more limited in utility.

## Currently In-Development Test Modules:
* dp4Regression.py
* capsRegression_spreadsheet.py
* spm2Regression_spreadsheet.py




## Test Module Usage:
Each test module should adhere to the following standard, with values provided in "double-quotes":
### python [test module, e.g., dp4Regression.py] [-h] [-r] [-e] <environment> [-d] <filepath> [-l] [-u] [--username] <username> [--password] <password>
#### Arguments:
* -h, --headless:       Specifies headless or display mode for browser (default False)
* -r, --random:         Specifies random or set response mode for assessment (default False)
* -e, --env:            Specifies the environment to login and perform actions (default "uat")
* -d, --directory:      Specifies the directory to save any generated files, such as logfiles or downloaded PDFs (default current working directory)
* -l, --log-to-file:    Specifies whether to log to the terminal output or to a text file (default False)
* -u, --upload:         Specifies whether or not files should be uploaded to S3 if boto3 is configured (default False)
* --username:           Specifies a username to use for logging in; default credentials require boto3 configuration and S3 access, so required if not available
* --password:           Specifies a password to use for logging in; default credentials require boto3 configuration and S3 access, so required if not available

The environment flag ("-e" or "--env") specifies the environment URL to be used by automation; for convenience, it is able to leverage shortcodes to use common environments.
If using a temporary or uncommon environment, such as a local URL, provide the URL value directly (ex., -e "http://localhost:77777"). For some test modules that involve the Platform Manager/Admin site, a single shortcode is usually all that's necessary, even if the test module involves both Practitioner and Platform Manager/Admin. If providing a URL value directly, however, you may need to specify the Practitioner and Platform Manager/Admin URLs separately.
#### Available Environment Shortcodes:

* "staging":           "https://platform.stage.wpspublish.com", "https://platform-admin.stage.wpspublish.com"
* "uat":               "https://practitioner-uat.wpspublish.io", "https://platformmanager-uat.wpspublish.io"
* "qa":                "https://practitioner-qa.wpspublish.io", "https://platformmanager-qa.wpspublish.io"
* "prod":              "https://platform.wpspublish.com", "https://platform-admin.wpspublish.com"
* "dev":               "https://practitioner-dev.wpspublish.io", "https://platformmanager-dev.wpspublish.io"
* "dev2":              "https://practitioner-dev2.wpspublish.io", "https://platformmanager-dev2.wpspublish.io"
* "dev1":              "https://practitioner-dev1.wpspublish.io", "https://platformmanager-dev1.wpspublish.io"
* "qa1":               "https://practitioner-qa1.wpspublish.io", "https://platformmanager-qa1.wpspublish.io"
* "uat1":              "https://practitioner-uat1.wpspublish.io", "https://platformmanager-uat1.wpspublish.io"
* "perf":              "https://platform.perf.wpspublish.com", "https://platform-admin.perf.wpspublish.com/"

#### Example
This command will run the generalRegression.py script in the QA1 environment (-e "qa1"), in headless mode so that the browser is not displayed (-h), with logging output saved to a file instead of console (-l). Generated files will be saved to the output directory "C:\outputDirectoryForResults" (-o "C:\outputDirectoryForResults"), and it will run all of the test modules located in "C:\inputDirectoryWithTestModules" (-i "C:\inputDirectoryWithTestModules"):
* python generalRegression.py -e "qa1" -h -l -o "C:\outputDirectoryForResults" -i "C:\inputDirectoryWithTestModules"


## generalRegression.py Usage:
The `generalRegression.py` module is a 4-thread parallelized wrapper for a directory of test modules, rather than a test module in its own right. As such, it works a bit differently:
### python generalRegression.py [-h] [-r] [-e] <environment> [-d] <filepath> [-i] <filepath> [-l] [-p] <logfile-prefix> [-u] [--username] <username> [--password] <password>
#### Arguments:
* -h, --headless:       Specifies headless or display mode for browser (default False)
* -r, --random:         Specifies random or set response mode for assessment (default False)
* -e, --env:            Specifies the environment to login and perform actions (default "uat")
* -o/-d, --output/--directory:         Specifies the directory to save any generated files, such as logfiles or downloaded PDFs (default current working directory)
* -i, --input:          Specifies the path to the input Python script test modules to be run (default none)
* -l, --log-to-file:    Specifies whether to log to the terminal output or to a text file in --output (default False)
* -p, --log-prefix:     Specifies the prefix to add to all generated log files (default '')
* -u, --upload:         Specifies whether or not files should be uploaded to S3 if boto3 is configured (default False)
* --username:           Specifies a username to use for logging in; default credentials require boto3 configuration and S3 access, so required if not available
* --password:           Specifies a password to use for logging in; default credentials require boto3 configuration and S3 access, so required if not available
* --admin-username:     Specifies a username to use for logging in to the Platform Admin site; default credentials require S3, so required if S3 not available
* --admin-password:     Specifies a password to use for logging in to the Platform Admin site; default credentials require S3, so required if S3 not available
* --admin-env:          Specifies the environment/url to login and perform actions on the Platform Admin site; default is to match "-e" value

## parallelSingleScript.py Usage:
The `parallelSingleScript.py` module is a 4-thread parallelized wrapper for running a single test module multiple times, rather than a test module in its own right or for a group of them like `generalRegression.py`:
### python parallelSingleScript.py [-h] [-r] [-n] <number-of-times-to-run> [-t] <number-of-threads-to-run> [-e] <environment> [-o] <filepath> [-i] <filepath> [-l] [-p] <logfile-prefix> [-u] [--username] <username> [--password] <password>
#### Arguments:
* -h, --headless:       Specifies headless or display mode for browser (default False)
* -r, --random:         Specifies random or set response mode for assessment (default False)
* -n, --number:         Specifies the number of times to run the script (default 1)
* -t, --threads:        Specifies the amount of simultaneous threads to use when running the script (default 4)
* -e, --env:            Specifies the environment to login and perform actions (default "uat")
* -o, --output:         Specifies the directory to save any generated files, such as logfiles or downloaded PDFs (default current working directory)
* -i, --input:          Specifies the path to the input Python script test modules to be run (default none)
* -l, --log-to-file:    Specifies whether to log to the terminal output or to a text file in --output (default False)
* -p, --log-prefix:     Specifies the prefix to add to all generated log files (default '')
* -u, --upload:         Specifies whether or not files should be uploaded to S3 if boto3 is configured (default False)
* --username:           Specifies a username to use for logging in; default credentials require boto3 configuration and S3 access, so required if not available
* --password:           Specifies a password to use for logging in; default credentials require boto3 configuration and S3 access, so required if not available
* --admin-username:     Specifies a username to use for logging in to the Platform Admin site; default credentials require S3, so required if S3 not available
* --admin-password:     Specifies a password to use for logging in to the Platform Admin site; default credentials require S3, so required if S3 not available
* --admin-env:          Specifies the environment/url to login and perform actions on the Platform Admin site; default is to match "-e" value

## loadTest.py Usage:
The `loadTest.py` module generates random reports in a specified number of loops, and does this across a specified number of threads, in order to try to stress/load test OES 1.0:
###  python loadTest.py [-h] [-e] [-l] [-d] [-t] [-i] [-u] [-w]
#### Arguments:
* -h, --headless:       Specifies headless or display mode for browser (default False)
* -e, --env:            Specifies the environment to login and perform actions (default "uat")
* -l, --log-to-file:    Specifies whether to log to the terminal output or to a text file in --output (default False)
* -d, --directory:      Specifies the directory to save any downloaded PDFs (default current working directory)
* -u, --upload:         Specifies whether to upload all generated files to S3 (default False)
* -w, --wait-time:      Specifies how long to wait between responses on a form in seconds (default 0.1)
* -t, --threads:        Specifies the number of parallel threads to run; generally limited by CPU cores (default 1)
* -i, --iterations:     Specifes the number of iterations (repetitions of a loop) to perform in each thread (default 1)
* --username:           Specifies a username to use for logging in; default credentials require S3, so required if S3 not available
* --password:           Specifies a password to use for logging in; default credentials require S3, so required if S3 not available

---------------------------------------------------------------------
## Docker Instructions

**<u>Commands**</u>
- Shell (docker-start.sh)
- Powershell (docker-start.ps1)

**<u>Prerequisites**</u>
1) Login into Leapp is a prerequisite
2) Navigate to docker-scripts folder
3) Replace the variables on the script
4) Run the script


### For Windows only, open powershell and run the following command before the script execution
```powershell
Set-ExecutionPolicy RemoteSigned
```
