import uuid
from typing import Dict

class PopupManager:
    def __init__(self):
        self.popup_data = []
        # self.popup_data: Dict[str, dict] = {}

    def set_popup_data(self, popup_data: dict):
        self.popup_data.append(popup_data)
    
    def get_popup_data(self):
        if self.popup_data:
            return self.popup_data[-1]
        else:
            return None
        
    def clear_popup_data(self):
        self.popup_data = []

popup_manager = PopupManager()