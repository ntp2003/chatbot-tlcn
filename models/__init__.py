from models.phone import (
    CreatePhoneModel,
    PhoneModel,
)
from models.phone_variant import (
    CreatePhoneVariantModel,
    PhoneVariantModel,
)

for model in [
    CreatePhoneModel,
    PhoneModel,
    CreatePhoneVariantModel,
    PhoneVariantModel,
]:
    model.model_rebuild()
