#!/usr/bin/python
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Author: Matias Kreder <mkreder@gmail.com> 

from megahal import *
from pprint import pprint 
import twitter 
import time
import pickle
import os
import random
################################################################################
# Parameters for Twitter API, register your app and save your parameters here: #
################################################################################
api = twitter.Api(consumer_key='consumer_key_from', consumer_secret='consumer_secret', access_token_key='access_token_key', access_token_secret='access_token_secret') 
#################################################################################
# Set here the directory where your bot will be running:                        #
#################################################################################
pwd = '/home/carlita'
#################################################################################
# Set your Twitter username here:                                               #
#################################################################################
usr = 'carlita'
#################################################################################
# Set the delay between API interactions                                        #
# https://dev.twitter.com/docs/rate-limiting                                    #
#################################################################################
dly = 15
## no need to set more vars after here
megahal = MegaHAL()
megahal.train( pwd + "/brain.trn")
true = 0
L = list()     
R = list()


# Get the DMs and reply them 
def messages(dm,L,R):
    for message in dm:
        sender = message.GetSenderScreenName()
        print 'received: ' + message.GetText() + 'from: ' + message.GetSenderScreenName()
        response = megahal.get_reply(message.GetText())
        megahal.learn(message.GetText())
        print  'sent: ' + response 
        if response in R:
            print "response already sent some time"
        else:
            try:
                api.PostDirectMessage(sender, response) 
                R.append(response)
            except twitter.TwitterError:
                pass
        api.DestroyDirectMessage(message.GetId())
        time.sleep(dly)

# Get the new followers and follow them
def followers(fr,friends):
    for flw in fr:
        haveit = 0
        for friend in friends:
            if (friend.GetScreenName() == flw.GetScreenName()):
                haveit = 1
        if haveit == 0:
            try:
                api.CreateFriendship(flw.GetScreenName())   
            except twitter.TwitterError:
                pass
            print "follwing:" + flw.GetScreenName()
        time.sleep(dly)

#learn stuff from my timeline 
def learnut(ut):
    for status in ut:
        megahal.learn(status.GetText())

# Get a random tweet from TL and reply it to say something
def saytt(ut,L,R):
    i = random.randint(0,9)
    if ut[i].GetId() in L:
        print "tweet already worked"
    else:
        response = "@" + ut[i].GetUser().GetScreenName() + " "  + megahal.get_reply(ut[i].GetText())
        if response in R:
            print "that was already said sometime"
        else:
            api.PostUpdates(response)
            R.append(response)
        L.append(ut[i].GetId())
    time.sleep(dly)

# Get mentions from the API and reply them
def mentions(mt,L,R):
    for mention in mt:
        if  mention.GetId() in L:
            print "tweet already replied"
        else:
            tweet = mention.GetText()
            tweet = tweet.replace(u"@" + usr," ")
            response = "oops"
            try:
                print "got tweet: " + tweet
                response = "@" + mention.GetUser().GetScreenName() + " " +  megahal.get_reply(tweet)
                megahal.learn(tweet)
            except UnicodeEncodeError:
                pass
            if response in R:
                print "response already sent some time"
            else:
                try:
                    api.PostUpdates(response)
                except twitter.TwitterError:
                    pass
                R.append(response)
            L.append(mention.GetId())
            time.sleep(dly)

# Find new users to friend in my TL
def newfriends(ut,friends):
    for status in ut:
        tweet = status.GetText()
        tweet = tweet.split()
        for word in tweet:
            word = word.replace(":"," ")
            word = word.split()
            if ( word[0].startswith("@")):
                word[0] = word[0].replace("@","")
                if word[0] in friends:
                    print word[0] + " is a friend already"
                else:
                    print "following: " + word[0]
                    try:
                        api.CreateFriendship(word[0])
                    except twitter.TwitterError:
                        pass
                    time.sleep(dly)
        
# Save responses and ids            
def save(L,R):
    print "Saving L"
    pprint(L)
    f = open(pwd + '/ids','wb')
    pickle.dump(L,f)
    f.close
    print "Saving R"
    pprint(R)
    f2 = open(pwd + '/responses','wb')
    pickle.dump(R,f2)
    f2.close


def main():
    # Load the responses and ids 
    if (os.path.exists(pwd + "/ids")):
        print "Loading messageIds replied"
        f = open(pwd + '/ids','rb')
        L = pickle.load(f)
        f.close
    else:
        L = []
    if (os.path.exists(pwd + "/responses")):
        print "Loading responses already sent"
        f2 = open(pwd + '/responses','rb')
        R = pickle.load(f2)
        f2.close
    else:
        R = []

    print "getting DMs"
    dm = api.GetDirectMessages()
    messages(dm,L,R)
    time.sleep(dly)

    print "checking for new followers"
    fr = api.GetFollowers()
    friends = api.GetFriends()
    followers(fr,friends)
    time.sleep(dly)

    print "getting new mentions"
    mt = api.GetMentions()
    mentions(mt,L,R)
    save(L,R)
    time.sleep(dly)

    print "getting my TL to learn new stuff and reply"
    ut = api.GetFriendsTimeline()
    learnut(ut)
    time.sleep(dly)

    sayornot = random.randint(1, 100)
    if (sayornot < 20):
        print "sayng something random"
        saytt(ut,L,R)
        time.sleep(dly)

    print "getting new friends from TL"
    newfriends(ut,friends)
    print "saving..."
    save(L,R)    
    megahal.sync()    
 
if __name__ == "__main__":
    main()

