from __future__ import annotations

import random
from datetime import datetime, timedelta
from typing import Final

from django.db import transaction
from django.db.models import F
from django.utils import timezone

from mobileid.models import (
    Barcode,
    BarcodeUsage,
)
from mobileid.project_code.dynamic_barcode import auto_send_code


