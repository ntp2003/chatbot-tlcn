from import_laptop_data import *
from import_phone_data import *
from import_brand_data import *
from import_faq_data import *
from import_accessories_data import *

'''
python tasks/import_data.py
'''
def main():
    import_faq_csv()
    import_brand_json()
    import_phone_data_jsonl_to_database()
    import_laptop_data_jsonl_to_database()
    import_accessories_data_jsonl_to_database()


if __name__ == "__main__":
    main()
