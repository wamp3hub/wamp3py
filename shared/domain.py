import dataclasses
import dacite


Domain = dataclasses.dataclass(kw_only=True, slots=True)

field = dataclasses.field

dump = dataclasses.asdict

load = dacite.from_dict
