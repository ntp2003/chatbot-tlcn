from models.phone import (
    CreatePhoneModel,
    PhoneModel,
)
from models.phone_variant import (
    CreatePhoneVariantModel,
    PhoneVariantModel,
)
from models.laptop import (
    CreateLaptopModel,
    LaptopModel,
)
from models.laptop_variant import (
    CreateLaptopVariantModel,
    LaptopVariantModel,
)

for model in [
    CreatePhoneModel,
    PhoneModel,
    CreatePhoneVariantModel,
    PhoneVariantModel,
    CreateLaptopModel,
    LaptopModel,
    CreateLaptopVariantModel,
    LaptopVariantModel,
]:
    model.model_rebuild()
