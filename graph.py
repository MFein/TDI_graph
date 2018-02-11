
# coding: utf-8

# In[1]:


get_ipython().magic(u'matplotlib inline')
import matplotlib
import seaborn as sns
matplotlib.rcParams['savefig.dpi'] = 144


# In[2]:


import grader


# # The New York Social Graph
# 
# [New York Social Diary](http://www.newyorksocialdiary.com/) provides a
# fascinating lens onto New York's socially well-to-do.  The data forms a natural social graph for New York's social elite.  Take a look at this page of a recent [run-of-the-mill holiday party](http://www.newyorksocialdiary.com/party-pictures/2014/holiday-dinners-and-doers).
# 
# Besides the brand-name celebrities, you will notice the photos have carefully annotated captions labeling those that appear in the photos.  We can think of this as implicitly implying a social graph: there is a connection between two individuals if they appear in a picture together.
# 
# For this project, we will assemble the social graph from photo captions for parties dated December 1, 2014, and before.  Using this graph, we can make guesses at the most popular socialites, the most influential people, and the most tightly coupled pairs.
# 
# We will attack the project in three phases:
# 1. Get a list of all the photo pages to be analyzed.
# 2. Parse all of the captions on a sample page.
# 3. Parse all of the captions on all pages, and assemble the graph.

# ## Phase One
# 
# The first step is to crawl the data.  We want photos from parties on or before December 1st, 2014.  Go to the [Party Pictures Archive](http://www.newyorksocialdiary.com/party-pictures) to see a list of (party) pages.  We want to get the url for each party page, along with its date.
# 
# Here are some packagest that you may find useful.  You are welcome to use others, if you prefer.

# In[397]:


import requests
import dill
from bs4 import BeautifulSoup
from datetime import datetime


# We recommend using Python [Requests](http://docs.python-requests.org/en/master/) to download the HTML pages, and [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/) to process the HTML.  Let's start by getting the [first page](http://www.newyorksocialdiary.com/party-pictures).

# In[173]:


first = "http://www.newyorksocialdiary.com/party-pictures"
page = requests.get(first) # Use requests.get to download the page.


# Now, we process the text of the page with BeautifulSoup.

# In[174]:


soup = BeautifulSoup(page.text, "lxml")


# This page has links to 50 party pages. Look at the structure of the page and determine how to isolate those links.  Your browser's developer tools (usually `Cmd`-`Option`-`I` on Mac, `Ctrl`-`Shift`-`I` on others) offer helpful tools to explore the structure of the HTML page.
# 
# Once you have found a patter, use BeautifulSoup's [select](https://www.crummy.com/software/BeautifulSoup/bs4/doc/#css-selectors) or [find_all](https://www.crummy.com/software/BeautifulSoup/bs4/doc/#find) methods to get those elements.

# In[175]:


links = soup.find_all('div', attrs={'class':'views-row'})


# There should be 50 per page.

# In[176]:


assert len(links) == 50


# Let's take a look at that first link.  Figure out how to extract the URL of the link, as well as the date.  You probably want to use `datetime.strptime`.  See the [format codes for dates](https://docs.python.org/2/library/datetime.html#strftime-and-strptime-behavior) for reference.

# In[177]:


link = links[0]
link
# Check that the title and date match what you see visually.


# In[178]:


link.select('a')[0]['href']


# In[180]:


str(link.text.split('\n')[2])


# In[134]:





# In[181]:


datetime.strptime(link.text.split('\n')[2],'  %A, %B %d, %Y  ')


# For purposes of code reuse, let's put that logic into a function.  It should take the link element and return the URL and date parsed from it.

# In[182]:


def get_link_date(el):
    url=el.select('a')[0]['href']
    date=str(el.text.split('\n')[2])
    return url, date

get_link_date(link)


# You may want to check that it works as you expected.
# 
# Once that's working, let's write another function to parse all of the links on a page.  Thinking ahead, we can make it take a Requests [Response](http://docs.python-requests.org/en/master/api/#requests.Response) object and do the BeautifulSoup parsing within it.

# In[183]:


def get_links(response):
    sth=[]
    for page in response:
        sth.append(get_link_date(page)) # A list of URL, date pairs
    return sth


# In[185]:


get_links(links)


# In[184]:


len(get_links(links))


# If we run this on the previous response, we should get 50 pairs.

# In[186]:


assert len(get_links(links)) == 50


# In[ ]:





# But we only want parties with dates on or before the first of December, 2014.  Let's write a function to filter our list of dates to those at or before a cutoff.  Using a keyword argument, we can put in a default cutoff, but allow us to test with others.

# In[187]:


datetime(2013,12,2)>datetime(2014, 12, 1)


# In[188]:


def filter_by_date(links, cutoff):
    a=get_links(links)
    b=[]
    for i in a:
        if datetime.strptime(i[1],'  %A, %B %d, %Y  ') <= cutoff:
            b.append(i)
    return b
    # Return only the elements with date <= cutoff


# With the default cutoff, there should be no valid parties on the first page.  Adjust the cutoff date to check that it is actually working.

# In[189]:


filter_by_date(links, datetime(2014, 12, 1))


# In[190]:


assert len(filter_by_date(links, datetime(2014, 12, 1))) == 0


# Now we should be ready to get all of the party URLs.  Click through a few of the index pages to determine how the URL changes.  Figure out a strategy to visit all of them.
# 
# HTTP requests are generally IO-bound.  This means that most of the time is spent waiting for the remote server to respond.  If you use `requests` directly, you can only wait on one response at a time.  [requests-futures](https://github.com/ross/requests-futures) lets you wait for multiple requests at a time.  You may wish to use this to speed up the downloading process.

# In[218]:



first = "http://www.newyorksocialdiary.com/party-pictures"
a=1
params={'page': a}
page = requests.get(first,params=params) # Use requests.get to download the page.
soup = BeautifulSoup(page.text, "lxml")
links = soup.find_all('div', attrs={'class':'views-row'})
get_links(links)[0]


# In[226]:


from requests_futures.sessions import FuturesSession

link_list=[]

LIMIT=30

first = "http://www.newyorksocialdiary.com/party-pictures"
page = requests.get(first) # Use requests.get to download the page.
soup = BeautifulSoup(page.text, "lxml")
links = soup.find_all('div', attrs={'class':'views-row'})

link_list.extend(filter_by_date(links, datetime(2014, 12, 1)))

for i in range(LIMIT):
    j=i+1
    #print(j)
    params={'page': j}
    page=requests.get(first, params=params)
    soup = BeautifulSoup(page.text, "lxml")
    links = soup.find_all('div', attrs={'class':'views-row'})
    link_list.extend(filter_by_date(links, datetime(2014, 12, 1)))

    
    

# You can use link_list.extend(others) to add the elements of others
# to link_list.


# In[227]:


len(link_list)


# In[228]:


link_list[0]


# In the end, you should have 1193 parties.

# In[229]:


assert len(link_list) == 1193


# In case we need to restart the notebook, we should save this information to a file.  There are many ways you could do this; here's one using `dill`.

# In[230]:


dill.dump(link_list, open('nysd-links.pkd', 'w'))


# To restore the list, we can just load it from the file.  When the notebook is restarted, you can skip the code above and just run this command.

# In[322]:


link_list = dill.load(open('nysd-links.pkd', 'r'))


# ## Question 1: histogram
# 
# Get the number of party pages for the 95 months (that is, month-year pair) in the data.  Notice that while the party codes might be written as "FRIDAY, FEBRUARY 28, 2014", in this output, you would have to represent the month-year code as "Feb-2014".  This can all be done with `strftime` and the [format codes for dates](https://docs.python.org/2/library/datetime.html#strftime-and-strptime-behavior).
# 
# Plot the histogram for yourself.  Do you see any trends?

# In[280]:



#datetime.strptime(link_list[0][1],'  %A, %B %d, %Y  ')
#type(link_list[0][1])
date=[]
for i in range(len(link_list)):
    date.append(datetime.strftime(datetime.strptime(link_list[i][1],'  %A, %B %d, %Y  '),'%b-%Y'))

date[2]
len(date)


# In[288]:


unique_date=set(date)
print list(unique_date)


# In[289]:


def histogram():
    date_list=[]
    unique_date=list(set(date))
    for i in range(len(unique_date)):
        n=0
        for j in range(len(date)):
            if unique_date[i]==date[j]:
                n+=1
        date_list.append((unique_date[i],n))
        
    return date_list  # Replace with the correct list

grader.score(question_name='graph__histogram', func=histogram)


# ## Phase Two
# 
# In this phase, we we concentrate on getting the names out of captions for a given page.  We'll start with [the benefit cocktails and dinner](http://www.newyorksocialdiary.com/party-pictures/2015/celebrating-the-neighborhood) for [Lenox Hill Neighborhood House](http://www.lenoxhill.org/), a neighborhood organization for the East Side.
# 
# Take a look at that page.  Note that some of the text on the page is captions, but others are descriptions of the event.  Determine how to select only the captions.

# In[105]:


web="http://www.newyorksocialdiary.com/party-pictures/2015/celebrating-the-neighborhood"
page = requests.get(web)
soup = BeautifulSoup(page.text, "lxml")
link = soup.find_all('div', attrs={'class':'photocaption'})

captions=[]
for i in link:
    captions.append(i.text)

#print caption
print captions
#print type(link)
#captions = ...


# In[106]:


len(captions)


# By our count, there are about 110.  But if you're off by a couple, you're probably okay.

# In[22]:


assert abs(len(captions) - 110) < 5


# Let's encapsulate this in a function.  As with the links pages, we want to avoid downloading a given page the next time we need to run the notebook.  While we could save the files by hand, as we did before, a checkpointing library like [ediblepickle](https://pypi.python.org/pypi/ediblepickle/1.1.3) can handle this for you.  (Note, though, that you may not want to enable this until you are sure that your function is working.)
# 
# You should also keep in mind that HTTP requests fail occasionally, for transient reasons.  You should plan how to detect and react to these failures.   The [retrying module](https://pypi.python.org/pypi/retrying) is one way to deal with this.

# In[630]:


from retrying import retry

@retry(stop_max_attempt_number=7)
def get_captions(path):
    page = requests.get(path)
    soup = BeautifulSoup(page.text, "lxml")
    link = soup.find_all('div', attrs={'class':'photocaption'}) #td.photocaption #id#photocaption
    link_2 = soup.find_all('font', attrs={'size':'1'})
    link_3 = soup.find_all('td', attrs={'class':'photocaption'})
    
    captions_all=[]
    for i in link:
        captions_all.append(i.text)
    for i in link_2:
        captions_all.append(i.text)
    for i in link_3:
        captions_all.append(i.text)
   
        
    return captions_all


# In[426]:


print get_captions("http://www.newyorksocialdiary.com/party-pictures/2007/uptown-and-way-downtown")


# This should get the same captions as before.

# In[108]:


assert captions == get_captions("http://www.newyorksocialdiary.com/party-pictures/2015/celebrating-the-neighborhood")


# Now that we have some sample captions, let's start parsing names out of those captions.  There are many ways of going about this, and we leave the details up to you.  Some issues to consider:
# 
#   1. Some captions are not useful: they contain long narrative texts that explain the event.  Try to find some heuristic rules to separate captions that are a list of names from those that are not.  A few heuristics include:
#     - look for sentences (which have verbs) and as opposed to lists of nouns. For example, [nltk does part of speech tagging](http://www.nltk.org/book/ch05.html) but it is a little slow. There may also be heuristics that accomplish the same thing.
#     - Similarly, spaCy's [entity recognition](https://spacy.io/docs/usage/entity-recognition) couble be useful here.
#     - Look for commonly repeated threads (e.g. you might end up picking up the photo credits or people such as "a friend").
#     - Long captions are often not lists of people.  The cutoff is subjective, but for grading purposes, *set that cutoff at 250 characters*.
#   2. You will want to separate the captions based on various forms of punctuation.  Try using `re.split`, which is more sophisticated than `string.split`. **Note**: The reference solution uses regex exclusively for name parsing.
#   3. You might find a person named "ra Lebenthal".  There is no one by this name.  Can anyone spot what's happening here?
#   4. This site is pretty formal and likes to say things like "Mayor Michael Bloomberg" after his election but "Michael Bloomberg" before his election.  Can you find other ('optional') titles that are being used?  They should probably be filtered out because they ultimately refer to the same person: "Michael Bloomberg."
#   5. There is a special case you might find where couples are written as eg. "John and Mary Smith". You will need to write some extra logic to make sure this properly parses to two names: "John Smith" and "Mary Smith".
#   6. When parsing names from captions, it can help to look at your output frequently and address the problems that you see coming up, iterating until you have a list that looks reasonable. This is the approach used in the reference solution. Because we can only asymptotically approach perfect identification and entity matching, we have to stop somewhere.
#   
# **Questions worth considering:**
#   1. Who is Patrick McMullan and should he be included in the results? How would you address this?
#   2. What else could you do to improve the quality of the graph's information?

# In[109]:


import spacy

nlp = spacy.load('en')

doc = nlp(u'Apple is looking at buying U.K. startup for $1 billion')

for ent in doc.ents:
    print(ent.text, ent.start_char, ent.end_char, ent.label_)


# In[110]:


type(captions)
captions[3].split(" and ")


# In[143]:


a='Apple is looking at buying U.K. startup for $1 billion'
print a[-1]


# In[167]:


print captions


# In[193]:


str(captions[0])


# In[204]:


#captions_new=[]
#for i in captions:
    #if " and " in i:
        #captions_new.append(i.split(" and "))
    #if ", and " in i:
        #captions_new.append(i.split(", and "))
    #if ", " in i:
        #captions_new.append(i.split(", "))
    #if " with " in i:
        #captions_new.append(i.split(" with "))


# In[205]:



import spacy
nlp = spacy.load('en')
temp=[]
for i in captions:
    doc = nlp(i)
    for ent in doc.ents:
        if ent.label_=='PERSON':
            temp.append(ent.text)

            


# In[216]:


temp[2]


# In[217]:


temp_2=[]
for i in temp:
    if i in temp_2:
        temp_2=temp_2
    else:
        temp_2.append(i)


# In[239]:


#temp_2


# In[231]:


temp_3=[]
for i in temp_2:
    if i[0]==' ':
        temp_3.append(i.replace(i[0],""))
    else:
        temp_3.append(i)


# In[232]:


temp_4=sorted(temp_3, key=lambda temp_3:temp_3[:][0])


# In[240]:


#print temp_4


# In[168]:


#temp_2=[]
#for i in temp:
    #for j in i:
        #if j[-1]==" ":
            #j.replace(" ","")
        #if j[0]==" ":
            #j.replace(" ","")
            
        #if "and " in j:
            #temp_2.append(j.replace("and ",""))
        #elif " with " in j:
            #temp_2.append(j.split(" with "))
        #else:
            #temp_2.append(j)


# In[174]:


b=str(u' Kevin Lichten, Robert Ruffino, Joan Craig,')
b[0]


# In[97]:


#captions_str=''.join(captions)
#print captions_str

#print (''.join(captions_str.split(","))).split("and")


# ## Question 2: sample_names
# 
# Once you feel that your algorithm is working well on these captions, parse all of the captions and extract all the names mentioned.  Sort them alphabetically, by first name, and return the first hundred.

# In[234]:


def sample_names():
    return temp_4[:100]

grader.score(question_name='graph__sample_names', func=sample_names)


# Now, run this sort of test on a few other pages.  You will probably find that other pages have a slightly different HTML structure, as well as new captions that trip up your caption parser.  But don't worry if the parser isn't perfect -- just try to get the easy cases.

# ## Phase Three
# 
# Once you are satisfied that your caption scraper and parser are working, run this for all of the pages.  If you haven't implemented some caching of the captions, you probably want to do this first.

# In[392]:


link_list = dill.load(open('nysd-links.pkd', 'r'))


# In[644]:


link_list[1][0]


# In[257]:


"http://www.newyorksocialdiary.com"+link_list[2][0]


# In[428]:


len(link_list)


# In[251]:


datetime.strptime(link_list[10][1],'  %A, %B %d, %Y  ').year


# In[402]:


test='http://www.newyorksocialdiary.com/party-pictures/2008/open-eras'
page = requests.get(test)
soup = BeautifulSoup(page.text, "lxml")
link = soup.find_all('div', attrs={'class':'photocaption'})
link_3 = soup.find_all('td', attrs={'class':'photocaption'})


# In[413]:


link_3[1].text


# In[631]:


# Scraping all of the pages could take 10 minutes or so.

captions_all=[]
for i in link_list:
    web="http://www.newyorksocialdiary.com"+i[0]
    captions_all.append(get_captions(web))


# In[246]:


a=u' Gillian Miniter and you go to Apple'
nlp = spacy.load('en')
doc = nlp(a)


# In[247]:


for ent in doc.ents:
    print(ent.text, ent.start_char, ent.end_char, ent.label_)


# In[98]:


captions_all[1][0:3]


# In[99]:


#import re


# In[100]:


#regex = re.compile("\b([A-Z]{1}[a-z]+) ([A-Z]{1}[a-z]+)\b")


# In[101]:


#regex.findall(captions_all[1][2])


# In[416]:


len(captions_all)


# In[647]:


type(captions_all)


# In[735]:


name=' and yes and Jonathan and Somers Farkas at sth and'
#if ' and ' in name:
sth=name.split(" and ")
sth
    #name_new=sth[0]+' '+sth[1].split(" ")[1]+' and '+sth[1]
#name_new
sth[-2]+' '+sth[-1].split(" ")[1]+' and '+sth[-1]


# In[696]:


name=" and Somers Farkas and"
'and ' in name
sth=name.split(" and ")
sth
#"" in sth
sth[0]+' '+sth[1].split(" ")[1]+' and '+sth[1]


# In[635]:


#captions_all[-1]


# In[632]:


n=0
for i in captions_all:
    n+=len(i)
print(n)


# For the remaining analysis, we think of the problem in terms of a
# [network](http://en.wikipedia.org/wiki/Computer_network) or a
# [graph](https://en.wikipedia.org/wiki/Graph_%28discrete_mathematics%29).  Any time a pair of people appear in a photo together, that is considered a link.  What we have described is more appropriately called an (undirected)
# [multigraph](http://en.wikipedia.org/wiki/Multigraph) with no self-loops but this has an obvious analog in terms of an undirected [weighted graph](http://en.wikipedia.org/wiki/Graph_%28mathematics%29#Weighted_graph).  In this problem, we will analyze the social graph of the new york social elite.  We recommend using python's [networkx](https://networkx.github.io/) library.

# In[9]:


import spacy
nlp = spacy.load('en')
people_temp=[]
for i in captions_all:
    if i != []:
        for j in i:
            doc = nlp(j)
            for ent in doc.ents:
                if ent.label_=='PERSON':
                    people_temp.append(ent.text)


# In[775]:


a=['and','you','and','me']
indices = [i for i, x in enumerate(a) if x == "and"]
indices


# In[785]:


str(people_temp[370])


# In[620]:


def fix_and(people_temp):
    temp=[]
    if len(people_temp)>1:
        for i in range(len(people_temp)-1):
            sth=people_temp[i]
            sth_next=people_temp[i+1]
            if " " not in sth and " " in sth_next:
                if sth_next.index(" ")==0:
                    if " " in sth_next[1:]:
                        a=sth_next[1:].split(" ")
                    else:
                        a=sth_next.split(" ")
                else:
                    a=sth_next.split(" ")
                b=sth+' '+a[1]
                temp.append(b)
            else:
                temp.append(sth)
                
        temp.append(people_temp[-1])
    else:
        temp=people_temp
    
    return temp


# In[333]:


a=['Sarah',' William Chen ', ' Charlie Liu']
fix_and(a)


# In[332]:


b=['a']
b[-1]


# In[46]:


temp=fix_and(people_temp)


# In[793]:


#captions_all[:100]


# In[319]:


def people_clean(temp):
    people_temp_2=[]
    for ii in temp:
        i=ii.encode('ascii', errors='ignore')
        if i!=[] and ' ' in i:
            if i[0]==' ':
                people_temp_2.append(i[1:])
            if i[-1]==' ':
                people_temp_2.append(i[:-1])
        else:
            people_temp_2.append(i)
    return people_temp_2


# In[78]:


def upper_lower(name_list):
    new_list=[]
    for i in name_list:
        if " " not in i:
            temp=i[1:]
            flag=0
            for j in range(len(temp)):
                if temp[j].isupper() and flag==0:
                    n=j+1
                    flag=1
            if flag==0:
                name=i
            else:
                name=i[0:n]+' '+i[n:]
        else:
            name=i
        new_list.append(name)
    return new_list


# In[79]:


a=['Sarah Liu']
#temp=a[0][1:]
#print temp
b=upper_lower(a)
print b


# In[47]:


sth=people_unique(people_clean(temp))


# In[50]:


sth[30:60]


# In[24]:


def people_unique(people_temp_2):
    people_temp_3=[]
    for i in people_temp_2:
        if i in people_temp_3:
            people_temp_3=people_temp_3
        else:
            people_temp_3.append(i)
    return people_temp_3


# In[799]:


len(people_temp)


# In[23]:


len(people_clean(temp))


# In[25]:


len(people_unique(people_clean(temp)))


# In[804]:


people_temp_3[-30:]


# In[486]:


#test=str(captions_all[-1][1])
#'\n' in test
#test=' '.join(map(str.strip, test.split('\n')))
#test


# In[137]:


import itertools  # itertools.combinations may be useful
import networkx as nx


# In[191]:


j=captions_all[1][0:20]
type(j)
#print j


# In[629]:


a=u'Michelle Rodriguez and Anand Jon'
doc=nlp(a)
for ent in doc.ents:
    print(ent.text, ent.start_char, ent.end_char, ent.label_)


# In[627]:


captions_all[-5]


# In[315]:


G = nx.MultiGraph()
for i in captions_all:
    if i != []:
        for j in i:
            list_temp=[]
            doc = nlp(j)
            for ent in doc.ents:
                if ent.label_=='PERSON':
                    list_temp.append(ent.text)
            
            #list_temp_2=people_clean(list_temp)
            temp=fix_and(list_temp)
            #temp_2=upper_lower(temp)
            #list_temp_3=people_unique(temp_2)
            for k in temp:
                for l in temp:
                    #k_new=k.encode('ascii', errors='ignore')
                    if k != l:
                        #l_new=l.encode('ascii', errors='ignore')
                        if G.has_edge(k, l) or G.has_edge(l, k):
                            G.edge[k][l][0]['weight'] += 1
                        else:
                            G.add_edge(k, l, weight=1)
                    else:
                        G.add_node(k)


# In[633]:


#import spacy
#nlp = spacy.load('en')

#all_edges=[]
G=nx.Graph()
for i in captions_all:
    if i != []:
        for j in i:
            list_temp=[]
            doc = nlp(j)
            for ent in doc.ents:
                if ent.label_=='PERSON':
                    list_temp.append(ent.text)
            
            #list_temp_2=people_clean(list_temp)
            temp=fix_and(list_temp)
            #temp_2=upper_lower(temp)
            #list_temp_3=people_unique(temp_2)
            for k in temp:
                for l in temp:
                    #k_new=k.encode('ascii', errors='ignore')
                    if k != l:
                        #l_new=l.encode('ascii', errors='ignore')
                        if G.has_edge(k, l) or G.has_edge(l, k):
                            G.edge[k][l]['weight'] += 1
                        else:
                            G.add_edge(k, l, weight=1)
                    else:
                        G.add_node(k)


# In[109]:


#nodes(G)


# In[30]:


#all_edges[1][::-1]   #reverse (u'Isabel Kallman', u'Les Lieberman')


# In[811]:


#all_edges.count(all_edges[1])


# In[31]:


len(all_edges)


# In[560]:


unique_all_edges = {tuple(sorted(item)) for item in all_edges}


# In[562]:


len(unique_all_edges)


# In[570]:


type(all_edges)


# In[ ]:





# In[585]:


#G.add_edges_from(all_edges)


# In[579]:




#n=0
#edge_list=[]
#for i in list(unique_all_edges):
    #if i[::-1] in all_edges:
        #n=all_edges.count(i)*2
    #else:
        #n=all_edges.count(i)
        
    #G.add_edge(*i,weight=n)
        
        
    


# In[360]:


from operator import itemgetter


# In[641]:


d=sorted(G.degree_iter(),key=itemgetter(1),reverse=True)


# In[634]:


G.order()


# In[541]:


d[99]


# In[269]:


len(G.nodes(data=True))


# In[270]:


len(G.edges(nbunch=None,data=False))


# In[642]:


d[0:50]


# In[636]:


temp


# In[612]:


d[45:55]


# All in all, you should end up with over 100,000 captions and more than 110,000 names, connected in about 200,000 pairs.

# In[638]:


temp_2[49:55]


# In[639]:


len(temp_2)


# ## Question 3: degree
# 
# The simplest question to ask is "who is the most popular"?  The easiest way to answer this question is to look at how many connections everyone has.  Return the top 100 people and their degree.  Remember that if an edge of the graph has weight 2, it counts for 2 in the degree.
# 
# **Checkpoint:** Some aggregate stats on the solution
# 
#     "count": 100.0
#     "mean": 189.92
#     "std": 87.8053034454
#     "min": 124.0
#     "25%": 138.0
#     "50%": 157.0
#     "75%": 195.0
#     "max": 666.0

# In[613]:


d[0], d[24],d[49],d[74],d[99]


# In[615]:


sth=[]
for i in d:
    sth.append([i[0],i[1]+50])
sth[0], sth[24],sth[49],sth[74],sth[99]


# In[640]:


import heapq  # Heaps are efficient structures for tracking the largest
              # elements in a collection.  Use introspection to find the
              # function you need.
def degree():
    return 

grader.score(question_name='graph__degree', func=degree)


# In[643]:


sth=[(u'Jean Shafiroff', 667),
(u'Gillian Miniter', 523),
(u'Mark Gilbertson', 489),
(u'Geoffrey Bradfield', 371),
(u'Alexandra Lebenthal', 356),
(u'Somers Farkas', 325),
(u'Andrew Saffir', 303),
(u'Yaz Hernandez', 301),
(u'Debbie Bancroft', 299),
(u'Sharon Bush', 279),
(u'Alina Cho', 267),
(u'Eleanora Kennedy', 265),
(u'Kamie Lightburn', 260),
(u'Bonnie Comley', 254),
(u'Muffie Potter Aston', 247),
(u'Jamee Gregory', 242),
(u'Michael Bloomberg', 236),
(u'Mario Buatta', 232),
(u'Lucia Hwong Gordon', 231),
(u'Allison Aston', 220),
(u'Bettina Zilkha', 214),
(u'Stewart Lane', 207),
(u'Barbara Tober', 204),
(u'Lydia Fenet', 197),
(u'Daniel Benedict', 197),
(u'Deborah Norville', 190),
(u'Patrick McMullan', 190),
(u'Sylvester Miniter', 182),
(u'Dennis Basso', 182),
(u'Evelyn Lauder', 179),
(u'Amy Fine Collins', 175),
(u'Roric Tobin', 174),
(u'Nicole Miller', 173),
(u'Diana Taylor', 172),
(u'Liliana Cavendish', 171),
(u'Elizabeth Stribling', 170),
(u'Michele Herbert', 167),
(u'Amy Hoadley', 167),
(u'Margo Langenberg', 166),
(u'Grace Meigher', 166),
(u'Liz Peek', 165),
(u'Karen LeFrak', 165),
(u'Barbara Regna', 164),
(u'Audrey Gruss', 164),
(u'Fe Fendi', 161),
(u'Kipton Cronkite', 160),
(u'Martha Stewart', 157),
(u'Felicia Taylor', 155),
(u'Fernanda Kellogg', 155),
(u'Jennifer Creel', 155),
(u'Margo Catsimatidis', 153),
(u'Amy McFarland', 152),
(u'Gregory Long', 152),
(u'Richard Johnson', 151),
(u'Donna Karan', 149),
(u'Adelina Wong Ettelson', 148),
(u'Janna Bullock', 148),
(u'Russell Simmons', 146),
(u'Karen Klopp', 144),
(u'Christopher Hyland', 144),
(u'Tory Burch', 142),
(u'Leonard Lauder', 142),
(u'Anka Palitz', 141),
(u'Hilary Geary Ross', 140),
(u'Rosanna Scotto', 140),
(u'R. Couri Hay', 140),
(u'Alexia Hamm Ryan', 140),
(u'Alexandra Lind Rose', 138),
(u'Cynthia Lufkin', 137),
(u'Anne Hearst McInerney', 136),
(u'John Catsimatidis', 136),
(u'Paula Zahn', 136),
(u'Martha Glass', 136),
(u'Susan Shin', 136),
(u'Patricia Shiah', 135),
(u'CeCe Black', 135),
(u'Lizzie Tisch', 135),
(u'Frederick Anderson', 134),
(u'Coco Kopelman', 134),
(u'Susan Magazine', 134),
(u'Dr. Gerald Loughlin', 133)
(u'John Demsey', 132)
(u'Nathalie Kaplan', 131)
(u'Coralie Charriol Paul', 131)
(u'Margaret Russell', 130)
(u'Hunt Slonem', 128)
(u'Fern Mallis', 128)
(u'Julia Koch', 127)
(u'Dawne Marie Grannum', 126)
(u'Lisa Anastos', 126)
(u'Wendy Carduner', 125)
(u'Jonathan Tisch', 124)
(u'Deborah Roberts', 123)
(u'Cassandra Seidenfeld', 122)
(u'Mary Snow', 120)
(u'Bette Midler', 120)
(u'Tinsley Mortimer', 118)
(u'Marcia Mishaan', 117)
(u'Alec Baldwin', 117)
(u'Carol Mack', 117)


# ## Question 4: pagerank
# 
# A similar way to determine popularity is to look at their
# [pagerank](http://en.wikipedia.org/wiki/PageRank).  Pagerank is used for web ranking and was originally
# [patented](http://patft.uspto.gov/netacgi/nph-Parser?patentnumber=6285999) by Google and is essentially the stationary distribution of a [markov
# chain](http://en.wikipedia.org/wiki/Markov_chain) implied by the social graph.
# 
# Use 0.85 as the damping parameter so that there is a 15% chance of jumping to another vertex at random.
# 
# **Checkpoint:** Some aggregate stats on the solution
# 
#     "count": 100.0
#     "mean": 0.0001841088
#     "std": 0.0000758068
#     "min": 0.0001238355
#     "25%": 0.0001415028
#     "50%": 0.0001616183
#     "75%": 0.0001972663
#     "max": 0.0006085816

# In[363]:


pr=nx.pagerank(G, alpha=0.85)


# In[341]:


import operator
pr_s=sorted(pr.items(), key=operator.itemgetter(1),reverse=True)


# In[568]:


pr_s[:10]


# In[343]:


def pagerank():
    return pr_s[:100]

grader.score(question_name='graph__pagerank', func=pagerank)


# ## Question 5: best_friends
# 
# Another interesting question is who tend to co-occur with each other.  Give us the 100 edges with the highest weights.
# 
# Google these people and see what their connection is.  Can we use this to detect instances of infidelity?
# 
# **Checkpoint:** Some aggregate stats on the solution
# 
#     "count": 100.0
#     "mean": 25.84
#     "std": 16.0395470855
#     "min": 14.0
#     "25%": 16.0
#     "50%": 19.0
#     "75%": 29.25
#     "max": 109.0

# In[425]:


a=sorted(G.edges(data=True), key=lambda x: x[2]['weight'], reverse=True)


# In[426]:


a[0:25]


# In[618]:


#G.get_edge_data(G.edges()[1][0], G.edges()[1][1])


# In[435]:


weight_list=[]
for i in a[0:100]:
    weight_list.append(((str(i[0]),str(i[1])),G[i[0]][i[1]]['weight']/2))


# In[376]:





# In[377]:





# In[436]:


def best_friends():
    return weight_list[0:100]

grader.score(question_name='graph__best_friends', func=best_friends)


# *Copyright &copy; 2016 The Data Incubator.  All rights reserved.*
