#!/usr/bin/env python
# encoding: utf-8
"""
load_tweets.py

Created by Hilary Mason on 2010-04-25.
Copyright (c) 2010 Hilary Mason. All rights reserved.
"""

import sys, os
import pymongo
import tweepy # Twitter API class: http://github.com/joshthecoder/tweepy
from lib import mongodb
from classifiers.classify_tweets import *

class loadTweets(object):
    TWITTER_USERNAME = 'username' # configure me
    TWITTER_PASSWORD = 'password' # configure me
    DB_NAME = 'tweets'
    
    def __init__(self, debug=False):
        self.debug = debug
        self.db = mongodb.connect(self.DB_NAME)
        self.api = self.init_twitter(self.TWITTER_USERNAME, self.TWITTER_PASSWORD)

        last_tweet_id = self.get_last_tweet_id()
        self.fetchTweets(last_tweet_id)
        self.classify_tweets()
        

    def get_last_tweet_id(self):
        for r in self.db[self.DB_NAME].find(fields={'id': True}).sort('id',direction=pymongo.DESCENDING).limit(1):
            return r['id']

    def fetchTweets(self, since_id=None):
        if since_id:
            tweets = self.api.home_timeline(since_id, count=500)
        else:
            tweets = self.api.home_timeline(count=500)
        
        # parse each incoming tweet
        ts = []
        for tweet in tweets: 
            t = {
            'author': tweet.author.screen_name,
            'contributors': tweet.contributors,
            'coordinates': tweet.coordinates,
            'created_at': tweet.created_at,
            # 'destroy': tweet.destroy,
            # 'favorite': tweet.favorite,
            'favorited': tweet.favorited,
            'geo': tweet.geo,
            'id': tweet.id,
            'in_reply_to_screen_name': tweet.in_reply_to_screen_name,
            'in_reply_to_status_id': tweet.in_reply_to_status_id,
            'in_reply_to_user_id': tweet.in_reply_to_user_id,
            # 'parse': tweet.parse,
            # 'parse_list': tweet.parse_list,
            'place': tweet.place,
            # 'retweet': dir(tweet.retweet),
            # 'retweets': dir(tweet.retweets),
            'source': tweet.source,
            # 'source_url': tweet.source_url,
            'text': tweet.text,
            'truncated': tweet.truncated,
            'user': tweet.user.screen_name,
            }
            ts.append(t)
        
        # insert into db
        try:
            self.db[self.DB_NAME].insert(ts)
        except pymongo.errors.InvalidOperation: # no tweets?
            pass
        
        if self.debug:
            print "added %s tweets to the db" % (len(ts))

    def classify_tweets(self):
        classifiers = []
        for active_classifier in active_classifiers:
            c = globals()[active_classifier]()
            classifiers.append(c)

        for r in self.db[self.DB_NAME].find(spec={'topics': {'$exists': False } },fields={'text': True, 'user': True}): # for all unclassified tweets
            topics = {}
            for c in classifiers:
                (topic, score) = c.classify(r['text'])
                topics[topic] = score

            self.db[self.DB_NAME].update({'_id': r['_id']}, {'$set': {'topics': topics }})

    
    # util classes    
    def init_twitter(self, username, password):
        auth = tweepy.BasicAuthHandler(username, password)
        api = tweepy.API(auth)
        return api


if __name__ == '__main__':
    l = loadTweets(debug=True)