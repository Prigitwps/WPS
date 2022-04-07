# -*- coding: UTF-8 -*-
# Documents verification test module for OES 1.0
# Requirements:
# Selenium Driver: https://www.selenium.dev/downloads/
# For default credentials and S3 upload, boto3: https://boto3.amazonaws.com/v1/documentation/api/latest/guide/quickstart.html
# Usage: python staticContentTesting.py [-h] [-e] [-d] [-l] [-u]
# Arguments:
# -h, --headless:       Specifies headless or display mode for browser (default False)
# -e, --env:            Specifies the environment to login and perform actions (default "uat")
# -d, --directory:      Specifies the directory to save any downloaded PDFs (default current working directory)
# -l, --log-to-file:    Specifies whether to log to the terminal output or to a text file in --directory (default False)
# -u, --upload:         Specifies whether to upload all generated files to S3 (default False)
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

fileHashes = {   'abas3': {   'documents': {   'ABAS-3 Adult Response Sheet': (   'abas_3_adult_response_sheet.pdf',
                                                                     '7f355504bc1b6542eec19eb0f15a07082e825ca03af743edba6c8d7320fbd972'),
                                  'ABAS-3 Parent 5-21 Response Sheet': (   'abas_3_parent_5_21_response_sheet.pdf',
                                                                           'd31c17f5640e2a1b53922411111f905769eb1db688904da7404cdc207f76859b'),
                                  'ABAS-3 Parent/Primary Caregiver 0-5 Response Sheet': (   'abas_3_parent_0_5_response_sheet.pdf',
                                                                                            'adc230cf7f348a62ebe131e05f816671c1c58a3d74d157f2ec818881c9f36bea'),
                                  'ABAS-3 Spanish Adult Response Sheet': (   'abas_3_adult_sp_response_sheet.pdf',
                                                                             'a12c3b82a3237d536eea15a4409b2465bf012ef1c5e85387fe1d09993f6c33dd'),
                                  'ABAS-3 Spanish Parent 5-21 Response Sheet': (   'abas_3_parent_5_21_sp_response_sheet.pdf',
                                                                                   '7e6a5d827f44e8c69b88e241384478bdea797b1f62be2342d2ee2a82c3c144a4'),
                                  'ABAS-3 Spanish Parent/Primary Caregiver 0-5 Response Sheet': (   'abas_3_parent_0_5_sp_response_sheet.pdf',
                                                                                                    '6cfcf1118f282269f3a2763efa6db16dffd61f69e061a6dba661eff30bb34075'),
                                  'ABAS-3 Spanish Teacher 5-21 Response Sheet': (   'abas_3_teacher_5_21_sp_response_sheet.pdf',
                                                                                    '376ad66928197b068411f53518c01bafbec7bc5f5945966db5a0a0f963b1fb35'),
                                  'ABAS-3 Spanish Teacher/Daycare Provider 2-5 Response Sheet': (   'abas_3_teacher_2_5_sp_response_sheet.pdf',
                                                                                                    '201fb5f31c3201c48db621b5edca5dc99222ead387811e541cd6fca24fe57328'),
                                  'ABAS-3 Teacher 5-21 Response Sheet': (   'abas_3_teacher_5_21_response_sheet.pdf',
                                                                            '43932a5b9193ebb4676feaec90fb4a4e2d56f793d70aafd18ebd6ffb053f2d9c'),
                                  'ABAS-3 Teacher/Daycare Provider 2-5 Response Sheet': (   'abas_3_teacher_2_5_response_sheet.pdf',
                                                                                            '96a76faf78f3049710e5029f4084afd1603dd265d579dfd692fb56801586fb2f'),
                                  'Ordered Content Listing': [   'ABAS-3 '
                                                                 'Parent/Primary '
                                                                 'Caregiver '
                                                                 '0-5 Response '
                                                                 'Sheet',
                                                                 'ABAS-3 '
                                                                 'Teacher/Daycare '
                                                                 'Provider 2-5 '
                                                                 'Response '
                                                                 'Sheet',
                                                                 'ABAS-3 '
                                                                 'Parent 5-21 '
                                                                 'Response '
                                                                 'Sheet',
                                                                 'ABAS-3 '
                                                                 'Teacher 5-21 '
                                                                 'Response '
                                                                 'Sheet',
                                                                 'ABAS-3 Adult '
                                                                 'Response '
                                                                 'Sheet',
                                                                 'ABAS-3 '
                                                                 'Spanish '
                                                                 'Parent/Primary '
                                                                 'Caregiver '
                                                                 '0-5 Response '
                                                                 'Sheet',
                                                                 'ABAS-3 '
                                                                 'Spanish '
                                                                 'Teacher/Daycare '
                                                                 'Provider 2-5 '
                                                                 'Response '
                                                                 'Sheet',
                                                                 'ABAS-3 '
                                                                 'Spanish '
                                                                 'Parent 5-21 '
                                                                 'Response '
                                                                 'Sheet',
                                                                 'ABAS-3 '
                                                                 'Spanish '
                                                                 'Teacher 5-21 '
                                                                 'Response '
                                                                 'Sheet',
                                                                 'ABAS-3 '
                                                                 'Spanish '
                                                                 'Adult '
                                                                 'Response '
                                                                 'Sheet']},
                 'manuals': {   'ABAS-3 Manual': {   'abas3_page1.jpg': '35617f9b8c989a84947bc95e0cf09ec563d873ac768acbd21841f097fa210503',
                                                     'abas3_page10.jpg': '16f0b01fafb63a345d8823f265d20c260f1ec32ff9a33b920d2de5d143fa6475',
                                                     'abas3_page11.jpg': '9bed16ca107f28231e3e0d1fc732ea126442190bfc4e16917fa98ab12c9e2b67',
                                                     'abas3_page294.jpg': '1a2ff73460de4e5cfeabc1de5c3c5510a6eea40fdc096499aa6205f7364e65e6'}}},
    'adir': {   'manuals': {   'ADI-R Manual': {   'adir_page1.jpg': 'bf0bfb7e3c45eaeb6c52b0849c34d4ef0fe09a4a9a55f211c0d8c35a340be631',
                                                   'adir_page10.jpg': 'f3fe4411c291878aa0bffb64d2498767416be0306bd295bd3299ebbe9d5273a7',
                                                   'adir_page11.jpg': '45aae6ca030cc005d715a3f00ef9209b206dcbe96db540ebf78647a2ead86207',
                                                   'adir_page74.jpg': '04d9b21d1671d1beb04e6bd58efb263f8ccd3eea5938e351aabb49f30da024c5',
                                                   'adir_page75.jpg': 'a0703cdb2e9f88db8f3e5329f3d874952435ffd5bd667c585c85551e78ae4d40'}}},
    'ados2': {   'manuals': {   'ADOS-2 Manual': {   'ados2_page1.jpg': '7441a09cbf82a08567cde8d2a117772bd1874bbc7a26759e5ae1e06545c1eb98',
                                                     'ados2_page10.jpg': '6c05929d8a3fe6a8ac7e71e7dec67459e492c0054c53654611a3d8278429eb97',
                                                     'ados2_page11.jpg': '332d0955aae3e93b528a9f850ce0cf51ca71ef9a872fbf852136596c670b4aa1',
                                                     'ados2_page460.jpg': '84c3950a28906d7e42c8e6c16f1652bf768580aa8224e76cb7e56ca63152f9f2',
                                                     'ados2_page461.jpg': '6c217759997664e896c78747e6a3eeb925e4b82ca82c7895f1ed8ecd7bf31873'}}},
    'arizona4': {   'documents': {   'Arizona-4 Guide to Report Writing': (   'arizona4-report-writing-guide.docx',
                                                                              '4c401804bf6b8ca214d953e2ba97431df8af2f48e2753086cc155cafb38d3947'),
                                     'Ordered Content Listing': [   'Arizona-4 '
                                                                    'Guide to '
                                                                    'Report '
                                                                    'Writing']},
                    'easels': {   'Administration Guide': {   'arizona4_page1.jpg': '9a0a04b4fdb4e3b56dc691c81a2f9bf0639762e94265b4207a9672ee1f0ebe52',
                                                              'arizona4_page11.jpg': '2a9f78cfec45f4df1954ed3f3c597c19480d3cb165076c5b43c04b51ec6c43c1',
                                                              'arizona4_page36.jpg': 'b9a431f560d8a0627de82bd4caf6b1b65509381e1e28f95cffc9f83172750a77'},
                                  'Digital Stimulus Images': {   'arizona4_page1.jpg': '198e4c6c453539d94b29f6377e171ae5bbba06b05eec483c2efb7adc46e6e5b2',
                                                                 'arizona4_page11.jpg': 'd7e134cc1de7ecdd040b346b047957c3a74e555565bec185af5964358ca5d4b2',
                                                                 'arizona4_page74.jpg': 'e3d2909ee6d7d3472a4d8096775102825b73d5840c9baa6479c8b6a65af379c0'}},
                    'manuals': {   'Arizona-4 Manual': {   'arizona4_page1.jpg': '065677b46ccc585afb08771ce8389768edd1282d252ae08b51527d6ec8692915',
                                                           'arizona4_page10.jpg': '04d9b21d1671d1beb04e6bd58efb263f8ccd3eea5938e351aabb49f30da024c5',
                                                           'arizona4_page11.jpg': 'be1b51a8f3fd2c5b4df2c856579950da325361ba7d66a8b2df13bfb8233a8a70',
                                                           'arizona4_page230.jpg': '165ae44301c9a05910617cf9217ced59e778962fd868859f1008af90cf79454e',
                                                           'arizona4_page231.jpg': 'c70e34225f98e09700af7c51766654f795dff466c80eb56481037daec6492c4b'}}},
    'caps': {   'documents': {   'CAPs Guide to Report Writing': (   'caps_report_writing_guide.docx',
                                                                     '02e40f794434a871ab968de2ca67cbb91878058a29b1b208bd957cb74244a702'),
                                 'CAPs Response Sheet': (   'caps_oes_response_sheet.pdf',
                                                            'bb24bd3934de8eae9f84e65ba2ce28c2ce98f37d0e4478868ef8e5a718085343'),
                                 'Ordered Content Listing': [   'CAPs Response '
                                                                'Sheet',
                                                                'CAPs Guide to '
                                                                'Report '
                                                                'Writing']},
                'manuals': {   'CAPs Manual': {   'caps_page1.jpg': '6ea92c7e955ecbe378adce88e652597d86d173770813fa050779912ed63ea963',
                                                  'caps_page10.jpg': '04d9b21d1671d1beb04e6bd58efb263f8ccd3eea5938e351aabb49f30da024c5',
                                                  'caps_page11.jpg': '324bb644e5751b914b1d12774d6b504cd32df6911234f6011941e3d11c511b63',
                                                  'caps_page120.jpg': 'f2d14743533c5526c7121b9b17cc9302d02742bac099c1619d2d712238dd5893'}}},
    'cars2': {   'manuals': {   'CARS-2 Online Manual': {   'cars2_page1.jpg': 'f7b862e691135e5c417846755abd204cf042fee91ff0e5a90ef96e53b2d09b15',
                                                            'cars2_page10.jpg': 'aff9312b3591d96df0656970164096f239d4553336f13740d217f490d2444efe',
                                                            'cars2_page11.jpg': 'bcbdfb8a3701667cf33a09afec9ab34f3020d6fc21561f4e9ac76f18edbca56d',
                                                            'cars2_page134.jpg': 'ba73a49f847010fe1700793e46d57cc4e1887a5778edb96d253d67e4779e5465'}}},
    'casl2': {   'documents': {   'CASL-2 Scoring and Reporting Guide': (   'casl2_scoring_guide.docx',
                                                                            '428cf4e843adb42bd5581d160ba7ee4f8ff2102f3d068c1841db4016e9727d12'),
                                  'CASL-2 Understanding Sensitivity and Specificity': (   'casl-2_sensitivity_and_specificity.pdf',
                                                                                          '98a3ca62d02d6a7f01be88f04140b9a310f8051099da1c21c430048d5c2e3cd0'),
                                  'Ordered Content Listing': [   'CASL-2 '
                                                                 'Scoring and '
                                                                 'Reporting '
                                                                 'Guide',
                                                                 'CASL-2 '
                                                                 'Understanding '
                                                                 'Sensitivity '
                                                                 'and '
                                                                 'Specificity']},
                 'easels': {   'CASL-2 Digital Easel 1 Administration Guide': {   'casl2_page1.jpg': 'f9b039e5f291417dcc3118f5cdbb7bc97b049d0c61222b45b0a051b89ef38940',
                                                                                  'casl2_page11.jpg': '60c6013ada94c79c51bc5edaad621ae08fc0ec798e8a7ef8efabc6c29b9c7c34',
                                                                                  'casl2_page175.jpg': '26fc2a0687665202b42fd3a0917f02d490ed9f9062f25e6adf9d27d8654b1f7e'},
                               'CASL-2 Digital Easel 1 Digital Stimulus Images': {   'casl2_page1.jpg': 'cb5645746bcb52e5afd7b63aedf9cabc52f79048c5ba56d50ba3564adb1b496e',
                                                                                     'casl2_page103.jpg': 'd82f14c5489d4a2c373964aa6ff77162dfac0954e7e2272909264b05e58d6dea',
                                                                                     'casl2_page11.jpg': '6c61497f1f8f7b3fd704ae364b82b7304effa783d03f614f45b2b52a737d2daf'},
                               'CASL-2 Digital Easel 2 Administration Guide': {   'casl2_page1.jpg': 'a2a12b64441f4d008e755757f6339f28bd82dbaf218a7d62b2284bd89b6fddbf',
                                                                                  'casl2_page11.jpg': 'd970bad65c3ad5988c94057dc362b07b5411bab7abfca799be0986e4eebc0c58',
                                                                                  'casl2_page154.jpg': 'ac8a23d189f18aaa323ef003d0a3ad6ae14cc6355e6f0a6ad25b9224655505ff'},
                               'CASL-2 Digital Easel 2 Digital Stimulus Images': {   'casl2_page1.jpg': 'e503ea4809c7945541d5e9d3fb55ab2b7e438e307d16b7ad67aa1dad6f24765c',
                                                                                     'casl2_page11.jpg': '182ca30c6910289511eabc55a78392d50b3be5fafe72e76a0e14249faf2b3588',
                                                                                     'casl2_page116.jpg': 'd82f14c5489d4a2c373964aa6ff77162dfac0954e7e2272909264b05e58d6dea'},
                               'CASL-2 Digital Easel 3 Administration Guide': {   'casl2_page1.jpg': 'e7213aca1661f8034a9197dc6876d4eaaff98a8e44dd33b1808c7d15f1997900',
                                                                                  'casl2_page11.jpg': '1fbd794033fd752be39c85c32f077391719d2d62d74bb757d42db10b8bca9dd0',
                                                                                  'casl2_page224.jpg': '301fe2f66bc930422a7ca5bcdd08e047972a844ba61bad5f18b9c3d328a1b749'},
                               'CASL-2 Digital Easel 3 Digital Stimulus Images': {   'casl2_page1.jpg': 'f9f7fdf850b326c829a69bf1f21776a9a2df426c0a43d6030e5ac095ddd78196',
                                                                                     'casl2_page11.jpg': '67fd20fc20d0890e017cfbdbf9b1d19b0fa009717bc5a166a00bb36494ea3cfd',
                                                                                     'casl2_page40.jpg': 'd82f14c5489d4a2c373964aa6ff77162dfac0954e7e2272909264b05e58d6dea'}},
                 'manuals': {   'CASL-2 Manual': {   'casl2_page1.jpg': '6d03e01f835fbdbbebd5e84dec09c695ab1267cf24d5a143fbc1e953da70cfbc',
                                                     'casl2_page10.jpg': '6a3e473a04186840fdac98dd6ab06c629adfe09024f23a70ca290bf623490486',
                                                     'casl2_page11.jpg': '7e099f6f86c6dc31f6d773e7dcb021dbd370784c9a538a2d4ba8d551180ff86a',
                                                     'casl2_page372.jpg': 'a75bdda491b030916a66cf88407eb8f43f0dbfff38e32d2ff8790bddc6e6f9ed'}}},
    'dbc2': {   'documents': {   'DBC2 Adult Form Response Sheet': (   'dbc2_adult_response_sheet.pdf',
                                                                       'bdb8a93b5b12bc7af3e9432c67e48bb40f0e6c4e368409bb29d0d7dcbd87501a'),
                                 'DBC2 Parent Form Response Sheet': (   'dbc2_parent_response_sheet.pdf',
                                                                        '6decc965ed18258650ba5884f4e9e528abd92c0453c90cc31b5e66c07185e1e9'),
                                 'DBC2 Teacher Form Response Sheet': (   'dbc2_teacher_response_sheet.pdf',
                                                                         'c796c9fa84a6714b50f2cb0e2f2fdb61dc8c41334d5062b6c05e88dbd96177b8'),
                                 'Ordered Content Listing': [   'DBC2 Parent '
                                                                'Form Response '
                                                                'Sheet',
                                                                'DBC2 Teacher '
                                                                'Form Response '
                                                                'Sheet',
                                                                'DBC2 Adult '
                                                                'Form Response '
                                                                'Sheet']},
                'manuals': {   'DBC2 Manual': {   'dbc2_page1.jpg': '7cb10b72fbb100eac19f37bf39244449432b5be7f61ad612fcb5c5e463d01395',
                                                  'dbc2_page10.jpg': 'a2ed3b5b7c79b3fa273b4a39c80d22d68e95de6b66c2d6b02d72189f96de9863',
                                                  'dbc2_page11.jpg': 'fcbf886f0343b898230005f7e63ecae176ccbd54e72ef952ed5cc42d26c28025',
                                                  'dbc2_page88.jpg': 'a60a13b5d40eeb994db67aadcbf057a2fc9c5b593200eb0d3d0161d6076ec8be'}}},
    'dp3': {   'documents': {   'DP-3 Interview Form Response Sheet': (   'dp_3_interview_response_sheet.pdf',
                                                                          '10fe46bc49156cde0094c17f650dcb6a06cd3ca96e12eb9ef7ca496e9ebfff07'),
                                'DP-3 Parent/Caregiver Checklist Response Sheet': (   'dp_3_parent_caregiver_checklist_response_sheet.pdf',
                                                                                      'e21a23788faeca148ce7f61eea26bd497b39927e701b9a32dafac1c0608be6fc'),
                                'DP-3 Spanish Interview Form Response Sheet': (   'dp_3_spanish_interview_response_sheet.pdf',
                                                                                  'b1510d423605f3f696a21836be0a5a26763f5e3d231d2e0f34cd4089e35481f5'),
                                'DP-3 Spanish Parent/Caregiver Checklist Response Sheet': (   'dp_3_spanish_parent_caregiver_checklist_response_sheet.pdf',
                                                                                              '07d2bfb03016b2bd072225f7949171ae4a8f2b91b514c3162eac8c07365c5594'),
                                'Ordered Content Listing': [   'DP-3 Interview '
                                                               'Form Response '
                                                               'Sheet',
                                                               'DP-3 '
                                                               'Parent/Caregiver '
                                                               'Checklist '
                                                               'Response Sheet',
                                                               'DP-3 Spanish '
                                                               'Interview Form '
                                                               'Response Sheet',
                                                               'DP-3 Spanish '
                                                               'Parent/Caregiver '
                                                               'Checklist '
                                                               'Response '
                                                               'Sheet']},
               'manuals': {   'DP-3 Manual': {   'dp3_page1.jpg': 'a00aa58f03c1ddfaa7e1c7c5ff192bd9da4cbb55474799db81be7e5ed013cdb6',
                                                 'dp3_page10.jpg': '4d10fad484547c6184c84da17c5d63a334a2868a356a23085e9d9d784e19b40b',
                                                 'dp3_page11.jpg': '8e6fbd89b15da3cb326f65a4d3b1fb5c316b876fe2fcae10a52f25b59f18f2e6',
                                                 'dp3_page234.jpg': '36fd67cfffe7c6e9805de196587a731bed0791e9f41324ea18f6f3c2bf355b9e'}}},
    'dp4': {   'documents': {   'DP-4 Clinician Rating Response Sheet': (   'dp4_clinician_rating_response_sheet.pdf',
                                                                            '83cf5827f035c9f22f491a15c4ff8baba360a80c7257daa543d0d1d873adb536'),
                                'DP-4 Developmental Chart': (   'dp4_developmental_chart.pdf',
                                                                '363bba1d6cf7c9bcbd3d1d9a280db7fff9b2a22f6255074701def91e1ccad869'),
                                'DP-4 Parent/Caregiver Checklist Response Sheet': (   'dp4_parent_caregiver_checklist_response_sheet.pdf',
                                                                                      '5e9c4ebd8a4cb4aa2c51e4ab59be910998a0384767efedb49a0671d6dc784b3b'),
                                'DP-4 Parent/Caregiver Interview Response Sheet': (   'dp4_parent_caregiver_interview_response_sheet.pdf',
                                                                                      'f595b679661e22cfe2502ec70c6cf7c2547d0f8cbfb68e9535287a34be2cb960'),
                                'DP-4 Rater Comparison Scoring Sheet': (   'dp4_rater_comparison_scoring_sheet.pdf',
                                                                           '695914b5e0bb7bf9c40eea21df13ef527c8f66b1c82785f4f13a499923f08d29'),
                                'DP-4 Spanish Parent/Caregiver Checklist Response Sheet': (   'dp4_sp_parent_caregiver_checklist_response_sheet.pdf',
                                                                                              '5d245598d55cd73177fec5b9e4e2676ac77c864ea40557cea7cd0f38403cd615'),
                                'DP-4 Spanish Parent/Caregiver Interview Response Sheet': (   'dp4_spanish_interview_response_sheet.pdf',
                                                                                              '18a97f883e43452c69d5a4a8e1f3e1d9083f71b41ea32784a55859955ec98639'),
                                'DP-4 Spanish Teacher Checklist Response Sheet': (   'dp4_sp_teacher_checklist_response_sheet.pdf',
                                                                                     'c548d574f5a915f1511351575547d583e5f5e5b36b8db470686b8a40fc83257b'),
                                'DP-4 Teacher Checklist Response Sheet': (   'dp4_teacher_checklist_response_sheet.pdf',
                                                                             'a4808cfb8c3d79f18f9cd63c9f17201c824125b1e8e8221e4fd4c98bf09dc2b4'),
                                'Ordered Content Listing': [   'DP-4 Rater '
                                                               'Comparison '
                                                               'Scoring Sheet',
                                                               'DP-4 '
                                                               'Parent/Caregiver '
                                                               'Interview '
                                                               'Response Sheet',
                                                               'DP-4 '
                                                               'Parent/Caregiver '
                                                               'Checklist '
                                                               'Response Sheet',
                                                               'DP-4 Teacher '
                                                               'Checklist '
                                                               'Response Sheet',
                                                               'DP-4 Clinician '
                                                               'Rating '
                                                               'Response Sheet',
                                                               'DP-4 Spanish '
                                                               'Parent/Caregiver '
                                                               'Interview '
                                                               'Response Sheet',
                                                               'DP-4 Spanish '
                                                               'Parent/Caregiver '
                                                               'Checklist '
                                                               'Response Sheet',
                                                               'DP-4 Spanish '
                                                               'Teacher '
                                                               'Checklist '
                                                               'Response Sheet',
                                                               'DP-4 '
                                                               'Developmental '
                                                               'Chart']},
               'manuals': {   'DP-4 Manual': {   'dp4_page1.jpg': '3e24a2de8b1fae4ada1d335353137d511c834707dce4dd3f91afcf17c4665fe7',
                                                 'dp4_page10.jpg': '04d9b21d1671d1beb04e6bd58efb263f8ccd3eea5938e351aabb49f30da024c5',
                                                 'dp4_page11.jpg': '4e9b55f32240f0b18c981af930fc31b9e32175a577a7310b66a1327ccb01cb44',
                                                 'dp4_page444.jpg': '79cdda365ba666990a3e8cfa4fb6325668a00a08c873a5b83aa3db9f3596d5d5'}}},
    'goal': {   'manuals': {   'GOAL Manual': {   'goal_page1.jpg': '932594d60872afe777fbe74dd6ccb785a3476c2cb28152f07099fa90692e264a',
                                                  'goal_page10.jpg': '2865fb7b051cb05796618c2a41fddd20b2ef0ce9500511698ff71a418034c069',
                                                  'goal_page11.jpg': '410734a97a86c006ec1ba86d7b306897bd1db557db1d788ca56110cbd1e06c3f',
                                                  'goal_page118.jpg': '04d9b21d1671d1beb04e6bd58efb263f8ccd3eea5938e351aabb49f30da024c5',
                                                  'goal_page119.jpg': 'f8057bce6a89e08dfb592c758abf352b3f7678eaaeb3e53b10ff13fef904b4d0'}}},
    'migdas2': {   'manuals': {   'MIGDAS-2 Manual': {   'migdas2_page1.jpg': '6719fd9995a65e1664bdcc78b8f6fccca98b34f1fe9af26dd7f5dc966012cac6',
                                                         'migdas2_page10.jpg': 'eafd93f4341b92986a52011e2073374b80c52b735ce8934027b250be1c89a24f',
                                                         'migdas2_page11.jpg': '9d579492ec5c13b9f696d6e278a73d1c4dc7e5ac9fc10bcec134010d9a08eea8',
                                                         'migdas2_page298.jpg': 'e2306b2abf2cffa1184b554e4425842e01fc57479a3a0939c38563bc8052d87a'}}},
    'opus': {   'audio': {   'OPUS Audio Files': (   'OPUS_Audio.zip',
                                                     'e84a4420b34e418c4798dc52792aa1b10ecdb3478b3658d867a7964e6602316a'),
                             'Ordered Content Listing': ['OPUS Audio Files']},
                'documents': {   'OPUS Scoring and Reporting Guide': (   'opus_scoring_guide.docx',
                                                                         'efe415cec7d2306e432f6c90743d22b753c1d73d9e0640098b808668ff661ce0'),
                                 'Ordered Content Listing': [   'OPUS Scoring '
                                                                'and Reporting '
                                                                'Guide']},
                'easels': {   'OPUS Digital Easel': {   'opus_page1.jpg': '335376a9ce185605db60e26991141d8bec6fce126fd7480dd25bee051f84240a',
                                                        'opus_page11.jpg': '68759d7c814617728002b94c8567009797ebb54f80923b9cbbdad22d4cf7a9bf',
                                                        'opus_page168.jpg': '65a42a20933fa72b81e19861caf4fa13fe41770df57d783f5b0b1f5c26f525bf'}},
                'manuals': {   'OPUS Manual': {   'opus_page1.jpg': '8540aa6a3d2a5748081165a4474fa2c3d4902343a846a257453c6ce225514886',
                                                  'opus_page10.jpg': '8e6fbd89b15da3cb326f65a4d3b1fb5c316b876fe2fcae10a52f25b59f18f2e6',
                                                  'opus_page11.jpg': '056508e51bc99c9c021747a99ed83579baad29b4c05b6e55dd3852dfb43b5063',
                                                  'opus_page138.jpg': 'e8349889c1d646ec049d607f1ee3449a963ecc08af44676681f0d6beed356ac0'}}},
    'owlsii': {   'easels': {   'OWLS–II Digital LC Easel - Form A Administration Guide': {   'owlsii_page1.jpg': 'd8b19693375e74a754c3fa16574cd6bf7cf6a5d9347dc8afe4810192336343e5',
                                                                                              'owlsii_page11.jpg': 'ccc5b1502f91730146d8e3db1a30fe8c8578103a6a9261f3f1a3ae6317cc8dc2',
                                                                                              'owlsii_page137.jpg': '86993d279c3bd84f91e030bab66ff29b791334eebb0c881174cab6d8e6b2b2a0'},
                                'OWLS–II Digital LC Easel - Form A Stimulus Images': {   'owlsii_page1.jpg': '646857dd6050cda96e7fe80bc7d5af0d561e1ff725b68f05542bc65561ec4adc',
                                                                                         'owlsii_page11.jpg': '7a675899fb43b4979d0b6c481b3911957b510bd185b9131bf99d3618702536b6',
                                                                                         'owlsii_page137.jpg': 'a67ff23fb02bc1e436a84c88e95ea93ee5e8c2f76b5ef1dc7a1c3b5a65faa691'},
                                'OWLS–II Digital LC Easel - Form B Administration Guide': {   'owlsii_page1.jpg': 'b599c7f8311867fca8e0324dbc715cb04d724fac202a88b03370cb29bbbf90ef',
                                                                                              'owlsii_page11.jpg': '6a4df8b344cdb88574af59ae7838a39baf5246d59542fc1a7c1050553452f2ed',
                                                                                              'owlsii_page137.jpg': '401bc1595e39c6b6a7aca5eb6b0606288aa4088e92a527daf1f96c707dcbfcc6'},
                                'OWLS–II Digital LC Easel - Form B Digital Stimulus Images': {   'owlsii_page1.jpg': '72cb76fb359bf0dc3c9abbc4e0904694b50c8913064f33023bd6faca460358b0',
                                                                                                 'owlsii_page11.jpg': 'b03fe618b7a3450c6ff0bed0529bab3111d86aa77d0d00e3c79575f4ef80d1cf',
                                                                                                 'owlsii_page137.jpg': 'a67ff23fb02bc1e436a84c88e95ea93ee5e8c2f76b5ef1dc7a1c3b5a65faa691'},
                                'OWLS–II Digital OE Easel - Form A Administration Guide': {   'owlsii_page1.jpg': '41abe142608ca4f19acf14089c3a0166d0cde17a8281b0769b3bd8be7c552ea3',
                                                                                              'owlsii_page11.jpg': '02647c37f5efba8fcf4ad3ec433c172a8707a169eba89de980b481c6ef8cfed7',
                                                                                              'owlsii_page115.jpg': 'f075422b795a6aad8e73074dc76488734420a1ea8a929c1ba66118fdf16bfd08'},
                                'OWLS–II Digital OE Easel - Form A Stimulus Images': {   'owlsii_page1.jpg': '56388bd2e373b8e959883a1f299192f1971b92ebca0f4abe2235956724da2e2b',
                                                                                         'owlsii_page11.jpg': 'ce58a1db48d1f7b0ba9640aab47406d6a2389a2fc16fe57d59b4f1c22c61a434',
                                                                                         'owlsii_page114.jpg': 'a67ff23fb02bc1e436a84c88e95ea93ee5e8c2f76b5ef1dc7a1c3b5a65faa691'},
                                'OWLS–II Digital OE Easel - Form B Administration Guide': {   'owlsii_page1.jpg': 'ea8313dc7eb35b1ab5492e41874b215c4759c4b03ccee4b851bb31ea8a125692',
                                                                                              'owlsii_page11.jpg': 'ea38b785cb3eeffeeac1b6461839cbb174ad4990c2f4e899e1d50cada8f12ebd',
                                                                                              'owlsii_page115.jpg': 'b4bf08d38092fc55ece232aeffee204ba1a38b46481fcd0e1a9a8c015b0eca37'},
                                'OWLS–II Digital OE Easel - Form B Digital Stimulus Images': {   'owlsii_page1.jpg': 'bec9a60abed9ac72eaeeaeaab7be1c776c79041b98189c331e53bd009f26efac',
                                                                                                 'owlsii_page11.jpg': '0c6e6705d3539f4314d88324e2902422c0e0ccdd008dfd64e7f82869c8749c4b',
                                                                                                 'owlsii_page114.jpg': 'a67ff23fb02bc1e436a84c88e95ea93ee5e8c2f76b5ef1dc7a1c3b5a65faa691'},
                                'OWLS–II Digital RC Easel - Form A Administration Guide': {   'owlsii_page1.jpg': 'a7a36507424b894a046dcaf6b02ce77eac1fde599e45b507e8500a042ef3b574',
                                                                                              'owlsii_page11.jpg': 'a1565fa3f4b32470a9eac0260424573bda53507586fe659c2d208ca5e43de2d3',
                                                                                              'owlsii_page146.jpg': 'ca5f84d99c9b2547c03009163a519393db69ffaf78fb32a95085e45cc2bd80f5'},
                                'OWLS–II Digital RC Easel - Form A Stimulus Images': {   'owlsii_page1.jpg': '77f8e15879e2d5f7692fcf790d6488fb7413e58bdb883eaed7a951d303e64ff0',
                                                                                         'owlsii_page11.jpg': 'c8cc2ab896bcf4d9523e941d41876e0a96cec63cfea70f672bad08415d626122',
                                                                                         'owlsii_page146.jpg': 'a67ff23fb02bc1e436a84c88e95ea93ee5e8c2f76b5ef1dc7a1c3b5a65faa691'},
                                'OWLS–II Digital RC Easel - Form B Administration Guide': {   'owlsii_page1.jpg': '2703167cfffcb56d76bb93d6e8850a810f255b0849a4e10496959eda50a4a487',
                                                                                              'owlsii_page11.jpg': '534cf54b09016b42f51b8099415aa7b80a51ea9c66b1d04d8607455982900f1d',
                                                                                              'owlsii_page146.jpg': 'a9f70985100a7daa49973140dd328cd58401b22cb9baa8dc01259a307788a63f'},
                                'OWLS–II Digital RC Easel - Form B Digital Stimulus Images': {   'owlsii_page1.jpg': 'd1a42e845fb439dea72e52c1f3c64ea4be6fb73cebe773e901b70eb1cf909bef',
                                                                                                 'owlsii_page11.jpg': 'abc369d30f851e0c879756b8126a6a69eb94673406910ff4e4d60453a383a026',
                                                                                                 'owlsii_page146.jpg': 'a67ff23fb02bc1e436a84c88e95ea93ee5e8c2f76b5ef1dc7a1c3b5a65faa691'},
                                'OWLS–II Digital WE Easel - Form A Administration Guide': {   'owlsii_page1.jpg': 'b72b706a10c92180c07f37bbe2d0cb03d361e1a3b0ef35a2940fbecf1d7191ec',
                                                                                              'owlsii_page11.jpg': 'fa37828425eebdd518419a2b5a56cd5b40ae5bba7d887cbae69b9421446e0177',
                                                                                              'owlsii_page54.jpg': 'f55d467ffeae2e1442a78c51aa89210e8285d472c3fecc130253cc914fe5d94e'},
                                'OWLS–II Digital WE Easel - Form A Stimulus Images': {   'owlsii_page1.jpg': '94e913994eae0d044021a5630b1c1aad1e3ac232536ce5e91e36f86fd6f816e3',
                                                                                         'owlsii_page11.jpg': '867deb6485a85d8c3abcc676f2aa0c7dd8f228d678270d03911b5cc41d998ae1',
                                                                                         'owlsii_page31.jpg': 'a67ff23fb02bc1e436a84c88e95ea93ee5e8c2f76b5ef1dc7a1c3b5a65faa691'},
                                'OWLS–II Digital WE Easel - Form B Administration Guide': {   'owlsii_page1.jpg': '0f9b4ed22c419aa9ae34bc5c1afc70834afcd591f4b65f46c6b02da9f59ccdc3',
                                                                                              'owlsii_page11.jpg': '150b16ca395ba509e790b27e525a6abcea239b05b0af6d49432da88c75ec4e48',
                                                                                              'owlsii_page54.jpg': '1048a331cd30b19fe37be367ce987c14d322a980177d9e6f891b51667879adaa'},
                                'OWLS–II Digital WE Easel - Form B Digital Stimulus Images': {   'owlsii_page1.jpg': 'a3cf2ddb8a9de4ffb5b09eabefe16598b123900872377b89e83d8766b25b0ccb',
                                                                                                 'owlsii_page11.jpg': '867deb6485a85d8c3abcc676f2aa0c7dd8f228d678270d03911b5cc41d998ae1',
                                                                                                 'owlsii_page31.jpg': 'a67ff23fb02bc1e436a84c88e95ea93ee5e8c2f76b5ef1dc7a1c3b5a65faa691'}},
                  'manuals': {   'OWLS-II LC/OE Online Manual': {   'owlsii_page1.jpg': 'fdc1d817af9ca0970476c62840d4af95b91a67f838653b5439eca9e04728845d',
                                                                    'owlsii_page10.jpg': 'f95ac04e4a5a99cbfbc613b2311f6324fcb2ba095045c9e7a9f7600fb50135c8',
                                                                    'owlsii_page11.jpg': '4e79f1ccda3fb4d5ff251f9f1515704ebcc494e330a8c183d52330744a8d7e25',
                                                                    'owlsii_page286.jpg': '04d9b21d1671d1beb04e6bd58efb263f8ccd3eea5938e351aabb49f30da024c5',
                                                                    'owlsii_page287.jpg': '5934e8e9f945f54f0a9407e2719c1114b453c821c58f188ca5d2cfa80c13c6f8'},
                                 'OWLS-II RC/WE Online Manual': {   'owlsii_page1.jpg': 'b3510edee0be510fee7afa80873e5dc93f582b77411ee3ab31cebb9587d80c52',
                                                                    'owlsii_page10.jpg': '720abb576c2b49eaf6194dcbd27457f55220e12a49e3efae48970b9f5a936e37',
                                                                    'owlsii_page11.jpg': 'a7a5a82367f38305fa5575b294c680caf7e41d3cf512728521eeef23e8778e1b',
                                                                    'owlsii_page446.jpg': '04d9b21d1671d1beb04e6bd58efb263f8ccd3eea5938e351aabb49f30da024c5',
                                                                    'owlsii_page447.jpg': 'f0e8eec4a57439b8874221f6096d428c4d261d1f7797dfcad4024f54ead6ee7e'}}},
    'piersharris3': {   'documents': {   'Ordered Content Listing': [   'Piers-Harris '
                                                                        '3 '
                                                                        'Response '
                                                                        'Sheet',
                                                                        'Piers-Harris '
                                                                        '3 '
                                                                        'Spanish '
                                                                        'Response '
                                                                        'Sheet'],
                                         'Piers-Harris 3 Response Sheet': (   'ph3_en-response_sheet.pdf',
                                                                              '473b911d1ef2070a97eda2d72b2a5022bd0f376d4a289db5ffcb01e933e2ab92'),
                                         'Piers-Harris 3 Spanish Response Sheet': (   'ph3_sp-response_sheet.pdf',
                                                                                      'af8dfd81888a511ee9eb5bef1a45a5ab3ba9928cac5c5b44821a105a75d87a47')},
                        'manuals': {   'Piers-Harris 3 Manual': {   'piersharris3_page1.jpg': '229944db4e4f6e1dbb7c1b61d7671b26927fcfc94983f0ccdae460f367b2afca',
                                                                    'piersharris3_page10.jpg': '04d9b21d1671d1beb04e6bd58efb263f8ccd3eea5938e351aabb49f30da024c5',
                                                                    'piersharris3_page11.jpg': '07351f8d716b96e925a44373faf3a70c8223a053b7b1a2b606274fe418ec944c',
                                                                    'piersharris3_page96.jpg': '765f1884626e5b5ab0b7a8ee85826eb8387196edf40abacdb98d4c7a3328a4a0'}}},
    'ppascale': {   'easels': {   'PPA Scale Digital Easel A Administration Guide': {   'ppascale_page1.jpg': '5303fee358c207939ceff441a0a27ee094653738a19c6e78c2542a63086a59fe',
                                                                                        'ppascale_page11.jpg': '2cc663d74ad3d3471ca22f3e74ea6f1dd503ac3d71bb97470d6628bfafd39d0c',
                                                                                        'ppascale_page86.jpg': '2028617485bf2c58909e41b94a1570b68e394a8f407d74742b760f79544c54f6'},
                                  'PPA Scale Digital Easel A Digital Stimulus Images': {   'ppascale_page1.jpg': '7e135a89e31d795e37b5b2ddfec49d669e5c2519634c8bc1217d573f9f579f25',
                                                                                           'ppascale_page11.jpg': '5fad153483bf3f4f49f1f52c0042fa9e4fa9a15b96608b3a9c95229602a4e48e',
                                                                                           'ppascale_page79.jpg': 'a67ff23fb02bc1e436a84c88e95ea93ee5e8c2f76b5ef1dc7a1c3b5a65faa691'},
                                  'PPA Scale Digital Easel B Administration Guide': {   'ppascale_page1.jpg': 'dc68b26ec6927db73825a23b3da55552d50de26a8b62004c4322a412515f7e35',
                                                                                        'ppascale_page11.jpg': 'c7a9ee8b891289d7ad6832e6f24b0e7b964292f92c28632e34c4cd02036da71e',
                                                                                        'ppascale_page86.jpg': '8419c17427cde5e45f1fe31320aeff08ce9c1b87e40b8e3cbf1d07e501a9e984'},
                                  'PPA Scale Digital Easel B Digital Stimulus Images': {   'ppascale_page1.jpg': '64cf6391aa720c9e9218e43bdc17fbb7fbb73433e3c7704771f0bb5482d8c411',
                                                                                           'ppascale_page11.jpg': 'a307d16dfb560f11b737010ef69831120b3bc9dfd624373c6012a60868907b9b',
                                                                                           'ppascale_page79.jpg': 'a67ff23fb02bc1e436a84c88e95ea93ee5e8c2f76b5ef1dc7a1c3b5a65faa691'},
                                  'PPA Scale Digital Easel C Administration Guide': {   'ppascale_page1.jpg': '12d91d0021a8352b1a0d1aa8f86fbd4876ac2a5c9f42ea756c0e771dbbc6e609',
                                                                                        'ppascale_page11.jpg': '7caf79525c119ae056606e64a240ef49a79f57612b369a42d678bf882d8227d8',
                                                                                        'ppascale_page86.jpg': 'fbdc67a25aed7d221b25b113ad211971199c7bcb76e80447644ee86265b325b7'},
                                  'PPA Scale Digital Easel C Digital Stimulus Images': {   'ppascale_page1.jpg': '6b15f2b8deb604eb53208a51563f9d2188ee000aa40aa57703971047c07d7b41',
                                                                                           'ppascale_page11.jpg': '49408e0333ba4a7a76436bd0a33962dffc752c907a848423159e280dfc032610',
                                                                                           'ppascale_page79.jpg': 'a67ff23fb02bc1e436a84c88e95ea93ee5e8c2f76b5ef1dc7a1c3b5a65faa691'}},
                    'manuals': {   'Building Early Literacy Skills -  Phonological and Print Awareness Activities': {   'ppascale_page1.jpg': '42c242f0971674c116401854105ae69df11645b545f871285ed3ed7ec5a8a4e9',
                                                                                                                        'ppascale_page10.jpg': '452d13fead73814e890a9ca04fa08965407c65387ad064e085e3fdcfaddf4316',
                                                                                                                        'ppascale_page11.jpg': '139f358e8f9ca141ea099fff5c01032f57b8cce3e075a759bba9acedd7a84ded',
                                                                                                                        'ppascale_page240.jpg': '0ec6409aee6fe8ed06fbb46671b4e85f74ec189c312f95c20c4420217579b478'},
                                   'PPA Scale Manual': {   'ppascale_page1.jpg': '916a5a8ea0b57cc78389ee67f5dbc1ea2620f445acb2e6f8ab99b5f954ddede9',
                                                           'ppascale_page10.jpg': '452d13fead73814e890a9ca04fa08965407c65387ad064e085e3fdcfaddf4316',
                                                           'ppascale_page11.jpg': 'eccf93b8723b8b1805ff02dc75d45db1ffe3d6548c089cc174402df0e6b27ead',
                                                           'ppascale_page90.jpg': '94e2590f4bb7c3687e1ba4b0c143870868368a4609e02abca2a729190bda653c'}}},
    'rcmas2': {   'audio': {   'Ordered Content Listing': [   'RCMAS-2 Audio '
                                                              'CD Files'],
                               'RCMAS-2 Audio CD Files': (   'RCMAS-2_Audio.zip',
                                                             '4322c26ff2ddb918c6950d852dc36f3bd0f26ec5c2548ce06d45c78daf8efe15')},
                  'documents': {   'Ordered Content Listing': [   'RCMAS-2 '
                                                                  'Response '
                                                                  'Sheet',
                                                                  'RCMAS-2 '
                                                                  'Spanish '
                                                                  'Response '
                                                                  'Sheet'],
                                   'RCMAS-2 Response Sheet': (   'rcmas-2_english_response_sheet.pdf',
                                                                 '7fa213b22229bec2b37401f3683c9fb606d47fdb8e34c80c305eb13ca3c91c3c'),
                                   'RCMAS-2 Spanish Response Sheet': (   'rcmas-2_spanish_response_sheet.pdf',
                                                                         '07b5dd87c6ada96be27f0de23e7bb2d3dff0f2e30d8bcd3125ba2f688750adc5')},
                  'manuals': {   'RCMAS-2 Manual': {   'rcmas2_page1.jpg': '73ed9500bc2c91d26266775817907b58ce1ad6d4bc7a8fdf6a564c2c78fc8af2',
                                                       'rcmas2_page10.jpg': 'f1cdc427d263befd854460d923194d4e4c2705e8831f88d156985f11bb337ba4',
                                                       'rcmas2_page11.jpg': 'ff5dcd8776489fda22a537cf14940a6fba80a088c8aa2a9b07f5aef20ce19a1a',
                                                       'rcmas2_page94.jpg': '96c975e0a7eb73f58d7bec85bd47884983eab96d7833a6b75593643ec664a6ce'}}},
    'rise': {   'documents': {   'Ordered Content Listing': [   'RISE Parent '
                                                                'Form Response '
                                                                'Sheet',
                                                                'RISE Teacher '
                                                                'Form Response '
                                                                'Sheet',
                                                                'RISE Self '
                                                                'Form Response '
                                                                'Sheet',
                                                                'RISE Spanish '
                                                                'Parent Form '
                                                                'Response '
                                                                'Sheet',
                                                                'RISE Spanish '
                                                                'Teacher Form '
                                                                'Response '
                                                                'Sheet',
                                                                'RISE Spanish '
                                                                'Self Form '
                                                                'Response '
                                                                'Sheet'],
                                 'RISE Parent Form Response Sheet': (   'rise_parent_response_sheet.pdf',
                                                                        '820bb368c6008ed3322367f2f61f3bb3c10b95f7dc0e329a65c71f724800333b'),
                                 'RISE Self Form Response Sheet': (   'rise_self_response_sheet.pdf',
                                                                      'b39ce76963be467c4ce21e42fd145667131be2c5f6a94e5c6876c04d5803a5d6'),
                                 'RISE Spanish Parent Form Response Sheet': (   'rise_parent_sp_response_sheet.pdf',
                                                                                '00900e29b2361f400b3bb88b9cd9b145adbf19d9cb6d0ee2aec33b1397f6b76e'),
                                 'RISE Spanish Self Form Response Sheet': (   'rise_self_sp_response_sheet.pdf',
                                                                              '2fa2de0eafa5ad7429bf323e8a234feca82137f7ecc391baafd4a7f1154bd957'),
                                 'RISE Spanish Teacher Form Response Sheet': (   'rise_teacher_sp_response_sheet.pdf',
                                                                                 '5ceaf5d7c32b183df97b5df1b2ac4d4d524a132c89f6acb96a74b71cd5a3ecaa'),
                                 'RISE Teacher Form Response Sheet': (   'rise_teacher_response_sheet.pdf',
                                                                         'ccde45d67327ca0ad6db8dac99d197f4c1c55f2b69f4470fd387ab7450e26519')},
                'manuals': {   'RISE Manual': {   'rise_page1.jpg': '695d97092994155eb230dae8064ca88518047a40049bee60b8dc9955341e8b4f',
                                                  'rise_page10.jpg': '02154ba6966ca86b65e834139bf23fda606e0f842935945c675ae4914f1874e0',
                                                  'rise_page11.jpg': 'b384aa0a2d8ee26e46ec0c3e06ab2ced9786501d3f7ee5d8e54e15aab7d8afad',
                                                  'rise_page160.jpg': '7f2c8d064dca1aa0824d43885bb13a5d356939dfe16a7d93d718716b9c13d47c'}}},
    'scq': {   'documents': {   'Ordered Content Listing': [   'SCQ Lifetime '
                                                               'Form Response '
                                                               'Sheet',
                                                               'SCQ Current '
                                                               'Form Response '
                                                               'Sheet',
                                                               'SCQ Spanish '
                                                               'Lifetime Form '
                                                               'Response Sheet',
                                                               'SCQ Spanish '
                                                               'Current Form '
                                                               'Response '
                                                               'Sheet'],
                                'SCQ Current Form Response Sheet': (   'scq_current_response_sheet.pdf',
                                                                       '1cb31c5e754bc091ff02dfc75efbbbf8eb0c6ddfa3c80334c5a0063eccf99445'),
                                'SCQ Lifetime Form Response Sheet': (   'scq_lifetime_response_sheet.pdf',
                                                                        '8eec5e5c7baf0451b533c2501b203ff030eb9246d4d76f49060482a92d446981'),
                                'SCQ Spanish Current Form Response Sheet': (   'scq_current_sp_response_sheet.pdf',
                                                                               '1efa0a196f72db93010c6bfa6e7f076952ed1e8895fc6a5bccfde8fd4c4bdebc'),
                                'SCQ Spanish Lifetime Form Response Sheet': (   'scq_lifetime_sp_response_sheet.pdf',
                                                                                '956e3bf308376860efb4f9bfb438a8b67cb250a3e1a3257069d17b128983f09c')},
               'manuals': {   'SCQ Manual': {   'scq_page1.jpg': '8b6a29e6fe18acb40216dc9cbee044cdccb1ea506bd6573058e07d1b8be76de5',
                                                'scq_page10.jpg': 'f2998a4c772429f0bf7ba27389a0af2f2f7a40db762cabcc2cae9740ee72c975',
                                                'scq_page11.jpg': '329b2349dda83b5529d34926c2fc0dde31337fa6933181525ef4a4a030d76ee7',
                                                'scq_page34.jpg': '2b5814fe5dd71120a8d5fc83a6581bdee6b7beca066a1e5921d20452e10979cb'}}},
    'smalsi': {   'audio': {   'Ordered Content Listing': [   'SMALSI Audio CD '
                                                              'Files'],
                               'SMALSI Audio CD Files': (   'SMALSI_Audio.zip',
                                                            '8f6c0a4c35b09239b7dc21228be7e0d7b692008d971a6f18e9cc2d579376a0fe')},
                  'documents': {   'Ordered Content Listing': [   'SMALSI '
                                                                  'Child Form '
                                                                  'Response '
                                                                  'Sheet',
                                                                  'SMALSI Teen '
                                                                  'Form '
                                                                  'Response '
                                                                  'Sheet',
                                                                  'SMALSI '
                                                                  'College '
                                                                  'Form '
                                                                  'Response '
                                                                  'Sheet',
                                                                  'SMALSI '
                                                                  'Spanish '
                                                                  'Child Form '
                                                                  'Response '
                                                                  'Sheet',
                                                                  'SMALSI '
                                                                  'Spanish '
                                                                  'Teen Form '
                                                                  'Response '
                                                                  'Sheet',
                                                                  'SMALSI '
                                                                  'Strategies '
                                                                  'Appendix B'],
                                   'SMALSI Child Form Response Sheet': (   'smalsi_child_response_sheet.pdf',
                                                                           'daf05e455685dc85306a2298dcd91f30cc3b10feeb5fd2ac31a2a711d68d765d'),
                                   'SMALSI College Form Response Sheet': (   'smalsi_college_response_sheet.pdf',
                                                                             '06b0398e3acd7781332528903b1e76bcad081fd5a26006805687d7d702548788'),
                                   'SMALSI Spanish Child Form Response Sheet': (   'smalsi_spanish_child_response_sheet.pdf',
                                                                                   '79202fca0c784b08777f61d5349319382068aed60b68aca505a4be7b31aca549'),
                                   'SMALSI Spanish Teen Form Response Sheet': (   'smalsi_spanish_teen_response_sheet.pdf',
                                                                                  '1cc4a53a284a1544aff85c5c468d5fb0c5ec1a27f46de320ea3f8a01df6c6180'),
                                   'SMALSI Strategies Appendix B': (   'smalsi_strategies_appendix-b.pdf',
                                                                       'bb27bf6129f2c52a71f3d71474b849ec6386ad52adacf2a38c9de96d35e24539'),
                                   'SMALSI Teen Form Response Sheet': (   'smalsi_teen_response_sheet.pdf',
                                                                          '251efe24d0855c86193762cddb84e8291dec418a5ad8a3fd7492e7d92e6682f0')},
                  'manuals': {   'SMALSI Manual': {   'smalsi_page1.jpg': '166dac040883dad3d11c7984b50259ec0345435bb219abd73adfeb9c436e659c',
                                                      'smalsi_page10.jpg': '1cfa01c2e20a5974d762e090f9b7df77cbf9796e71d2679f28c19ef3d5a44253',
                                                      'smalsi_page11.jpg': 'b75a0351a7a523863e3f38ac47708e5b60f6824cfad35d62aacebb7e28934d91',
                                                      'smalsi_page156.jpg': 'afe77e820cbaa6f0cbd90222a288dd9c71364722e6a8da6432921ae42c2453c6'},
                                 'SMALSI Strategies for Academic Success Handbook': {   'smalsi_page1.jpg': '1a38ea21ffa63f25f8273bfaecd47585fbbf9420f36a0b266f41f78cd8486f72',
                                                                                        'smalsi_page10.jpg': '12d5883973324c240b60e8b4786ea3f2355a42e44ef4d5720dc0f07217a2de32',
                                                                                        'smalsi_page11.jpg': 'fe27196162f940c0450b0709b997b09c831b1f018a09dd66f1b387aa0763046b',
                                                                                        'smalsi_page264.jpg': 'd5251f871abeaa4ba9d521996600c404bd3158c169a23bdeb9f000c806b18fff'}}},
    'spm': {   'documents': {   'Ordered Content Listing': [   'SPM Quick Tips '
                                                               'Record Form '
                                                               '(Fillable)',
                                                               'SPM Home Form',
                                                               'SPM Main '
                                                               'Classroom Form',
                                                               'SPM Art Class '
                                                               '(ART) Rating '
                                                               'Sheet',
                                                               'SPM Music '
                                                               'Class (MUS) '
                                                               'Rating Sheet',
                                                               'SPM Physical '
                                                               'Education '
                                                               'Class (PHY) '
                                                               'Rating Sheet',
                                                               'SPM '
                                                               'Recess/Playground '
                                                               '(REC) Rating '
                                                               'Sheet',
                                                               'SPM Cafeteria '
                                                               '(CAF) Rating '
                                                               'Sheet',
                                                               'SPM School Bus '
                                                               '(BUS) Rating '
                                                               'Sheet',
                                                               'SPM Spanish '
                                                               'Home Form',
                                                               'SPM Spanish '
                                                               'Main Classroom '
                                                               'Form',
                                                               'SPM Spanish '
                                                               'Art Class '
                                                               '(ART) Rating '
                                                               'Sheet',
                                                               'SPM Spanish '
                                                               'Music Class '
                                                               '(MUS) Rating '
                                                               'Sheet',
                                                               'SPM Spanish '
                                                               'Physical '
                                                               'Education '
                                                               'Class (PHY) '
                                                               'Rating Sheet',
                                                               'SPM Spanish '
                                                               'Recess/Playground '
                                                               '(REC) Rating '
                                                               'Sheet',
                                                               'SPM Spanish '
                                                               'Cafeteria '
                                                               '(CAF) Rating '
                                                               'Sheet',
                                                               'SPM Spanish '
                                                               'School Bus '
                                                               '(BUS) Rating '
                                                               'Sheet'],
                                'SPM Art Class (ART) Rating Sheet': (   'spm_art_response_sheet.pdf',
                                                                        '7231534576d10116b17517f567c1aacdc3c347ffc56c7cf2548b374615aed349'),
                                'SPM Cafeteria (CAF) Rating Sheet': (   'spm_cafeteria_response_sheet.pdf',
                                                                        '338a960a0602c6f8e1a0221d28c8d1607ab9890306cde580a35731d9c4ecafea'),
                                'SPM Home Form': (   'spm_response_sheet_home.pdf',
                                                     '2b08fbbfd54d486b311cb559776d1a5e56dc9aed12edfd23321d29a812706d28'),
                                'SPM Main Classroom Form': (   'spm_response_sheet_class.pdf',
                                                               '7d6229b42cd11ef98887b9ca69a5addcc29dac6d893e956cfd0bec9dec3cf1d3'),
                                'SPM Music Class (MUS) Rating Sheet': (   'spm_music_response_sheet.pdf',
                                                                          '54a283a828ca2a8eb42d7905fc0cd3f5a05fb509956206285ee712c0dd6485c3'),
                                'SPM Physical Education Class (PHY) Rating Sheet': (   'spm_pe_response_sheet.pdf',
                                                                                       '501c95072f8bd6e459bf6601348e03fad187fd82e904559afdaf36238c73c05e'),
                                'SPM Quick Tips Record Form (Fillable)': (   'spm-spmp-qt-recordform.pdf',
                                                                             'a48a6f6f62696be1c81004eec31e79125b5524e43e3b38ead689fc753bfe71a0'),
                                'SPM Recess/Playground (REC) Rating Sheet': (   'spm_recess_response_sheet.pdf',
                                                                                '958559198a47c3e9078c90ae91f739ade626314d2d770a93bc127b5ecb5c242a'),
                                'SPM School Bus (BUS) Rating Sheet': (   'spm_bus_response_sheet.pdf',
                                                                         '30d1335e6a497717a5d60cdc4a5d45568dfa4984a8d2993ed1fc5995648835c5'),
                                'SPM Spanish Art Class (ART) Rating Sheet': (   'spm_sp_art_response_sheet.pdf',
                                                                                'd2be2c0b44ddab91fc681f8cae101685ee6e470303f6c9c6d50c5f3303dae0b2'),
                                'SPM Spanish Cafeteria (CAF) Rating Sheet': (   'spm_sp_cafeteria_response_sheet.pdf',
                                                                                '5dd6c2c4458c8856adb88b3e19b40487706bac27b087de21621ca71bcebe6c55'),
                                'SPM Spanish Home Form': (   'spm_sp_response_sheet_home.pdf',
                                                             '64ed5d3d1c794252974019941712adaabb54eba560d6872e890b9e5667d9cc01'),
                                'SPM Spanish Main Classroom Form': (   'spm_sp_response_sheet_class.pdf',
                                                                       'a797ebfbdd1a9e3a9fbacdfb5807ff8af55e9fcdcc66a019e2ea2397d503f7f9'),
                                'SPM Spanish Music Class (MUS) Rating Sheet': (   'spm_sp_music_response_sheet.pdf',
                                                                                  '1e89fb1dce473d12914911b9fd55fd0d6ac13697424ab5be5d3e0647ccd425a0'),
                                'SPM Spanish Physical Education Class (PHY) Rating Sheet': (   'spm_sp_pe_response_sheet.pdf',
                                                                                               '6b1d3800c8926070ea4b5e06c67181135c0339163a85a8fe15e342f3547d8bd3'),
                                'SPM Spanish Recess/Playground (REC) Rating Sheet': (   'spm_sp_recess_response_sheet.pdf',
                                                                                        '12b7050adedc4c93d1fca86468f38dcb6294a0107fa349629fb63bff9296310c'),
                                'SPM Spanish School Bus (BUS) Rating Sheet': (   'spm_sp_bus_response_sheet.pdf',
                                                                                 'be77c5984fcd7528dbf90030429852c77a14c427566314465e17cd7d4f344d6b')},
               'manuals': {   'SPM Manual': {   'spm_page1.jpg': 'd8c12401b94bac359e42b5409a3472ed17606d21f4531e772023a48fa24425fb',
                                                'spm_page10.jpg': '0e073f690bc0e5396cd8ddec5cc80adc34f5698f3faa3ee0bf99ad66f3cd0f44',
                                                'spm_page108.jpg': '932a2db7b99833cbd32ec663c881bdcc038d47ee549ff226baa677075336907f',
                                                'spm_page11.jpg': 'f40b700983a4a4bd5b27415d385b19b8079bede69a03ad5878223e8e87424e70'},
                              'SPM Quick Tips User Guide': {   'spm_page1.jpg': 'c75e23dd995b6852e7ff9545d5fce0d11894a28c697cbf8e90eb3c8aeaa14bc0',
                                                               'spm_page11.jpg': 'c591fb6bfbddbb03d64dfaf4b07fa2c81c16c0a8e24964831a9332a37470f97b',
                                                               'spm_page50.jpg': '02759b23ebdea6e2a4ebbde48aa49f17248746025f9d0af5c59d0f0e1fe3fdf9'}}},
    'spm2': {   'documents': {   'Ordered Content Listing': [   'SPM-2 Quick '
                                                                'Tips Record '
                                                                'Form '
                                                                '(Fillable)',
                                                                'SPM-2 Form '
                                                                'Comparison '
                                                                'Worksheet',
                                                                'SPM-2 Infant '
                                                                'Form',
                                                                'SPM-2 Toddler '
                                                                'Form',
                                                                'SPM-2 '
                                                                'Infant/Toddler '
                                                                'Caregiver '
                                                                'Self-Report '
                                                                'Form',
                                                                'SPM-2 '
                                                                'Preschool '
                                                                'Home Form',
                                                                'SPM-2 '
                                                                'Preschool '
                                                                'School Form',
                                                                'SPM-2 Child '
                                                                'Home Form',
                                                                'SPM-2 Child '
                                                                'School Form',
                                                                'SPM-2 Child '
                                                                'School '
                                                                'Environment - '
                                                                'Art (ART) '
                                                                'Form',
                                                                'SPM-2 Child '
                                                                'School '
                                                                'Environment - '
                                                                'School Bus '
                                                                '(BUS) Form',
                                                                'SPM-2 Child '
                                                                'School '
                                                                'Environment - '
                                                                'Cafeteria '
                                                                '(CAF) Form',
                                                                'SPM-2 Child '
                                                                'School '
                                                                'Environment - '
                                                                'Music (MUS) '
                                                                'Form',
                                                                'SPM-2 Child '
                                                                'School '
                                                                'Environment - '
                                                                'Physical '
                                                                'Education '
                                                                '(PHY) Form',
                                                                'SPM-2 Child '
                                                                'School '
                                                                'Environment - '
                                                                'Recess/Playground '
                                                                '(REC) Form',
                                                                'SPM-2 '
                                                                'Adolescent '
                                                                'Home Form',
                                                                'SPM-2 '
                                                                'Adolescent '
                                                                'School Form',
                                                                'SPM-2 '
                                                                'Adolescent '
                                                                'Self-Report '
                                                                'Form',
                                                                'SPM-2 '
                                                                'Adolescent '
                                                                'Driving '
                                                                'Environment - '
                                                                'Self-Report '
                                                                'Form',
                                                                'SPM-2 '
                                                                'Adolescent '
                                                                'Driving '
                                                                'Environment - '
                                                                'Rater Report '
                                                                'Form',
                                                                'SPM-2 Adult '
                                                                'Self-Report '
                                                                'Form',
                                                                'SPM-2 Adult '
                                                                'Rater Report '
                                                                'Form',
                                                                'SPM-2 Adult '
                                                                'Driving '
                                                                'Environment - '
                                                                'Self-Report '
                                                                'Form',
                                                                'SPM-2 Adult '
                                                                'Driving '
                                                                'Environment - '
                                                                'Rater Report '
                                                                'Form',
                                                                'SPM-2 Spanish '
                                                                'Infant Form',
                                                                'SPM-2 Spanish '
                                                                'Toddler Form',
                                                                'SPM-2 Spanish '
                                                                'Infant/Toddler '
                                                                'Caregiver '
                                                                'Self-Report '
                                                                'Form',
                                                                'SPM-2 Spanish '
                                                                'Preschool '
                                                                'Home Form',
                                                                'SPM-2 Spanish '
                                                                'Preschool '
                                                                'School Form',
                                                                'SPM-2 Spanish '
                                                                'Child Home '
                                                                'Form',
                                                                'SPM-2 Spanish '
                                                                'Child School '
                                                                'Form',
                                                                'SPM-2 Spanish '
                                                                'Child School '
                                                                'Environment - '
                                                                'Art (ART) '
                                                                'Form',
                                                                'SPM-2 Spanish '
                                                                'Child School '
                                                                'Environment - '
                                                                'School Bus '
                                                                '(BUS) Form',
                                                                'SPM-2 Spanish '
                                                                'Child School '
                                                                'Environment - '
                                                                'Cafeteria '
                                                                '(CAF) Form',
                                                                'SPM-2 Spanish '
                                                                'Child School '
                                                                'Environment - '
                                                                'Music (MUS) '
                                                                'Form',
                                                                'SPM-2 Spanish '
                                                                'Child School '
                                                                'Environment - '
                                                                'Physical '
                                                                'Education '
                                                                '(PHY) Form',
                                                                'SPM-2 Spanish '
                                                                'Child School '
                                                                'Environment - '
                                                                'Recess/Playground '
                                                                '(REC) Form',
                                                                'SPM-2 Spanish '
                                                                'Adolescent '
                                                                'Home Form',
                                                                'SPM-2 Spanish '
                                                                'Adolescent '
                                                                'School Form',
                                                                'SPM-2 Spanish '
                                                                'Adolescent '
                                                                'Self-Report '
                                                                'Form',
                                                                'SPM-2 Spanish '
                                                                'Adolescent '
                                                                'Driving '
                                                                'Environment - '
                                                                'Self-Report '
                                                                'Form',
                                                                'SPM-2 Spanish '
                                                                'Adolescent '
                                                                'Driving '
                                                                'Environment - '
                                                                'Rater Report '
                                                                'Form',
                                                                'SPM-2 Spanish '
                                                                'Adult '
                                                                'Self-Report '
                                                                'Form',
                                                                'SPM-2 Spanish '
                                                                'Adult Rater '
                                                                'Report Form',
                                                                'SPM-2 Spanish '
                                                                'Adult Driving '
                                                                'Environment - '
                                                                'Self-Report '
                                                                'Form',
                                                                'SPM-2 Spanish '
                                                                'Adult Driving '
                                                                'Environment - '
                                                                'Rater Report '
                                                                'Form'],
                                 'SPM-2 Adolescent Driving Environment - Rater Report Form': (   'spm2-adolescent_driving_rater_response_sheet.pdf',
                                                                                                 '5e5f79ef8cfc3fd24e86ab62be8e77a84a3e9bcff9eba50ee7bc18960be0ac34'),
                                 'SPM-2 Adolescent Driving Environment - Self-Report Form': (   'spm2-adolescent_driving_self-report_response_sheet.pdf',
                                                                                                '4d2ee471494168700a5044721333584df41ba05375fd999aa87eb50c5b3a651c'),
                                 'SPM-2 Adolescent Home Form': (   'spm2-adolescent_home_response_sheet.pdf',
                                                                   'eaf995c2ffb118772f0ebf6cb51fea1a654c1329b8264690c4cca0b42e355b87'),
                                 'SPM-2 Adolescent School Form': (   'spm2-adolescent_school_response_sheet.pdf',
                                                                     '4f3a9e553bd25b3f7140c1735607bd66d7224bf7701f91c5c8f080eb1df0a9a2'),
                                 'SPM-2 Adolescent Self-Report Form': (   'spm2-adolescent_self-report_response_sheet.pdf',
                                                                          '6779595dc1dcbf0a0ef7b1121cae46d47ed4df3cca8a1372253edb2aafc79173'),
                                 'SPM-2 Adult Driving Environment - Rater Report Form': (   'spm2-adult_driving_rater_response_sheet.pdf',
                                                                                            '26befbcceae1f70af3b614b095d6b7456f784d08cb8af3a336589bf86bf702fc'),
                                 'SPM-2 Adult Driving Environment - Self-Report Form': (   'spm2-adult_driving_self-report_response_sheet.pdf',
                                                                                           '9c54a87aa5a63d269f9509ba3ac452349eaae974b3e471c625f37019a0664e39'),
                                 'SPM-2 Adult Rater Report Form': (   'spm2-adult_rater_response_sheet.pdf',
                                                                      '66cae6e9b9f45a78d3449415783ee1d6880c520e670257d6bd8b61072f6d1bd7'),
                                 'SPM-2 Adult Self-Report Form': (   'spm2-adult_self-report_response_sheet.pdf',
                                                                     'd813310efc7d5ce9ed1f1860085442eb8b9a763b07d6fa7c3e78f0e0914ea815'),
                                 'SPM-2 Child Home Form': (   'spm2-child_home_response_sheet.pdf',
                                                              '5250e2d764e2e6a9e5296b3abe7aff705dc9a204dac431d6b381b59067d14d58'),
                                 'SPM-2 Child School Environment - Art (ART) Form': (   'spm2-art_response_sheet.pdf',
                                                                                        '6ae03107293dfb5879825008fa2f81169780e51f47bb86f2b57b6272f879cf04'),
                                 'SPM-2 Child School Environment - Cafeteria (CAF) Form': (   'spm2-cafeteria_response_sheet.pdf',
                                                                                              '0fe885e40a6a7c378307081585fb859fd9b1f08277e8c4b7f203a71edcb406b2'),
                                 'SPM-2 Child School Environment - Music (MUS) Form': (   'spm2-music_response_sheet.pdf',
                                                                                          '5bc80f86dd4496648690f20939644395dbff416ea7e842237ef7933c052f4810'),
                                 'SPM-2 Child School Environment - Physical Education (PHY) Form': (   'spm2-phy_response_sheet.pdf',
                                                                                                       '8260fa788bcdf22de982a32c433b6f9192eb8b4bb8563dd2a75361e40f001420'),
                                 'SPM-2 Child School Environment - Recess/Playground (REC) Form': (   'spm2-recess_response_sheet.pdf',
                                                                                                      '485d14a2f1d4eaa46d49ffe9933e38c1124f3ff16301c02945dfa02d337cc7c5'),
                                 'SPM-2 Child School Environment - School Bus (BUS) Form': (   'spm2-bus_response_sheet.pdf',
                                                                                               '430f1124830949115df5ed425353bfe52e69fe4423e21d414a38b0e151111e3f'),
                                 'SPM-2 Child School Form': (   'spm2-child_school_response_sheet.pdf',
                                                                '9a537b8228e64163b3d19aa8e5167b29a9abed60e45e9ffcae9cab83e64ebbd8'),
                                 'SPM-2 Form Comparison Worksheet': (   'spm2-form_comparison_worksheet.pdf',
                                                                        '888579ae45fdd59fb3d07ba4e8fae956deb218ae7754030994d7c0d8eb2e7ec8'),
                                 'SPM-2 Infant Form': (   'spm2-infant_form_response_sheet.pdf',
                                                          '820d052875e13b7dfcbc32636496bf41bd5551b2cc8a2ecf8075394af8739a84'),
                                 'SPM-2 Infant/Toddler Caregiver Self-Report Form': (   'spm2-caregiver_response_sheet.pdf',
                                                                                        'a61e7895b6d68b18965ab58e01d3ea7ab4c7b1ef0e7c18d286b4eca61720168e'),
                                 'SPM-2 Preschool Home Form': (   'spm2-preschool_home_response_sheet.pdf',
                                                                  '4b42c481a31231b6b02c5234a99733bd6ab300285e30079f7fb0659d8d2047f3'),
                                 'SPM-2 Preschool School Form': (   'spm2-preschool_school_response_sheet.pdf',
                                                                    '4125a98636525a209238da16a265c4ecc2eb4f3715611fbcbd430d246fa47570'),
                                 'SPM-2 Quick Tips Record Form (Fillable)': (   'spm2-quick_tips_record_form_fillable.pdf',
                                                                                'c838bb25862eab37a809ac23bcf004f89bfe91541c433e9244a3863a6a38d961'),
                                 'SPM-2 Spanish Adolescent Driving Environment - Rater Report Form': (   'spm2-sp-adolescent_driving_rater_response_sheet.pdf',
                                                                                                         '3dd611870b8f4a9b8be9dd084c815832ea606c49cb1da0fa6fda0db498f84332'),
                                 'SPM-2 Spanish Adolescent Driving Environment - Self-Report Form': (   'spm2-sp-adolescent_driving_self-report_response_sheet.pdf',
                                                                                                        '565fbcf8dfb6bec80113deed8479c9e5a73e24ea7cb5fee015626f9d8a7e50d3'),
                                 'SPM-2 Spanish Adolescent Home Form': (   'spm2-sp-adolescent_home_response_sheet.pdf',
                                                                           '079b7bcbd596c554c5f87f8ad8f920b9c9c4a7f796676fb5b7b0ec52a530627e'),
                                 'SPM-2 Spanish Adolescent School Form': (   'spm2-sp-adolescent_school_response_sheet.pdf',
                                                                             'e62892b9363c73053f79541ee02eae6d5c8f871140119393cde76f46817bc4ff'),
                                 'SPM-2 Spanish Adolescent Self-Report Form': (   'spm2-sp-adolescent_self-report_response_sheet.pdf',
                                                                                  '6d2bbf88e13e2493e969e8da74757cfe3286809d259531859e7f1141e22d177c'),
                                 'SPM-2 Spanish Adult Driving Environment - Rater Report Form': (   'spm2-sp-adult_driving_rater_response_sheet.pdf',
                                                                                                    '7b7293390a4a58e2dc70c9fa802321eebbc9590a51635d4267c92b0d3e952174'),
                                 'SPM-2 Spanish Adult Driving Environment - Self-Report Form': (   'spm2-sp-adult_driving_self-report_response_sheet.pdf',
                                                                                                   '140254b15e27486933b9febf2807bd01a5d4d2b80f7926c594a825d6736fb501'),
                                 'SPM-2 Spanish Adult Rater Report Form': (   'spm2-sp-adult_rater_response_sheet.pdf',
                                                                              '1eeb24423cee63b3e2eb884ebd1c47a9784dab7be52f5f198b49c765d535b1db'),
                                 'SPM-2 Spanish Adult Self-Report Form': (   'spm2-sp-adult_self-report_response_sheet.pdf',
                                                                             '0f3de4fdc77d753a26b3f0c868e06b056f83fcd97442db16f0489f4e9ed3d866'),
                                 'SPM-2 Spanish Child Home Form': (   'spm2-sp-child_home_response_sheet.pdf',
                                                                      'f7e2b4197e1307ed3322c93f83a633182c48adfaf2023d9e0b760bd44905c5b3'),
                                 'SPM-2 Spanish Child School Environment - Art (ART) Form': (   'spm2-sp-art_response_sheet.pdf',
                                                                                                '2bead14fb7f5487d03bae4f7328763b29a5791ed8500e3515872f8ec754655f9'),
                                 'SPM-2 Spanish Child School Environment - Cafeteria (CAF) Form': (   'spm2-sp-cafeteria_response_sheet.pdf',
                                                                                                      'd4465afa33ddb239e88bcfdd7defddc42b89ba06ab3a5592ce4d9c9a01f2228c'),
                                 'SPM-2 Spanish Child School Environment - Music (MUS) Form': (   'spm2-sp-music_response_sheet.pdf',
                                                                                                  '149ac148a3ca891f0511a3a95f6c716a03e272baf57693aa5f5492a9d825647d'),
                                 'SPM-2 Spanish Child School Environment - Physical Education (PHY) Form': (   'spm2-sp-phy_response_sheet.pdf',
                                                                                                               '5c6983ec09368ad5bb3e5306ec2a42331a2d5456f2dc29eb8a9e7b880bf832af'),
                                 'SPM-2 Spanish Child School Environment - Recess/Playground (REC) Form': (   'spm2-sp-recess_response_sheet.pdf',
                                                                                                              'fc6cd641dcb4838fbac1a9abb3c53352bd976a2b786bdadd58d45d1932eb9fa9'),
                                 'SPM-2 Spanish Child School Environment - School Bus (BUS) Form': (   'spm2-sp-bus_response_sheet.pdf',
                                                                                                       '4db34c82d75b792bdc668517f1a561e1dc2068b587edb14023bde7c310e9507c'),
                                 'SPM-2 Spanish Child School Form': (   'spm2-sp-child_school_response_sheet.pdf',
                                                                        'cf7fbbe36b603c9e7d3da6aabf2f423f301690a1577f0813e2fca57d4c2c6c1e'),
                                 'SPM-2 Spanish Infant Form': (   'spm2-sp-infant_form_response_sheet.pdf',
                                                                  '2afb37569ad7adc55833d5462edef36db6e17c8506261505511eb13c1c1712d9'),
                                 'SPM-2 Spanish Infant/Toddler Caregiver Self-Report Form': (   'spm2-sp-caregiver_response_sheet.pdf',
                                                                                                'ef82b9bae31a48e9c506ceadbaf97dfa985691956702b325d6895d25d321fca1'),
                                 'SPM-2 Spanish Preschool Home Form': (   'spm2-sp-preschool_home_response_sheet.pdf',
                                                                          'a6d4da0edd25b956e143d3dd2104d6b883606736284e703c3a85ff48d2e0a80d'),
                                 'SPM-2 Spanish Preschool School Form': (   'spm2-sp-preschool_school_response_sheet.pdf',
                                                                            '09ac7a95c35a4e8fb3a6f0caf9bfafe5c5dddc81a7290cd08d46225e618254ef'),
                                 'SPM-2 Spanish Toddler Form': (   'spm2-sp-toddler_form_response_sheet.pdf',
                                                                   'abb8cc93574ad0f30e4610e876172a3c8c475d719e126e809fc8f7a90330a401'),
                                 'SPM-2 Toddler Form': (   'spm2-toddler_form_response_sheet.pdf',
                                                           '6e1c28f441276deeb38f857c6f7704c7e59fe73bd6db3042fdd5376795964208')},
                'manuals': {   'SPM-2 Child Quick Tips User Guide': {   'spm2_page1.jpg': '39118a7914189a5515100831ea8e72e712d85ceafe7832402477bec64c6e8433',
                                                                        'spm2_page11.jpg': '2105d9cf1356c10825538b072f20285c70134ca584dcf2cd732339a9ea734f2d',
                                                                        'spm2_page60.jpg': '96281157fb6ebc2181d92f2e6894068698f81bd8fe1b4e9b7957ff3510042160'},
                               'SPM-2 Manual': {   'spm2_page1.jpg': '903f7c6508a0582232e4cb635384b269b862a59eda570bca37b962e461ac197e',
                                                   'spm2_page10.jpg': 'ec6ca4c8a65ce40058c230569a4b27489437b77ec8b426da5bf569fe60b7786b',
                                                   'spm2_page11.jpg': '2b577bf2fb2ae5031b5574aec07cb2a895aba0b8afacd8d4c54d31390e5afacb',
                                                   'spm2_page220.jpg': '0dbeccc8820a84fcb5d01aa0057a7bfa5304687c4485462cfa6d417b5e324853'},
                               'SPM-2 Preschool Quick Tips User Guide': {   'spm2_page1.jpg': '38a3465920b8512d2fee39f696ba7b553c5fbf2d06d37fa051fdaa18f88248bb',
                                                                            'spm2_page11.jpg': 'fe318f7bd7140cb39ec43a7d0e49bab15f057dfa1c9569698e8b6931f8212f17',
                                                                            'spm2_page62.jpg': '9c514c1c759000be5a08ed92bed03f611aadd6335f26d210fc3995e31b728d0a'}}},
    'spmp': {   'documents': {   'Ordered Content Listing': [   'SPM-P Quick '
                                                                'Tips Record '
                                                                'Form '
                                                                '(Fillable)',
                                                                'SPM-P Home '
                                                                'Form',
                                                                'SPM-P School '
                                                                'Form',
                                                                'SPM-P Spanish '
                                                                'Home Form',
                                                                'SPM-P Spanish '
                                                                'School Form'],
                                 'SPM-P Home Form': (   'spm-p_response_sheet_home.pdf',
                                                        'fe37c3e509b089eb68b4e18341ba88e7c004caa1d1a05d698330d435d772f35c'),
                                 'SPM-P Quick Tips Record Form (Fillable)': (   'spm-spmp-qt-recordform.pdf',
                                                                                'a48a6f6f62696be1c81004eec31e79125b5524e43e3b38ead689fc753bfe71a0'),
                                 'SPM-P School Form': (   'spm-p_response_sheet_school.pdf',
                                                          '8d02c433f2d72df178b17ffc751368f324e0ca298841cf27948aede0488c4e93'),
                                 'SPM-P Spanish Home Form': (   'spm-p_sp_response_sheet_home.pdf',
                                                                '8443598333f2981ca1315d89ef8cd877600d3191ce19da9b53ce0a2e0afba999'),
                                 'SPM-P Spanish School Form': (   'spm-p_sp_response_sheet_school.pdf',
                                                                  '730bce4a3da13ef9ac77c33d24b04d5fe56a3ee80da57196d985189593a82f06')},
                'manuals': {   'SPM-P Manual': {   'spmp_page1.jpg': 'b053d4ff5f3c491e71de18a0cbf65bac1f32c37f3dd734b5ab597dc43fbfbb8e',
                                                   'spmp_page10.jpg': '31a5b990748473c625b6c73a20ba44b5e89d6d99abd432daa0df86ef1c8ad0eb',
                                                   'spmp_page11.jpg': '300f830ff4b564618270c50fa4c2411e1cc4983e45cf4f3a201abc34826902aa',
                                                   'spmp_page98.jpg': '0dc9ea8695c7410f4248caea9268707fd58f30894bc4b04071e82852dc652a10'},
                               'SPM-P Quick Tips User Guide': {   'spmp_page1.jpg': 'c75e23dd995b6852e7ff9545d5fce0d11894a28c697cbf8e90eb3c8aeaa14bc0',
                                                                  'spmp_page11.jpg': 'c591fb6bfbddbb03d64dfaf4b07fa2c81c16c0a8e24964831a9332a37470f97b',
                                                                  'spmp_page50.jpg': '02759b23ebdea6e2a4ebbde48aa49f17248746025f9d0af5c59d0f0e1fe3fdf9'}}},
    'srs2': {   'documents': {   'Adult (Relative/Other Report) Form Response Sheet': (   'adult_other_form_response_sheet.pdf',
                                                                                          '923d88aa13c98bece444fad925746a33a86fc7a100b9b496012b394000f0f26d'),
                                 'Adult (Self-Report) Form Response Sheet': (   'adult_self_form_response_sheet.pdf',
                                                                                '28e4ed4acb840b1bd7f15ccd03a9cd3be65186a1cd106d13d9d8fc6b1e02821e'),
                                 'Ordered Content Listing': [   'School-Age '
                                                                'Form Response '
                                                                'Sheet',
                                                                'Preschool '
                                                                'Form Response '
                                                                'Sheet',
                                                                'Adult '
                                                                '(Relative/Other '
                                                                'Report) Form '
                                                                'Response '
                                                                'Sheet',
                                                                'Adult '
                                                                '(Self-Report) '
                                                                'Form Response '
                                                                'Sheet',
                                                                'Spanish '
                                                                'School-Age '
                                                                'Form Response '
                                                                'Sheet',
                                                                'Spanish '
                                                                'Preschool '
                                                                'Form Response '
                                                                'Sheet',
                                                                'Spanish Adult '
                                                                '(Relative/Other '
                                                                'Report) Form '
                                                                'Response '
                                                                'Sheet',
                                                                'Spanish Adult '
                                                                '(Self-Report) '
                                                                'Form Response '
                                                                'Sheet'],
                                 'Preschool Form Response Sheet': (   'preschool_form_response_sheet.pdf',
                                                                      'f2583c14b48403bc9ae5b5e58dd47e66e0464a57f7c60f51666202f7aa22d050'),
                                 'School-Age Form Response Sheet': (   'school_form_response_sheet.pdf',
                                                                       'a3100304aa8826f6244bc7d25e077df3540ca40efc6b57b633fe94b2e86809d2'),
                                 'Spanish Adult (Relative/Other Report) Form Response Sheet': (   'adult_sp_other_form_response_sheet.pdf',
                                                                                                  '1277d0b5d40ee192763087c13ad6e820095ce480e96cb99a9110009aca3f276a'),
                                 'Spanish Adult (Self-Report) Form Response Sheet': (   'adult_sp_self_form_response_sheet.pdf',
                                                                                        '7ff25bb949bff0a98257101d4c314362a0e8de6f0b27dd7c965f41034ee243cf'),
                                 'Spanish Preschool Form Response Sheet': (   'preschool_sp_form_response_sheet.pdf',
                                                                              '09457a52762359757daae0331c3c967f6b636444298523d71fcd2fe32ea9bec4'),
                                 'Spanish School-Age Form Response Sheet': (   'school_sp_form_response_sheet.pdf',
                                                                               'bfa050ab9a7058f6f138cec8363891879e58810f17712170abea23d8f92a1788')},
                'manuals': {   'SRS™-2 Manual': {   'srs2_page1.jpg': '14f0b80c842f386d7f0d899bf249f6acd3b52fbffaeaf1da44c0a4526dc2bf95',
                                                    'srs2_page10.jpg': 'f1196a1ced1c566d8f9caccbdd0d97605cc39751dc697725d2df0b1e77134623',
                                                    'srs2_page11.jpg': '1bfaa6356c000660e1744fc672dcecf5198715272e88a2ddeb88a652a4f03693',
                                                    'srs2_page122.jpg': '3c63053da4bc8667bf57331a46037f2ac6c435a3909b66408cf318bb445fca48'}}}}
                                                    
def runTestModule(kwargs):
# def runTestModule(env="uat", headless=False, randomResponse=False, directory=None, logToFile=False, logName=None, uploadToS3=False, username=None, password=None):
# def runTestModule(env="uat", headless=False, randomResponse=False, directory=None, input=None, logToFile=False, waitTime=None):
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
            
        try:
            randomResponse = kwargs.pop('random')
        except:
            randomResponse = None

        if logToFile:
            logging.warning("Setting up logfile at " + os.path.join(str(outputDirectory), str(logNameStamped)+'.log'))
            loggingSetup(output=os.path.join(str(outputDirectory), str(logNameStamped)+'.log'))
        else:
            loggingSetup()
            
        logger = logging.getLogger(str(logNameStamped))
        
        logger.info("Specified output directory is: " + str(outputDirectory))
        runTest(env=env, headless=headless, username=username, password=password, directory=str(outputDirectory), logName=logger)
        
        # if logToFile:
            # with open(os.path.join(os.path.join(str(directory), str(logName)), str(logName + (time.strftime("_%F_%T", time.gmtime())).replace(":", "-") + ".txt")), 'w', encoding='utf-8') as f:
                # with redirect_stdout(f), redirect_stderr(f):
                    # # runTest(env=env, headless=headless, randomResponse=randomResponse, directory=str(os.path.join(str(directory), str(logName))), input=input, waitTime=waitTime)
                    # loggingPrint("Specified output directory is: " + str(directory))
                    # runTest(env=env, headless=headless, randomResponse=randomResponse, directory=os.path.join(str(directory), str(logName)))
        # else:
            # loggingPrint("Specified output directory is: " + str(directory))
            # runTest(env=env, headless=headless, randomResponse=randomResponse, directory=os.path.join(str(directory), str(logName)))
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

def runTest(env="uat", headless=False, username=None, password=None, directory=None, logName=None):
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
        
        Prac = oesPractitioner(loginUrl, username=username, password=password, logName=logName)
        logger = Prac.logger
        Prac.headless = headless
        if directory is None:
            Prac.download_dir = str(os.getcwd())
        else:
            Prac.download_dir = str(directory)
        
        Prac.setUp()
        Prac.login()
        
        # manualAssessments = ['ppascale']
        # easelAssessments = ['ppascale']
        # documentsAssessments = []
        # audioAssessments = []
        
        manualAssessments = ['owlsii', 'spm2', 'opus', 'dp3', 'casl2', 'ppascale', 'abas3', 'spm', 'spmp', 'srs2', 'smalsi', 'scq', 'arizona4', 'rcmas2', 'dbc2', 'piersharris3', 'rise', 'caps', 'dp4', 'adir', 'ados2', 'cars2', 'goal', 'migdas2']
        easelAssessments = ['owlsii', 'casl2', 'ppascale', 'opus', 'arizona4']
        documentsAssessments = ['opus', 'spm2', 'dp3', 'abas3', 'spm', 'spmp', 'srs2', 'smalsi', 'casl2', 'scq', 'arizona4', 'rcmas2', 'dbc2', 'piersharris3', 'rise', 'caps', 'dp4']
        audioAssessments = ['opus', 'rcmas2', 'smalsi']
        # These are just for record-keeping right now, they're not actually used in automation currently
        # videoAssessments = ['caps', 'ados2']
        # unreleasedAssessments = []
        
        manualsEasels = (manualAssessments + list(set(easelAssessments) - set(manualAssessments)))
        documentsAudio = (documentsAssessments + list(set(audioAssessments) - set(documentsAssessments)))
        allAssessments = (manualsEasels + list(set(documentsAudio) - set(manualsEasels)))
        
        for assessment in allAssessments:
            assessmentDir = os.path.join(str(Prac.download_dir), str(assessment))
            
            try:
                logger.info("Creating directory for assessment files...")
                os.mkdir(assessmentDir)
            except:
                logger.info("Assessment directory already exists, just using that...")

            try:
                if assessment in manualAssessments:
                    logger.info("Beginning manuals check for assessment " + str(assessment) + "...")
                    checkManualHashes(assessment, False, Prac)
            except:
                logger.exception("Manuals regression failed for " + str(assessment) + "!!!")
            
            try:
                if assessment in easelAssessments:
                    logger.info("Beginning easels check for assessment " + str(assessment) + "...")
                    checkManualHashes(assessment, True, Prac)
            except:
                logger.exception("Easels regression failed for " + str(assessment) + "!!!")
            
            try:
                if assessment in documentsAssessments:
                    logger.info("Beginning documents check for assessment " + str(assessment) + "...")
                    checkDocumentHashes(assessment, False, Prac)
            except:
                logger.exception("Documents regression failed for " + str(assessment) + "!!!")
                
            try:
                if assessment in audioAssessments:
                    logger.info("Beginning audio files check for assessment " + str(assessment) + "...")
                    checkDocumentHashes(assessment, True, Prac)
            except:
                logger.exception("Audio files regression failed for " + str(assessment) + "!!!")
        
        for assessment in allAssessments:
            assessmentDir = os.path.join(str(Prac.download_dir), str(assessment))
            files = glob.glob(assessmentDir + '/**', recursive=True)

            # The way the file search works, it will always include the parent directory, so an empty directory will include the 1 path
            if len(files)>1:
                logger.warning("Assessment " + str(assessment) + " encountered errors, leaving files for investigation!!!")
                logger.warning(files)
            else:
                logger.info("Assessment " + str(assessment) + " did not encounter errors")
                try:
                    # loggingPrint("Cleaning up...")
                    os.rmdir(assessmentDir)
                except:
                    logger.exception("Error encountered attempting to clean up assessment!!!")
            
    except:
        try:
            logger.exception("Regression failed!!!")
        except:
            logging.exception("Regression failed!!!")
        Prac.browser.save_screenshot(os.path.join(str(Prac.download_dir), "regression_failed" + (time.strftime("_%F_%T", time.gmtime())).replace(":", "-") + ".png"))
    finally:
        Prac.logout()
        Prac.tearDown()
    
def checkDocumentHashes(assessment='dp3', audio=False, Prac=None):
    if Prac is None or Prac == '':
        logging.error("No oesPractitioner object provided!!!")
        raise
    
    logger = Prac.logger
    
    if assessment is None or assessment == '':
        assessment = 'dp3'
    else:
        assessment = str(assessment).lower().replace(' ','').replace('&#160;', '').replace('-','')
    
    if audio:
        Prac.navigateToAssessmentTab(assessmentType=assessment, tab='audio')
    else:
        Prac.navigateToAssessmentTab(assessmentType=assessment, tab='documents')
    
    assessmentDir = os.path.join(str(Prac.download_dir), str(assessment))
    
    documentsEntryXPath = "//*[contains(@class, 'List')]//tr[contains(@class, 'Row')]"
    
    if audio:
        assessmentDocuments = fileHashes[assessment]['audio']
    else:
        assessmentDocuments = fileHashes[assessment]['documents']
    
    # we're waiting to make sure the page is properly loaded with the documents
    if assessmentDocuments is not None and assessmentDocuments != {}:
        if audio:
            logger.info("Verifying that audio has loaded...")
        else:
            logger.info("Verifying that documents have loaded...")
        documents = WebDriverWait(Prac.browser, 20).until(EC.presence_of_element_located((By.XPATH, documentsEntryXPath)))
        
        if audio:
            logger.info("Audio has loaded successfully")
        else:
            logger.info("Documents have loaded successfully")
    
    documents = Prac.browser.find_elements(By.XPATH, documentsEntryXPath + "//*[contains(@class, 'Title')]")
    documentsOrder = []
    
    try:
        expectedOrder = assessmentDocuments.pop('Ordered Content Listing')
    except:
        pass

    if audio:
        logger.info("Beginning audio verification")
    else:
        logger.info("Beginning document verification")
    
    errorsFound = False
    if len(documents) == len(assessmentDocuments):
        for document in documents:
            newfile = None
            try:
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
                        logger.exception("Error parsing document title!")
                        print(documentTitle)
                        raise

                documentFile = WebDriverWait(Prac.browser, 20).until(EC.presence_of_element_located((By.XPATH, xpathStr)))
                logger.info("Attempting to download '" + str(documentTitle) + "'...")
            
                filesBeforeDownload = [filename for filename in glob.glob(os.path.join(str(Prac.download_dir), '*.*')) if not filename.endswith('crdownload') and not filename.endswith('tmp') and not filename.endswith('part')]
                start = time.time()
                elapsed = 0
                Prac.browser.execute_script("arguments[0].click();", documentFile)
                logger.info("Confirming successful file download...")
                
                historicalSize = -1

                while elapsed < 45:
                    filesAfterDownload = [filename for filename in glob.glob(os.path.join(str(Prac.download_dir), '*.*')) if not filename.endswith('crdownload') and not filename.endswith('tmp') and not filename.endswith('part')]
                    done = time.time()
                    elapsed = done - start
                    filesAfterDownload = [filename for filename in glob.glob(os.path.join(str(Prac.download_dir), '*.*')) if not filename.endswith('crdownload') and not filename.endswith('tmp') and not filename.endswith('part')]
                    newfile = list(set(filesAfterDownload).difference(filesBeforeDownload))
                    if len(newfile):
                        if historicalSize != os.path.getsize(newfile[0]) and os.path.getsize(newfile[0]) > 0:
                            logger.info("Waiting for download to complete...")
                            historicalSize = os.path.getsize(newfile[0])
                            # May need to force this sleep but I don't think so
                            # time.sleep(1)
                        else:
                            downloadSuccess = True
                            file = newfile[0]
                            filesBeforeDownload = None
                            if Prac.headless:
                                # This is dumb and I hate this, but there's a lag between Python messing with files and the OS updating
                                # So without waiting for them to sync, it throws everything off and you can end up with weird empty files
                                # This delay becomes a problem really only when running headless for some reason, need to fix at some point
                                time.sleep(2)
                            break
                    else:
                        downloadSuccess = False
                
                if downloadSuccess and os.path.basename(newfile[0])==assessmentDocuments[documentTitle][0]:
                    logger.info("Download successful, verifying file hash...")
                    with open(newfile[0], "rb") as f:
                        data = f.read()
                        downloadHash = hashlib.sha256(data).hexdigest()
                    
                    if downloadHash == assessmentDocuments[documentTitle][1]:
                        logger.info("Filehash matches as expected")
                        # loggingPrint("Expected: " + assessmentDocuments[documentTitle][1])
                        # loggingPrint("Received: " + str(downloadHash))
                        try:
                            logger.info("Attempting to cleanup file...")
                            # loggingPrint("Filepath: " + newfile[0])
                            if os.path.exists(newfile[0]):
                                logger.info("Deleting file...")
                                os.remove(newfile[0])
                                # try:
                                    # os.remove(newfile[0])
                                    # loggingPrint("HIT FALLBACK DELETE!!!")
                                    # if Prac.headless:
                                        # time.sleep(1)
                                # except:
                                    # pass
                        except:
                            logger.exception("Failed to delete document!!!")
                    else:
                        logger.error("Filehash DOES NOT MATCH!!! Please verify file has not been updated!")
                        logger.error("Expected: " + assessmentDocuments[documentTitle][1])
                        logger.error("Received: " + str(downloadHash))
                        # loggingPrint("Filepath: " + newfile[0])
                        Prac.browser.execute_script("arguments[0].scrollIntoView();", document)
                        prevStyle = document.get_attribute('style')
                        Prac.browser.execute_script("arguments[0].setAttribute('style', 'background: yellow; border: 2px solid red;');", document)
                        WebDriverWait(Prac.browser, 5).until(EC.presence_of_element_located((By.XPATH, documentsEntryXPath + "//*[@class='documentTitle' and text()='" + documentTitle + "']"+"[@style='background: yellow; border: 2px solid red;']")))
                        Prac.browser.save_screenshot(os.path.join(str(Prac.download_dir), "incorrect_document_hash_" + str(assessment) + "_" + downloadHash + (time.strftime("_%F_%T", time.gmtime())).replace(":", "-") + ".png"))
                        Prac.browser.execute_script("arguments[0].setAttribute('style', '" + prevStyle + "');", document)
                        WebDriverWait(Prac.browser, 5).until(EC.presence_of_element_located((By.XPATH, documentsEntryXPath + "//*[@class='documentTitle' and text()='" + documentTitle + "']"+"[@style='" + prevStyle + "']")))
                        os.rename(newfile[0], os.path.join(str(assessmentDir), os.path.basename(newfile[0])))
                        raise
                else:
                    if str(os.path.basename(os.path.normpath(newfile[0])))!=assessmentDocuments[documentTitle][0]:
                        logger.error("Downloaded filename was unexpected!!!")
                        logger.error("Expected: " + assessmentDocuments[documentTitle][0])
                        logger.error("Received: " + str(os.path.basename(os.path.normpath(newfile[0]))))
                        # loggingPrint("Filepath: " + newfile[0])
                    else:
                        logger.error("Download failed!!!")
                        
                    Prac.browser.execute_script("arguments[0].scrollIntoView();", document)
                    prevStyle = document.get_attribute('style')
                    Prac.browser.execute_script("arguments[0].setAttribute('style', 'background: yellow; border: 2px solid red;');", document)
                    WebDriverWait(Prac.browser, 5).until(EC.presence_of_element_located((By.XPATH, documentsEntryXPath + "//*[@class='documentTitle' and text()='" + documentTitle + "']"+"[@style='background: yellow; border: 2px solid red;']")))
                    Prac.browser.save_screenshot(os.path.join(str(Prac.download_dir), "incorrect_document_download_" + str(assessment) + "_" + downloadHash + (time.strftime("_%F_%T", time.gmtime())).replace(":", "-") + ".png"))
                    Prac.browser.execute_script("arguments[0].setAttribute('style', '" + prevStyle + "');", document)
                    WebDriverWait(Prac.browser, 5).until(EC.presence_of_element_located((By.XPATH, documentsEntryXPath + "//*[@class='documentTitle' and text()='" + documentTitle + "']"+"[@style='" + prevStyle + "']")))
                    os.rename(newfile[0], os.path.join(str(assessmentDir), os.path.basename(newfile[0])))
                    raise
            except:
                if audio:
                    logging.exception("Error checking for audio files!!!")
                    Prac.browser.save_screenshot(os.path.join(str(assessmentDir), "audio_error_" + str(assessment) + "_" + downloadHash + (time.strftime("_%F_%T", time.gmtime())).replace(":", "-") + ".png"))
                else:
                    logging.exception("Error checking for documents!!!")
                    Prac.browser.save_screenshot(os.path.join(str(assessmentDir), "document_error_" + str(assessment) + "_" + downloadHash + (time.strftime("_%F_%T", time.gmtime())).replace(":", "-") + ".png"))
                errorsFound = True
                
        logger.info("Checking displayed order of content...")
        if documentsOrder != expectedOrder:
            errorsFound = True
            logger.error("Content display order is incorrect!!!")
            logger.error("Expected: " + str(expectedOrder))
            logger.error("Received: " + str(documentsOrder))
        else:
            logger.info("Content displayed in correct order")
        
        if errorsFound:
            if audio:
                logger.error("Errors found while checking for audio files!!!")
            else:
                logger.error("Errors found while checking for documents!!!")
            raise
    else:
        if len(documents) > len(assessmentDocuments):
            if audio:
                logger.error("More audio files listed than expected!!!\n Found: " + str(len(documents)) + "\n Exepected: " + str(len(assessmentDocuments)))
            else:
                logger.error("More documents listed than expected!!!\n Found: " + str(len(documents)) + "\n Exepected: " + str(len(assessmentDocuments)))
        else:
            if audio:
                logger.error("Less audio files listed than expected!!!\n Found: " + str(len(documents)) + "\n Exepected: " + str(len(assessmentDocuments)))
            else:
                logger.error("Less documents listed than expected!!!\n Found: " + str(len(documents)) + "\n Exepected: " + str(len(assessmentDocuments)))
        
        raise
    
    if audio:
        logger.info("All files matched as expected, audio files check completed")
    else:
        logger.info("All files matched as expected, documents check completed")
    
def checkManualHashes(assessment='dp3', easels=False, Prac=None):
    if Prac is None or Prac == '':
        logger.error("No oesPractitioner object provided!!!")
        raise

    logger = Prac.logger

    errorsFound = False
    assessmentDir = os.path.join(str(Prac.download_dir), str(assessment))
                
    try:
        logger.info("Creating assessment directory...")
        os.mkdir(assessmentDir)
    except:
        logger.warning("Directory already exists, just using that...")
        
    
    if easels:
        Prac.navigateToAssessmentEasels(assessmentType=assessment)
    else:
        Prac.navigateToAssessmentManuals(assessmentType=assessment)
    
    manualsEntryXPath = "//*//input[contains(@class, 'redButn') and not(contains(@class, 'Resend'))]"
    
    if easels:
        assessmentManuals = fileHashes[assessment]['easels']
    else:
        assessmentManuals = fileHashes[assessment]['manuals']
    
    manuals = []

    # we're waiting to make sure the page is properly loaded with the manuals
    if assessmentManuals is not None and assessmentManuals != {}:
        if easels:
            logger.info("Verifying that easels have loaded...")
        else:
            logger.info("Verifying that manuals have loaded...")
        try:
            manuals = WebDriverWait(Prac.browser, 20).until(EC.presence_of_element_located((By.XPATH, manualsEntryXPath)))
            if easels:
                logger.info("Easels have loaded successfully")
            else:
                logger.info("Manuals have loaded successfully")
                
            manuals = Prac.browser.find_elements(By.XPATH, manualsEntryXPath)
    
            if easels:
                logger.info("Beginning easels verification")
            else:
                logger.info("Beginning manuals verification")
            
        except:
            if easels:
                logger.error("Easels did not load in time! Refreshing and trying one more time...")
            else:
                logger.error("Manuals did not load in time! Refreshing and trying one more time...")

            try:
                Prac.browser.refresh()
                manuals = WebDriverWait(Prac.browser, 20).until(EC.presence_of_element_located((By.XPATH, manualsEntryXPath)))
            except:
                errorsFound = True
                if easels:
                    logger.exception("Easels failed to load successfully!!!")
                else:
                    logger.exception("Manuals failed to load successfully!!!")
                
                if easels:
                    Prac.browser.save_screenshot(os.path.join(str(assessmentDir), "easels_load_error_" + str(assessment) + (time.strftime("_%F_%T", time.gmtime())).replace(":", "-") + ".png"))
                else:
                    Prac.browser.save_screenshot(os.path.join(str(assessmentDir), "manuals_load_error_" + str(assessment) + (time.strftime("_%F_%T", time.gmtime())).replace(":", "-") + ".png"))
    
    
    
    if len(manuals)>0 and str(len(manuals)) == str(len(assessmentManuals)):
        for manual in manuals:
            manualName = "Undetermined"
            try:
                manualName = str(manual.get_attribute('onclick')).split("'")[3]
                manualName = manualName.replace(":", " - ")

                if easels:
                    logger.info("Checking easel '" + str(manualName) + "'")
                else:
                    logger.info("Checking manual '" + str(manualName) + "'")
                
                try:
                    if easels:
                        logger.info("Creating easel directory...")
                    else:
                        logger.info("Creating manual directory...")
                    os.mkdir(os.path.join(assessmentDir, manualName.replace("/", "-").replace("\\", "-")))
                except:
                    logger.warning("Directory already exists, just using that...")
                
                with wait_for_new_window(Prac.browser):
                    Prac.browser.execute_script("arguments[0].click();", manual)
                
                Prac.switchToNewWindow()
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
                logger.info("Page loaded, beginning download...")
                
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
                # Should probably shove a bunch of the code from here on on downloading and checking into functions
                # But...do that later, just needs to work right now
                if rightPageImage is not None and rightPageImage != '':
                    pageImage = requests.get(rightPageImage, cookies=cookies, stream=True, allow_redirects=True)
                    filePath = os.path.join(assessmentDir, str(manualName.replace("/", "-").replace("\\", "-")), assessment+'_'+rightPageImage.rsplit('/', 1)[-1])
                    with open(filePath, 'wb') as f:
                        f.write(pageImage.content)
                        
                    if os.path.basename(filePath) in assessmentManuals[manualName].keys():
                        logger.info("Download of '" + os.path.basename(filePath) + "' successful, verifying file hash...")
                        with open(filePath, "rb") as f:
                            data = f.read()
                            downloadHash = hashlib.sha256(data).hexdigest()
                        
                        if downloadHash == assessmentManuals[manualName][os.path.basename(filePath)]:
                            logger.info("Filehash matches as expected")
                            try:
                                if os.path.exists(filePath):
                                    os.remove(filePath)
                            except:
                                logger.exception("Failed to delete file!!!")
                        else:
                            logger.error("Filehash DOES NOT MATCH!!! Please verify file has not been updated!")
                            logger.error("Expected: " + assessmentManuals[manualName][os.path.basename(filePath)])
                            logger.error("Received: " + str(downloadHash))
                            Prac.browser.save_screenshot(os.path.join(str(assessmentDir), "incorrect_document_" + str(assessment) + "_" + downloadHash + (time.strftime("_%F_%T", time.gmtime())).replace(":", "-") + ".png"))
                    
                if leftPageImage is not None and leftPageImage != '':
                    pageImage = requests.get(leftPageImage, cookies=cookies, stream=True, allow_redirects=True)
                    filePath = os.path.join(assessmentDir, str(manualName.replace("/", "-").replace("\\", "-")), assessment+'_'+leftPageImage.rsplit('/', 1)[-1])
                    with open(filePath, 'wb') as f:
                        f.write(pageImage.content)
                    
                    if os.path.basename(filePath) in assessmentManuals[manualName].keys():
                        logger.info("Download of '" + os.path.basename(filePath) + "' successful, verifying file hash...")
                        with open(filePath, "rb") as f:
                            data = f.read()
                            downloadHash = hashlib.sha256(data).hexdigest()
                        
                        if downloadHash == assessmentManuals[manualName][os.path.basename(filePath)]:
                            logger.info("Filehash matches as expected")
                            try:
                                if os.path.exists(filePath):
                                    os.remove(filePath)
                            except:
                                logger.exception("Failed to delete file!!!")
                        else:
                            logger.error("Filehash DOES NOT MATCH!!! Please verify file has not been updated!")
                            logger.error("Expected: " + assessmentManuals[manualName][os.path.basename(filePath)])
                            logger.error("Received: " + str(downloadHash))
                            Prac.browser.save_screenshot(os.path.join(str(assessmentDir), "incorrect_document_" + str(assessment) + "_" + downloadHash + (time.strftime("_%F_%T", time.gmtime())).replace(":", "-") + ".png"))
                
                logger.info("Navigating to last page...")
                Prac.browser.execute_script("arguments[0].click();", lastPage)
                if doublePage:
                    #loaded = WebDriverWait(Prac.browser, 20).until(AnyEc(EC.visibility_of_element_located((By.XPATH, "//*//img[@id='rightpage']")), EC.visibility_of_element_located((By.XPATH, "//*//img[@id='leftpage']"))))
                    try:
                        loaded = WebDriverWait(Prac.browser, 20).until(AnyEc(wait_for_not_attribute_value((By.XPATH, "//*//img[@id='rightpage']"), 'src', ''), wait_for_not_attribute_value((By.XPATH, "//*//img[@id='leftpage']"), 'src', '')))
                    except:
                        logger.exception("Page didn't load in time, trying again...")
                        loaded = WebDriverWait(Prac.browser, 20).until(AnyEc(wait_for_not_attribute_value((By.XPATH, "//*//img[@id='rightpage']"), 'src', ''), wait_for_not_attribute_value((By.XPATH, "//*//img[@id='leftpage']"), 'src', '')))
                else:
                    # Single-page manuals sometimes get the src attribute cleared as above; just do a quick navigate to fix
                    # loggingPrint("Prev Page Nav...")
                    Prac.browser.execute_script("arguments[0].click();", prevPage)
                    loaded = WebDriverWait(Prac.browser, 20).until(AnyEc(wait_for_not_attribute_value((By.XPATH, "//*//img[@id='rightpage']"), 'src', ''), wait_for_not_attribute_value((By.XPATH, "//*//img[@id='leftpage']"), 'src', '')))
                    leftPageImage = leftPage.get_attribute('src')
                    rightPageImage = rightPage.get_attribute('src')
                    # loggingPrint("Next Page Nav...")
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
                
                logger.info("Page loaded, beginning download...")
                
                if rightPageImage is not None and rightPageImage != '':
                    pageImage = requests.get(rightPageImage, cookies=cookies, stream=True, allow_redirects=True)
                    filePath = os.path.join(assessmentDir, str(manualName.replace("/", "-").replace("\\", "-")), assessment+'_'+rightPageImage.rsplit('/', 1)[-1])
                    with open(filePath, 'wb') as f:
                        f.write(pageImage.content)
                        
                    if os.path.basename(filePath) in assessmentManuals[manualName].keys():
                        logger.info("Download of '" + os.path.basename(filePath) + "' successful, verifying file hash...")
                        with open(filePath, "rb") as f:
                            data = f.read()
                            downloadHash = hashlib.sha256(data).hexdigest()
                        
                        if downloadHash == assessmentManuals[manualName][os.path.basename(filePath)]:
                            logger.info("Filehash matches as expected")
                            try:
                                if os.path.exists(filePath):
                                    os.remove(filePath)
                            except:
                                logger.exception("Failed to delete file!!!")
                        else:
                            logger.error("Filehash DOES NOT MATCH!!! Please verify file has not been updated!")
                            logger.error("Expected: " + assessmentManuals[manualName][os.path.basename(filePath)])
                            logger.error("Received: " + str(downloadHash))
                            Prac.browser.save_screenshot(os.path.join(str(assessmentDir), "incorrect_document_" + str(assessment) + "_" + downloadHash + (time.strftime("_%F_%T", time.gmtime())).replace(":", "-") + ".png"))
                    
                if leftPageImage is not None and leftPageImage != '':
                    pageImage = requests.get(leftPageImage, cookies=cookies, stream=True, allow_redirects=True)
                    filePath = os.path.join(assessmentDir, str(manualName.replace("/", "-").replace("\\", "-")), assessment+'_'+leftPageImage.rsplit('/', 1)[-1])
                    with open(filePath, 'wb') as f:
                        f.write(pageImage.content)
                    
                    if os.path.basename(filePath) in assessmentManuals[manualName].keys():
                        logger.info("Download of '" + os.path.basename(filePath) + "' successful, verifying file hash...")
                        with open(filePath, "rb") as f:
                            data = f.read()
                            downloadHash = hashlib.sha256(data).hexdigest()
                        
                        if downloadHash == assessmentManuals[manualName][os.path.basename(filePath)]:
                            logger.info("Filehash matches as expected")
                            try:
                                if os.path.exists(filePath):
                                    os.remove(filePath)
                            except:
                                logger.exception("Failed to delete file!!!")
                        else:
                            logger.error("Filehash DOES NOT MATCH!!! Please verify file has not been updated!")
                            logger.error("Expected: " + assessmentManuals[manualName][os.path.basename(filePath)])
                            logger.error("Received: " + str(downloadHash))
                            Prac.browser.save_screenshot(os.path.join(str(assessmentDir), "incorrect_document_" + str(assessment) + "_" + downloadHash + (time.strftime("_%F_%T", time.gmtime())).replace(":", "-") + ".png"))
                
                logger.info("Jumping to page 11")
                currPage.send_keys('11')
                currPage.send_keys(Keys.ENTER)
                if doublePage:
                    #loaded = WebDriverWait(Prac.browser, 20).until(AnyEc(EC.visibility_of_element_located((By.XPATH, "//*//img[@id='rightpage']")), EC.visibility_of_element_located((By.XPATH, "//*//img[@id='leftpage']"))))
                    loaded = WebDriverWait(Prac.browser, 20).until(AnyEc(wait_for_not_attribute_value((By.XPATH, "//*//img[@id='rightpage']"), 'src', ''), wait_for_not_attribute_value((By.XPATH, "//*//img[@id='leftpage']"), 'src', '')))
                else:
                    # Single-page manuals sometimes get the src attribute cleared as above; just do a quick navigate to fix
                    # loggingPrint("Prev Page Nav...")
                    Prac.browser.execute_script("arguments[0].click();", prevPage)
                    loaded = WebDriverWait(Prac.browser, 20).until(AnyEc(wait_for_not_attribute_value((By.XPATH, "//*//img[@id='rightpage']"), 'src', ''), wait_for_not_attribute_value((By.XPATH, "//*//img[@id='leftpage']"), 'src', '')))
                    leftPageImage = leftPage.get_attribute('src')
                    rightPageImage = rightPage.get_attribute('src')
                    # loggingPrint("Next Page Nav...")
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
                
                logger.info("Page loaded, beginning download...")
                
                if rightPageImage is not None and rightPageImage != '':
                    pageImage = requests.get(rightPageImage, cookies=cookies, stream=True, allow_redirects=True)
                    filePath = os.path.join(assessmentDir, str(manualName.replace("/", "-").replace("\\", "-")), assessment+'_'+rightPageImage.rsplit('/', 1)[-1])
                    with open(filePath, 'wb') as f:
                        f.write(pageImage.content)
                        
                    if os.path.basename(filePath) in assessmentManuals[manualName].keys():
                        logger.info("Download of '" + os.path.basename(filePath) + "' successful, verifying file hash...")
                        with open(filePath, "rb") as f:
                            data = f.read()
                            downloadHash = hashlib.sha256(data).hexdigest()
                        
                        if downloadHash == assessmentManuals[manualName][os.path.basename(filePath)]:
                            logger.info("Filehash matches as expected")
                            try:
                                if os.path.exists(filePath):
                                    os.remove(filePath)
                            except:
                                logger.exception("Failed to delete file!!!")
                        else:
                            logger.error("Filehash DOES NOT MATCH!!! Please verify file has not been updated!")
                            logger.error("Expected: " + assessmentManuals[manualName][os.path.basename(filePath)])
                            logger.error("Received: " + str(downloadHash))
                            Prac.browser.save_screenshot(os.path.join(str(assessmentDir), "incorrect_document_" + str(assessment) + "_" + downloadHash + (time.strftime("_%F_%T", time.gmtime())).replace(":", "-") + ".png"))
                    
                if leftPageImage is not None and leftPageImage != '':
                    pageImage = requests.get(leftPageImage, cookies=cookies, stream=True, allow_redirects=True)
                    filePath = os.path.join(assessmentDir, str(manualName.replace("/", "-").replace("\\", "-")), assessment+'_'+leftPageImage.rsplit('/', 1)[-1])
                    with open(filePath, 'wb') as f:
                        f.write(pageImage.content)
                    
                    if os.path.basename(filePath) in assessmentManuals[manualName].keys():
                        logger.info("Download of '" + os.path.basename(filePath) + "' successful, verifying file hash...")
                        with open(filePath, "rb") as f:
                            data = f.read()
                            downloadHash = hashlib.sha256(data).hexdigest()
                        
                        if downloadHash == assessmentManuals[manualName][os.path.basename(filePath)]:
                            logger.info("Filehash matches as expected")
                            try:
                                if os.path.exists(filePath):
                                    os.remove(filePath)
                            except:
                                logger.exception("Failed to delete file!!!")
                        else:
                            logger.error("Filehash DOES NOT MATCH!!! Please verify file has not been updated!")
                            Prac.browser.save_screenshot(os.path.join(str(assessmentDir), "incorrect_document_" + str(assessment) + "_" + downloadHash + (time.strftime("_%F_%T", time.gmtime())).replace(":", "-") + ".png"))
                
                logger.info("Navigating to first page...")
                Prac.browser.execute_script("arguments[0].click();", firstPage)
                if doublePage:
                    #loaded = WebDriverWait(Prac.browser, 20).until(AnyEc(EC.visibility_of_element_located((By.XPATH, "//*//img[@id='rightpage']")), EC.visibility_of_element_located((By.XPATH, "//*//img[@id='leftpage']"))))
                    loaded = WebDriverWait(Prac.browser, 20).until(AnyEc(wait_for_not_attribute_value((By.XPATH, "//*//img[@id='rightpage']"), 'src', ''), wait_for_not_attribute_value((By.XPATH, "//*//img[@id='leftpage']"), 'src', '')))
                else:
                    # Single-page manuals sometimes get the src attribute cleared as above; just do a quick navigate to fix
                    # loggingPrint("Next Page Nav...")
                    Prac.browser.execute_script("arguments[0].click();", nextPage)
                    loaded = WebDriverWait(Prac.browser, 20).until(AnyEc(wait_for_not_attribute_value((By.XPATH, "//*//img[@id='rightpage']"), 'src', ''), wait_for_not_attribute_value((By.XPATH, "//*//img[@id='leftpage']"), 'src', '')))
                    leftPageImage = leftPage.get_attribute('src')
                    rightPageImage = rightPage.get_attribute('src')
                    # loggingPrint("Prev Page Nav...")
                    Prac.browser.execute_script("arguments[0].click();", prevPage)
                
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
                
                logger.info("Page loaded, beginning download...")
                
                if rightPageImage is not None and rightPageImage != '':
                    pageImage = requests.get(rightPageImage, cookies=cookies, stream=True, allow_redirects=True)
                    filePath = os.path.join(assessmentDir, str(manualName.replace("/", "-").replace("\\", "-")), assessment+'_'+rightPageImage.rsplit('/', 1)[-1])
                    with open(filePath, 'wb') as f:
                        f.write(pageImage.content)
                        
                    if os.path.basename(filePath) in assessmentManuals[manualName].keys():
                        logger.info("Download of '" + os.path.basename(filePath) + "' successful, verifying file hash...")
                        with open(filePath, "rb") as f:
                            data = f.read()
                            downloadHash = hashlib.sha256(data).hexdigest()
                        
                        if downloadHash == assessmentManuals[manualName][os.path.basename(filePath)]:
                            logger.info("Filehash matches as expected")
                            try:
                                if os.path.exists(filePath):
                                    os.remove(filePath)
                            except:
                                logger.exception("Failed to delete file!!!")
                        else:
                            logger.error("Filehash DOES NOT MATCH!!! Please verify file has not been updated!")
                            logger.error("Expected: " + assessmentManuals[manualName][os.path.basename(filePath)])
                            logger.error("Received: " + str(downloadHash))
                            Prac.browser.save_screenshot(os.path.join(str(assessmentDir), "incorrect_document_" + str(assessment) + "_" + downloadHash + (time.strftime("_%F_%T", time.gmtime())).replace(":", "-") + ".png"))
                    
                if leftPageImage is not None and leftPageImage != '':
                    pageImage = requests.get(leftPageImage, cookies=cookies, stream=True, allow_redirects=True)
                    filePath = os.path.join(assessmentDir, str(manualName.replace("/", "-").replace("\\", "-")), assessment+'_'+leftPageImage.rsplit('/', 1)[-1])
                    with open(filePath, 'wb') as f:
                        f.write(pageImage.content)
                    
                    if os.path.basename(filePath) in assessmentManuals[manualName].keys():
                        logger.info("Download of '" + os.path.basename(filePath) + "' successful, verifying file hash...")
                        with open(filePath, "rb") as f:
                            data = f.read()
                            downloadHash = hashlib.sha256(data).hexdigest()
                        
                        if downloadHash == assessmentManuals[manualName][os.path.basename(filePath)]:
                            logger.info("Filehash matches as expected")
                            try:
                                if os.path.exists(filePath):
                                    os.remove(filePath)
                            except:
                                logger.exception("Failed to delete file!!!")
                        else:
                            logger.error("Filehash DOES NOT MATCH!!! Please verify file has not been updated!")
                            logger.error("Expected: " + assessmentManuals[manualName][os.path.basename(filePath)])
                            logger.error("Received: " + str(downloadHash))
                            Prac.browser.save_screenshot(os.path.join(str(assessmentDir), "incorrect_document_" + str(assessment) + "_" + downloadHash + (time.strftime("_%F_%T", time.gmtime())).replace(":", "-") + ".png"))
               
            except:
                if easels:
                    try:
                        logger.exception("Failed to check easel '" + str(manualName) + "'!!!")
                    except:
                        logging.exception("Failed to check easel '" + str(manualName) + "'!!!")
                    Prac.browser.save_screenshot(os.path.join(str(assessmentDir), "easels_error_" + str(assessment) + "_" + downloadHash + (time.strftime("_%F_%T", time.gmtime())).replace(":", "-") + ".png"))
                else:
                    try:
                        logger.exception("Failed to check manual '" + str(manualName) + "'!!!")
                    except:
                        logging.exception("Failed to check manual '" + str(manualName) + "'!!!")
                    Prac.browser.save_screenshot(os.path.join(str(assessmentDir), "manuals_error_" + str(assessment) + "_" + downloadHash + (time.strftime("_%F_%T", time.gmtime())).replace(":", "-") + ".png"))
                errorsFound = True
                
            Prac.browser.close()
            Prac.switchToPractitioner()
            
            if len(os.listdir(os.path.join(assessmentDir, str(manualName.replace("/", "-").replace("\\", "-"))))) !=0:
                if easels:
                    logger.error("Easels check encountered errors, leaving files for investigation!!!")
                else:
                    logger.error("Manuals check encountered errors, leaving files for investigation!!!")
            else:
                if easels:
                    logger.info("Easels check did not encounter errors, cleaning up...")
                else:
                    logger.info("Manuals check did not encounter errors, cleaning up...")
                try:
                    os.rmdir(os.path.join(assessmentDir, str(manualName.replace("/", "-").replace("\\", "-"))))
                except:
                    logging.exception("Error encountered attempting to clean up!!!")

    else:
        errorsFound = True
        if len(manuals) > len(assessmentManuals):
            if easels:
                logger.error("More easels listed than expected!!!\n Found: " + str(len(manuals)) + "\n Exepected: " + str(len(assessmentManuals)))
            else:
                logger.error("More manuals listed than expected!!!\n Found: " + str(len(manuals)) + "\n Exepected: " + str(len(assessmentManuals)))
        else:
            if easels:
                logger.error("Less easels listed than expected!!!\n Found: " + str(len(manuals)) + "\n Exepected: " + str(len(assessmentManuals)))
            else:
                logger.error("Less manuals listed than expected!!!\n Found: " + str(len(manuals)) + "\n Exepected: " + str(len(assessmentManuals)))
        
        if easels:
            Prac.browser.save_screenshot(os.path.join(str(assessmentDir), "easels_number_error_" + str(assessment) + (time.strftime("_%F_%T", time.gmtime())).replace(":", "-") + ".png"))
        else:
            Prac.browser.save_screenshot(os.path.join(str(assessmentDir), "manuals_number_error_" + str(assessment) + (time.strftime("_%F_%T", time.gmtime())).replace(":", "-") + ".png"))
        

    if errorsFound:
        if easels:
            logger.error("Errors found while checking for easels!!!")
        else:
            logger.error("Errors found while checking for manuals!!!")
        raise

    if easels:
        logger.info("All files matched as expected, easels check completed")
    else:
        logger.info("All files matched as expected, manuals check completed")
                        
                            
if __name__ == "__main__":
    
    short_options = "he:d:lu"
    long_options = ["headless", "env=", "directory=", "log-to-file", "upload", "username=", "password="]
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

            #print (("Enabling special output mode (%s)") % (current_value))
    if directory is None or directory == 'None' or directory == '':
        directory = str(os.getcwd())
        
    testModuleArgs = {'env': env, 'headless': headless, 'directory': str(directory), 'logToFile': logToFile, 'uploadToS3': uploadToS3, 'username': username, 'password': password}
    
    if uploadToS3:
        logging.warning("S3 upload is currently enabled")
        # s3 = boto3.resource('s3', region_name='us-west-2')
        # bucket = s3.Bucket(uploadBucket)
        # bucket.put_object(Key=str("output/oes-1.0-automation/" + str(env) + "/" + os.path.basename(directory) + "/"))
    
    if logToFile:
        logging.warning("Logging to file is enabled; each test case will log to file and console")
    
    if headless:
        logging.warning("Headless mode is enabled; browser sessions will not be displayed!")
    
    runTestModule(testModuleArgs)
