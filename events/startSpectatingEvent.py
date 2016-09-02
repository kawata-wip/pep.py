from constants import clientPackets
from constants import serverPackets
from constants import exceptions
from objects import glob
from helpers import userHelper
from helpers import logHelper as log
from helpers import chatHelper as chat

def handle(userToken, packetData):
	try:
		# Get usertoken data
		userID = userToken.userID
		username = userToken.username

		# Start spectating packet
		packetData = clientPackets.startSpectating(packetData)

		# Stop spectating old user if needed
		if userToken.spectating != 0:
			oldTargetToken = glob.tokens.getTokenFromUserID(userToken.spectating)
			oldTargetToken.enqueue(serverPackets.removeSpectator(userID))
			userToken.stopSpectating()

		# Start spectating new user
		userToken.startSpectating(packetData["userID"])

		# Get host token
		targetToken = glob.tokens.getTokenFromUserID(packetData["userID"])
		if targetToken is None:
			raise exceptions.tokenNotFoundException

		# Add us to host's spectators
		targetToken.addSpectator(userID)

		# Send spectator join packet to host
		targetToken.enqueue(serverPackets.addSpectator(userID))

		# Create and join #spectator (#spect_userid) channel
		glob.channels.addTempChannel("#spect_{}".format(targetToken.userID))
		chat.joinChannel(token=userToken, channel="#spect_{}".format(targetToken.userID))
		if len(targetToken.spectators) == 1:
			# First spectator, send #spectator join to host too
			chat.joinChannel(token=targetToken, channel="#spect_{}".format(targetToken.userID))

		# send fellowSpectatorJoined to all spectators
		for spec in targetToken.spectators:
			if spec is not userID:
				c = glob.tokens.getTokenFromUserID(spec)
				userToken.enqueue(serverPackets.fellowSpectatorJoined(c.userID))
				c.enqueue(serverPackets.fellowSpectatorJoined(userID))

		# Console output
		log.info("{} are spectating {}".format(username, userHelper.getUsername(packetData["userID"])))
	except exceptions.tokenNotFoundException:
		# Stop spectating if token not found
		log.warning("Spectator start: token not found")
		userToken.stopSpectating()
