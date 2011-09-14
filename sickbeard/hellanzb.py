# Author: Nic Wolfe <nic@wolfeden.ca>
# URL: http://code.google.com/p/sickbeard/
#
# This file is part of Sick Beard.
#
# Sick Beard is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Sick Beard is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Sick Beard.  If not, see <http://www.gnu.org/licenses/>.



import httplib
import datetime

import sickbeard

from base64 import standard_b64encode
import xmlrpclib

from sickbeard.providers.generic import GenericProvider

from sickbeard import logger

def sendNZB(nzb):

    addToTop = False
    hellanzbXMLrpc = "http://hellanzb:%(password)s@%(host)s/xmlrpc"

    if sickbeard.HELLANZB_HOST == None:
        logger.log(u"No HellaNZB host found in configuration. Please configure it.", logger.ERROR)
        return False

    url = hellanzbXMLrpc % {"host": sickbeard.HELLANZB_HOST, "password": sickbeard.HELLANZB_PASSWORD}

    hellanzbRPC = xmlrpclib.ServerProxy(url)
    try:
        if hellanzbRPC.system.listMethods():
            logger.log(u"Successful connected to HellaNZB", logger.DEBUG)
        else:
            logger.log(u"Successful connected to HellaNZB, but unable to send a message" % (nzb.name + ".nzb"), logger.ERROR)

    except httplib.socket.error:
        logger.log(u"Please check your HellaNZB host and port (if it is running). HellaNZB is not responding to this combination", logger.ERROR)
        return False

    except xmlrpclib.ProtocolError, e:
        if (e.errmsg == "Unauthorized"):
            logger.log(u"HellaNZB password is incorrect.", logger.ERROR)
        else:
            logger.log(u"Protocol Error: " + e.errmsg, logger.ERROR)
        return False

    # if it aired recently make it high priority
    for curEp in nzb.episodes:
        if datetime.date.today() - curEp.airdate <= datetime.timedelta(days=7):
            addToTop = True

    # if it's a normal result need to download the NZB content
    if nzb.resultType == "nzb":
        genProvider = GenericProvider("")
        data = genProvider.getURL(nzb.url)
        if (data == None):
            return False

    # if we get a raw data result thats even better
    elif nzb.resultType == "nzbdata":
        data = nzb.extraInfo[0]

    # nzbcontent64 = standard_b64encode(data)

    logger.log(u"Sending NZB to HellaNZB")
    logger.log(u"URL: " + url, logger.DEBUG)

    # if hellanzbRPC.append(nzb.name + ".nzb", sickbeard.HELLANZB_CATEGORY, addToTop, nzbcontent64):
    if hellanzbRPC.enqueue(nzb.name + ".nzb", data):
        logger.log(u"NZB sent to HellaNZB successfully", logger.DEBUG)
        return True
    else:
        logger.log(u"HellaNZB could not add %s to the queue" % (nzb.name + ".nzb"), logger.ERROR)
        return False
