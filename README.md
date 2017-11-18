# Toggl to Redmine
This script will convert Toggl time entries to Redmine time entries

## Requirements
* python-redmine 1.5.1

## Config
You will need:
* Redmine Url
* Redmine API Key
* Redmine User ID
* Redmine Activiy ID

Optional:
* Round -- A value you would like round by.

Copy the example file and fill in the necessary fields:
```
cp config.json.example config.json
```

## Running the program
**Note: The program expects the redmine ticket number at the beginning of the toggl
decription in the format `[Task #12345]`**

Example:
> [Task #12345] Worked on project xyz

To execute the program, run the command:
```
python main.py <csv_file>
```
where `csv_file` is the name of your Toggl csv download *with* extension

### Command Line Options
```
-v, --verbose Prints out information about the tasks being update or created
```
```
-dr, --dry-run Runs program without updating or creating tasks in Redmine
```

## Notes
* The program uses the Redmine ticket number, Toggl description, Toggl tags
and Toggl start date as a key
Example:
> 12345[Task #12345] Worked on project xyz Tags: Development2017-10-24
