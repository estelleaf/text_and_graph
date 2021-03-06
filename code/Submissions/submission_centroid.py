#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Thu Feb 23 11:50:30 2017

@author: estelleaflalo
"""

# import sys pour ajouter le path_to_code pour que import init fonctionne

import sys


from paths import path
import numpy as np
from init import split, init_dic, csv_to_sub
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from numpy.linalg import norm
from sklearn.metrics.pairwise import linear_kernel
#from loss_function import score
#from tfidf_centroid import centroid

##########################
# load some of the files #                           
##########################





path_to_code, path_to_data, path_to_results = path('estelle')
path_to_code, path_to_data, path_to_results = path('domitille')



sys.path.append(path_to_code)



training = pd.read_csv(path_to_data + 'training_set.csv', sep=',', header=0)

training_info = pd.read_csv(path_to_data + 'training_info.csv', sep=',', header=0)

test = pd.read_csv(path_to_data + 'test_set.csv', sep=',', header=0)

test_info= pd.read_csv(path_to_data + 'test_info.csv', sep=',', header=0)



print "Building dictionnaries"

_ , all_senders, _ ,address_books ,_=init_dic(training,training_info)

X_train,Y_train,X_test=csv_to_sub(training,training_info,test,test_info)

predictions_per_sender={}


# set the hyper-parameters like : use_id, etc...
use_idf = True
print 'Parameter use_idf is set to {}'.format(use_idf)
max_df = 0.8
min_df = 0.05
print 'To build the covabulary, the tfidfVectorizer witll use max_df={} and min_df={}'.format(max_df, min_df)


#Creation of centroids for each recipient
def centroid(sender,dataset_info,bow):
    df_tfidf = pd.DataFrame(columns=('recipient','tf_idf'))
    i=0
    for r in [elt[0] for elt in address_books[sender]]:
        info_recip_index=dataset_info[dataset_info['recipients'].str.contains(r)].index.tolist() #"rick.dietz@enron.com"
        bow_recip=bow[info_recip_index]  
        norma=norm(bow_recip, axis=1, ord=2) 
        bow_recip_normzd=bow_recip.astype(np.float) / (norma[:,None]+10**(-7))
        centroid_s_r= np.sum(bow_recip_normzd,axis=0) 
        df_tfidf.loc[i]  = [r, centroid_s_r]
        i+=1
    return df_tfidf
    
for p in range(len(all_senders)):
    
    #Select a sender S
    index=p
    sender=all_senders[index]
    X_train_S=X_train[sender]
    X_dev_S=X_test[sender]
    Y_train_S=Y_train[sender]
    
    
    ##############Create TF IDF vector from mails sent by sender S
    
    
    #vectorize mails sent by a unique sender
    vectorizer_sender = TfidfVectorizer(max_df=max_df, min_df=min_df, stop_words='english',use_idf=use_idf)
    
    #train
    training_info_S=training_info.loc[training_info['mid'].isin(X_train_S)]
    training_info_S=training_info_S.set_index(np.arange(len(training_info_S)))                                                                 
    training_info_S_mat=training_info_S.as_matrix()
    content_train=training_info_S_mat[:,2]
    
    vec_train = vectorizer_sender.fit_transform(content_train)
    bow_train=vec_train.toarray()
    #test
    test_info_S=test_info.loc[test_info['mid'].isin(X_dev_S)] 
    test_info_S=test_info_S.set_index(np.arange(len(test_info_S)))                                                                 
    test_info_S_mat=test_info_S.as_matrix()
    content_test=test_info_S_mat[:,2]
    
    
    vec_test = vectorizer_sender.transform(content_test)
    bow_test=vec_test.toarray()
            
    
        
    centroid_S_df=centroid(sender,training_info_S,bow_train)
    
    centroid_S_arr=np.vstack(centroid_S_df['tf_idf'].as_matrix())
    
    #Similiarity
    rec_pred_S=[]
    for k in range(bow_test.shape[0]):
        mail_test=bow_test[k]
        cosine_similarities = linear_kernel(mail_test[np.newaxis, :], centroid_S_arr).flatten() #np.newaxis cause skl deprecation warning
        similar_centroids = cosine_similarities.argsort()[::-1].tolist()
        rec_pred_S.append(centroid_S_df.ix[similar_centroids[:10]]['recipient'].tolist())

    predictions_per_sender[sender] = []
    for (mid, pred) in zip(X_test[sender], rec_pred_S):
        predictions_per_sender[sender].append([mid, pred])
        # alternative
        # predictions_per_sender[sender].append(mid)
        # predictions_per_sender[sender].append([pred])
    print "Sender Number : " + str(p)
        
    


c=0 # compteur : a priori faut que ce soit 2362
with open(path_to_results + 'predictions_knn_with_use_idf_set_to_{}_max_df_{}_and_min_df_{}.txt'.format(use_idf, max_df, min_df), 'wb') as my_file:
    my_file.write('mid,recipients' + '\n')
    for sender, preds_for_sender in predictions_per_sender.iteritems():

        for (mid, pred) in  preds_for_sender:
            c += 1
            print 'mid',  mid
            print 'pred', pred
            my_file.write(str(mid) + ',' + ' '.join(pred) + '\n')


if c !=2362:
    print 'Pb: the doc shoul have 2362 rows but there are {}'.format(c)
else:
    print 'Ok'

