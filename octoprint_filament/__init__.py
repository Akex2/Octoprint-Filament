# coding=utf-8
from __future__ import absolute_import

import octoprint.plugin
import octoprint.settings
import octoprint.util

from octoprint.events import eventManager, Events
from flask import jsonify, request
#from pushbullet.pushbullet import PushBullet
from pushbullet import PushBullet, Listener

import logging
import logging.handlers
import RPi.GPIO as GPIO

apiKey = "iJqqpUXVEZiBuxFuv35LQYeigq4Ido0L"
pb = PushBullet(apiKey)
#devices = p.getDevices()
#contacts = p.getContacts()

class FilamentSensorPlugin(octoprint.plugin.StartupPlugin,
							octoprint.plugin.SettingsPlugin,
							octoprint.plugin.EventHandlerPlugin,
							octoprint.plugin.BlueprintPlugin):

	def initialize(self):
		self._logger.setLevel(logging.DEBUG)
		
		self._logger.info("Running RPi.GPIO version '{0}'...".format(GPIO.VERSION))
		if GPIO.VERSION < "0.6":
			raise Exception("RPi.GPIO must be greater than 0.6")
			
		GPIO.setmode(GPIO.BCM)
		GPIO.setwarnings(False)
		
		self._logger.info("Filament Sensor Plugin [%s] initialized..."%self._identifier)

	def on_after_startup(self):
		self.PIN_FILAMENT = self._settings.get(["pin"])
		self.BOUNCE = self._settings.get_int(["bounce"])
		#MODIFICATION - Add additional GPIO options
		self.PAUSE_OPTIONS = self._settings.get(["pauseOptions"])
		self.ZPAUSE = False # Z-Change Pause Flag
		self.GPIO_OPTIONS = self._settings.get(["gpioOptions"])
		if self.GPIO_OPTIONS == 1:
			self._logger.info("Filament Sensor Plugin setup on GPIO Options set to [%s]..."%self.GPIO_OPTIONS)
			self.GPIO_OPTIONS = GPIO.PUD_UP
		else:
			self._logger.info("Filament Sensor Plugin setup on GPIO Options set to [%s]..."%self.GPIO_OPTIONS)
			self.GPIO_OPTIONS = GPIO.PUD_DOWN

		if self.PIN_FILAMENT != -1:
			self._logger.info("Filament Sensor Plugin setup on GPIO [%s]..."%self.PIN_FILAMENT)
			GPIO.setup(self.PIN_FILAMENT, GPIO.IN, pull_up_down = self.GPIO_OPTIONS ) #MODIFICATIONS - self.GPIO_OPTIONS

	def get_settings_defaults(self):
		return dict(
			pin = -1,
			bounce = 300,
			gpioOptions = 0,
			pauseOptions = 0,
		)
		
	@octoprint.plugin.BlueprintPlugin.route("/status", methods=["GET"])
	def check_status(self):
		status = "-1"
		if self.PIN_FILAMENT != -1:
			status = "1" if GPIO.input(self.PIN_FILAMENT) else "0"
		return jsonify( status = status )
		
	def on_event(self, event, payload):
		if event == Events.PRINT_STARTED:
			self._logger.info("Printing started. Filament sensor enabled.")
			self.setup_gpio()
            		self._logger.info("Filament Sensor PIN Set to GPIO [%s]..."%self.PIN_FILAMENT)
		elif event in (Events.PRINT_DONE, Events.PRINT_FAILED, Events.PRINT_CANCELLED):
			self._logger.info("Printing stopped. Filament sensor disabled.")
			try:
				GPIO.remove_event_detect(self.PIN_FILAMENT)
			except:
				pass
		elif event == Events.Z_CHANGE and self.ZPAUSE == True:
			self._printer.toggle_pause_print()
			self.ZPAUSE = False

	def setup_gpio(self):
		try:
			GPIO.remove_event_detect(self.PIN_FILAMENT)
		except:
			pass
		if self.PIN_FILAMENT != -1:
			GPIO.add_event_detect(self.PIN_FILAMENT, GPIO.FALLING, callback=self.check_gpio, bouncetime=self.BOUNCE)

	def check_gpio(self, channel):
		state = GPIO.input(self.PIN_FILAMENT)
		self._logger.debug("Detected sensor [%s] state [%s]? !"%(channel, state))

		if not state: #safety pin ?
			self._logger.debug("Sensor [%s]!"%state)
			if self._printer.is_printing() and self.PAUSE_OPTIONS != 1:
				self._printer.toggle_pause_print()
				self._printer.toggle_home(['x', 'y'])
				self._printer.toggle_set_temperature('tool0', '40')
				push = pb.push_note("Probleme de filament", " ")
			elif self._printer.is_printing():
				self.ZPAUSE = True

	def get_version(self):
		return self._plugin_version


	def get_update_information(self):
		return dict(
			octoprint_filament=dict(
				displayName="Filament Sensor",
				displayVersion=self._plugin_version,

				# version check: github repository
				type="github_release",
				user="Akex2",
				repo="OctoPrint-Filament",
				current=self._plugin_version,

				# update method: pip
				pip="https://github.com/Akex2/OctoPrint-Filament/archive/{target_version}.zip"
			)
		)

__plugin_name__ = "Filament Sensor"
__plugin_version__ = "1.0.1"
__plugin_description__ = "Use a filament sensor to pause printing when filament runs out."

def __plugin_load__():
	global __plugin_implementation__
	__plugin_implementation__ = FilamentSensorPlugin()
