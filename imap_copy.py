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

import getopt
import getpass
import imaplib
import sys

#-------------------------------------------------------------------------------
# Some helpers
#-------------------------------------------------------------------------------
class ConfigError( Exception ):
    pass

class Folder:
    def __init__( self, name, separator = '/' ):
        self.separator = separator
        self.__path      = name.split( separator )

    def __eq__( self, other ):
        return self.__repr__() == other

    def __repr__( self ):
        return '/'.join( self.__path )

    def imapRepr( self ):
        return self.separator.join( self.__path )

#-------------------------------------------------------------------------------
# Get IMAP connection
#-------------------------------------------------------------------------------
def getIMAPConnection( hostPort ):
    l = hostPort.split( ':' )
    if len(l) != 2:
        raise ConfigError( 'Malformed address' )

    try:
        port = int( l[1] )
    except TypeError, e:
        raise ConfigError( str(e) )

    user   = getpass.getpass( l[0] + '\'s username (won\'t be echoed): ')
    passwd = getpass.getpass( l[0] + '\'s password (won\'t be echoed): ')

    m = imaplib.IMAP4_SSL( l[0], port )
    m.login( user, passwd )
    return m

#-------------------------------------------------------------------------------
# Get list of folders
#-------------------------------------------------------------------------------
def getList( server ):
    st, folders = server.list( '' )
    fList = []
    for folder in folders:
        f = [spl.strip() for spl in folder.split( '"' ) if spl.strip()]
        folder = Folder( f[2], f[1] )
        if folder == '[Gmail]':
            continue
        fList.append( ( folder, server.select( folder.imapRepr(), True )[1][0] ) )
    return fList

#-------------------------------------------------------------------------------
# Figure out the delimiter at the destination
#-------------------------------------------------------------------------------    
def getSeparator( server ):
    st, folders = server.list( '' )
    if not folders:
        return '/'
    return [f.strip() for f in folders[0].split( '"' ) if f.strip()][1]

#-------------------------------------------------------------------------------
# List the IMAP folders on the source
#-------------------------------------------------------------------------------
def list( opts ):
    if '--source' not in opts:
        raise Exception( 'Source server is missing' )

    conn = getIMAPConnection( opts['--source'] )
    folders = getList( conn )
    for folder in folders:
        print "%s (%s)" % (folder[0], folder[1] )
    conn.logout()
    return 0

#-------------------------------------------------------------------------------
# Build copy list out of source folder list and copy string
#-------------------------------------------------------------------------------
def buildCopyList( sourceListing, toCopy, sep ):
    copyList = []
    skipped  = []
    if toCopy == '*':
        return ([(f, Folder( str(f) ) ) for f in sourceListing], [])

    toCopy = toCopy.split( ',' )
    for item in toCopy:
        spl = item.split( '.' )
        if len( spl ) == 1:
            spl.append( spl[0] )
        elif len( spl ) == 2:
            pass
        else:
            skipped.append( item )

        if not spl[0] in sourceListing:
            skipped.append( item )
        else:
            dst = Folder( spl[1] )
            dst.separator = sep
            copyList.append( (Folder( spl[0] ), dst ) )
    return (copyList, skipped)

#-------------------------------------------------------------------------------
# Copy the messages
#-------------------------------------------------------------------------------
def copyMessages( src, dest, srcMbox, destMbox ):
    print "Copying %s => %s" % (srcMbox, destMbox)

    src.select( srcMbox.imapRepr(), True )
    st, m = dest.create( destMbox.imapRepr() )

    if st != 'OK':
        raise Exception( "Unable to create destination folder: " + str(m) )

    st, data = src.search( None, 'ALL' )
    msgs = data[0].split()
    numMsgs = len( msgs )
    currMsg = 1

    for num in msgs:
        print "\rCopying", currMsg, "of", numMsgs,
        currMsg += 1
        sys.stdout.flush()
        st, data = src.fetch( num, '(RFC822)' )
        dest.append( destMbox.imapRepr(), None, None, data[0][1] )
    print ''

#-------------------------------------------------------------------------------
# List the IMAP folders on the destination
#-------------------------------------------------------------------------------
def copy( opts ):
    #---------------------------------------------------------------------------
    # Check the input params
    #---------------------------------------------------------------------------
    if '--source' not in opts:
        raise Exception( 'Source server is missing' )

    if '--destination' not in opts:
        raise Exception( 'Source server is missing' )

    folders = opts['--copy']

    if not folders:
        raise Exception( 'Invalid folder list' )

    #---------------------------------------------------------------------------
    # Get the create the copy list
    #---------------------------------------------------------------------------
    src  = getIMAPConnection( opts['--source'] )
    dest = getIMAPConnection( opts['--destination'] )
    sourceList = [i[0] for i in getList( src )]
    destSep  = getSeparator( dest )
    
    copyList, skipped = buildCopyList( sourceList, folders, destSep )
    if skipped:
        print 'The following folders were not found on the source server:',
        print skipped

    #---------------------------------------------------------------------------
    # Perform the copy
    #---------------------------------------------------------------------------
    for job in copyList:
        copyMessages( src, dest, job[0], job[1] )
    print "ALL DONE"
    dest.logout()
    src.logout()

    return 0

#-------------------------------------------------------------------------------
# Print help
#-------------------------------------------------------------------------------
def printHelp():
    print( 'imap_copy.py [options]' )
    print( ' --souce=host:port       source server' )
    print( ' --destination=host:port destination server' )
    print( ' --list                  list the imap folders on the source' )
    print( ' --copy=FOLDERS          copy the folders from the source server' )
    print( '                         to the destination, where folders is:' )
    print( '                           *         - copy all folders' )
    print( '                           x,y,z     - copy only x, y and z' )
    print( '                           x.x1,y.y1 - copy and rename' )
    print( '                         for all folders' )
    print( ' --help                  this help message' )

#-------------------------------------------------------------------------------
# Run the show
#-------------------------------------------------------------------------------
def main():
    try:
        params = ['source=', 'destination=', 'list', 'copy=', 'help']
        optlist, args = getopt.getopt( sys.argv[1:], '', params )
    except getopt.GetoptError, e:
        print '[!]', e
        return 1

    opts = dict(optlist)
    if '--help' in opts or not opts:
        printHelp()
        return 0

    commandMap = {'--list': list, '--copy': copy}
    for command in commandMap:
        if command in opts:
            i = 0
            try:
                i = commandMap[command]( opts )
            except Exception, e:
                print '[!]', e 

if __name__ == '__main__':
    sys.exit(main())
