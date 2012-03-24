#!/usr/bin/env python
#-------------------------------------------------------------------------------
# Copyright (c) 2012, Lukasz Janyst <ljanyst@buggybrain.net>
#
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED 'AS IS' AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
#-------------------------------------------------------------------------------
#
# Based on:
# https://developers.google.com/google-apps/gmail/imap_extensions
# http://goo.gl/ac5eD

import getpass
import imaplib
import sys
import re

#-------------------------------------------------------------------------------
# Helpers
#-------------------------------------------------------------------------------
labRe = re.compile( '^(?P<msgid>\d+) +\(X-GM-LABELS +\((?P<labels>.+)\)\)$' )
lblParseRe = re.compile( '^\s*(?:"(.*?)"|(\S+))' )

class GMError( Exception ):
    pass

#-------------------------------------------------------------------------------
# Extract the label names from the list
#-------------------------------------------------------------------------------
def extractLabels( labelList ):
    vals  = []
    start = 0
    while True:
        res = lblParseRe.match( labelList[start:] )
        if not res:
            break
        start += res.span()[1]
        if res.group(1):
            val = res.group(1)
        else:
            val = res.group(2)
        vals.append(val)
    return vals

#-------------------------------------------------------------------------------
# Attach all the present labels to all the messages in a thread so that
# they could end up in the same IMAP folder
#-------------------------------------------------------------------------------
def rebindLabels( srv, thid, thread ):

    #---------------------------------------------------------------------------
    # Get the labels
    #---------------------------------------------------------------------------
    msgSelector = ','.join( thread )
    rsp = srv.fetch( msgSelector, '(X-GM-LABELS)' )
    if rsp[0] != 'OK':
        raise GMError( 'Unable to fetch labels for thread ' + str(thid) )

    #---------------------------------------------------------------------------
    # Find all the unique labels
    #---------------------------------------------------------------------------
    labels    = []
    labelsMsg = []
    orphaned  = False
    sentOnly  = False
    
    for item in rsp[1]:
        mt = labRe.match( item )
        if not mt:
            continue
        labelsMsg = extractLabels( mt.groupdict()['labels'] )
        for l in labelsMsg:
            if not l.startswith( '\\\\' ) or l == '\\\\Inbox':
                if l and l not in labels:
                    labels.append( l )

    #---------------------------------------------------------------------------
    # Add some labels when non was found
    #---------------------------------------------------------------------------
    if not labels:
        if len(thread) == 1 and '\\\\Sent' in labelsMsg:
            sentOnly = True
            labels.append( 'sent_only' )
        else:
            orphaned = True
            labels.append( 'orphaned' )

    #---------------------------------------------------------------------------
    # Assign labels
    #---------------------------------------------------------------------------
    labels = '(' + ' '.join( ['"'+l+'"' for l in labels] ) + ')'
    rsp = srv.store( msgSelector, '+X-GM-LABELS', labels )
    if rsp[0] != 'OK':
        raise GMError( 'Unable to fetch labels for thread ' + str(thid) )

    return (orphaned, sentOnly)

#-------------------------------------------------------------------------------
# Let the show begin
#-------------------------------------------------------------------------------
def main():
    #---------------------------------------------------------------------------
    # Log in to gmail
    #---------------------------------------------------------------------------
    user   = getpass.getpass( 'username (won\'t be echoed): ')
    passwd = getpass.getpass( 'password (won\'t be echoed): ')

    srv = imaplib.IMAP4_SSL( 'imap.gmail.com', 993 )
    srv.login( user, passwd )

    #---------------------------------------------------------------------------
    # Find out the name of the 'All Mail' label
    #---------------------------------------------------------------------------
    print '[i] Identify the IMAP folder name for "All Mail"...'
    allMailName = None

    rsp = srv.xatom( 'XLIST', '', '*' )
    if rsp[0] != 'OK':
        raise GMError( 'Unable to find the "All Mail" label: ' + str(rsp[1]) )

    rsp = srv.response( 'XLIST' )[1]
    for folder in rsp:
        if '\\AllMail' in folder:
            allMailName = [i.strip() for i in folder.split( '"' ) if i.strip()][2]
    print '[i] Done:', allMailName

    #---------------------------------------------------------------------------
    # Select the folder
    #---------------------------------------------------------------------------
    print '[i] Opening', allMailName
    rsp = srv.select( allMailName )
    if rsp[0] != 'OK':
        raise GMError( 'Unable to open folder: ' + allMailName )
    print '[i] %s contains %d messages' % (allMailName, int(rsp[1][0]))

    #---------------------------------------------------------------------------
    # Identify all the threads
    #---------------------------------------------------------------------------
    print '[i] Identify all the threads (may take some time)'
    rsp = srv.fetch( '1:'+rsp[1][0], '(X-GM-THRID)' )
    threads = {}
    if rsp[0] != 'OK':
        raise GMException( 'Unable to identify the threads' + str(rsp[1]) )
    for item in rsp[1]:
        spl = item.split( ' ' )
        threadId = int(spl[2][0:-1])
        if threadId not in threads:
            threads[threadId] = [spl[0]]
        else:
            threads[threadId].append( spl[0] )
    numThreads = len(threads.keys())
    print '[i] Found %d threads' % (numThreads)

    #---------------------------------------------------------------------------
    # Rebind the labels
    #---------------------------------------------------------------------------
    currThread = 1
    orphThread = 0
    sentThread = 0
    for th in threads.items():
        print "\r[i] Processing thread", currThread, "of", numThreads,
        sys.stdout.flush()
        currThread += 1
        orph, snt = rebindLabels( srv, th[0], th[1] )
        if orph:
            orphThread += 1
        if snt:
            sentThread += 1
    print ''
    print '[i] Orphaned threads:  ', orphThread
    print '[i] Sent only threads: ', sentThread
    print '[i] ALL DONE'
    srv.logout()

#-------------------------------------------------------------------------------
# RunMe
#-------------------------------------------------------------------------------
if __name__ == '__main__':
    try:
        main()
    except GMError, e:
        print '[!] Error:', e
