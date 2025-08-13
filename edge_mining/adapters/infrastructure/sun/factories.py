"""Collection of factories to create Sun."""

from datetime import datetime

from astral import LocationInfo
from astral.sun import sun

from edge_mining.application.interfaces import SunFactoryInterface
from edge_mining.domain.policy.value_objects import Sun


class AstralSunFactory(SunFactoryInterface):
    """
    Factory to create Sun Value Objects using the astral library.
    """

    def __init__(
        self,
        latitude: float,
        longitude: float,
        timezone: str,
        name: str = "",
        region: str = "",
    ):
        """
        Initializes the factory with location information.
        """
        location_info = LocationInfo(
            name=name,
            region=region,
            timezone=timezone,
            latitude=latitude,
            longitude=longitude,
        )
        self._location = location_info

    def create_sun_for_date(self, for_date: datetime = datetime.now) -> Sun:
        """
        Creates a Sun object for a specific date.
        """
        s = sun(self._location.observer, date=for_date)

        return Sun(
            dawn=s["dawn"],
            sunrise=s["sunrise"],
            noon=s["noon"],
            midnight=s["midnight"],
            sunset=s["sunset"],
            dusk=s["dusk"],
            daylight=s["daylight"],
            night=s["night"],
            twilight=s["twilight"],
            azimuth=s["azimuth"],
            zenith=s["zenith"],
            elevation=s["elevation"],
        )
