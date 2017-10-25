import csv
import re
import datetime
import json
import sys
from redmine import Redmine

def main():
    if (len(sys.argv) < 2):
        print "run command: python main.py <csv_file>"
        exit()

    togglFile = sys.argv[1]

    config = []
    with open('config.json') as configFile:
        config = json.load(configFile)

    for field in ['REDMINE_URL', 'REDMINE_KEY', 'USER', 'ACTIVITY_ID']:
        if (field not in config):
            print "Config File is missing:", field
            exit()

    redmine = Redmine(config['REDMINE_URL'], key=config['REDMINE_KEY'])
    startDate = datetime.datetime.today() - datetime.timedelta((datetime.date.today().isoweekday() % 7) -1)
    endDate = startDate + datetime.timedelta(6)

    timeEntries = {}
    with open(togglFile, 'rb') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        next(csvfile)
        for row in reader:

            tags = row[12]
            description = row[5]
            date = row[7]

            entryDate = datetime.datetime.strptime(date, "%Y-%m-%d")

            if ( entryDate < startDate ):
                startDate = entryDate;
            elif ( entryDate > endDate ):
                endDate = entryDate;

            ticketNumber = re.match(r'\[(?:Task|Bug|Story) #(\d+)\]', description)
            if (ticketNumber):
                ticketNumber = ticketNumber.group(1)
                timeEntry = {
                    'issue_id': ticketNumber,
                    'spent_on': date,
                    'hours': convert_time(str(row[11])),
                    'comments': description + ' Tags: ' + tags,
                    'activity_id': 55
                }

                key = str(ticketNumber) + timeEntry['comments'] + str(date)

                if (key in timeEntries):
                    if (timeEntries[key]['comments'] == timeEntry['comments']):
                        timeEntry['hours'] = round(
                                timeEntry['hours'] + timeEntries[key]['hours'], 2)
                        timeEntries[key] = timeEntry
                else:
                    timeEntries[key] = timeEntry

    entriesList = []
    existingEntries = {}
    for entry in redmine.time_entry.filter(
            from_date=startDate.strftime('%Y-%m-%d'),
            to_date=endDate.strftime('%Y-%m-%d'),
            user_id=config['USER'],
            activity_id=55):
        entriesList.append(entry)

    entriesList.sort(key=lambda entry: entry.id)

    for entry in entriesList:
        key = str(entry.issue) + entry.comments + str(entry.spent_on)
        existingEntries[key] = { 'hours': entry.hours, 'id': entry.id }

    for key in timeEntries:
        newEntry = timeEntries[key]

        if (key in existingEntries):
            if (existingEntries[key]['hours'] != newEntry['hours']):
                print "Updating Entry: ", existingEntries[key]['id']
                print "    issue_id: ", newEntry['issue_id']
                print "    spent_on: ", newEntry['spent_on']
                print "    hours: ", newEntry['hours']
                print "    comments: ", newEntry['comments']
                print "    ", existingEntries[key]['hours'], ' vs ', newEntry['hours']

                if ('SEND_TO_REDMINE' not in config or config['SEND_TO_REDMINE']):
                    redmine.time_entry.update(
                            existingEntries[key]['id'],
                            issue_id=str(newEntry['issue_id']),
                            spent_on=newEntry['spent_on'],
                            hours=newEntry['hours'],
                            comments=newEntry['comments'],
                            activity_id=config['ACTIVITY_ID'])
        else:
            print "Creating:"
            print "    issue_id: ", newEntry['issue_id']
            print "    spent_on: ", newEntry['spent_on']
            print "    hours: ", newEntry['hours']
            print "    comments: ", newEntry['comments']

            if ('SEND_TO_REDMINE' not in config or config['SEND_TO_REDMINE']):
                redmine.time_entry.create(
                        issue_id=str(newEntry['issue_id']),
                        spent_on=newEntry['spent_on'],
                        hours=newEntry['hours'],
                        comments=newEntry['comments'],
                        activity_id=config['ACTIVITY_ID'])

def convert_time(time):
    b = datetime.datetime.strptime(time, "%H:%M:%S")
    c = datetime.timedelta(hours=b.hour, minutes=b.minute, seconds=b.second)
    hours = c.seconds / 3600.0

    return round(hours, 2)


main()
