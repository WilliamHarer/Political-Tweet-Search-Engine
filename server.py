from flask import Flask, redirect, url_for, render_template, request
from flask_bootstrap import Bootstrap
import whoosh
import json
from whoosh import scoring
from whoosh.index import create_in
from whoosh.index import open_dir
from whoosh.fields import *
from whoosh.qparser import QueryParser
from whoosh.qparser import MultifieldParser, OrGroup
from whoosh import qparser
from whoosh import query

app = Flask(__name__)
#Bootstrap(app)
@app.route('/', methods=['GET','POST'])
def home():
	return render_template('index.html')
@app.route('/senator/', methods=['GET','POST'])
def senator():
	#open Jsons and save as data
	parse=request.args
	senator=parse.get('senator_id')
	#get senator from args
	f=open('./Desktop/Flask-practice/senator.json', encoding='utf-8')
	SenatorData=json.load(f)
	f=open('./Desktop/Flask-practice/followers.json', encoding='utf-8')
	SenatorFollowers=json.load(f)
	f=open('./Desktop/Flask-practice/PhotoList.json', encoding='utf-8')
	photoFile=json.load(f)
	photoFile=photoFile[senator]
	#find photoFiles
	photourl='/static/senatorPhotos/'+str(photoFile)
	#create photo url
	followers=SenatorFollowers[senator]
	#get followers(currently unused?)
	return render_template('SenatorPage.html',data=SenatorData[senator],senator=senator,followers=followers,photo=photourl)
@app.route('/results/', methods=['GET', 'POST'])
def results():
	global mysearch
	if request.method == 'POST':
		data = request.form
		inputs=request.input
		#get data Inputs for debugging
	else:
		data = request.args
	TestQuery = data.get('TestQuery')
	#testQuery
	rtAndLike=data.get('RtAndLikes')
	#get rt and likes
	state=data.get('States')
	#get states for filtering
	f=open('./Desktop/Flask-practice/PhotoList.json', encoding='utf-8')
	photoFile=json.load(f)
	#open photoList
	if "page" in data:
		page=int(data.get('page'))
		#get page number
	else:
		page=1
		#default page
	title,content,pc,u,l,r,ID = mysearch.search(TestQuery,rtAndLike,state,page)
	#get name, tweet,page,user,likes,retweets,ID and render
	return render_template('SearchResults.html', query=TestQuery, results=zip(title, content,u,l,r,ID),pc=pc,page=page,rtAndLike=rtAndLike,state=state,photos=photoFile)
class MyWhooshSearch(object):
    #"""docstring for MyWhooshSearch"""
    def __init__(self):
        super(MyWhooshSearch, self).__init__()
    def search(self, queryEntered, rtAndLike, State,page):
        title=list()
        description=list()
        user=list()
        like=list()
        retweet=list()
        ID=list()
        #all returned values
        with self.indexer.searcher() as search:
            qp = MultifieldParser(['title', 'content'], schema=self.indexer.schema)
            #allow searching of sen name
            user_q = qp.parse(queryEntered)
            #create query
            if State != 'None':
            	#if a state is there create filter
            	filter_q= query.Term('state',State)
            	results= search.search_page(user_q,page,filter=filter_q)
            else:
            	#no filter
            	results=search.search_page(user_q,page)
            	#get pagecount
            PageCount=results.pagecount
            if rtAndLike:
            	#if filtered by rt and like
            	#get the average 
            	#use the new scoring method
            	avg=0
            	count=0
            	newResults=[]
            	for x in results:
            		avg+=int(x['rtAndLike'])
            		count+=1
            	if count!=0:
            		avg=float(avg/count)
            	for x in results:
            		x.score=x.score+float(x.score*float(x['rtAndLike'])/avg)
            		newResults.append(x)
            	newResults=sorted(newResults,key=lambda x: x.score, reverse=True)
            	for x in newResults:
            		title.append(x['title'])
            		description.append(x['content'])
            		user.append(x['user'])
            		like.append(x['like'])
            		retweet.append(x['retweet'])
            		ID.append(x['ID'])
            		print(x.score)
            else:
            	#otherwise go like normal
            	for x in results:
            		title.append(x['title'])
            		description.append(x['content'])
            		user.append(x['user'])
            		like.append(x['like'])
            		retweet.append(x['retweet'])
            		ID.append(x['ID'])
            		print(x.score)
            return title,description,PageCount,user,like,retweet,ID
    def index(self):
    	#schema
        schema = Schema(title=TEXT(stored=True), content=TEXT(stored=True),rtAndLike=TEXT(stored=True),state=KEYWORD(stored=True),user=TEXT(stored=True),ID=TEXT(stored=True),like=TEXT(stored=True),retweet=TEXT(stored=True))
        sample=open("C:/Users/william harer/Desktop/corpus.csv","r",encoding="utf8")
        sample=sample.read()
        sample=sample.splitlines()
        for i in range(len(sample)):
            sample[i]=sample[i].split(",")
        indexer = create_in('C:/Users/william harer/Desktop/Flask-practice/exampleIndex', schema)
        self.indexer = indexer
        writer=indexer.writer()
        for i in range(len(sample)):
        	if len(sample[i])>=8:
        		writer.add_document(title=str(sample[i][3]),content=(sample[i][2]),rtAndLike=(sample[i][5]+sample[i][6]),state=(sample[i][7]),user=(sample[i][8]),ID=(sample[i][9]),like=(sample[i][5]),retweet=(sample[i][6]))
        	else:
        		print(i)
        writer.commit()
if __name__ == '__main__':
	global mysearch
	mysearch = MyWhooshSearch()
	mysearch.index()
	app.run(debug=True)