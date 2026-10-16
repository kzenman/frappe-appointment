__version__ = "0.0.4"

from frappe_appointment import monkey_patch

monkey_patch.patch_all()
