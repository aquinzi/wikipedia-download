 # -*- coding: utf_8 -*-

from __future__ import unicode_literals, print_function

import requests
from bs4 import BeautifulSoup
import os
import sys
import codecs
import re

def error(msg):
	print(" " + msg)
	exit()

# parse args 
if len(sys.argv) < 2:
	error("Must specify input and output")

if "-h" in sys.argv or "help" in sys.argv:
	print ("\n Specify input_file output [options]")
	print (" Options:")
	print ("          -f    first language. Will look at articles from this. Defaults to 'en'")
	print ("          -t    language to look translations to")
	exit()

if not "-t" in sys.argv:
	error("Specify article translation")
	
args = sys.argv[1:]

INPUT_FILE    = args[0]
OUTPUT_FOLDER = args[1]

if '-f' in args:
	INPUT_LANG = args[args.index("-f") + 1]
	if len(INPUT_LANG.split(",")) > 1:
		error("Invalid input language")
else:
	INPUT_LANG = 'en'

OUTPUT_LANG = args[args.index("-t") + 1]
if len(OUTPUT_LANG.split(",")) > 1:
	error("Invalid output language")

if not os.path.isfile(INPUT_FILE):
	error("Input file invalid")

if not os.path.isdir(OUTPUT_FOLDER):
	error("Output folder invalid")


# ------------------- 
#  A bit of config
# --------------------- 

PRINT_PARAMS     = {'printable': 'yes'}
SEARCH_PARAMS    = {'action': 'query', 'list': 'search', 'srlimit': '5', 'format': 'json'}
LANGS_PARAMS     = {'action': 'parse', 'format': 'json', 'prop': 'langlinks'}
EXISTANCE_PARAMS = {'action': 'query', 'format': 'json', 'redirects': True, 'prop':'info', 'inprop':'url'}

WIKIPEDIA_URL  = "http://{lang}.wikipedia.org/"
WIKIPEDIA_BASE = "http://{lang}.wikipedia.org/".format(lang=INPUT_LANG)
WIKIPEDIA_API  = WIKIPEDIA_BASE + "w/api.php"

CSS_FILE = """
	.referencetooltip{position:absolute;list-style:none;list-style-image:none;opacity:0;font-size:10px;margin:0;z-index:5;padding:0}
	.referencetooltip li{border:#080086 2px solid;max-width:260px;padding:10px 8px 13px 8px;margin:0px;background-color:#F7F7F7;box-shadow:2px 4px 2px rgba(0,0,0,0.3);-moz-box-shadow:2px 4px 2px rgba(0,0,0,0.3);-webkit-box-shadow:2px 4px 2px rgba(0,0,0,0.3)}
	.referencetooltip li+li{margin-left:7px;margin-top:-2px;border:0;padding:0;height:3px;width:0px;background-color:transparent;box-shadow:none;-moz-box-shadow:none;-webkit-box-shadow:none;border-top:12px #080086 solid;border-right:7px transparent solid;border-left:7px transparent solid}
	.referencetooltip>li+li::after{content:'';border-top:8px #F7F7F7 solid;border-right:5px transparent solid;border-left:5px transparent solid;margin-top:-12px;margin-left:-5px;z-index:1;height:0px;width:0px;display:block}
	.client-js body .referencetooltip li li{border:none;box-shadow:none;-moz-box-shadow:none;-webkit-box-shadow:none;height:auto;width:auto;margin:auto;padding:0;position:static}
	.RTflipped{padding-top:13px}
	.referencetooltip.RTflipped li+li{position:absolute;top:2px;border-top:0;border-bottom:12px #080086 solid}
	.referencetooltip.RTflipped li+li::after{border-top:0;border-bottom:8px #F7F7F7 solid;position:absolute;margin-top:7px}
	.RTsettings:hover{opacity:1;filter:alpha(opacity=100)}
	.RTTarget{border:#080086 2px solid}
	sup.reference{unicode-bidi:-moz-isolate;unicode-bidi:-webkit-isolate;unicode-bidi:isolate}
	.client-nojs #ca-ve-edit,.ve-not-available #ca-ve-edit,.noprint,.mw-jump,div.top,div#column-one,#colophon,.tochidden,li#viewcount,li#about,li#disclaimer,li#mobileview,li#privacy,tr.mw-metadata-show-hide-extended,span.mw-filepage-other-resolutions,#filetoc,.usermessage,.patrollink{display:none}
	a.stub,a.new{color:#ba0000;text-decoration:none}
	#toc{border:1px solid #aaaaaa;background-color:#f9f9f9;padding:5px;display:-moz-inline-block;display:inline-block;display:table;zoom:1;*display:inline}
	div.floatright{float:right;clear:right;position:relative;margin:0.5em 0 0.8em 1.4em}
	div.floatright p, div.floatleft p{font-style:italic}
	div.floatleft{float:left;clear:left;position:relative;margin:0.5em 1.4em 0.8em 0}
	div.center{text-align:center}
	div.thumb{border:none;width:auto;margin-top:0.5em;margin-bottom:0.8em;background-color:transparent}
	div.thumbinner{padding:3px !important;background-color:White;font-size:94%;text-align:center;overflow:hidden}
	html .thumbimage, div.thumbinner{border:1px solid #cccccc}
	html .thumbcaption{border:none;text-align:left;line-height:1.4em;padding:3px !important;font-size:94%}
	div.magnify{display:none}
	div.tright{float:right;clear:right;margin:0.5em 0 0.8em 1.4em}
	div.tleft{float:left;clear:left;margin:0.5em 1.4em 0.8em 0}
	img.thumbborder{border:1px solid #dddddd}
	table.rimage{float:right;width:1pt;position:relative;margin-left:1em;margin-bottom:1em;text-align:center}
	body{background:white;color:black;margin:0;padding:0}
	ul{list-style-type:square}
	#content{background:none;border:none !important;padding:0 !important;margin:0 !important;direction:ltr}
	#footer{background :white;color :black;margin-top:1em;border-top:1px solid #AAA;direction:ltr}
	h1,h2,h3,h4,h5,h6{font-weight:bold}
	dt{font-weight:bold}
	p{margin:1em 0;line-height:1.2em}
	pre,.mw-code{border:1pt dashed black;white-space:pre;font-size:8pt;overflow:auto;padding:1em 0;background:white;color:black}
	table.listing,table.listing td{border:1pt solid black;border-collapse:collapse}
	a{color:black !important;background:none !important;padding:0 !important}
	a:link,a:visited{color:#520;background:transparent;text-decoration:underline}
	#content a.external.text:after,#content a.external.autonumber:after{content:" (" attr(href) ")"}
	#globalWrapper{width:100% !important;min-width:0 !important}
	#content{background:white;color:black}
	#column-content{margin:0 !important}
	#column-content #content{padding:1em;margin:0 !important}
	a,a.external,a.new,a.stub{color:black !important;text-decoration:none !important}
	a,a.external,a.new,a.stub{color:inherit !important;text-decoration:inherit !important}
	img{border:none;vertical-align:middle}
	span.texhtml{font-family:serif}
	#siteNotice{display:none}
	li.gallerybox{vertical-align:top;display:-moz-inline-box;display:inline-block}
	ul.gallery,li.gallerybox{zoom:1;*display:inline}
	ul.gallery{margin:2px;padding:2px;display:block}
	li.gallerycaption{font-weight:bold;text-align:center;display:block;word-wrap:break-word}
	li.gallerybox div.thumb{text-align:center;border:1px solid #ccc;margin:2px}
	div.gallerytext{overflow:hidden;font-size:94%;padding:2px 4px;word-wrap:break-word}
	table.diff{background:white}
	td.diff-otitle,td.diff-ntitle{background:#ffffff}
	td.diff-addedline{background:#ccffcc;font-size:smaller;border:solid 2px black}
	td.diff-deletedline{background:#ffffaa;font-size:smaller;border:dotted 2px black}
	td.diff-context{background:#eeeeee;font-size:smaller}
	.diffchange{color:silver;font-weight:bold;text-decoration:underline}
	table.wikitable,table.mw_metadata{margin:1em 0;border:1px #aaa solid;background:white;border-collapse:collapse}
	table.wikitable > tr > th,table.wikitable > tr > td,table.wikitable > * > tr > th,table.wikitable > * > tr > td,.mw_metadata th,.mw_metadata td{border:1px #aaa solid;padding:0.2em}
	table.wikitable > tr > th,table.wikitable > * > tr > th,.mw_metadata th{text-align:center;background:white;font-weight:bold}
	table.wikitable > caption,.mw_metadata caption{font-weight:bold}
	a.sortheader{margin:0 0.3em}
	.wikitable,.thumb,img{page-break-inside:avoid}
	h2,h3,h4,h5,h6{page-break-after:avoid}
	p{widows:3;orphans:3}
	.catlinks ul{display:inline;margin:0;padding:0;list-style:none;list-style-type:none;list-style-image:none;vertical-align:middle !ie}
	.catlinks li{display:inline-block;line-height:1.15em;padding:0 .4em;border-left:1px solid #AAA;margin:0.1em 0;zoom:1;display:inline !ie}
	.catlinks li:first-child{padding-left:.2em;border-left:none}
	@media screen{
		html{font-size:1em}
	html,body{height:100%;margin:0;padding:0;font-family:sans-serif}
	body{background-color:#f6f6f6;font-size:1em}
	div#content{line-height:1.5em;margin-left:10em;padding:1.25em 1.5em 1.5em 1.5em;border:1px solid #a7d7f9;border-right-width:0;margin-top:-1px;background-color:white;color:black;direction:ltr}
	div.emptyPortlet{display:none}
	ul{list-style-type:disc;list-style-image:url(data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAUAAAANAQMAAABb8jbLAAAABlBMVEX///8AUow5QSOjAAAAAXRSTlMAQObYZgAAABNJREFUCB1jYEABBQw/wLCAgQEAGpIDyT0IVcsAAAAASUVORK5CYII=);list-style-image:url(//bits.wikimedia.org/static-1.23wmf11/skins/vector/images/bullet-icon.png?2014-01-16T16:15:00Z) !ie}
	pre,.mw-code{line-height:1.3em}
	#siteNotice{font-size:0.8em}
	#firstHeading{padding-top:0;margin-top:0;font-size:1.6em}
	.redirectText{font-size:140%}
	.redirectMsg img{vertical-align:text-bottom}
	#bodyContent{position:relative;width:100%;line-height:1.5em;font-size:0.8em}
	.tipsy{font-size:0.8em}
	body.vector-animateLayout div#content,body.vector-animateLayout div#footer,body.vector-animateLayout #left-navigation{-webkit-transition:margin-left 250ms,padding 250ms;transition:margin-left 250ms,padding 250ms}
	body.vector-animateLayout #mw-panel{-webkit-transition:padding-right 250ms;transition:padding-right 250ms}
	body.vector-animateLayout #p-search{-webkit-transition:margin-right 250ms;transition:margin-right 250ms}
	body.vector-animateLayout #p-personal{-webkit-transition:right 250ms;transition:right 250ms}
	body.vector-animateLayout #mw-head-base{-webkit-transition:margin-left 250ms;transition:margin-left 250ms}
	#mw-panel.collapsible-nav .portal{background-position:left top;background-repeat:no-repeat;background-image:url(data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAIwAAAABCAAAAAAphRnkAAAAJ0lEQVQIW7XFsQEAIAyAMPD/b7uLWz8wS5youFW1UREfiIpH1Q2VBz7fGPS1dOGeAAAAAElFTkSuQmCC);background-image:url(//bits.wikimedia.org/static-1.23wmf11/skins/vector/images/portal-break.png?2014-01-16T16:15:00Z) !ie;padding:0.25em 0 !important;margin:-11px 9px 10px 11px}
	#mw-panel.collapsible-nav .portal h3{font-size:0.75em;color:#4D4D4D;font-weight:normal;background-position:left center;background-repeat:no-repeat;background-image:url(//bits.wikimedia.org/static-1.23wmf11/skins/vector/images/arrow-expanded.png?2014-01-16T16:15:00Z);background-image:-webkit-linear-gradient(transparent,transparent),url(//bits.wikimedia.org/static-1.23wmf11/skins/vector/images/arrow-expanded.svg?2014-01-16T16:15:00Z);background-image:linear-gradient(transparent,transparent),url(//bits.wikimedia.org/static-1.23wmf11/skins/vector/images/arrow-expanded.svg?2014-01-16T16:15:00Z)!ie;padding:4px 0 3px 1.5em;margin-bottom:0}
	#mw-panel.collapsible-nav .portal h3:hover{cursor:pointer;text-decoration:none}
	#mw-panel.collapsible-nav .portal h3 a{color:#4D4D4D;text-decoration:none}
	#mw-panel.collapsible-nav .portal .body{margin:0 0 0 1.25em;background-image:none !important;padding-top:0;display:none}
	#mw-panel.collapsible-nav .portal .body ul li{padding:0.25em 0}
	#mw-panel.collapsible-nav .portal.first{background-image:none;margin-top:0}
	#mw-panel.collapsible-nav .portal.first h3{display:none}
	#mw-panel.collapsible-nav .portal.persistent .body{display:block;margin-left:0.5em}
	#mw-panel.collapsible-nav .portal.persistent h3{background-image:none !important;padding-left:0.7em;cursor:default}
	#mw-panel.collapsible-nav .portal.collapsed h3{color:#0645AD;background-position:left center;background-repeat:no-repeat;background-image:url(//bits.wikimedia.org/static-1.23wmf11/skins/vector/images/arrow-collapsed-ltr.png?2014-01-16T16:15:00Z);background-image:-webkit-linear-gradient(transparent,transparent),url(//bits.wikimedia.org/static-1.23wmf11/skins/vector/images/arrow-collapsed-ltr.svg?2014-01-16T16:15:00Z);background-image:linear-gradient(transparent,transparent),url(//bits.wikimedia.org/static-1.23wmf11/skins/vector/images/arrow-collapsed-ltr.svg?2014-01-16T16:15:00Z)!ie;margin-bottom:0}
	#mw-panel.collapsible-nav .portal.collapsed h3:hover{text-decoration:underline}
	#mw-panel.collapsible-nav .portal.collapsed h3 a{color:#0645AD}
	#mw-navigation h2{position:absolute;top:-9999px}
	#mw-page-base{height:5em;background-color:white;background-image:url(data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAAsCAIAAAArRUU2AAAAOklEQVR42lWNWwoAQAgCde9/59mgF30EOmgKeJLmUHjGpzbBdXnl6F5oV5/J9e/tr/czydmt7RT33floBCM5ZQLqdwAAAABJRU5ErkJggg==);background-image:url(//bits.wikimedia.org/static-1.23wmf11/skins/vector/images/page-fade.png?2014-01-16T16:15:00Z) !ie;background-position:bottom left;background-repeat:repeat-x}
	#mw-head-base{margin-top:-5em;margin-left:10em;height:5em}
	div#mw-head{position:absolute;top:0;right:0;width:100%}
	div#mw-head h3{margin:0;padding:0}
	div#mw-panel{font-size:inherit;position:absolute;top:160px;padding-top:1em;width:10em;left:0}
	div#mw-panel div.portal{padding-bottom:1.5em;direction:ltr}
	div#mw-panel div.portal h3{font-weight:normal;color:#444;padding:0 1.75em 0.25em 0.25em;cursor:default;border:none;font-size:0.75em}
	div#mw-panel div.portal div.body{padding-top:0.5em;margin:0 0 0 1.25em;background-image:url(data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAIwAAAABCAAAAAAphRnkAAAAJ0lEQVQIW7XFsQEAIAyAMPD/b7uLWz8wS5youFW1UREfiIpH1Q2VBz7fGPS1dOGeAAAAAElFTkSuQmCC);background-image:url(//bits.wikimedia.org/static-1.23wmf11/skins/vector/images/portal-break.png?2014-01-16T16:15:00Z) !ie;background-repeat:no-repeat;background-position:top left}
	div#mw-panel div.portal div.body ul{list-style-type:none;list-style-image:none;padding:0;margin:0}
	div#mw-panel div.portal div.body ul li{line-height:1.125em;padding:0;padding-bottom:0.5em;margin:0;font-size:0.75em;word-wrap:break-word}
	div#mw-panel div.portal div.body ul li a{color:#0645ad}
	div#mw-panel div.portal div.body ul li a:visited{color:#0b0080}
	div#footer{margin-left:10em;margin-top:0;padding:0.75em;direction:ltr}
	div#footer ul{list-style-type:none;list-style-image:none;margin:0;padding:0}
	div#footer ul li{margin:0;padding:0;padding-top:0.5em;padding-bottom:0.5em;color:#333;font-size:0.7em}
	div#footer #footer-icons{float:right}
	div#footer #footer-icons li{float:left;margin-left:0.5em;line-height:2em;text-align:right}
	div#footer #footer-info li{line-height:1.4em}
	div#footer #footer-places li{float:left;margin-right:1em;line-height:2em}
	body.ltr div#footer #footer-places{float:left}
	.skin-vector .mw-notification-area{font-size:0.8em}
	.skin-vector .mw-notification-area-layout{top:7em}
	.skin-vector .mw-notification{background-color:#fff;background-color:rgba(255,255,255,0.93);padding:0.75em 1.5em;border:solid 1px #a7d7f9;border-radius:0.75em;-webkit-box-shadow:0 2px 10px 0 rgba(0,0,0,0.125);box-shadow:0 2px 10px 0 rgba(0,0,0,0.125)}
	div#content a.external{background-position:center right;background-repeat:no-repeat;background-image:url(//bits.wikimedia.org/static-1.23wmf11/skins/vector/images/external-link-ltr-icon.png?2014-01-16T16:15:00Z);background-image:-webkit-linear-gradient(transparent,transparent),url(//bits.wikimedia.org/static-1.23wmf11/skins/vector/images/external-link-ltr-icon.svg?2014-01-16T16:15:00Z);background-image:linear-gradient(transparent,transparent),url(//bits.wikimedia.org/static-1.23wmf11/skins/vector/images/external-link-ltr-icon.svg?2014-01-16T16:15:00Z)!ie;padding-right:13px}
	div#content a.external[href ^="https://"],.link-https{background-position:center right;background-repeat:no-repeat;background-image:url(//bits.wikimedia.org/static-1.23wmf11/skins/vector/images/lock-icon.png?2014-01-16T16:15:00Z);background-image:-webkit-linear-gradient(transparent,transparent),url(//bits.wikimedia.org/static-1.23wmf11/skins/vector/images/lock-icon.svg?2014-01-16T16:15:00Z);background-image:linear-gradient(transparent,transparent),url(//bits.wikimedia.org/static-1.23wmf11/skins/vector/images/lock-icon.svg?2014-01-16T16:15:00Z)!ie;padding-right:13px}
	div#content a.external[href ^="mailto:"],.link-mailto{background-position:center right;background-repeat:no-repeat;background-image:url(//bits.wikimedia.org/static-1.23wmf11/skins/vector/images/mail-icon.png?2014-01-16T16:15:00Z);background-image:-webkit-linear-gradient(transparent,transparent),url(//bits.wikimedia.org/static-1.23wmf11/skins/vector/images/mail-icon.svg?2014-01-16T16:15:00Z);background-image:linear-gradient(transparent,transparent),url(//bits.wikimedia.org/static-1.23wmf11/skins/vector/images/mail-icon.svg?2014-01-16T16:15:00Z)!ie;padding-right:13px}
	div#content a.external[href ^="news:"]{background-position:center right;background-repeat:no-repeat;background-image:url(//bits.wikimedia.org/static-1.23wmf11/skins/vector/images/news-icon.png?2014-01-16T16:15:00Z);background-image:-webkit-linear-gradient(transparent,transparent),url(//bits.wikimedia.org/static-1.23wmf11/skins/vector/images/news-icon.svg?2014-01-16T16:15:00Z);background-image:linear-gradient(transparent,transparent),url(//bits.wikimedia.org/static-1.23wmf11/skins/vector/images/news-icon.svg?2014-01-16T16:15:00Z)!ie;padding-right:13px}
	div#content a.external[href ^="ftp://"],.link-ftp{background-position:center right;background-repeat:no-repeat;background-image:url(//bits.wikimedia.org/static-1.23wmf11/skins/vector/images/file-icon.png?2014-01-16T16:15:00Z);background-image:-webkit-linear-gradient(transparent,transparent),url(//bits.wikimedia.org/static-1.23wmf11/skins/vector/images/file-icon.svg?2014-01-16T16:15:00Z);background-image:linear-gradient(transparent,transparent),url(//bits.wikimedia.org/static-1.23wmf11/skins/vector/images/file-icon.svg?2014-01-16T16:15:00Z)!ie;padding-right:13px}
	div#content a.external[href ^="irc://"],div#content a.external[href ^="ircs://"],.link-irc{background-position:center right;background-repeat:no-repeat;background-image:url(//bits.wikimedia.org/static-1.23wmf11/skins/vector/images/talk-icon.png?2014-01-16T16:15:00Z);background-image:-webkit-linear-gradient(transparent,transparent),url(//bits.wikimedia.org/static-1.23wmf11/skins/vector/images/talk-icon.svg?2014-01-16T16:15:00Z);background-image:linear-gradient(transparent,transparent),url(//bits.wikimedia.org/static-1.23wmf11/skins/vector/images/talk-icon.svg?2014-01-16T16:15:00Z)!ie;padding-right:13px}
	div#content a.external[href $=".ogg"],div#content a.external[href $=".OGG"],div#content a.external[href $=".mid"],div#content a.external[href $=".MID"],div#content a.external[href $=".midi"],div#content a.external[href $=".MIDI"],div#content a.external[href $=".mp3"],div#content a.external[href $=".MP3"],div#content a.external[href $=".wav"],div#content a.external[href $=".WAV"],div#content a.external[href $=".wma"],div#content a.external[href $=".WMA"],.link-audio{background-position:center right;background-repeat:no-repeat;background-image:url(//bits.wikimedia.org/static-1.23wmf11/skins/vector/images/audio-icon.png?2014-01-16T16:15:00Z);background-image:-webkit-linear-gradient(transparent,transparent),url(//bits.wikimedia.org/static-1.23wmf11/skins/vector/images/audio-icon.svg?2014-01-16T16:15:00Z);background-image:linear-gradient(transparent,transparent),url(//bits.wikimedia.org/static-1.23wmf11/skins/vector/images/audio-icon.svg?2014-01-16T16:15:00Z)!ie;padding-right:13px}
	div#content a.external[href $=".ogm"],div#content a.external[href $=".OGM"],div#content a.external[href $=".avi"],div#content a.external[href $=".AVI"],div#content a.external[href $=".mpeg"],div#content a.external[href $=".MPEG"],div#content a.external[href $=".mpg"],div#content a.external[href $=".MPG"],.link-video{background-position:center right;background-repeat:no-repeat;background-image:url(//bits.wikimedia.org/static-1.23wmf11/skins/vector/images/video-icon.png?2014-01-16T16:15:00Z);background-image:-webkit-linear-gradient(transparent,transparent),url(//bits.wikimedia.org/static-1.23wmf11/skins/vector/images/video-icon.svg?2014-01-16T16:15:00Z);background-image:linear-gradient(transparent,transparent),url(//bits.wikimedia.org/static-1.23wmf11/skins/vector/images/video-icon.svg?2014-01-16T16:15:00Z)!ie;padding-right:13px}
	div#content a.external[href $=".pdf"],div#content a.external[href $=".PDF"],div#content a.external[href *=".pdf#"],div#content a.external[href *=".PDF#"],div#content a.external[href *=".pdf?"],div#content a.external[href *=".PDF?"],.link-document{background-position:center right;background-repeat:no-repeat;background-image:url(//bits.wikimedia.org/static-1.23wmf11/skins/vector/images/document-icon.png?2014-01-16T16:15:00Z);background-image:-webkit-linear-gradient(transparent,transparent),url(//bits.wikimedia.org/static-1.23wmf11/skins/vector/images/document-icon.svg?2014-01-16T16:15:00Z);background-image:linear-gradient(transparent,transparent),url(//bits.wikimedia.org/static-1.23wmf11/skins/vector/images/document-icon.svg?2014-01-16T16:15:00Z)!ie;padding-right:13px}
	}
	@media screen and (min-width:982px){
	div#content{margin-left:11em;padding:1.5em 1.5em 1.5em 1.75em}
	div#footer{margin-left:11em;padding:1.25em}
	#mw-panel{padding-left:0.5em}
	#mw-head-base{margin-left:11em}
	}

	/* cache key: enwiki:resourceloader:filter:minify-css:7:ba9bdbd42d67749e1b5f0f985d283405 */


	dfn{font-style:inherit}
	sup,sub{line-height:1em}
	#interwiki-completelist{font-weight:bold}
	body.action-info :target{background:#DEF}
	ol.references,div.reflist,div.refbegin{font-size:90%;margin-bottom:0.5em}
	div.refbegin-100{font-size:100%}
	div.reflist ol.references{font-size:100%;list-style-type:inherit}
	div.columns{margin-top:0.3em}
	div.columns dl,div.columns ol,div.columns ul{margin-top:0}
	div.columns li,div.columns dd dd{-webkit-column-break-inside:avoid;page-break-inside:avoid;break-inside:avoid-column}
	ol.references li:target,sup.reference:target,span.citation:target{background-color:#DEF}
	sup.reference{font-weight:normal;font-style:normal}
	span.brokenref{display:none}
	.citation{word-wrap:break-word}
	@media screen,handheld{.citation *.printonly{display:none}}
	.flowlist ul{overflow-x:hidden;margin-left:0em;padding-left:1.6em}
	.flowlist ol{overflow-x:hidden;margin-left:0em;padding-left:3.2em}
	.flowlist dl{overflow-x:hidden}
	.hlist dl,.hlist ol,.hlist ul{margin:0;padding:0}
	.hlist dd,.hlist dt,.hlist li{margin:0;display:inline}
	.hlist dl dl,.hlist dl ol,.hlist dl ul,.hlist ol dl,.hlist ol ol,.hlist ol ul,.hlist ul dl,.hlist ul ol,.hlist ul ul{display:inline}
	.hlist dt:after{content:":"}
	.hlist dd:after,.hlist li:after{content:" · ";font-weight:bold}
	.hlist dd:last-child:after,.hlist dt:last-child:after,.hlist li:last-child:after{content:none}
	.hlist dd.hlist-last-child:after,.hlist dt.hlist-last-child:after,.hlist li.hlist-last-child:after{content:none}
	.hlist dd dd:first-child:before,.hlist dd dt:first-child:before,.hlist dd li:first-child:before,.hlist dt dd:first-child:before,.hlist dt dt:first-child:before,.hlist dt li:first-child:before,.hlist li dd:first-child:before,.hlist li dt:first-child:before,.hlist li li:first-child:before{content:" (";font-weight:normal}
	.hlist dd dd:last-child:after,.hlist dd dt:last-child:after,.hlist dd li:last-child:after,.hlist dt dd:last-child:after,.hlist dt dt:last-child:after,.hlist dt li:last-child:after,.hlist li dd:last-child:after,.hlist li dt:last-child:after,.hlist li li:last-child:after{content:") ";font-weight:normal}
	.hlist dd dd.hlist-last-child:after,.hlist dd dt.hlist-last-child:after,.hlist dd li.hlist-last-child:after,.hlist dt dd.hlist-last-child:after,.hlist dt dt.hlist-last-child:after,.hlist dt li.hlist-last-child:after,.hlist li dd.hlist-last-child:after,.hlist li dt.hlist-last-child:after,.hlist li li.hlist-last-child:after{content:") ";font-weight:normal}
	.hlist ol{counter-reset:listitem}
	.hlist ol > li{counter-increment:listitem}
	.hlist ol > li:before{content:" " counter(listitem) " "}
	.hlist dd ol > li:first-child:before,.hlist dt ol > li:first-child:before,.hlist li ol > li:first-child:before{content:" (" counter(listitem) " "}
	.plainlist ul{line-height:inherit;list-style:none none;margin:0}
	.plainlist ul li{margin-bottom:0}
	.navbox{border:1px solid #aaa;width:100%;margin:auto;clear:both;font-size:88%;text-align:center;padding:1px}
	.navbox-inner,.navbox-subgroup{width:100%}
	.navbox-group,.navbox-title,.navbox-abovebelow{padding:0.25em 1em;line-height:1.5em;text-align:center}
	th.navbox-group{white-space:nowrap;text-align:right}
	.navbox,.navbox-subgroup{background:#fdfdfd}
	.navbox-list{line-height:1.8em;border-color:#fdfdfd}
	.navbox th,.navbox-title{background:#ccccff}
	.navbox-abovebelow,th.navbox-group,.navbox-subgroup .navbox-title{background:#ddddff}
	.navbox-subgroup .navbox-group,.navbox-subgroup .navbox-abovebelow{background:#e6e6ff}
	.navbox-even{background:#f7f7f7}
	.navbox-odd{background:transparent}
	table.navbox + table.navbox{margin-top:-1px}
	.navbox .hlist td dl,.navbox .hlist td ol,.navbox .hlist td ul,.navbox td.hlist dl,.navbox td.hlist ol,.navbox td.hlist ul{padding:0.125em 0}
	ol + table.navbox,ul + table.navbox{margin-top:0.5em}
	.navbar{display:inline;font-size:88%;font-weight:normal}
	.navbar ul{display:inline;white-space:nowrap}
	.navbar li{word-spacing:-0.125em}
	.navbar.mini li span{font-variant:small-caps}
	.infobox .navbar{font-size:100%}
	.navbox .navbar{display:block;font-size:100%}
	.navbox-title .navbar{float:left;text-align:left;margin-right:0.5em;width:6em}
	.collapseButton{float:right;font-weight:normal;margin-left:0.5em;text-align:right;width:auto}
	.navbox .collapseButton{width:6em}
	.mw-collapsible-toggle{font-weight:normal;text-align:right}
	.navbox .mw-collapsible-toggle{width:6em}
	.infobox{border:1px solid #aaa;background-color:#f9f9f9;color:black;margin:0.5em 0 0.5em 1em;padding:0.2em;float:right;clear:right;text-align:left;font-size:88%;line-height:1.5em}
	.infobox caption{font-size:125%;font-weight:bold}
	.infobox td,.infobox th{vertical-align:top}
	.infobox.bordered{border-collapse:collapse}
	.infobox.bordered td,.infobox.bordered th{border:1px solid #aaa}
	.infobox.bordered .borderless td,.infobox.bordered .borderless th{border:0}
	.infobox.sisterproject{width:20em;font-size:90%}
	.infobox.standard-talk{border:1px solid #c0c090;background-color:#f8eaba}
	.infobox.standard-talk.bordered td,.infobox.standard-talk.bordered th{border:1px solid #c0c090}
	.infobox.bordered .mergedtoprow td,.infobox.bordered .mergedtoprow th{border:0;border-top:1px solid #aaa;border-right:1px solid #aaa}
	.infobox.bordered .mergedrow td,.infobox.bordered .mergedrow th{border:0;border-right:1px solid #aaa}
	.infobox.geography{border-collapse:collapse;line-height:1.2em;font-size:90%}
	.infobox.geography td,.infobox.geography th{border-top:1px solid #aaa;padding:0.4em 0.6em 0.4em 0.6em}
	.infobox.geography .mergedtoprow td,.infobox.geography .mergedtoprow th{border-top:1px solid #aaa;padding:0.4em 0.6em 0.2em 0.6em}
	.infobox.geography .mergedrow td,.infobox.geography .mergedrow th{border:0;padding:0 0.6em 0.2em 0.6em}
	.infobox.geography .mergedbottomrow td,.infobox.geography .mergedbottomrow th{border-top:0;border-bottom:1px solid #aaa;padding:0 0.6em 0.4em 0.6em}
	.infobox.geography .maptable td,.infobox.geography .maptable th{border:0;padding:0}
	.wikitable.plainrowheaders th[scope=row]{font-weight:normal;text-align:left}
	.wikitable td ul,.wikitable td ol,.wikitable td dl{text-align:left}
	.wikitable.hlist td ul,.wikitable.hlist td ol,.wikitable.hlist td dl{text-align:inherit}
	div.listenlist{background:url(//upload.wikimedia.org/wikipedia/commons/3/3f/Gnome_speakernotes_30px.png);padding-left:40px}
	table.mw-hiero-table td{vertical-align:middle}
	div.medialist{min-height:50px;margin:1em;background-position:top left;background-repeat:no-repeat}
	div.medialist ul{list-style-type:none;list-style-image:none;margin:0}
	div.medialist ul li{padding-bottom:0.5em}
	div.medialist ul li li{font-size:91%;padding-bottom:0}
	div#content a[href$=".pdf"].external,div#content a[href*=".pdf?"].external,div#content a[href*=".pdf#"].external,div#content a[href$=".PDF"].external,div#content a[href*=".PDF?"].external,div#content a[href*=".PDF#"].external,div#mw_content a[href$=".pdf"].external,div#mw_content a[href*=".pdf?"].external,div#mw_content a[href*=".pdf#"].external,div#mw_content a[href$=".PDF"].external,div#mw_content a[href*=".PDF?"].external,div#mw_content a[href*=".PDF#"].external{background:url(//upload.wikimedia.org/wikipedia/commons/2/23/Icons-mini-file_acrobat.gif) no-repeat right;padding-right:18px}
	div#content span.PDFlink a,div#mw_content span.PDFlink a{background:url(//upload.wikimedia.org/wikipedia/commons/2/23/Icons-mini-file_acrobat.gif) no-repeat right;padding-right:18px}
	div.columns-2 div.column{float:left;width:50%;min-width:300px}
	div.columns-3 div.column{float:left;width:33.3%;min-width:200px}
	div.columns-4 div.column{float:left;width:25%;min-width:150px}
	div.columns-5 div.column{float:left;width:20%;min-width:120px}
	.messagebox{border:1px solid #aaa;background-color:#f9f9f9;width:80%;margin:0 auto 1em auto;padding:.2em}
	.messagebox.merge{border:1px solid #c0b8cc;background-color:#f0e5ff;text-align:center}
	.messagebox.cleanup{border:1px solid #9f9fff;background-color:#efefff;text-align:center}
	.messagebox.standard-talk{border:1px solid #c0c090;background-color:#f8eaba;margin:4px auto}
	.mbox-inside .standard-talk,.messagebox.nested-talk{border:1px solid #c0c090;background-color:#f8eaba;width:100%;margin:2px 0;padding:2px}
	.messagebox.small{width:238px;font-size:85%;float:right;clear:both;margin:0 0 1em 1em;line-height:1.25em}
	.messagebox.small-talk{width:238px;font-size:85%;float:right;clear:both;margin:0 0 1em 1em;line-height:1.25em;background:#F8EABA}
	th.mbox-text,td.mbox-text{border:none;padding:0.25em 0.9em;width:100%}
	td.mbox-image{border:none;padding:2px 0 2px 0.9em;text-align:center}
	td.mbox-imageright{border:none;padding:2px 0.9em 2px 0;text-align:center}
	td.mbox-empty-cell{border:none;padding:0px;width:1px}
	table.ambox{margin:0px 10%;border:1px solid #aaa;border-left:10px solid #1e90ff;background:#fbfbfb}
	table.ambox + table.ambox{margin-top:-1px}
	.ambox th.mbox-text,.ambox td.mbox-text{padding:0.25em 0.5em}
	.ambox td.mbox-image{padding:2px 0 2px 0.5em}
	.ambox td.mbox-imageright{padding:2px 0.5em 2px 0}
	table.ambox-notice{border-left:10px solid #1e90ff}
	table.ambox-speedy{border-left:10px solid #b22222;background:#fee}
	table.ambox-delete{border-left:10px solid #b22222}
	table.ambox-content{border-left:10px solid #f28500}
	table.ambox-style{border-left:10px solid #f4c430}
	table.ambox-move{border-left:10px solid #9932cc}
	table.ambox-protection{border-left:10px solid #bba}
	table.imbox{margin:4px 10%;border-collapse:collapse;border:3px solid #1e90ff;background:#fbfbfb}
	.imbox .mbox-text .imbox{margin:0 -0.5em;display:block}
	.mbox-inside .imbox{margin:4px}
	table.imbox-notice{border:3px solid #1e90ff}
	table.imbox-speedy{border:3px solid #b22222;background:#fee}
	table.imbox-delete{border:3px solid #b22222}
	table.imbox-content{border:3px solid #f28500}
	table.imbox-style{border:3px solid #f4c430}
	table.imbox-move{border:3px solid #9932cc}
	table.imbox-protection{border:3px solid #bba}
	table.imbox-license{border:3px solid #88a;background:#f7f8ff}
	table.imbox-featured{border:3px solid #cba135}
	table.cmbox{margin:3px 10%;border-collapse:collapse;border:1px solid #aaa;background:#DFE8FF}
	table.cmbox-notice{background:#D8E8FF}
	table.cmbox-speedy{margin-top:4px;margin-bottom:4px;border:4px solid #b22222;background:#FFDBDB}
	table.cmbox-delete{background:#FFDBDB}
	table.cmbox-content{background:#FFE7CE}
	table.cmbox-style{background:#FFF9DB}
	table.cmbox-move{background:#E4D8FF}
	table.cmbox-protection{background:#EFEFE1}
	table.ombox{margin:4px 10%;border-collapse:collapse;border:1px solid #aaa;background:#f9f9f9}
	table.ombox-notice{border:1px solid #aaa}
	table.ombox-speedy{border:2px solid #b22222;background:#fee}
	table.ombox-delete{border:2px solid #b22222}
	table.ombox-content{border:1px solid #f28500}
	table.ombox-style{border:1px solid #f4c430}
	table.ombox-move{border:1px solid #9932cc}
	table.ombox-protection{border:2px solid #bba}
	table.tmbox{margin:4px 10%;border-collapse:collapse;border:1px solid #c0c090;background:#f8eaba}
	.mediawiki .mbox-inside .tmbox{margin:2px 0;width:100%}
	.mbox-inside .tmbox.mbox-small{line-height:1.5em;font-size:100%}
	table.tmbox-speedy{border:2px solid #b22222;background:#fee}
	table.tmbox-delete{border:2px solid #b22222}
	table.tmbox-content{border:2px solid #f28500}
	table.tmbox-style{border:2px solid #f4c430}
	table.tmbox-move{border:2px solid #9932cc}
	table.tmbox-protection,table.tmbox-notice{border:1px solid #c0c090}
	table.dmbox{clear:both;margin:0.9em 1em;border-top:1px solid #ccc;border-bottom:1px solid #ccc;background:transparent}
	table.fmbox{clear:both;margin:0.2em 0;width:100%;border:1px solid #aaa;background:#f9f9f9}
	table.fmbox-system{background:#f9f9f9}
	table.fmbox-warning{border:1px solid #bb7070;background:#ffdbdb}
	table.fmbox-editnotice{background:transparent}
	div.mw-warning-with-logexcerpt,div.mw-lag-warn-high,div.mw-cascadeprotectedwarning,div#mw-protect-cascadeon{clear:both;margin:0.2em 0;border:1px solid #bb7070;background:#ffdbdb;padding:0.25em 0.9em}
	div.mw-lag-warn-normal,div.fmbox-system{clear:both;margin:0.2em 0;border:1px solid #aaa;background:#f9f9f9;padding:0.25em 0.9em}
	body.mediawiki table.mbox-small{clear:right;float:right;margin:4px 0 4px 1em;width:238px;font-size:88%;line-height:1.25em}
	body.mediawiki table.mbox-small-left{margin:4px 1em 4px 0;width:238px;border-collapse:collapse;font-size:88%;line-height:1.25em}
	.compact-ambox table .mbox-image,.compact-ambox table .mbox-imageright,.compact-ambox table .mbox-empty-cell{display:none}
	.compact-ambox table.ambox{border:none;border-collapse:collapse;background:transparent;margin:0 0 0 1.6em !important;padding:0 !important;width:auto;display:block}
	body.mediawiki .compact-ambox table.mbox-small-left{font-size:100%;width:auto;margin:0}
	.compact-ambox table .mbox-text{padding:0 !important;margin:0 !important}
	.compact-ambox table .mbox-text-span{display:list-item;line-height:1.5em;list-style-type:square;list-style-image:url(//bits.wikimedia.org/skins/common/images/bullet.gif)}
	.skin-vector .compact-ambox table .mbox-text-span{list-style-type:circle;list-style-image:url(//bits.wikimedia.org/skins/vector/images/bullet-icon.png) }
	.compact-ambox .hide-when-compact{display:none}
	div.noarticletext{border:none;background:transparent;padding:0}
	.visualhide{position:absolute;left:-10000px;top:auto;width:1px;height:1px;overflow:hidden}
	#wpSave{font-weight:bold}
	.hiddenStructure{display:inline !important;color:#f00;background-color:#0f0}
	.check-icon a.new{display:none;speak:none}
	.nounderlines a,.IPA a:link,.IPA a:visited{text-decoration:none !important}
	div.NavFrame{margin:0;padding:4px;border:1px solid #aaa;text-align:center;border-collapse:collapse;font-size:95%}
	div.NavFrame + div.NavFrame{border-top-style:none;border-top-style:hidden}
	div.NavPic{background-color:#fff;margin:0;padding:2px;float:left}
	div.NavFrame div.NavHead{height:1.6em;font-weight:bold;background-color:#ccf;position:relative}
	div.NavFrame p,div.NavFrame div.NavContent,div.NavFrame div.NavContent p{font-size:100%}
	div.NavEnd{margin:0;padding:0;line-height:1px;clear:both}
	a.NavToggle{position:absolute;top:0;right:3px;font-weight:normal;font-size:90%}
	.rellink,.dablink{font-style:italic;padding-left:1.6em;margin-bottom:0.5em}
	.rellink i,.dablink i{font-style:normal}
	.listify td{display:list-item}
	.listify tr{display:block}
	.listify table{display:block}
	.geo-default,.geo-dms,.geo-dec{display:inline}
	.geo-nondefault,.geo-multi-punct{display:none}
	.longitude,.latitude{white-space:nowrap}
	.nonumtoc .tocnumber{display:none}
	.nonumtoc #toc ul,.nonumtoc .toc ul{line-height:1.5em;list-style:none none;margin:.3em 0 0;padding:0}
	.nonumtoc #toc ul ul,.nonumtoc .toc ul ul{margin:0 0 0 2em}
	.toclimit-2 .toclevel-1 ul,.toclimit-3 .toclevel-2 ul,.toclimit-4 .toclevel-3 ul,.toclimit-5 .toclevel-4 ul,.toclimit-6 .toclevel-5 ul,.toclimit-7 .toclevel-6 ul{display:none}
	blockquote.templatequote{margin-top:0}
	blockquote.templatequote div.templatequotecite{line-height:1em;text-align:left;padding-left:2em;margin-top:0}
	blockquote.templatequote div.templatequotecite cite{font-size:85%}
	div.user-block{padding:5px;margin-bottom:0.5em;border:1px solid #A9A9A9;background-color:#FFEFD5}
	.nowrap,.nowraplinks a,.nowraplinks .selflink,sup.reference a{white-space:nowrap}
	.wrap,.wraplinks a{white-space:normal}
	.template-documentation{clear:both;margin:1em 0 0 0;border:1px solid #aaa;background-color:#ecfcf4;padding:1em}
	.imagemap-inline div{display:inline}
	#wpUploadDescription{height:13em}
	.thumbinner{min-width:100px}
	div.thumb .thumbimage{background-color:#fff}
	div#content .gallerybox div.thumb{background-color:#F9F9F9}
	.gallerybox .thumb img{background:#fff url(//bits.wikimedia.org/skins/common/images/Checker-16x16.png) repeat}
	.ns-0 .gallerybox .thumb img,.ns-2 .gallerybox .thumb img,.ns-100 .gallerybox .thumb img,.nochecker .gallerybox .thumb img{background:#fff}
	#mw-subcategories,#mw-pages,#mw-category-media,#filehistory,#wikiPreview,#wikiDiff{clear:both}
	body.rtl #mw-articlefeedbackv5,body.rtl #mw-articlefeedback{display:block;margin-bottom:1em;clear:right;float:right}
	.wpb .wpb-header{display:none}
	.wpbs-inner .wpb .wpb-header{display:block}
	.wpbs-inner .wpb .wpb-header{display:table-row}
	.wpbs-inner .wpb-outside{display:none}
	.mw-tag-markers{font-family:sans-serif;font-style:italic;font-size:90%}
	.sysop-show,.accountcreator-show,.templateeditor-show,.autoconfirmed-show{display:none}
	.ve-init-mw-viewPageTarget-toolbar-editNotices-notice .editnotice-redlink{display:none !important}
	ul.permissions-errors > li{list-style:none none}
	ul.permissions-errors{margin:0}
	body.page-Special_UserLogin .mw-label label,body.page-Special_UserLogin_signup .mw-label label{white-space:nowrap}
	.transborder{border:solid transparent}
	* html .transborder{border:solid #000001;filter:chroma(color=#000001)}
	.updatedmarker{background-color:transparent;color:#006400}
	li.mw-changeslist-line-watched .mw-title,table.mw-changeslist-line-watched .mw-title,table.mw-enhanced-watch .mw-enhanced-rctime{font-weight:normal}
	span.texhtml{font-family:"Times New Roman","Nimbus Roman No9 L",Times,serif;font-size:118%;white-space:nowrap}
	span.texhtml span.texhtml{font-size:100%}
	div.mw-geshi div,div.mw-geshi div pre,span.mw-geshi,pre.source-css,pre.source-javascript,pre.source-lua{font-family:monospace,Courier !important}
	table#mw-prefixindex-list-table,table#mw-prefixindex-nav-table{width:98%}
	.portal-column-left{float:left;width:50%}
	.portal-column-right{float:right;width:49%}
	.portal-column-left-wide{float:left;width:60%}
	.portal-column-right-narrow{float:right;width:39%}
	.portal-column-left-extra-wide{float:left;width:70%}
	.portal-column-right-extra-narrow{float:right;width:29%}
	@media only screen and (max-width:800px){.portal-column-left,.portal-column-right,.portal-column-left-wide,.portal-column-right-narrow,.portal-column-left-extra-wide,.portal-column-right-extra-narrow{float:inherit;width:inherit}
	}
	#bodyContent .letterhead{background-image:url(//upload.wikimedia.org/wikipedia/commons/e/e0/Tan-page-corner.png);background-repeat:no-repeat;padding:2em;background-color:#faf9f2}
	.treeview ul{padding:0;margin:0}
	.treeview li{padding:0;margin:0;list-style-type:none;list-style-image:none;zoom:1}
	.treeview li li{background:url(//upload.wikimedia.org/wikipedia/commons/f/f2/Treeview-grey-line.png) no-repeat 0 -2981px;padding-left:20px;text-indent:0.3em}
	.treeview li li.lastline{background-position:0 -5971px }
	.treeview li.emptyline > ul{margin-left:-1px}
	.treeview li.emptyline > ul > li:first-child{background-position:0 9px }
	td .sortkey,th .sortkey{display:none;speak:none}
	.inputbox-hidecheckboxes form .inputbox-element{display:none !important}
	#editpage-specialchars{display:none}
	.k-player .k-attribution{visibility:hidden}
	#coordinates{position:absolute;top:0em;right:0em;float:right;margin:0em;padding:0em;line-height:1.5em;text-align:right;text-indent:0;font-size:85%;text-transform:none;white-space:nowrap}
	div.topicon{position:absolute;top:-2em;margin-right:-10px;display:block !important}
	div.flaggedrevs_short{position:absolute;top:-3em;right:80px;z-index:1;margin-left:0;margin-right:-10px}
	body.rtl #protected-icon{left:55px}
	body.rtl #spoken-icon,body.rtl #commons-icon{left:30px}
	body.rtl #featured-star{left:10px}
	div.vectorMenu div{z-index:2}
	#siteSub{display:inline;font-size:92%}
	div.redirectMsg img{vertical-align:text-bottom}
	.redirectText{font-size:150%;margin:5px}
	.ns-0 .ambox,.ns-0 .navbox,.ns-0 .vertical-navbox,.ns-0 .infobox.sisterproject,.ns-0 .dablink,.ns-0 .metadata,.editlink,.navbar,a.NavToggle,span.collapseButton,span.mw-collapsible-toggle,th .sortkey,td .sortkey{display:none !important}
	#content cite a.external.text:after,.nourlexpansion a.external.text:after,.nourlexpansion a.external.autonumber:after{display:none !important}
	table.collapsible tr,div.NavPic,div.NavContent{display:block !important}
	table.collapsible tr{display:table-row !important}
	#firstHeading{margin:0px}
	#content a.external.text:after,#content a.external.autonumber:after{word-wrap:break-word}

	/* cache key: enwiki:resourceloader:filter:minify-css:7:80990796d5e39c9bc549141e43765bc3 */
"""

def deleteAll(the_list):
	for tmp in the_list:
		tmp.extract()

def processHTML(text, base_img_url):
	"""Returns processed HTML

	:param:base_img_url base wikipedia url for img links 
	"""

	soup = BeautifulSoup(text)

	deleteAll(soup.find_all(["script", "style", "noscript"]))

	unneeded = soup.find_all("div", id=["siteSub", "catlinks", "jump-to-nav", "mw-navigation", "p-interaction", "p-coll-print_export", "p-lang", "p-tb", "left-navigation", "right-navigation"
		])
	deleteAll(unneeded)

	deleteAll(soup.find_all(class_=["noprint", "printfooter", "dablink", "navbox", "Template-Fact"]))

	deleteAll(soup.find_all(id=["footer-info-copyright", "footer-places"]))

	deleteAll(soup.find_all("span", class_="mw-editsection"))

	cites = soup.find_all("sup", class_="reference")
	#keep real footnotes
	cites = [x for x in cites if "[fn" not in x.text]
	deleteAll(cites)

	reflist = soup.find_all("div", class_=["reflist", "refbegin"])
	if reflist:
		from bs4 import NavigableString

		for ref in reflist:
			heading = ref.previous_sibling.previous_sibling

			if isinstance(heading, NavigableString):
				#like ja: it has an empty line before
				heading = ref.previous_sibling.previous_sibling.previous_sibling

			heading.extract()
			ref.extract()	

	toc = soup.find(id="toc")
	if toc:
		toc.extract()

	deleteAll(soup.find_all("link", {"rel": ["stylesheet"]}))
	new_css = soup.new_tag("style")
	new_css.string = CSS_FILE
	soup.head.append(new_css)

	# fix images
	imgs = soup.find_all("img")
	for img in imgs:
		img_src     = img['src']

		if not img_src.startswith("http"):
			img['src'] = "http:" + img_src

			try:
				anchor_href = img.parent['href']
			except KeyError:
				pass
			else:
				if not anchor_href.startswith("http"):
					img.parent['href'] = base_img_url + anchor_href

	anchor = soup.find_all("a", href=re.compile("^/wiki/"))
	for a in anchor:
		del a['href']

	return soup.renderContents()


def searchTranslations(lang, title=None, pageid=None):
	""" Query wikipedia API to get the available langs and url. Returns dictionary 
	with info from that lang.

	:param:lang     lang to search translation for 
	:param:title    article title 
	:param:pageid   article id 

	title and id are mutually exclusive, wins id 
	"""

	if not pageid and not title:
		return None 

	if pageid and title:
		title = None

	if pageid:
		LANGS_PARAMS.update({'pageid': pageid})
	if title:
		LANGS_PARAMS.update({'page': title})

	rlang = requests.get(WIKIPEDIA_API, params=LANGS_PARAMS).json()
	list_langs = rlang["parse"]["langlinks"]

	info = dict()

	for this_lang in list_langs:
		if this_lang['lang'] == lang:
			info = {
				'code'    : this_lang['lang']
				, 'title' : this_lang['*']
				, 'url'   : this_lang['url']
			}
			return info 

	return info

def getPage(lang, url, save):
	"""Get page from url, process, and save 

	:param:lang  the language
	:param:url   full url to article 
	:param:save  save_as filename 
	"""
	base_filename = "{file}_{lang}.html"

	r = requests.get(url, params=PRINT_PARAMS)
	html_original = r.text

	current_filename = base_filename.format(file=save, lang=lang)
	print (" Processing {now}/{total}: {file}".format(
		file=current_filename, now=index, total=total_items))

	base_url = WIKIPEDIA_URL.format(lang=lang)
	
	final_text = processHTML(html_original, base_url)
	with open(os.path.join(OUTPUT_FOLDER, current_filename), 'w') as output_file:
		output_file.write(final_text)


# ----------- 
#  Start!
# ----------- 

# collect data
print(" Reading file... ")
new_pages = dict()

with codecs.open(INPUT_FILE, 'r', encoding='utf-8-sig') as filee:

	the_csv = filee.read()
	the_csv = the_csv.splitlines()

	for line in the_csv:
		if not line: 
			continue

		page_title, save_as = line.split("\t")

		if not save_as:
			save_as = page_title

		new_pages[page_title] = dict()
		new_pages[page_title]['save_as'] = save_as


titles = [key for key, val in list(new_pages.items())]

if len(titles) > 50:
	titles = [titles[start:start+50] for start in range(0, len(titles), 50)]
else:
	titles = [titles]

print(" Querying... ")

real_pages     = dict()
not_found      = list()

for group_titles in titles:

	titles_query = "|".join(group_titles)
	EXISTANCE_PARAMS.update({'titles':titles_query})

	r = requests.get(WIKIPEDIA_API, params=EXISTANCE_PARAMS).json()
	result = r['query'] 

	# fix titles 
	if "normalized" in result:
		for norm in result['normalized']:
			if norm['from'] in new_pages:
				new_pages[norm['to']] = new_pages[norm['from']]
				del new_pages[norm['from']]

	if "redirects" in result:
		for redir in result['redirects']:
			if redir['from'] in new_pages:
				new_pages[redir['to']] = new_pages[redir['from']]
				del new_pages[redir['from']]

	result_pages = result['pages']

	for key, items in list(result_pages.items()):
		if int(key) < 0:
			not_found.append(items['title'])
			continue

		current_title = items['title']

		new_pages[current_title]['fullurl'] = items['fullurl']
		new_pages[current_title]['lang']    = searchTranslations(OUTPUT_LANG, pageid=items['pageid'])


not_found = tuple(set(not_found))

for title in not_found:
	SEARCH_PARAMS.update({'srsearch' : title})
	rs = requests.get(WIKIPEDIA_API, params=SEARCH_PARAMS).json()

	if not rs['query']['search']:
		print (" Article for {article} not found".format(article=title))
		del new_pages[title]
		continue

	page_title = rs['query']['search'][0]["title"]

	if not page_title in new_pages:
		new_pages[page_title] = dict()

	if not new_pages[title]['save_as']:
		new_pages[page_title]['save_as'] = page_title

	new_pages[page_title]['fullurl'] = WIKIPEDIA_BASE + "wiki/" + page_title
	new_pages[page_title]['lang']    = dict()	
	new_pages[page_title]['lang']    = searchTranslations(OUTPUT_LANG, title=page_title)


for title, prop in list(new_pages.items()):
	if not prop['lang']:
		print (" Article {article} doesn't have translation in {lang}".format(
			article=title, lang=OUTPUT_LANG))
		del new_pages[title]


total_items = len(new_pages.keys())*2
index = 0

for title, props in list(new_pages.items()):
	index += 1
	getPage(INPUT_LANG, props['fullurl'], props['save_as'])
	
	index += 1
	getPage(props["lang"]['code'], props["lang"]['url'], props['save_as'])
