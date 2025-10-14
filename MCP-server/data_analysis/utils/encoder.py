import pandas as pd
import numpy as np
import json

class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (np.integer, np.int64)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, (pd.Timestamp, np.datetime64)):
            return str(pd.to_datetime(obj))
        elif isinstance(obj, (np.bool_)):
            return bool(obj)
        return super().default(obj)
