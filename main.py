# -*- coding: utf-8 -*-

import logging
import signal
import sys
import yaml

from bot import Bot
from utils import parse_args

bot = None

if __name__ == '__main__':

	args = parse_args()
	try:
		config_file = open('config.yaml', 'r')
		config = yaml.load(config_file, Loader=yaml.FullLoader)

	except FileNotFoundError:
		print("\"config.yaml\" has to exist on root directory.")
		sys.exit(0)

	except IOError:
		print("Modmail doesn't have the proper permissions to read \"config.yaml\".")
		sys.exit(0)

	if(not args.token):
		print("You need to provide a secret token with \"--token\" or \"-t\" ")
		sys.exit(0)

	#gateway = logging.getLogger("gateway")
	#gateway.setLevel(logging.INFO)
	#dispatch = logging.getLogger("dispatch")
	#dispatch.setLevel(logging.INFO)

	bot = Bot(config=config)
	bot.run(args.token)
