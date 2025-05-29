from db import Session
from typing import Optional, List
from models.phone_variant import (
    CreatePhoneVariantModel,
    PhoneVariant,
    PhoneVariantModel,
)
from sqlalchemy import Select, select, case, update as sql_update
