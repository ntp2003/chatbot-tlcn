from import_laptop_data import *
from import_phone_data import *
from import_brand_data import *
from import_faq_data import *
from tasks.import_brand_data import import_json as import_brand_json
from tasks.import_phone_data import import_jsonl_to_database as import_phone_data_jsonl_to_database
from tasks.import_laptop_data import import_laptop_data_jsonl_to_database 
from tasks.import_accessory_data import import_accessories_data_jsonl_to_database 
'''
python tasks/import_data.py
'''
def main():
    '''
    import_faq_csv()

    # clear cac file jsonl trc khi chay
    extract_fpt_accessories_data()
    extract_fpt_laptop_data()
    extract_fpt_phone_data()

    import_brand_json()
    
    import_phone_data_jsonl_to_database()
    import_laptop_data_jsonl_to_database()
    import_accessories_data_jsonl_to_database()
    '''
    #extract_fpt_phone_data()
    #extract_fpt_accessories_data()
    #extract_fpt_laptop_data()
    #import_brand_json()
    #import_phone_data_jsonl_to_database()
    import_laptop_data_jsonl_to_database()
    
if __name__ == "__main__":
    main()