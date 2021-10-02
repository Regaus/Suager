# Changelog for the Regaus time module

## v1.0.0a1 - 26 September 2021
- Created first working version of the module

## v1.0.0rc1 - 30 September 2021
- Created changelog
- Added Virkada, Qevenerus Kargadian and Usturian calendars to the system

## v1.0.0rc2 - 1 October 2021
- Fixed Kargadian leap days breaking from not having a day name specified
- Added Usturian translations to Kargadian calendar

## v1.0.0 - 2 October 2021
- Added `.convert_time_class()` method to convert between time classes without having to call `.to_earth_time().from_earth_time()`