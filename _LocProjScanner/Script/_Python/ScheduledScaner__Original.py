#!/usr/bin/env python
#coding=utf-8

__author__ = 'Tinyliu@wistronits.com, tinyliu@me.com'

import subprocess, re, simplejson, os, sys, time, datetime
reload(sys) 
sys.setdefaultencoding('utf-8')
sys.path.append(os.path.dirname(__file__))
from RadarArgs import RadarArgs
pyScript = os.path.dirname(__file__)

projectFolder = pyScript[:pyScript.find('Script/_Python')] + '_ScheduleProjects'

shScript = pyScript[:pyScript.find('_Python')] + '_sh'

FindScheduledTest = '%s/FindScheduledTest.sh'%shScript
GetScheduleTestDataCase = '%s/GetScheduleTestData.sh'%shScript

def creatLocDirs(locDirs):
	try:
		os.makedirs(locDirs)
	except:
		pass

def projectFrame(project):
	TestSuiteFolder = '%s/%s/_TestSuite'%(projectFolder, project)
	RequestBody = '%s/%s/_RequestBody'%(projectFolder, project)
	Logs = '%s/%s/_Logs'%(projectFolder, project)
	creatLocDirs(TestSuiteFolder)
	creatLocDirs(RequestBody)
	creatLocDirs(Logs)
	return TestSuiteFolder, RequestBody, Logs

def creatAsiaRequestBodyFiles(Folder, contents=list):
	fileList = []
	for n in range(len(contents)):
		requestBody = os.path.join(Folder, 'RequestBody_%s.txt'%n)
		open(requestBody, 'w').write(contents[n])
		fileList.append(requestBody)
	return fileList

def useAPI(command, requestBoday='', ScheduleID=''):
	response = subprocess.Popen('%s %s %s'%(command, requestBoday, ScheduleID), shell=True, stdout=subprocess.PIPE).stdout.read()
	if response.strip()[-1] == ']':
		try:
			json = re.findall('\[[\w\W]+\]', response)[-1]
		except:
			return []
	else:
		try:
			json = re.findall('\{[\w\W]+\}', response)[-1]
		except IndexError, e:
			print '%s\n%s'%(e, response)
			return
	return simplejson.loads(json)

def creatLocFilesbyID(ScheduledTest, targetFolder):
	TestSuite = os.path.join(targetFolder, str(ScheduledTest['suiteID']))
	if not os.path.isdir(TestSuite):
		os.mkdir(TestSuite)
		os.chdir(TestSuite)
	os.chdir(TestSuite)
	open(str(ScheduledTest['scheduledID']), 'w').write(simplejson.dumps(ScheduledTest))

def TestSuiteInfos(testSuiteFolder):
	ScheduleDetails = {}
	for file in os.listdir(testSuiteFolder):
		if file.isdigit():
			ScheduleContents = open(os.path.join(testSuiteFolder, file)).read()
			ScheduleDetails[file] = simplejson.loads(ScheduleContents)

def lastModifiedAt(advance=7):
	today = datetime.date.today()
	lastWeek = today - datetime.timedelta(days=advance)
	return lastWeek.isoformat()

times = 0
coveredProj = ['ARD', 'OSX', 'OSX Updates', 'Final Cut Pro', 'Compressor', 'Motion',
		'Pages', 'Numbers', 'Keynote', 'iWork', 'Spark', 'Server OSX', 'CPU', 'Logic',
		'iTunes Mac', 'iTunes Win', 'Aperture', 'iMovie', 'iBooks Author', 'iCloud CP Win', 'iPhoto',
		'ACUtil', 'MainStage', 'Safari Mac', 'iTunesProducer', 'QuickTime Mac', 'QuickTime Windows',
		'AirPort Mac', 'AirPort Win', 'Java'] # Loc:Proj:OSX Updates

while True:
	for proj in coveredProj:
		LocProj = 'Loc:Proj:%s'%proj
		RequestBodyComponents = {'component':[{'name':LocProj,'version':'CH'},
				{'name':LocProj,'version':"TA"},
				{'name':LocProj,'version':"KH"},
				{'name':LocProj,'version':"J"},
				{'name':LocProj,'version':"ID"},
				{'name':LocProj,'version':"VN"},
				{'name':LocProj,'version':"MY"}],
			'lastModifiedAt':{'gt':'2015-03-01T16:00:00'}}
		if times:
			RequestBodyComponents['lastModifiedAt']['gt'] = '%sT16:00:00'%lastModifiedAt()
		t, r, l = projectFrame(proj.replace(' ', '_'))
		b = creatAsiaRequestBodyFiles(r, [simplejson.dumps(RequestBodyComponents)])
		s = []
		for body in b:
			print '\n%s - %s ...'%(proj, os.path.basename(body))
			s += useAPI(FindScheduledTest, body)

		total = len(s)
		for unit in s:
			if total%10 == 0:
				time.sleep(5)
			scheduleFile = '%s/%s/%s'%(t, unit['suiteID'], unit['scheduledID'])
			print '\n%s left, processing %s/%s ...'%(total, unit['suiteID'], unit['scheduledID'])
			if os.path.isfile(scheduleFile):
				contents = open(scheduleFile).read()
				if '"status": "Complete"' not in contents:
					ScheduleCase = useAPI(GetScheduleTestDataCase, ScheduleID=unit['scheduledID'])
					try:
						unit["cases"] = ScheduleCase["cases"]
						creatLocFilesbyID(unit, t)
					except:
						print '\n\n## TimeOut.\n'
			else:
				ScheduleCase = useAPI(GetScheduleTestDataCase, ScheduleID=unit['scheduledID'])
				try:
					unit["cases"] = ScheduleCase["cases"]
				except:
					print ScheduleCase
				creatLocFilesbyID(unit, t)
			total -= 1
	times = 1
	print '\n%s\nFinished, process will restart after 15 minutes.\n'%time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
	sys.exit()
	time.sleep(900)

