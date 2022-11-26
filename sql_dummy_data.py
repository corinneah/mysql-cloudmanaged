#import packages
import pandas as pd
import dbm
import sqlalchemy
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv 
from faker import Faker
import uuid
import random 

load_dotenv()

MYSQL_HOSTNAME = os.getenv ('MYSQL_HOSTNAME')
MYSQL_USER = os.getenv ('MYSQL_USER')
MYSQL_PASSWORD = os.getenv ('MYSQL_PASSWORD')
MYSQL_DATABASE = os.getenv ('MYSQL_DATABASE')

connection_string = f'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOSTNAME}:3306/{MYSQL_DATABASE}'
db = create_engine(connection_string)
print (db.table_names())


# Patient Info 
#### fake stuff ##
fake = Faker()

fake_patients = [
    {
        #keep just the first 8 characters of the uuid
        'mrn': str(uuid.uuid4())[:8], 
        'first_name':fake.first_name(), 
        'last_name':fake.last_name(),
        'zip_code':fake.zipcode(),
        'dob':(fake.date_between(start_date='-90y', end_date='-20y')).strftime("%Y-%m-%d"),
        'gender': fake.random_element(elements=('M', 'F')),
        'pronouns':fake.random_element(elements=('She', 'He', 'They', 'N/A')),
        'contact_number':fake.phone_number()
    } for x in range(50)]

df_fake_patients = pd.DataFrame(fake_patients)
# drop duplicate mrn
df_fake_patients = df_fake_patients.drop_duplicates(subset=['mrn'])

insertQuery = "INSERT INTO patients (mrn, first_name, last_name, zip_code, dob, gender, pronouns, contact_number) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"

for index, row in df_fake_patients.iterrows():
    db.execute(insertQuery, (row['mrn'], row['first_name'], row['last_name'], row['zip_code'], row['dob'], row['gender'], row['pronouns'], row['contact_number']))
    print("inserted row: ", index)

#### real icd10 codes ###
icd10codes = pd.read_csv('https://raw.githubusercontent.com/Bobrovskiy/ICD-10-CSV/master/2020/diagnosis.csv')
list(icd10codes.columns)
#icd10codesShort = icd10codes[['CodeWithSeparator', 'ShortDescription']]
icd10codesShort_1k = icd10codes.sample(n=1000, random_state=1)
# drop duplicates
icd10codesShort_1k = icd10codesShort_1k.drop_duplicates(subset=['CodeWithSeparator'], keep='first')



#### real ndc codes ###
ndc_codes = pd.read_csv('https://raw.githubusercontent.com/hantswilliams/FDA_NDC_CODES/main/NDC_2022_product.csv')
list(ndc_codes.columns)
ndc_codes_1k = ndc_codes.sample(n=1000, random_state=1)

# drop duplicates from ndc_codes_1k
ndc_codes_1k = ndc_codes_1k.drop_duplicates(subset=['PRODUCTNDC'], keep='first')


# real cpt codes ###
cpt_codes = pd.read_csv('https://gist.githubusercontent.com/lieldulev/439793dc3c5a6613b661c33d71fdd185/raw/25c3abcc5c24e640a0a5da1ee04198a824bf58fa/cpt4.csv')
list(cpt_codes.columns)
new_cpt_codes = cpt_codes.rename(columns={'com.medigy.persist.reference.type.clincial.CPT.code':'CPT_code', 'label':'CPT_description'})
new_cpt_codes = cpt_codes.sample(n=1000, random_state=1)

# drop duplicates from cpt_codes_1k
cnew_cpt_codes = new_cpt_codes.drop_duplicates(subset=['com.medigy.persist.reference.type.clincial.CPT.code'], keep='first')


# real loinc codes ###
loinc_codes = pd.read_csv('data/Loinc.csv', low_memory=False)
list(loinc_codes)
loinc_codes_1k = loinc_codes.sample(n=1000, random_state=1)

# drop duplicates from loinc_codes_1k
loinc_codes_1k = loinc_codes.drop_duplicates(subset=['LOINC_NUM'], keep='first')



## Inserting Medications 

insertQuery = "INSERT INTO medications (med_ndc, med_human_name) VALUES (%s, %s)"

medRowCount = 0
for index, row in ndc_codes_1k.iterrows():
    medRowCount += 1
    # db_azure.execute(insertQuery, (row['PRODUCTNDC'], row['NONPROPRIETARYNAME']))
    db.execute(insertQuery, (row['PRODUCTNDC'], row['NONPROPRIETARYNAME']))
    print("inserted row: ", index)
    ## stop once we have 50 rows
    if medRowCount == 75:
        break
    
## Inserting Condtions 

insertQuery = "INSERT INTO patient_conditions (icd10_code, icd10_description) VALUES (%s, %s)"

startingRow = 0
for index, row in icd10codesShort_1k.iterrows():
    startingRow += 1
    print('startingRow: ', startingRow)
    # db_azure.execute(insertQuery, (row['CodeWithSeparator'], row['ShortDescription']))
    print("inserted row db_azure: ", index)
    db.execute(insertQuery, (row['CodeWithSeparator'], row['ShortDescription']))
    print("inserted row db_gcp: ", index)
    ## stop once we have 100 rows
    if startingRow == 100:
        break


## Insterting Social Determinants

insertQuery = "INSERT INTO social_determinants (loinc, description) VALUES (%s, %s)"

startingRow = 0
for index, row in loinc_codes_1k.iterrows():
    startingRow += 1
    print('startingRow: ', startingRow)
    db.execute(insertQuery, (row['LOINC_NUM'], row['COMPONENT']))
    print("inserted row db_azure: ", index)
    ## stop once we have 100 rows
    if startingRow == 100:
        break


 ##Inserting Treatment Process 

insertQuery = "INSERT INTO treatment_process (desciption, cpt_codes) VALUES (%s, %s)"

startingRow= 0
for index, row in new_cpt_codes.iterrows():
    startingRow += 1
    db.execute(insertQuery, (row['label'], row['com.medigy.persist.reference.type.clincial.CPT.code']))
    print("inserted row: ", index)
    ## stop once we have 100 rows
    if startingRow == 100:
        break