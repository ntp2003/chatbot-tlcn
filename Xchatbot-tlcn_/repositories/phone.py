from ast import stmt
from db import Session
from typing import Optional, List
from models.phone import CreatePhoneModel, Phone, PhoneModel
from sqlalchemy import select, case
from tools.utils.search i