from typing import Optional, Tuple

class ChargeTargetManager:
    """
    Manages the charge target feature: predicting when the target temperature 
    will be reached with the target RoR.
    """
    def __init__(self) -> None:
        self.target_temp: float = 0.0
        self.target_ror: float = 0.0
        self.temp_tolerance: float = 0.0
        self.ror_tolerance: float = 6.0 # Default 0.1 deg/s = 6 deg/min
        
        self.enabled: bool = False
        self.active: bool = True
        self.prediction_time: Optional[float] = None
        self.prediction_window: float = 5.0 # seconds
        
        # Snapshot values at Charge
        self.charged_temp: float = 0.0
        self.charged_ror: float = 0.0

    def update_settings(self, target_temp: float, target_ror: float, enabled: bool, 
                       temp_tolerance: float = 0.0, ror_tolerance: float = 6.0) -> None:
        self.target_temp = target_temp
        self.target_ror = target_ror
        self.enabled = enabled
        self.temp_tolerance = temp_tolerance
        self.ror_tolerance = ror_tolerance

    def on_charge_event(self, current_temp: float = 0.0, current_ror: float = 0.0) -> None:
        self.active = False
        self.charged_temp = current_temp
        self.charged_ror = current_ror

    def reset(self) -> None:
        self.active = True
        self.prediction_time = None
        self.charged_temp = 0.0
        self.charged_ror = 0.0

    def predict(self, current_temp: float, current_ror: Optional[float]) -> Optional[float]:
        """
        Predict time to reach target_temp based on current_temp and current_ror.
        """
        if current_temp >= self.target_temp:
            self.prediction_time = 0.0
            return 0.0

        if current_ror is None or current_ror <= 0:
            self.prediction_time = None
            return None

        # Use average of current RoR and target RoR for prediction
        avg_ror_min = (current_ror + self.target_ror) / 2.0
        if avg_ror_min <= 0:
            self.prediction_time = None
            return None
            
        avg_ror_sec = avg_ror_min / 60.0
        
        temp_diff = self.target_temp - current_temp
        time_sec = temp_diff / avg_ror_sec
        
        self.prediction_time = time_sec
        return time_sec

    def should_show_annotation(self) -> bool:
        if not self.enabled:
            return False
        return True

    def get_status_message(self, current_ror: Optional[float], current_temp: float) -> Tuple[str, str]:
        """
        Returns a tuple of (Message, ColorString) based on Temp and RoR comparison.
        """
        # 1. Check Temperature Status
        if current_temp > self.target_temp + self.temp_tolerance:
            return "温度过高！需降温", "red"
        
        if abs(current_temp - self.target_temp) <= self.temp_tolerance:
             return "温度达标！准备投豆", "green"

        # 2. Check RoR Status
        if current_ror is None:
            return "数据无效", "gray"
            
        diff = current_ror - self.target_ror
        
        if abs(diff) <= self.ror_tolerance:
            return "升温速率正常", "green"
        
        if diff > 0:
            return "升温太快！需减火", "red"
        else:
            return "升温太慢！需加火", "blue"
            
    # Static helpers for RWT conversion (RoR per minute, DeltaT=10)
    @staticmethod
    def calculate_rwt(ror: Optional[float]) -> float:
        """Returns RWT in seconds for a 10 degree rise at given RoR."""
        if ror is None or ror <= 0:
            return 0.0
        return 600.0 / ror

    @staticmethod
    def calculate_ror(rwt: float) -> float:
        """Returns RoR in deg/min for a 10 degree rise in rwt seconds."""
        if rwt <= 0:
            return 0.0
        return 600.0 / rwt