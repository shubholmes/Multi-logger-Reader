Read data from 4 different dataloggers, resamples the data and plots the graph.

For example we monitor the temperature and relative humidity of structures e.g Dome Shaped Solar Dryer (dssd) and compare with the environment (ambient). Different types of loggers are usually used and they don't present their data in the same format(both extention and display)

We use:
EasyLog High Temperature, thermocouple logger (don't read relative humidity), Temtop and ST-172(read relative humidity)

Takes parameters like this:
analyze(files, Parameters, names, references=None, form='hourly', factor=1, save='untitled', graph=False, markers=True):

files is a list of file names without their extention. They are replicas. Their hourly or day and night averages are determined.

Parameters is a list containing 'temperature', 'relative humidity' or both. 
If EasyLog High Temperature and thermocouple logger are used, 'relative humidity' should not be included

names is a list of names for the average of files and averages of each list in references. The names must be in order of appearance

references(i should come up with a better name) is a list of list(s) to compare with the average of files.

form is the mode of analyses, either an hourly analyses or splitting data into day and night time.
form='hourly' for hourly analyses or
form='day_night' for day and night analyses

factor is the frquency of analyses e.g
factor=4 is every 4 hours or every 4 days and night

save is name to save result for table and graph

graph to plot graph of result or not

markers to use markers on plot or not

NB: All logger files must be in the same folder as the script


e.g
dssd = ['Dome Up', 'Dome Down']
ref = [['DMVent1', 'DMVent2'], ['DMVent3(Aspirator)', 'DMVent4(Aspirator)'], ['Ambient']]
param = ['temperature', 'relative humidity']
namez = ['dssd_in', 'dssd_vent', 'dssd_aspirator', 'ambient']

analyze(dssd, param, namez, ref, form='day_night', factor=1, save='DSSD', graph=True, markers=True)