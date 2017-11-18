import csv
import re
import datetime
import json
import sys
import argparse
from redmine import Redmine

parser = argparse.ArgumentParser(description='Process Toggl CsV')
parser.add_argument('file_name', action='store')
parser.add_argument('-dr', '--dry-run', action='store_true',
        help='Disables sending information to Redmine')
parser.add_argument('-v', '--verbose', action='store_true',
        help='Prints out information about what is being created or updated')

args = vars(parser.parse_args())
config = []
with open('config.json') as configFile:
    config = json.load(configFile)

def main():
    togglFile = args['file_name']

    for field in ['REDMINE_URL', 'REDMINE_KEY', 'USER_ID', 'ACTIVITY_ID']:
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
                description = description.replace(ticketNumber.group(0), '')

                if (tags):
                    description += ' [' + tags + ']'

                ticketNumber = ticketNumber.group(1)
                timeEntry = {
                    'issue_id': ticketNumber,
                    'spent_on': date,
                    'hours': convert_time(str(row[11])),
                    'comments': description,
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
            user_id=config['USER_ID'],
            activity_id=config['ACTIVITY_ID']):
        entriesList.append(entry)

    entriesList.sort(key=lambda entry: entry.id)

    for entry in entriesList:
        key = str(entry.issue) + entry.comments + str(entry.spent_on)
        existingEntries[key] = { 'hours': entry.hours, 'id': entry.id }

    for key in timeEntries:
        newEntry = timeEntries[key]

        if (key in existingEntries):
            if (str(existingEntries[key]['hours']) != str(newEntry['hours'])):
                if (args['verbose']):
                    print "Updating Entry: ", existingEntries[key]['id']
                    print "    issue_id: ", newEntry['issue_id']
                    print "    spent_on: ", newEntry['spent_on']
                    print "    hours: ", newEntry['hours']
                    print "    comments: ", newEntry['comments']
                    print "    ", existingEntries[key]['hours'], ' vs ', newEntry['hours']

                if (args['dry_run'] is False):
                    redmine.time_entry.update(
                            existingEntries[key]['id'],
                            issue_id=str(newEntry['issue_id']),
                            spent_on=newEntry['spent_on'],
                            hours=newEntry['hours'],
                            comments=newEntry['comments'],
                            activity_id=config['ACTIVITY_ID'])
        else:
            if (args['verbose']):
                print "Creating:"
                print "    issue_id: ", newEntry['issue_id']
                print "    spent_on: ", newEntry['spent_on']
                print "    hours: ", newEntry['hours']
                print "    comments: ", newEntry['comments']

            if (args['dry_run'] is False):
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

    return custom_rounding(round(hours, 2))

# Round to the nearest 6 minutes
def custom_rounding(hours):
    if config['ROUND']:
        customHours = round(hours / config['ROUND']) * config['ROUND']

        if (customHours > hours):
            return customHours

    return hours


main()
