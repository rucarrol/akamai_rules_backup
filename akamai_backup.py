#!/usr/local/bin/python

import argparse  
import requests  
import urlparse
import json
from akamai.edgegrid import EdgeGridAuth, EdgeRc  
import unicodedata

##
## get the JSON config from the PAPI endpoint
## 
def papi_get(edgerc_path, path):  
    edgerc = EdgeRc(edgerc_path)  
    section = 'default'  
  
    s = requests.Session()  
    s.auth = EdgeGridAuth.from_edgerc(edgerc, section)  
    baseurl = 'https://%s' % edgerc.get(section, 'host')  
    body = s.get(urlparse.urljoin(baseurl, path))
    if body.status_code > 200:
        print "Error, got HTTP status code %s" % body.status_code
        print body.content
        exit(1)
    if body.status_code == 200:
        return s.get(urlparse.urljoin(baseurl, path))  

##
## list groups at the PAPI end point.
##
def ls_groups(args):
    test = json.loads(papi_get(args.edgerc, '/papi/v0/groups/').content)
    groups = list()
    for i in test['groups']['items']:
        if 'contractIds' in i:
            if len(i['contractIds']) == 1:
                groups.append({"groupName" : i['groupName'],
                               "groupId" : i['groupId'],
                               "contractIds" : i['contractIds'][0]})
            elif len(i['contractIds']) == 2:
                groups.append({"groupName" : i['groupName'],
                               "groupId" : i['groupId'],
                               "contractIds" : i['contractIds'][0]})
                groups.append({"groupName" : i['groupName'],
                               "groupId" : i['groupId'],
                               "contractIds" : i['contractIds'][1]})
    ls_properties(groups)


##
## get the configuration in JSON format of the web property. Pass this to write_config to push to disk. 
##
def get_config(properties):
    for i in properties:
        if i['productionVersion'] is not None:
            test_string =  '/papi/v0/properties/%s/versions/%s/rules/?contractId=%s&groupId=%s' % (i['propertyId'], i['productionVersion'], i['contractId'], i['groupId'] )
            print "Found property %s" % i['propertyName']
            result = papi_get(args.edgerc, test_string )
            json_result = json.loads(result.content)

            write_config(json_result, i['propertyName'])

##
## List Akamai properties, pass result to get_config to return the JSON 
## 
def ls_properties(groups):
    properties = list()
    for i in groups:
        #print i
        #print "~" * 25
        result = papi_get(args.edgerc, '/papi/v0/properties/?contractId=%s&groupId=%s'
                          % (i['contractIds'], i['groupId']))

        if result.status_code == 200:
            test = json.loads(result.content)
            for j in test['properties']['items']:
                if j is not None:
                    properties.append(({"contractId" : j['contractId'],
                                        "groupId" : j['groupId'],
                                        "propertyId" : j['propertyId'],
                                        "productionVersion" : j['productionVersion'],
                                        "propertyName" : j['propertyName']}))
    get_config(properties)

##
## write json to disk. fail if IO error. 
##
def write_config(content, fname):

    outfile = "%s/%s.json" % (directory, fname )

    try:
       fh = open(outfile, "w")
       fh.writelines(json.dumps(content, indent=2))
       #fh.write(content)
    except IOError:
       print "Error: cant write to file %s, permissions issue?" % outfile
       exit(1)
    else:
       print "Wrote %s successfully" % outfile
       fh.close()

    return 0


##
## MAIN
##

help_text = "A script to fetch all property configs from Akamai's {OPEN} API and save them locally as json files. -h for help" 

parser = argparse.ArgumentParser(help_text)
subparsers = parser.add_subparsers()

parser.add_argument('--edgerc', default='.edgerc')
parser.add_argument('--directory',help='Output directory for JSON configs',action='store', default='.')

# groups listing
sp = subparsers.add_parser('backup')
sp.set_defaults(func=ls_groups)

args = parser.parse_args()
directory = args.directory

args.func(args)

