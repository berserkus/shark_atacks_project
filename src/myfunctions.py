import pandas as pd
import re
import numpy as np

def cleaning(df):

    # Drop rows where date and year have NaN values
    df=df.dropna(subset=['Date','Year'])

    # Define a pattern from the date column and extract date values to a new column
    pattern_date="\d{2}\-\w{3}\-\d{4}"
    #pattern_month="\w{3}"

    #compile the pattern into regex
    reg_date=re.compile(pattern_date)
    
    df["Date_clean"]=df.apply(lambda row: str(re.findall(pattern_date,row["Date"]))[2:-2] if reg_date.search(str(row["Date"])) else row["Year"], axis=1)
    #create a month column
    df['Month']=df['Date_clean'].apply(lambda x: x.split('-')[1] if type(x) == str else np.nan)

    # Year as int
    df['Year']=df['Year'].astype(int)

    # remove the unnecessary columns: Case Number, pdf, href formula, href, Case Number.1, Case Number.2, original order, 22 and 23
    df=df.drop(['Case Number','pdf', 'href formula', 'href', 'Case Number.1', 'Case Number.2','original order','Unnamed: 22','Unnamed: 23'],axis=1)

    # remove values where Year and Date_clean are 0
    df=df[(df['Year']!=0)&(df['Date_clean']!=0)]

    # replace Date with Date_clean
    df['Date']=df['Date_clean']

    # Drop Date_clean
    df=df.drop(['Date_clean'],axis=1)
    
    # replace 0 years with years from the date
    df['Year']=df.apply(lambda row: str(row['Date'])[-4:] if row['Year']==0 else row['Year'], axis=1)

    #Strip the column names of spaces
    df=df.rename(columns=lambda x: x.strip())

    # Change column names - make them shorter
    df=df.rename(columns={'Fatal (Y/N)':'Fatal','Investigator or Source':'Source'})

    # Clean the values from Fatal and Sex
    df['Fatal']=df['Fatal'].str.strip().str.upper()
    df['Sex']=df['Sex'].str.strip().str.upper()
    # Filter out the values where Fatal or Sex is not clear
    df=df[((df['Fatal']=='N') | (df['Fatal']=='Y')) & ((df['Sex']=='M') | (df['Sex']=='F'))]

    # Define a function that will classify shark names
    shark_list=['white shark', 'tiger shark', 'bull shark', 'wobbegong shark', 'blacktip shark', 'blue shark']

    def clean_spec(element,list,remain): # remain is the value that is given if no match is found, 'same' leaves the same value
        sk=[i.capitalize() for i in list if i in str(element).lower()]
        if sk==[]:
            if remain=='same':
                sk=element
            else:
                sk=remain
        else:
            sk=str(sk[0]) 
        return sk

    #run the species clean function on the relevant column
    df['Species']=df['Species'].apply(clean_spec,args=(shark_list,'Shark'))

    # Run the clean_spec function on the specified activity list
    activities=['kite surfing', 'windsurfing', 'surfing', 'free diving', 'diving', 'snorkeling', 'fishing', 'wading', 'swimming', 'bathing', 'boarding', 'standing', 'kayking', 'surf']
    df['Activity']=df['Activity'].apply(clean_spec, args=(activities,'same'))

    df['Activity'].replace(to_replace='Surf', value='Surfing', inplace=True)
    df['Activity'].replace(to_replace='Wading', value='Fishing', inplace=True)
    df['Activity'].replace(to_replace='Bathing', value='Swimming', inplace=True)
    df['Activity'].replace(to_replace='Boarding', value='Surfing', inplace=True)

    # Clean up the country list
    # Put all the country names in lower letters and capitalize
    # Replace Usa with USA
    df['Country']=df['Country'].str.split('/').str[0].str.strip()
    df['Country']=df['Country'].str.lower().str.capitalize()
    df['Country'].replace(to_replace='Usa', value='USA', inplace=True)



    # Clean up the age column
    def clean_age(age):
        if isinstance(age, int):
            if age>100:
                age=100
        elif re.findall('\d{1,2}',age)!=[]:
            age=int(re.findall('\d{1,2}',age)[0])
        else:
            age=0
        return age

    df['Age']=df['Age'].fillna(0)
    df['Age']=df['Age'].apply(clean_age)

    return df

def year_stats(df2):
    # Create index of years and calculate the fatality rates for each year
    years=[]
    fatality_rate=[]
    fatality_r_male=[]
    fatality_r_female=[]

    for i in range(int(df2['Year'].min()),int(df2['Year'].max())+1):
        years.append(i)
        if len(df2[df2['Year']==i])==0:
            fatality_rate.append(0)
        else:
            fatality_rate.append(len(df2[(df2['Year']==i)&(df2['Fatal']=='Y')])/len(df2[df2['Year']==i])*100)
            
        if len(df2[(df2['Year']==i)&(df2['Sex']=='M')])==0:
            fatality_r_male.append(0)
        else:
            fatality_r_male.append(len(df2[(df2['Year']==i)&(df2['Sex']=='M')&(df2['Fatal']=='Y')])/len(df2[(df2['Year']==i)&(df2['Sex']=='M')])*100)

        if len(df2[(df2['Year']==i)&(df2['Sex']=='F')])==0:
            fatality_r_female.append(0)
        else:
            fatality_r_female.append(len(df2[(df2['Year']==i)&(df2['Sex']=='F')&(df2['Fatal']=='Y')])/len(df2[(df2['Year']==i)&(df2['Sex']=='F')])*100)

    # build a dictionary which will be used to build a dataframe
    dict=list(zip(years,fatality_rate))
    df_y=pd.DataFrame(dict,columns=['Year','Fatality rate'])
    df_y['Fatality rate male']=fatality_r_male
    df_y['Fatality rate female']=fatality_r_female

    # calculate the 5 year averages
    df_y['Fatality rate 5y_avg']=df_y['Fatality rate'].rolling(5).mean()
    df_y['Fatality rate male 5y_avg']=df_y['Fatality rate male'].rolling(5).mean()
    df_y['Fatality rate female 5y_avg']=df_y['Fatality rate female'].rolling(5).mean()

    return df_y

# create a dataframe for countries
def country_stats(df2, top):
    top_countries=df2['Country'].value_counts()[:top]
    top_df=pd.DataFrame(top_countries,columns=['Country'])
    top_countries=list(top_countries.index)
    top_df.rename(columns={'Country':'Cases'}, inplace=True)

    fatal_y=[]
    fatal_n=[]
    males=[]
    females=[]
    males_fatal=[]
    females_fatal=[]
    for i in top_countries:
        fatal_y.append(df2[(df2['Country']==i)&(df2['Fatal']=='Y')]['Fatal'].count())
        fatal_n.append(df2[(df2['Country']==i)&(df2['Fatal']=='N')]['Fatal'].count())
        males.append(df2[(df2['Country']==i)&(df2['Sex']=='M')]['Fatal'].count())
        females.append(df2[(df2['Country']==i)&(df2['Sex']=='F')]['Fatal'].count())
        males_fatal.append(df2[(df2['Country']==i)&(df2['Sex']=='M')&(df2['Fatal']=='Y')]['Fatal'].count())
        females_fatal.append(df2[(df2['Country']==i)&(df2['Sex']=='F')&(df2['Fatal']=='Y')]['Fatal'].count())
    
    top_df['Fatal']=fatal_y
    top_df['Not fatal']=fatal_n
    top_df['Males']=males
    top_df['Females']=females
    top_df['Males fatal']=males_fatal
    top_df['Females fatal']=females_fatal

    top_df['Fatality rate']=top_df['Fatal']/top_df['Cases']
    top_df['Fatality rate males']=top_df['Males fatal']/top_df['Males']
    top_df['Fatality rate females']=top_df['Females fatal']/top_df['Females']

    return top_df

# Create activities dataframe

def activity_stats(df2,top):
    top_activities=df2['Activity'].value_counts()[:10]
    top_a_df=pd.DataFrame(top_activities,columns=['Activity'])
    top_a_df.rename(columns={'Activity':'Cases'}, inplace=True)
    top_activities=list(top_activities.index)

    fatal_y=[]
    fatal_n=[]
    males=[]
    females=[]
    males_fatal=[]
    females_fatal=[]
    for i in top_activities:
        fatal_y.append(df2[(df2['Activity']==i)&(df2['Fatal']=='Y')]['Fatal'].count())
        fatal_n.append(df2[(df2['Activity']==i)&(df2['Fatal']=='N')]['Fatal'].count())
        males.append(df2[(df2['Activity']==i)&(df2['Sex']=='M')]['Fatal'].count())
        females.append(df2[(df2['Activity']==i)&(df2['Sex']=='F')]['Fatal'].count())
        males_fatal.append(df2[(df2['Activity']==i)&(df2['Sex']=='M')&(df2['Fatal']=='Y')]['Fatal'].count())
        females_fatal.append(df2[(df2['Activity']==i)&(df2['Sex']=='F')&(df2['Fatal']=='Y')]['Fatal'].count())
    
    top_a_df['Fatal']=fatal_y
    top_a_df['Not fatal']=fatal_n
    top_a_df['Males']=males
    top_a_df['Females']=females
    top_a_df['Males fatal']=males_fatal
    top_a_df['Females fatal']=females_fatal

    top_a_df['Fatality rate']=top_a_df['Fatal']/top_a_df['Cases']
    top_a_df['Fatality rate males']=top_a_df['Males fatal']/top_a_df['Males']
    top_a_df['Fatality rate females']=top_a_df['Females fatal']/top_a_df['Females']

    return top_a_df

# create a dataframe specific for the USA and based on the unemployment rate data
def usa_database(unrate,df_usa):
    years=unrate['Year'].tolist()

    # into the unrate database calculate the total number of cases, fatal cases, Surfing, Fishing, Swimming, Diving, and calculate the fatality rates

    cases=[]
    fatal_y=[]
    surfing=[]
    fishing=[]
    swimming=[]
    diving=[]
    surfing_fatal=[]
    fishing_fatal=[]
    swimming_fatal=[]
    diving_fatal=[]
    for i in years:
        cases.append(df_usa[(df_usa['Year']==i)]['Fatal'].count())
        fatal_y.append(df_usa[(df_usa['Year']==i)&(df_usa['Fatal']=='Y')]['Fatal'].count())
        surfing.append(df_usa[(df_usa['Year']==i)&(df_usa['Activity']=='Surfing')]['Fatal'].count())
        surfing_fatal.append(df_usa[(df_usa['Year']==i)&(df_usa['Activity']=='Surfing')&(df_usa['Fatal']=='Y')]['Fatal'].count())
        fishing.append(df_usa[(df_usa['Year']==i)&(df_usa['Activity']=='Fishing')]['Fatal'].count())
        fishing_fatal.append(df_usa[(df_usa['Year']==i)&(df_usa['Activity']=='Fishing')&(df_usa['Fatal']=='Y')]['Fatal'].count())
        swimming.append(df_usa[(df_usa['Year']==i)&(df_usa['Activity']=='Swimming')]['Fatal'].count())
        swimming_fatal.append(df_usa[(df_usa['Year']==i)&(df_usa['Activity']=='Swimming')&(df_usa['Fatal']=='Y')]['Fatal'].count())
        diving.append(df_usa[(df_usa['Year']==i)&(df_usa['Activity']=='Diving')]['Fatal'].count())
        diving_fatal.append(df_usa[(df_usa['Year']==i)&(df_usa['Activity']=='Diving')&(df_usa['Fatal']=='Y')]['Fatal'].count())

    unrate['Cases']=cases
    unrate['Fatal_y']=fatal_y
    unrate['Surfing']=surfing
    unrate['Surfing fatal']=surfing_fatal
    unrate['Fishing']=fishing
    unrate['Fishing fatal']=fishing_fatal
    unrate['Swimming']=swimming
    unrate['Swimming fatal']=swimming_fatal
    unrate['Diving']=diving
    unrate['Diving fatal']=diving_fatal

    unrate['UNRATE_log']=np.log(unrate['UNRATE'])
    unrate['Cases_log']=np.log(unrate['Cases'])
    unrate['Surfing_log']=np.log(unrate['Surfing'])
    unrate['Fishing_log']=np.log(unrate['Fishing'])
    unrate['Swimming_log']=np.log(unrate['Swimming'])
    unrate['Diving_log']=np.log(unrate['Diving'])

    return unrate
        