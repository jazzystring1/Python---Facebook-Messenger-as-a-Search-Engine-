import json
import time
import re
import urllib.parse
import urllib.request as urllib2
import os
from bs4 import BeautifulSoup
from flask import Flask, request
from pymessenger.bot import Bot

API_KEY = os.environ['API_KEY']
API_URL = os.environ['API_URL']

app = Flask(__name__)
PAGE_ACCESS_TOKEN = os.environ['ACCESS_TOKEN']
VERIFY_TOKEN = os.environ['VERIFY_TOKEN']
bot = Bot(PAGE_ACCESS_TOKEN)
 
#We will receive messages that Facebook sends our bot at this endpoint 
@app.route("/", methods=['GET', 'POST'])
def receive_message():
    if request.method == 'GET':
       token_sent = request.args.get("hub.verify_token")
       return verify_fb_token(token_sent)
    #if the request was not get, it must be POST and we can just proceed with sending a message back to user
    else:
       # get whatever message a user sent the bot
       # set the recipient_id to global variable for the api2image api to access it
       output = request.get_json()
       for event in output['entry']:
          messaging = event['messaging']
          for message in messaging:
            if message.get('message'):
                #Facebook Messenger ID for user so we know where to send response back to
                recipient_id = message['sender']['id']
                if message['message'].get('text'):
                	command = message['message'].get('text').split(' ')
                	if len(command) > 1:
                		if command[0] in ["Google", "google"] and command[1] in ["Search", "search"]:
                			if urllib.parse.parse_qs(command[len(command) - 1]) != {}:
                				search_keyword = ' '.join(command[2:len(command) - 1])           				
                				stripped_options = urllib.parse.parse_qs(command[len(command) - 1])
                				if "select" in stripped_options:
	                				send_message(recipient_id, "Selecting page %s on '%s' google search results. Please wait :D" % (stripped_options["select"][0], search_keyword))	       
	                			else:
	                				send_message(recipient_id, "Invalid options parameter :/")
	                				return 'Failed'
	                			response_sent_text = call_urlbox(search_keyword, 'Google', stripped_options)	                			
	                			send_image(recipient_id, response_sent_text)
	                		else:
	                			#get the search keywords
	                			search_keyword = ' '.join(command[2:])
	                			#notify the user
	                			send_message(recipient_id, 'Screenshot is on process barbs. Please wait. ;)')
	                			#get the json result
		                		response_sent_text = call_urlbox(search_keyword, 'Google')
		                		#check the status
		                		send_image(recipient_id, response_sent_text)
	                	elif command[0] in ["Youtube", "youtube"]:
	                		if command[1] in ["Trend", "trend"]:
	                			send_message(recipient_id, 'Getting youtube trends barbs <3')
	                			response_sent_text = call_urlbox(' ', 'Youtube')
		                		send_image(recipient_id, response_sent_text)
	                	elif command[0] in ["Surf", "surf"]:
	                		surf_keyword = ' '.join(command[1:])
	                		#check if their are special symbols
	                		if re.findall('[^A-Za-z0-9\-\.]', surf_keyword):
	                			send_message(recipient_id, "Invalid website name barbs :/")
	                		else:
	                			send_message(recipient_id, "Surfing %s. Please wait ;)" % surf_keyword)
	                			response_sent_text = call_urlbox(surf_keyword, 'Custom')
		                		send_image(recipient_id, response_sent_text)		                		
	                	elif command[0] in ["Stackoverflow", "stackoverflow"] and command[1] in ["Search", "search"]:
	                		#If the user added options in command such as page=X, convert it to dictionary
	                		if urllib.parse.parse_qs(command[len(command) - 1]) != {}:
	                			search_keyword = ' '.join(command[2:len(command) - 1])
	                			stripped_options = urllib.parse.parse_qs(command[len(command) - 1])
	                			if "select" in stripped_options:
	                				send_message(recipient_id, "Selecting page %s on '%s' stackoverflow search results. Please wait ;)" % (stripped_options["select"][0], search_keyword))
	                			else:
	                				send_message(recipient_id, "Invalid options parameter :/")
	                			response_sent_text = call_urlbox(search_keyword, 'Stackoverflow', stripped_options)
	                			send_image(recipient_id, response_sent_text)
	                		else:
	                			search_keyword = ' '.join(command[2:])
	                			send_message(recipient_id, "Searching '%s' in Stackoverflow. Please wait. ;)" % search_keyword)
	                			response_sent_text = call_urlbox(search_keyword, 'Stackoverflow')
	                			send_image(recipient_id, response_sent_text)
	                	elif command[0] in ["Facebook", "facebook"] and command[1] in ["Photoview", "photoview"]:
	                			search_keyword = ' '.join(command[2:])
	                			send_message(recipient_id, "Viewing facebook photo '%s'. Please wait. ;)" % search_keyword)
	                			response_sent_text = call_urlbox(search_keyword, 'Facebook')
	                			send_image(recipient_id, response_sent_text)
	                	else:
	                		send_message(recipient_id, "Command modifier '%s' is invalid barbs " % command[0])
	                else:
	                	send_message(recipient_id, 'Invalid command barbs :/')
                              
                #if user sends us a GIF, photo,video, or any other non-text item
                if message['message'].get('attachments'):
                    bot.send_text_message(recipient_id, "Sorry barbs but I dont entertain images hehe :D")
    return "Message Processed"
 
 
def verify_fb_token(token_sent):
    #take token sent by facebook and verify it matches the verify token you sent
    #if they match, allow the request, else return an error 
    if token_sent == VERIFY_TOKEN:
        return request.args.get("hub.challenge")
    return 'Invalid verification token'
 
def send_message(recipient_id, msg):
	bot.send_text_message(recipient_id, msg)

def send_image(recipient_id, data):
	bot.send_image_url(recipient_id, data['image'])
	bot.send_text_message(recipient_id, data['left_calls'])

def get_contents(url):
	#set headers to access
	url = urllib2.Request(url, headers={'User-Agent' : 'Magic Browser'})

	#load url
	file = urllib2.urlopen(url)

	#return read file
	return file.read()

def get_google_results(url, page):
	#get url content
	contents = get_contents(url)

	#initialize beautifulsoup
	css_soup = BeautifulSoup(contents, "html.parser")

	#get all the a tags in google search results
	result_tags = css_soup.select('h3 > a')

    #get the href
	link = [v['href'] for k, v in enumerate(result_tags) if k == int(page) - 1]

	#return link
	return link[0]

def get_url(keyword, website = ''):
	if website in ["Google", "google"]:
		url = "http://www.google.com/search?q=%s" % keyword

	if website in ["Youtube", "youtube"]:
		url = "www.youtube.com/feed/trending"

	if website in ["Custom", "custom"]:
		url = keyword

	if website in ["Stackoverflow", "stackoverflow"]:
		url = "www.stackoverflow.com/search?q=%s" % keyword

	if website in ["Facebook", "facebook"]:
		url = keyword.replace('free.facebook', 'facebook')

	return url

def call_urlbox(keyword, website = '', options = ''):
	global API_URL
	url = get_url(keyword, website)

	API_URL = "https://api.urlbox.io/v1/%s/png?" % os.environ['URLBOX_API_KEY']

	post_data = {
		"url": url,
        "ttl" : "86400",
        "full_page" : "true"
	}

	#add api parameters
	if website in ["Stackoverflow", "stackoverflow"]:
		if "select" in options:
			post_data['click'] = "div[data-position='%s'] > .summary > .result-link > span > a" % options['select'][0]
	elif website in ["Google", "google"]:
		if "select" in options:
			post_data['click'] = ".g:nth-child(%s) a" % options['select'][0]
	elif website in ["Facebook", "facebook"]:
		post_data['selector'] = '._5pcr.userContentWrapper'
	IMAGE_URL  = urllib.parse.urlencode(post_data, True)
	urllib2.urlopen(API_URL + IMAGE_URL)
	return { "image" : "%s" % API_URL + IMAGE_URL, "left_calls" : "Unknown left calls :/" }


if __name__ == "__main__":
    app.run()