#!/usr/bin/env python
# traduko.py
# Copyright (C) 2007 Phil Bordelon
# This file is part of Endgame: Singularity.

# Endgame: Singularity is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

# Endgame: Singularity is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with Endgame: Singularity; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

# This file contains the 'traduko' utility, meant to ease translating strings
# for the game.


from __future__ import unicode_literals
from future import standard_library
standard_library.install_aliases()
import configparser
import optparse
import os.path
import sys

# A list of all available modes.
MODE_LIST = ["update", "verify", "package"]

# A list of things that can be translated.  Tracked are whether or
# not they have a standalone file that defines certain things and the
# prefix of the filename.
TRANSLATION_LIST = [
    {"prefix": "bases", "has_standalone": True},
    {"prefix": "events", "has_standalone": True},
    {"prefix": "items", "has_standalone": True},
    {"prefix": "strings", "has_standalone": False},
    {"prefix": "techs", "has_standalone": True},
    {"prefix": "locations", "has_standalone": True},
]

def build_option_parser():
    """
buildOptionParser() builds an 'optparse' object to handle traduko's myriad
arguments and options.  Unfortunately, optparse isn't really made for modal
applications like traduko, so we'll have to abuse the code a bit.  But it
should be good enough.
"""

# Fear the usage string!
    usage = """
    %prog MODE [options] trans_lang

traduko is an application for helping translations of Endgame: Singularity.
Using it is much like using a revision control system.  There are a number
of different modes, and each mode takes a set of options or other arguments
to properly run.

For each option, the modes in which it works are listed in brackets at the
end of the help text.  All options take the --directory option, which states
which directory the translation files are in, as well as the --verbose option.

MODES

The various modes available for use with traduko are as follows:

    update [--source LANG] [--restart] trans_lang

The 'update' mode is for when you want to start a new translation, or pull
new strings to keep a translation updated.  It will always use the en_US
translation as the base (as that is the "source" translation), but if you
pass --source as a parameter it will override en_US strings with those from
another available language.  This is useful if you are translating into a
language that is a variant of an extant one.  --restart will create a new
language file for trans_lang, erasing any data already there.  THIS IS
DANGEROUS.

   verify trans_lang

This will do a verification pass on the language, informing you of which
strings still need to be translated, don't exist in the current language
file, and so on.

   package [--file PACKFILE] trans_lang

This will generate a nice .tar.gz file to send to the Endgame: Singularity
developers with your translation.  The --file parameter allows you to pick
the filename of the output file.

TRANSLATION FILES

The files are in a fairly basic file format.  Strings that are sourced from
en_US will be marked with three exclamation points at the beginning and end;
strings sourced from a different 'source' language will be marked with three
asterisks at the beginning and end.
"""

    parser = optparse.OptionParser(usage = usage)

    parser.add_option("-v", "--verbose", dest="verbose", default=False,
     action="store_true", help="Be talkative [all]")

    parser.add_option("-d", "--directory", dest="directory", default=".",
     help="Use language files out of directory DIR (default %default) [all]",
     metavar="DIR")

    parser.add_option("-s", "--source", dest="source", default=None,
     help="Use language LANG as the source for the translation [update]",
     metavar="LANG")

    parser.add_option("--restart", dest="restart", default=False,
     action="store_true",
     help="Restart a language translation entirely (DANGEROUS!) [update]",)

    parser.add_option("-f", "--filename", dest="filename", default=None,
     help="Write package to file FILE instead of trans_lang.tar.gz")

    return parser

def error_and_out(message):
    """
error_and_out() prints a mildly helpful error message and bails.
"""

    sys.stderr.write("ERROR: %s\n" % message)
    sys.stderr.write("       Please run again with --help to see proper usage.\n")
    sys.exit(1)

def verbout(message):
    """
verbout() is a shortcut for sys.stderr.write("V: " + message + "\n").
"""

    sys.stderr.write("V: " + message + "\n")

def update(trans_lang, trans_path, source, restart, verbose):
    """
update() is an implementation of the 'update' option.

TODO: Describe better.
"""

    # First things first: For each file, we need to pull in the strings from
    # the en_US version, and then overwrite them with the source (if set).  In
    # addition, if there's already a translation started, we don't want to
    # overwrite those options either.
    for trans_file_dict in TRANSLATION_LIST:

        prefix = trans_file_dict["prefix"]

        # Get all the filenames.
        dest_filename = prefix + "_" + trans_lang + ".dat"
        en_US_filename = prefix + "_en_US.dat"
        if source:
            source_filename = prefix + "_" + source + ".dat"

        dest_parser = configparser.RawConfigParser()
        dest_filepath = os.path.join(trans_path, dest_filename)

        # If we're not restarting, try to preload the translation with what's
        # already there.  This may fail, which is fine; that should just mean
        # it's a brand-new translation.
        if not restart:
            try:

                # We're pedantic about the opening and closing, /just in case/
                # Python wants to hold onto the file object longer than we
                # want, since we have to write to it later.

                if verbose:
                    verbout("Trying to preload %s." % dest_filepath)

                fp = open(dest_filepath, "r")
                dest_parser.readfp(fp)
                fp.close()
            except:

                # Okay, couldn't read the new translation file.  That's to be
                # expected.
                if verbose:
                    verbout("Preload attempt failed.")

        # Now that we've got our parser object, we need to start preloading
        # data.  We want to load the 'source' language first, as it's a
        # better source than the en_US fallback.
        read_list = []
        if source:
            read_list.append({
             "filename": source_filename, "signal": "***", "required": False})

        # Add the en_US fallback at the end.
        read_list.append({
         "filename": en_US_filename, "signal": "!!!", "required": True})

        for read_elem in read_list:

            # This seems ridiculous, but when you come back to code five years
            # later and forgot to document your formats, you'll thank yourself
            # for being this pedantic.
            filename = read_elem["filename"]
            signal = read_elem["signal"]
            required = read_elem["required"]

            # Read the data from this translation file.
            source_parser = configparser.RawConfigParser()
            source_filepath = os.path.join(trans_path, filename)
            try:
                if verbose:
                    verbout("Loading translation from %s." % source_filepath)
                source_parser.readfp(open(source_filepath))
            except:
                if required:
                    error_and_out("Incomplete required translation.  Cannot proceed.")
                elif verbose:
                    verbout("Failed to find translation data.")

            for section in source_parser.sections():

                # Add this section if the new translation doesn't have it.
                if not dest_parser.has_section(section):
                    if verbose:
                        verbout("Adding section %s." % section)
                    dest_parser.add_section(section)

                for option in source_parser.options(section):
                    if not dest_parser.has_option(section, option):

                        # New data!  Splice it into the new translation.
                        value = signal + source_parser.get(section, option) + signal

                        if verbose:
                            verbout("Adding option %s with value %s." % (option, value))

                        dest_parser.set(section, option, value)

        # We have a "complete" file.  Write it out.
        if verbose:
            verbout("Writing out translation file %s." % dest_filepath)
        fp = open(dest_filepath, "w")
        dest_parser.write(fp)
        fp.close()

def verify(trans_lang, trans_path, verbose):
    """
verify() is an implementation of the 'verify' option.

TODO: Describe better.
"""
    sys.stdout.write("TODO: Implement verify.\n")

def package(trans_lang, trans_path, filename, verbose):
    """
package() is an implementation of the 'package' option.

TODO: Describe better.
"""

    sys.stdout.write("TODO: Implement package.\n")

if "__main__" == __name__:

    option_parser = build_option_parser()

    (options, args) = option_parser.parse_args()

    # Boring error-checking time!
    if len(args) != 2:
        error_and_out("traduko requires at least two arguments.")

    mode, trans_lang = args

    if mode not in MODE_LIST:
        error_and_out("%s is not a valid mode." % mode)

    if (options.source or options.restart) and mode != "update":
        error_and_out("Cannot use --source or --restart unless in 'update' mode.")

    trans_path=os.path.abspath(os.path.join(os.getcwd(), options.directory))
    if mode == "update":
        update(trans_lang, trans_path, options.source, options.restart, options.verbose)
    elif mode == "verify":
        verify(trans_lang, trans_path, options.verbose)
    elif mode == "package":
        package(trans_lang, trans_path, options.filename, options.verbose)
