import json
from decimal import Decimal


class SimpleDecimalEncoder(json.JSONEncoder):
    """
    Simple decimal encoder for encoding objects/dictionaries containing Decimal instances.
    Usage: json.dumps(obj, cls=SimpleDecimalEncoder)
    """
    def default(self, o):
        if isinstance(o, Decimal):
            return str(o)
        return super(SimpleDecimalEncoder, self).default(o)
