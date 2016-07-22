Pause print on GPIO filament runout sensor

The following needs to be added to the config.yaml:

```
  filament:
    pin: XX
    bounce: 400
    gpioOptions: 0
    pauseOptions: 0
```
where XX represent the GPIO pin where your sensor is connected.

Option Descriptions:
pin = The GPIO Pin, this is in BCM mode, so for pin 26, you'd enter 7 (for GPIO7)
bounce = The time to wait for the switch to settle, in ms.
gpioOptions = Configure the default GPIO pull_up_down mode. 0 [default] is PULL_DOWN mode. 1 is for PULL_UP mode.
pauseOptions = Configure the pause action. 0 [default] pauses immediately. 1 waits for the next ZChange event (layer change).

An API is available to check the filament sensor status via a GET method to `/plugin/filament/status` which returns a JSON

- `{status: "-1"}` if the sensor is not setup
- `{status: "0"}` if the sensor is OFF (filament not present)
- `{status: "1"}` if the sensor is ON (filament present)

The status 0/1 depends on the type of sensor, and it might be reversed if using a normally closed switch.

A build using an optical switch can be found at http://www.thingiverse.com/thing:1646220

Note: Needs RPi.GPIO version greater than 0.6.0 to allow access to GPIO for non root and `chmod a+rw /dev/gpiomem`.
This requires a fairly up to date system.
