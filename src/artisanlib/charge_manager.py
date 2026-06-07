from dataclasses import dataclass
import math
from typing import Literal, Optional, Tuple


ReadinessStatus = Literal['insufficient', 'waiting', 'near', 'ready', 'hot', 'unstable']


@dataclass(frozen=True)
class ChargeReadiness:
    status: ReadinessStatus
    title: str
    reason: str
    color: str
    prediction_seconds: Optional[float]
    current_rwt: float
    target_rwt: float


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

    @staticmethod
    def _is_valid_number(value: Optional[float]) -> bool:
        return value is not None and math.isfinite(value)

    @staticmethod
    def _is_valid_positive_number(value: Optional[float]) -> bool:
        return value is not None and math.isfinite(value) and value > 0

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

    def evaluate_readiness(
        self,
        current_temp: float,
        current_ror: Optional[float],
        short_ror: Optional[float] = None,
        long_ror: Optional[float] = None,
        et_bt_gap: Optional[float] = None,
        reference_et_bt_gap: Optional[float] = None,
    ) -> ChargeReadiness:
        target_rwt = self.calculate_rwt(self.target_ror)
        current_rwt = self.calculate_rwt(current_ror)

        if not self._is_valid_number(current_temp) or not self._is_valid_positive_number(current_ror):
            self.prediction_time = None
            return ChargeReadiness(
                status='insufficient',
                title='等待数据',
                reason='升温数据不足',
                color='gray',
                prediction_seconds=None,
                current_rwt=current_rwt,
                target_rwt=target_rwt,
            )

        if current_temp > self.target_temp + self.temp_tolerance:
            self.prediction_time = 0.0
            return ChargeReadiness(
                status='hot',
                title='偏热',
                reason='温度超过目标',
                color='red',
                prediction_seconds=0.0,
                current_rwt=current_rwt,
                target_rwt=target_rwt,
            )

        prediction_seconds = self.predict(current_temp, current_ror)
        temp_in_range = abs(current_temp - self.target_temp) <= self.temp_tolerance
        ror_in_range = abs(current_ror - self.target_ror) <= self.ror_tolerance

        trend_limit = max(1.5, self.ror_tolerance / 2.0)
        trend_unstable = (
            self._is_valid_number(short_ror)
            and self._is_valid_number(long_ror)
            and abs(short_ror - long_ror) > trend_limit
        )

        heat_gap_limit = max(3.0, self.temp_tolerance * 2.0)
        heat_gap_unstable = (
            self._is_valid_number(et_bt_gap)
            and self._is_valid_number(reference_et_bt_gap)
            and abs(et_bt_gap - reference_et_bt_gap) > heat_gap_limit
        )

        if temp_in_range and ror_in_range and not trend_unstable and not heat_gap_unstable:
            return ChargeReadiness(
                status='ready',
                title='可以投豆',
                reason='温度到位，升温稳定',
                color='green',
                prediction_seconds=prediction_seconds,
                current_rwt=current_rwt,
                target_rwt=target_rwt,
            )

        if temp_in_range and (trend_unstable or heat_gap_unstable or not ror_in_range):
            reason = '升温变化过大' if trend_unstable else '升温偏离目标'
            if heat_gap_unstable:
                reason = '炉内热状态偏离参考'
            return ChargeReadiness(
                status='unstable',
                title='趋势不稳',
                reason=reason,
                color='blue',
                prediction_seconds=prediction_seconds,
                current_rwt=current_rwt,
                target_rwt=target_rwt,
            )

        near_window = max(10.0, self.prediction_window)
        if prediction_seconds is not None and prediction_seconds <= near_window:
            return ChargeReadiness(
                status='near',
                title='接近目标',
                reason='接近目标，继续观察',
                color='green',
                prediction_seconds=prediction_seconds,
                current_rwt=current_rwt,
                target_rwt=target_rwt,
            )

        return ChargeReadiness(
            status='waiting',
            title='等待升温',
            reason='距离目标还远',
            color='gray',
            prediction_seconds=prediction_seconds,
            current_rwt=current_rwt,
            target_rwt=target_rwt,
        )

    def should_show_annotation(self) -> bool:
        if not self.enabled:
            return False
        return True

    def get_status_message(self, current_ror: Optional[float], current_temp: float) -> Tuple[str, str]:
        """
        Returns a tuple of (Message, ColorString) based on Temp and RoR comparison.
        """
        readiness = self.evaluate_readiness(current_temp=current_temp, current_ror=current_ror)
        return readiness.reason, readiness.color
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