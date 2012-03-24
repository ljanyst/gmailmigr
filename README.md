GMailMigr
=========

*gmailmigr* is essentially two small python scripts that may prove helpful
should you feel a sudden urge to move your email messages out of *gmail* to
some other email provider using IMAP. I know, I know, *gmail* rocks big
time, but some people may still have some pretty valid resons to move away.
If you're one of them: **ENJOY!**

Disclaimer
----------

I have used these scripts to move thousands of my own messages from *gmail*
to my current email provider and they worked like a charm, but still, be
aware that you're using them at your own risk and I am not responsible if
something goes wrong and you lose messages. See the license text at the bottom.

gmail_label_remap.py
--------------------
The concept of *gmail* labels doesn't really match one-to-one to the concept
of IMAP folders (mailboxes). This may result with you not seeing all the
messages in your conversation threads while accessing *gmail* using ie.
*Thunderbird*. This will also render it impossible for the other script in
this package, described below, to properly identify and copy all your
labeled conversations to proper IMAP folders elsewhere. The problem and the
solution have been described [here](http://goo.gl/ac5eD). It definitely
is way too painfull to apply this procedure by hand to thousands of
conversation threads that you must have probably accumulated, but fear not,
gmail_label_remap.py will do this for you using
[magic](https://developers.google.com/google-apps/gmail/imap_extensions).

It will show up as something like this when you run it:

    ]==> ./gmail_label_remap.py
    username (won't be echoed): 
    password (won't be echoed):
    [i] Identify the IMAP folder name for "All Mail"...
    [i] Done: [Gmail]/Tous les messages
    [i] Opening [Gmail]/Tous les messages
    [i] [Gmail]/Tous les messages contains 15299 messages
    [i] Identify all the threads (may take some time)
    [i] Found 4182 threads
    [i] Processing thread 4182 of 4182 
    [i] Orphaned threads:   414
    [i] Sent only threads:  255
    [i] ALL DONE

It will create two extra labels:

 * *orphaned*  - for the conversations without labels
 * *sent_only* - for the emails that you have sent but got no answer
    to them, so they have no assigned label

imap_copy.py
------------
imap_copy.py will allow you to *list* the folders in an IMAP account. This
includes also accessing *gmail* via IMAP, in which case the labels are listed
as folders, ie:

    ]==> ./imap_copy.py --list --source=imap.gmail.com:993
    imap.gmail.com's username (won't be echoed): 
    imap.gmail.com's password (won't be echoed): 
    Fun (1641)
    INBOX (114)
    Private (484)
    Work (1010)
    [Gmail]/Brouillons (0)
    [Gmail]/Corbeille (563)
    [Gmail]/Important (5204)
    [Gmail]/Messages envoy&AOk-s (4440)
    [Gmail]/Spam (16)
    [Gmail]/Suivis (59)
    [Gmail]/Tous les messages (14736)

It will also let you *copy* the messages from one IMAP account to another:

    ]==> ./imap_copy.py --copy=INBOX.gmail-inbox,Fun \
                        --source=imap.gmail.com:993  \
                        --destination=imap.somewhere.else:993
    imap.gmail.com's username (won't be echoed): 
    imap.gmail.com's password (won't be echoed): 
    imap.somewhere.else's username (won't be echoed): 
    imap.somewhere.else's password (won't be echoed): 
    Copying INBOX => gmail-inbox
    Copying 114 of 114 
    Copying Fun => Fun
    Copying 1641 of 1641
    ALL DONE

What you specify after the 'equal' sign of the *--copy* parameter is a comma
separated list of folders. It may just be a folder name, like *Fun* in the
example above. Or something like: *INBOX.gmail-inbox* which will take the
*INBOX* folder at the source and copy its contents to the *gmail-inbox*
folder at the destination.

License
-------

Copyright (c) 2012, Lukasz Janyst &lt;ljanyst@buggybrain.net&gt;

Permission to use, copy, modify, and/or distribute this software for any
purpose with or without fee is hereby granted, provided that the above
copyright notice and this permission notice appear in all copies.

THE SOFTWARE IS PROVIDED 'AS IS' AND THE AUTHOR DISCLAIMS ALL WARRANTIES
WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
