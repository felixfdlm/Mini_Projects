# -*- coding: utf-8 -*-
"""
Created on Wed Jan 19 18:17:33 2022

@author: Felix
"""

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import requests
import os
import soundfile
import librosa
import numpy as np

SPOTIPY_CLIENT_ID = #Your Client ID here
SPOTIPY_CLIENT_SECRET = #Your Secret Key here

credentials = SpotifyClientCredentials(client_id=SPOTIPY_CLIENT_ID,client_secret=SPOTIPY_CLIENT_SECRET)
spotify = spotipy.Spotify(client_credentials_manager=credentials)

#Example URI for starting scrapesearch
initial_URI = 'spotify:artist:2pH3wEn4eYlMMIIQyKPbVR'

def getTrackURLS(artistURI,spotify_object=spotify):
    previews = {}
    for album in spotify_object.artist_albums(artistURI)['items']:
        album_uri = album['uri']
        for track in spotify_object.album_tracks(album_uri)['items']:
            if track['preview_url'] is not None:
                previews[track['name']] = track['preview_url']
    return previews

def downloadPreviews(previews,folder = ''):
    for track in previews.keys():
        r = requests.get(previews[track],allow_redirects=False)
        with open(os.path.join(folder,track.replace('/','') +'.mp3'), 'wb') as f:
            f.write(r.content)
    

def array2WAV(array,filename,samplerate=22050):
    soundfile.write(filename+'.wav',array, samplerate=samplerate,format='WAV')
    
    
def get_related_artists(uri,spotify_object=spotify):
    artist_list = spotify_object.artist_related_artists(uri)['artists']
    uri_list = [artist['uri'] for artist in artist_list]
    return uri_list

def clean_uri_list(uri_list,tag='metal',spotify_object=spotify):
    return [uri for uri in uri_list if tag in spotify_object.artist(uri)['genres']]

#This function gets the uris of related artists starting at starting_uri with default depth 2.
def deep_Uri_Search(starting_uri,depth=2,spotify_object=spotify):
    uri_list = [starting_uri]
    for i in range(depth):
        newuris = []
        for uri in uri_list:
            newuris = newuris + get_related_artists(uri)
        uri_list = uri_list + newuris
        uri_list = list(set(uri_list))
        uri_list = clean_uri_list(uri_list)
    return uri_list

#This function performs a deep uri search through deep_Uri_Search and downloads every sample track available in all the artists
def deep_Download(starting_uri,depth=2,spotify_object=spotify,folder='tracks'):
    artist_uris = deep_Uri_Search(starting_uri,depth=2)
    track_uris = [getTrackURLS(artist_uri) for artist_uri in artist_uris]
    track_uris = {k:v for element in track_uris for k,v in element.items()}
    downloadPreviews(track_uris,folder=folder)

#This function parses a spectrogram as a [1025,n,2] numpy array     
def create_Spectrogram(track):
    spectrogram_complex = librosa.stft(track)
    real = spectrogram_complex.real.reshape(spectrogram_complex.shape+(1,))
    imaginary = spectrogram_complex.imag.reshape(spectrogram_complex.shape+(1,))
    spectrogram = np.concatenate((real,imaginary),axis = 2)
    return spectrogram

#This function parses all the tracks in a given folder into spectrograms and stores them in spectrogram folder
def tracks2Spectrogram(trackfolder='tracks',spectrogramfolder='spectrograms'):
    parsed_tracks = [parsed_track_id[:-4] for parsed_track_id in os.listdir(spectrogramfolder)]
    for track_id in os.listdir(trackfolder):
        if track_id[:-4] not in parsed_tracks and track_id[-4:] == '.mp3':
            track = librosa.load(os.path.join(trackfolder,track_id))[0]
            spectrogram = create_Spectrogram(track)
            np.save(os.path.join(spectrogramfolder,track_id[:-4])
                    ,spectrogram,allow_pickle=True)
    