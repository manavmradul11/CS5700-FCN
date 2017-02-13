#!/usr/bin/python

from bs4 import BeautifulSoup
import requests
import lxml.html
import sys

USERNAME = str(sys.argv[-2])
PASSWORD = str(sys.argv[-1])


# As we are authenticating, we need to handle session related data such as cookies, csrf tokens
# Create a session object; s
s = requests.session()

# Request the web page using GET
page = s.get('http://cs5700sp17.ccs.neu.edu/accounts/login/?next=/fakebook/')

# Lets extract hidden data from the web page such as csrfmiddlewaretoken and other field such as 'next'
# We will use lxml library to translate the web page so that we can extract the necessary content
# fromstring() is used to create element from a string containing XML
page_source = lxml.html.fromstring(page.text)
hidden_form_data = page_source.xpath(r'//form//input[@type="hidden"]')
# Extract hidden data and add it to dictionary - unique value pairs
form = {x.attrib["name"]: x.attrib["value"] for x in hidden_form_data}
if(form["csrfmiddlewaretoken"]==''):
    print ('Program quit because of invalid user credentials or 500 Internal Error - Please recheck and retry')
    exit()
# add username and password to dictionary
form['username'] = USERNAME
form['password'] = PASSWORD
# send this information in a form of post request to server

response = s.post('http://cs5700sp17.ccs.neu.edu/accounts/login/?next=/fakebook/', data=form)
next_url = response.url
if(next_url=='http://cs5700sp17.ccs.neu.edu/accounts/login/?next=/fakebook/'):
    print ('Program quit because of invalid user credentials or 500 Internal Error - Please recheck and retry')
    exit()
i = 1
urls = [next_url]  # stack of URLS
visited = [next_url]  # Historic URL's which are already visited

while len(urls) > 0:
    sourcecode = s.get(urls[0])  # Visit URL's and fetch data. URL are stored in form of list.

    status = sourcecode.status_code     # extract status code like 200, 302, 500 etc
    #Handling different HTTP Status code

    if status == 200:
        pass
    elif status == 301:
        getnewlink = sourcecode.headers['Location']      # Extra new link from the Location Header
        urls.append(getnewlink)                          # Append it to new url list to search again
    elif status == 403 or status == 404:                           # drop the url by adding it to visited list
        visited.append(urls[0])                               # testing message
    elif status == 500:                                # Re-try the request
        sourcecode = s.get(urls[0])

    plaintext = sourcecode.text  # Extract plain text and ignore http headers and request/response messages
    soup = BeautifulSoup(plaintext, "html.parser")  # Convert plaintext to beautifulsoup object
    if status != 500:
        urls.pop(0)         # Otherwise loop will run infinite times

    for link in soup.findAll('a'):  # Get only href content from class name info_odd

        href = 'http://cs5700sp17.ccs.neu.edu' + link.get('href')  # Get only href content
        if next_url in href and href not in visited:        # If the URI belongs to the same domain and not been visited

            urls.append(href)
            visited.append(href)
            for ctf in soup.findAll('h2', {'class': 'secret_flag'}):  # Get only secret flag from class h2
                d = []

                d = ctf.string   # capture the flag (ctf) and print
                print(d[6:])     # Display only the flag numbers and filter "FLAG = " string
                i += 1
                if i == 6:
                    exit()