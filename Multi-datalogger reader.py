import numpy as np
import pandas as pd
from xlrd.biffh import XLRDError #For ST-172 logger Error
from functools import reduce
import math
import pathlib
import os
import matplotlib.pyplot as plt
import matplotlib.ticker as tic
plt.style.use('ggplot')


def read_files(files):
    global lst
    lst = []
    for file in files:
        if [file[-3], file[-1]] == ['[', ']']: #for thermocouple logger with 4 channels
            path = str(pathlib.Path(__file__).parent.absolute()) + '\\' + file[:-3] + '.TXT'
        else:
            path = str(pathlib.Path(__file__).parent.absolute()) + '\\' + file +'.txt'
        
        
        try:
            with open(path, 'r') as reader:
                line = reader.readline()
                signal = line[-5: -1]

            if signal == 'mber':  # EasyLog High Temperature logger
                df = pd.read_csv(path, encoding="unicode_escape", parse_dates=True, usecols=[1,2], index_col=0)
                df.rename(columns={'Celsius(°C)': 'Temperature°C'}, inplace=True)

            elif signal == 'unit': # Thermocouple logger
                channel_num = int(file[-2])
                channel_col = 3+channel_num
                df = pd.read_csv(path, delim_whitespace=True, parse_dates=[['date','time']], usecols=[1,2,channel_col], index_col=0)
                df.index.name = 'Time'
                df.rename(columns={file[-2]+'ch': 'Temperature°C'}, inplace=True)
         
        except (UnicodeDecodeError, FileNotFoundError):
            try:
                path = str(pathlib.Path(__file__).parent.absolute()) + '\\' + file + '.xls'
                df = pd.read_excel(path, skiprows=25, parse_dates=True, usecols=[1,2,3], index_col=0) #Temtop logger
                df['Temperature°C'].replace(to_replace='NC', value=np.nan, inplace=True)
                df['Humidity%RH'].replace(to_replace='NC', value=np.nan, inplace=True)

            except (XLRDError):  #ST-172 logger
                path = str(pathlib.Path(__file__).parent.absolute()) + '\\' + file + '.xls'
                df = pd.read_csv(path, delimiter='\t', parse_dates=True, skiprows=10, usecols=[1,2,3], index_col=2, dayfirst=True)
                df.index.name = 'Time'
                df.rename(columns={'Temp(C)': 'Temperature°C', 'RH(%RH)': 'Humidity%RH'}, inplace=True)
                   
                
        df = df[~df.index.duplicated(keep='first')]
        lst.append(df)
        
    return lst

def reduce_data(data):
    DATA = reduce(lambda left, right: pd.merge(left, right, on='Time', how='outer'), data)
    main_mean = DATA.mean(axis=1)
    return main_mean
    

def process(tables, para, form, fac):
    Data = []
    if form == 'hourly':
        for i,table in zip(range(len(tables)), tables):
            table = table.astype(float)
            if len(para) == 1:
                if 'temperature' in para: 
                    hourly_temp = table['Temperature°C'].resample(f'{fac}H').mean()
                    main = pd.DataFrame({(str(i), 'Temp'): hourly_temp})
                    
                elif 'relative humidity' in para:
                    hourly_rh = table['Humidity%RH'].resample(f'{fac}H').mean()
                    main = pd.DataFrame({(str(i), 'RH'): hourly_rh})
                    
            elif 'temperature' in para:
                if 'relative humidity' in para:
                    hourly_temp = table['Temperature°C'].resample(f'{fac}H').mean()
                    hourly_rh = table['Humidity%RH'].resample(f'{fac}H').mean()

                    main = pd.DataFrame({(str(i), 'Temp'): hourly_temp, (str(i), 'RH'): hourly_rh})
            
        
    elif form == 'day_night':
        for i,table in zip(range(len(tables)), tables):   
            days = table.astype(float).between_time('07:00:00', '19:00:00', include_end=False)
            nights = table.astype(float).between_time('19:00:00', '07:00:00', include_end=False)

            if len(para) == 1:
                if 'temperature' in para: 
                    days_temp_daily = days['Temperature°C'].resample(f'{fac}D').mean()
                    nights_temp_daily = nights['Temperature°C'].resample(f'{fac}D').mean()
                    main = pd.DataFrame({(str(i), 'Temp', 'Day'): days_temp_daily,
                                         (str(i), 'Temp', 'Night'): nights_temp_daily})
                    
                elif 'relative humidity' in para:
                    days_rh_daily = days['Humidity%RH'].resample(f'{fac}D').mean()
                    nights_rh_daily = nights['Humidity%RH'].resample(f'{fac}D').mean()
                    main = pd.DataFrame({(str(i), 'RH', 'Day'): days_rh_daily,
                                        (str(i), 'RH', 'Night'): nights_rh_daily})
                    
            elif 'temperature' in para:
                if 'relative humidity' in para:
                    days_temp_daily = days['Temperature°C'].resample(f'{fac}D').mean()
                    nights_temp_daily = nights['Temperature°C'].resample(f'{fac}D').mean()
                    days_rh_daily = days['Humidity%RH'].resample(f'{fac}D').mean()
                    nights_rh_daily = nights['Humidity%RH'].resample(f'{fac}D').mean()

                    main = pd.DataFrame({(str(i), 'Temp', 'Day'): days_temp_daily, (str(i), 'Temp', 'Night'): nights_temp_daily,
                                         (str(i), 'RH', 'Day'): days_rh_daily, (str(i), 'RH', 'Night'): nights_rh_daily})

        
    Data.append(main)
    Data_reduce = reduce(lambda left, right: pd.merge(left, right, on='Time', how='outer'), Data)
    
    if form == 'hourly':
        Data_mean = Data_reduce.groupby(level=[1], axis=1).mean()
    elif form == 'day_night':
        Data_mean = Data_reduce.groupby(level=[1,2], axis=1).mean()
        
    
    if 'temperature' in para:
        if 'relative humidity' in para:
            Data_mean = Data_mean[['Temp', 'RH']]

    return Data_mean #means of days_temp, nights_temp, days_rh, nights_rh respectively

        
def analyze(files, Parameters, names, references=None, form='hourly', factor=1, save='untitled', graph=False, markers=True):
    global main
    parameters = []
    for i in Parameters:
        parameters.append(i.casefold())

    df1 = read_files(files)
        
    main = [process(df1, parameters, form, factor)]

    if references != None:
        df2s = [read_files(reference) for reference in references]
        refer = [process(df2, parameters, form, factor) for df2 in df2s]
        main.extend(refer)

    if form == 'hourly':
        if len(parameters) == 1:
            if 'temperature' in parameters:
                columns = pd.MultiIndex.from_product([names, ['Temperature']],
                                                     names=['Sample', 'Parameter'])
                    
                    
            elif 'relative humidity' in parameters:
                columns = pd.MultiIndex.from_product([names, ['Relative Humidity']],
                                                     names=['Sample', 'Parameter'])
                            
        elif 'temperature' in parameters:
            if 'relative humidity' in parameters:
                columns = pd.MultiIndex.from_product([names, ['Temperature', 'Relative Humidity']],
                                                     names=['Sample', 'Parameter'])

    elif form == 'day_night':
        if len(parameters) == 1:
            if 'temperature' in parameters:
                columns = pd.MultiIndex.from_product([names, ['Temperature'], ['Day', 'Night']],
                                                     names=['Sample', 'Parameter', 'Day/Night Time'])
                    
                    
            elif 'relative humidity' in parameters:
                columns = pd.MultiIndex.from_product([names, ['Relative Humidity'], ['Day', 'Night']],
                                                     names=['Sample', 'Parameter', 'Day/Night Time'])
                            
        elif 'temperature' in parameters:
            if 'relative humidity' in parameters:
                columns = pd.MultiIndex.from_product([names, [ 'Temperature', 'Relative Humidity'], ['Day', 'Night']],
                                                     names=['Sample', 'Parameter', 'Day/Night Time'])  
               
    
    grand = pd.concat(main, axis=1)

    TABLE = pd.DataFrame(grand.values, index=grand.index, columns=columns)

    print(TABLE)

    TABLE.to_excel(str(pathlib.Path(__file__).parent.absolute()) + f'/{save}.xlsx')

    if graph == True:
        if markers == True:
            marks = ['-o', '--v']
        elif markers == False:
            marks = ['-', '--']
        if form == 'hourly':        
            if len(parameters) == 1:
                if parameters[0] == 'temperature':
                    sign = '°C'
                elif parameters[0] == 'relative humidity':
                    sign = '%'
                i = parameters[0]
                fig, ax = plt.subplots(figsize=(7,4))
                
                TABLE[names[0]][i.title()].plot(ax=ax, style=marks[0], label=names[0])
                if references != None:
                    for name in names[1:]:
                        TABLE[name][i.title()].plot(ax=ax, style=marks[1], label=name)
                        
                ax.legend(loc='best', frameon=True)
                ax.set_xlabel('Date')
                ax.set_ylabel(f'{i.title()} ({sign})')
                ax.axis('auto')
                if factor == 1:
                    ax.set_title(f'{factor}-Hour Average {i.title()} ({names[0]})')
                elif factor > 1:
                    ax.set_title(f'{factor}-Hours Average {i.title()} ({names[0]})')
                if references:
                    if factor == 1:
                        ax.set_title(f'{factor}-Hour Average {i.title()}')
                    elif factor > 1:
                        ax.set_title(f'{factor}-Hours Average {i.title()}')
                
            elif 'temperature' in parameters:
                if 'relative humidity' in parameters:
                    
                    fig, ax = plt.subplots(1, 2, figsize=(14,4))
                    for i,j in zip(parameters, range(len(parameters))):
                        if i == 'temperature':
                            sign = '°C'
                        elif i == 'relative humidity':
                            sign = '%'
                          
                        TABLE[names[0]][i.title()].plot(ax=ax[j], style=marks[0], label=names[0])
                
                        if references != None:
                            for name in names[1:]:
                                TABLE[name][i.title()].plot(ax=ax[j], style=marks[1], label=name)


                        ax[j].legend(loc='best', frameon=True)
                
                        ax[j].set_xlabel('Date')
                        ax[j].set_ylabel(f'{i.title()} ({sign})')
                        ax[j].axis('auto')
                        
                        if factor == 1:
                            ax[j].set_title(f'{factor}-Hour Average {i.title()} ({names[0]})')
                        elif factor > 1:
                            ax[j].set_title(f'{factor}-Hours Average {i.title()} ({names[0]})')
                            
                        if references:
                            if factor == 1:
                                ax[j].set_title(f'{factor}-Hour Average {i.title()}')
                            elif factor > 1:
                                ax[j].set_title(f'{factor}-Hours Average {i.title()}')
                

                '''ymin, ymax= TABLE[names[0]][i.title()].min(), TABLE[names[0]][i.title()].max()
                if i.casefold() == 'temperature':
                    ax[j].set_yticks(np.arange(math.floor((ymin)-1), math.ceil(ymax+1)))
                elif i.casefold() == 'relative humidity':
                    ax[j].set_yticks(np.arange((ymin//10)*10, 101, 10))

                xlabels = pd.date_range(TABLE.index.min(), periods=len(TABLE.index)+1, freq=f'{factor}H').strftime('%Y-%m-%d')
                ax[j].set_xticks(xlabels)
                
                ax[j].tick_params(which='minor', color='k')
                ax[j].tick_params(which='major', color='k', length=7)'''
                
            if len(parameters) == 2:
                plt.savefig(f'{save}_{form.title()}_temp_rh.png', dpi=600, bbox_inches='tight')
            elif len(parameters) == 1:
                plt.savefig(f'{save}_{form.title()}_{i.title()}.png', dpi=600, bbox_inches='tight')

            

        elif form == 'day_night':
            for i in parameters:
                if i.casefold() == 'temperature':
                    sign = '°C'
                elif i.casefold() == 'relative humidity':
                    sign = '%'
                fig, ax = plt.subplots(1, 2, figsize=(14,4))
                
                TABLE[names[0]][i.title()]['Day'].plot(ax=ax[0], style=marks[0], label=names[0])
                TABLE[names[0]][i.title()]['Night'].plot(ax=ax[1], style=marks[0], label=names[0])
                ax[0].axis('auto')
                ax[1].axis('auto')

                #ymax= max(TABLE[names[0]][i.title()]['Day'].max(), TABLE[names[0]][i.title()]['Night'].max())
                #ymin= min(TABLE[names[0]][i.title()]['Day'].min(),TABLE[names[0]][i.title()]['Night'].min())
                
                if references != None:
                    for name in names[1:]:
                        TABLE[name][i.title()]['Day'].plot(ax=ax[0], style=marks[1], label=name)
                        TABLE[name][i.title()]['Night'].plot(ax=ax[1], style=marks[1], label=name)
                        '''ymax= max(TABLE[names[0]][i.title()]['Day'].max(), TABLE[f'{name}'][i.title()]['Day'].max(),
                                    TABLE[names[0]][i.title()]['Night'].max(), TABLE[f'{name}'][i.title()]['Night'].max())
                        ymin= min(TABLE[names[0]][i.title()]['Day'].min(), TABLE[f'{name}'][i.title()]['Day'].min(),
                                    TABLE[names[0]][i.title()]['Night'].min(), TABLE[f'{name}'][i.title()]['Night'].min())
                else:
                    ymax= max(TABLE[names[0]][i.title()]['Day'].max(), TABLE[names[0]][i.title()]['Night'].max())
                    ymin= min(TABLE[names[0]][i.title()]['Day'].min(),TABLE[names[0]][i.title()]['Night'].min())'''
                

                ax[0].legend(loc='best', frameon=True)
                ax[1].legend(loc='best', frameon=True)

                ax[0].set_xlabel('Date')
                ax[0].set_ylabel(f'{i.title()} ({sign})')

                ax[1].set_xlabel('Date')
                ax[1].set_ylabel(f'{i.title()} ({sign})')

                    


                '''if i.casefold() == 'temperature':
                    ax[0].set_yticks(np.arange(math.floor((ymin)-1), math.ceil(ymax+1)))
                    ax[1].set_yticks(np.arange(math.floor((ymin)-1), math.ceil(ymax+1)))
                if i.casefold() == 'relative humidity':
                    ax[0].set_yticks(np.arange((ymin//10)*10, 101, 10))
                    ax[1].set_yticks(np.arange((ymin//10)*10, 101, 10))

                xlabels = pd.date_range(TABLE.index.min(), TABLE.index.max(), freq='3D').strftime('%Y-%m-%d')
                ax[0].set_xticks(xlabels)
                ax[1].set_xticks(xlabels)


                ax[0].xaxis.set_minor_locator(tic.AutoMinorLocator(3))
                ax[0].yaxis.set_minor_locator(tic.AutoMinorLocator(5))
                ax[1].xaxis.set_minor_locator(tic.AutoMinorLocator(3))
                ax[1].yaxis.set_minor_locator(tic.AutoMinorLocator(5))

                ax[0].tick_params(which='minor', color='k')
                ax[0].tick_params(which='major', color='k', length=7)
                ax[0].set_xticklabels(xlabels, rotation=45)'''
                

                '''ax[1].tick_params(which='minor', color='k')
                ax[1].tick_params(which='major', color='k', length=7)
                ax[1].set_xticklabels(xlabels, rotation=45)'''

                
                if factor == 1:
                    ax[0].set_title(f'{factor}-Day Daytime Average {i.title()}')
                    ax[1].set_title(f'{factor}-Night Night-time Average {i.title()}')
                elif factor > 1:
                    ax[0].set_title(f'{factor}-Days Daytime Average {i.title()}')
                    ax[1].set_title(f'{factor}-Nights Night-time Average {i.title()}')
               
            
                plt.savefig(f'{save}_{form.title()}_{i.title()}.png', dpi=600, bbox_inches='tight')
        plt.close('all')

    
    
    
