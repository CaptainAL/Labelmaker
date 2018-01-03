#!/usr/bin/env python
# (Be in -*- python -*- mode.)

## LabelNation: command-line label printing
## 
## For printing address labels, business cards, or any other kind
## of regularly-arranged rectangles on a printer-ready sheet.
## Run it with the "--help" flag to see usage and options.
##
## Copyright (C) 2000-2011 Karl Fogel <kfogel {_AT_} red-bean.com>
## 
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 3 of the License, or
## (at your option) any later version.
## 
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
## 
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

import re
import os
import sys
import csv
import string
import getopt

# Make sure this Python is recent enough.
if sys.hexversion < 0x2000000:
  sys.stderr.write("ERROR: Python 2.0 or higher required, "
                   "see www.python.org.\n")
  sys.exit(1)

# Pretend we have booleans on older python versions
try:
  True
except:
  True = 1
  False = 0

################ Classes ###################

class SheetSpec:
  default_first_label = 1             # start printing here
  default_font_name = "Times-Roman"   # uncontroversial fallback font
  default_font_size = 12              # a normal font size for labels

  def __init__(self,
               left_margin=None,      # first label from left starts here
               bottom_margin=None,    # first label from bottom starts here
               label_width=None,      # not including unused inter-label space
               label_height=None,     # not including unused inter-label space
               horiz_space=None,      # unused inter-label horizontal space
               vert_space=None,       # unused inter-label vertical space
               horiz_num_labels=None, # how many labels across?
               vert_num_labels=None,  # how many labels up and down?
               first_label=default_first_label,
               font_name=default_font_name,
               font_size=default_font_size,
               ):
    self.left_margin = left_margin
    self.bottom_margin = bottom_margin
    self.label_width = label_width
    self.label_height = label_height
    self.horiz_space = horiz_space
    self.vert_space = vert_space
    self.horiz_num_labels = horiz_num_labels
    self.vert_num_labels = vert_num_labels
    self.first_label = first_label
    self.font_name = font_name
    self.font_size = font_size

  # Set up standard params, but preserving manual overrides:
  def absorb(self, spec):
    """Merge SPEC into self, taking SPEC's values for any of self's
    values that are still at their defaults, but keeping own values
    where they are different from the default."""
    if self.left_margin is None:
      self.left_margin = spec.left_margin
    if self.bottom_margin is None:
      self.bottom_margin = spec.bottom_margin
    if self.label_width is None:
      self.label_width = spec.label_width
    if self.label_height is None:
      self.label_height = spec.label_height
    if self.horiz_space is None:
      self.horiz_space = spec.horiz_space
    if self.vert_space is None:
      self.vert_space = spec.vert_space
    if self.horiz_num_labels is None:
      self.horiz_num_labels = spec.horiz_num_labels
    if self.vert_num_labels is None:
      self.vert_num_labels = spec.vert_num_labels
    if self.first_label == SheetSpec.default_first_label:
      self.first_label = spec.first_label
    if self.font_name == SheetSpec.default_font_name:
      self.font_name = spec.font_name
    if self.font_size == SheetSpec.default_font_size:
      self.font_size = spec.font_size

  def __str__(self):
    s  = "LeftMargin:      %d\n" % self.left_margin
    s += "BottomMargin:    %d\n" % self.bottom_margin
    s += "LabelWidth:      %d\n" % self.label_width
    s += "LabelHeight:     %d\n" % self.label_height
    s += "HorizSpace:      %d\n" % self.horiz_space
    s += "VertSpace:       %d\n" % self.vert_space
    s += "HorizNumLabels:  %d\n" % self.horiz_num_labels
    s += "VertNumLabels:   %d\n" % self.vert_num_labels
    s += "FontName:        %s\n" % self.font_name
    s += "FontSize:        %d\n" % self.font_size
    return s




### Subroutines.

def dedelimit_string(str):
  str = str.replace('\n', '')
  str = str.replace('"', '')
  str = str.replace("'", '')
  str = str.replace('\t', '')
  str = str.replace(' ', '')
  return str


def normalize_string(str):
  str = dedelimit_string(str)
  str = str.lower()
  str = str.replace('-', '')
  str = str.replace('_', '')
  str = str.replace('.', '')
  return str


def sheetspec_for_type(type):
  """Return a SheetSpec object that matches TYPE."""
  type = normalize_string(type)

  # Don't know Maco's number for Avery 5x61 series yet...
  if (   type == "avery5161"
      or type == "avery5261"
      or type == "avery5661"
      or type == "avery5961"):
    # Large and wide address labels, 20 per page
    return SheetSpec(left_margin=11.25,
                     bottom_margin=16.0,
                     label_width=270.0,
                     label_height=72.0,
                     horiz_space=20.0,
                     vert_space=0.0,
                     horiz_num_labels=2.0,
                     vert_num_labels=10.0,
                     font_name="Times-Roman",
                     font_size=12.0)

  elif (   type == "avery5162"
        or type == "avery5262"
        or type == "avery5662"
        or type == "avery5962"
        or type == "avery15162"
        or type == "avery8162"
        or type == "avery8252"
        or type == "avery8462"
        or type == "avery18162"
        or type == "avery18662"):
    # 14 per page
    return SheetSpec(left_margin=11.52,
                     bottom_margin=62.0,
                     label_width=300.0,
                     label_height=96.0,
                     horiz_space=0.0,
                     vert_space=0.0,
                     horiz_num_labels=2.0,
                     vert_num_labels=7.0,
                     font_name="Times-Roman",
                     font_size=12.0)

  elif type == "avery5168":
    # Big shipping labels, 4 per page
    return SheetSpec(left_margin=31.0,
                     bottom_margin=33.0,
                     label_width=254.0,
                     label_height=363.0,
                     horiz_space=37.0,
                     vert_space=0.0,
                     horiz_num_labels=2.0,
                     vert_num_labels=2.0,
                     font_name="Arial",
                     font_size=33.0)

  elif type == "avery5444":
    # Really big shipping labels, 2 per page.
    return SheetSpec(left_margin=164.25,
                     bottom_margin=408.0,
                     label_width=290.0,
                     label_height=145.0,
                     horiz_space=0.0,
                     vert_space=54.0,
                     horiz_num_labels=1.0,
                     vert_num_labels=2.0,
                     font_name="Arial",
                     font_size=18.0)

  elif type == "avery5264":
    # Moderately big shipping labels, 6 per page
    return SheetSpec(left_margin=20.0,
                     bottom_margin=25.0,
                     label_width=270.0,
                     label_height=245.0,
                     horiz_space=37.0,
                     vert_space=0.0,
                     horiz_num_labels=2.0,
                     vert_num_labels=3.0,
                     font_name="Arial",
                     font_size=24.0)

  elif (   type == "avery5160"
        or type == "avery5260"
        or type == "avery5560"
        or type == "avery5660"
        or type == "avery5960"
        or type == "avery5970"
        or type == "avery5971"
        or type == "avery5972"
        or type == "avery5979"
        or type == "avery5980"
        or type == "avery6241"
        or type == "avery6460"
        or type == "avery8660" # But offset differently from 5160 etc?
        or type == "avery6245" # Not listed on Avery's equivalence sheet.
        or type == "macoll5805"):
    # Large address labels, 30 per page
    return SheetSpec(left_margin=11.25,
                     bottom_margin=16.0,
                     label_width=180.0,
                     label_height=72.0,
                     horiz_space=20.0,
                     vert_space=0.0,
                     horiz_num_labels=3.0,
                     vert_num_labels=10.0,
                     font_name="Times-Roman",
                     font_size=12.0)

  elif type == "avery7162":
    # Large and wide address labels, 16 per page
    # Added by nathanh{_AT_}manu.com.au 20031125
    return SheetSpec(left_margin=18.0,
                     bottom_margin=28.0,
                     label_width=281.0,
                     label_height=96.0,
                     horiz_space=20.0,
                     vert_space=0.0,
                     horiz_num_labels=2.0,
                     vert_num_labels=8.0,
                     font_name="Times-Roman",
                     font_size=12.0)

  elif type == "avery7163":
    # Large and wide address labels, 14 per page
    # Added by chrisjrob{_AT_}gmail.com 20120721
    return SheetSpec(left_margin=14.2,
                     bottom_margin=42.5,
                     label_width=280.6,
                     label_height=107.7,
                     horiz_space=8.5,
                     vert_space=0,
                     horiz_num_labels=2.0,
                     vert_num_labels=7.0,
                     font_name="Arial",
                     font_size=11.0)

  elif type == "avery7160":
    # Large address labels, 21 per A4 page
    k = 72.0/25.4             # Convert mm to points
    return SheetSpec(left_margin=(k * 10.25),
                     bottom_margin=(k * 19.0),
                     label_width=(k * 56),
                     label_height=(k * 33.5),
                     horiz_space=(k * 10.75),
                     vert_space=(k * 4.5),
                     horiz_num_labels=3.0,
                     vert_num_labels=7.0,
                     font_name="Times-Roman",
                     font_size=11.0)

  elif type == "avery6571":
    # 32 labels per page; more than that I don't know.  Ask
    # William R Thomas <corvar{_AT_}theonering.net>, who sent it in.
    return SheetSpec(left_margin=60.0,
                     bottom_margin=38.0,
                     label_width=216.0,
                     label_height=45.0,
                     horiz_space=58.0,
                     vert_space=0.0,
                     horiz_num_labels=2.0,
                     vert_num_labels=16.0,
                     font_name="Times-Roman",
                     font_size=7.0)



  elif (   type == "avery5167"
        or type == "avery5267"
        or type == "avery5667"
        or type == "avery6467"
        or type == "avery8167"
        or type == "macoll8100"):
    # Small address labels, 80 per page
    return SheetSpec(left_margin=14.0,
                     bottom_margin=17.0,
                     label_width=126.0,
                     label_height=36.0,
                     horiz_space=22.5,
                     vert_space=0.0,
                     horiz_num_labels=4.0,
                     vert_num_labels=20.0,
                     font_name="Times-Roman",
                     font_size=7.0)

  elif type == "avery5371" or type == "macoll8550":
    # Business cards, 10 per page
    return SheetSpec(left_margin=48.0,
                     bottom_margin=16.0,
                     label_width=253.5,
                     label_height=145.3,
                     horiz_space=0.0,
                     vert_space=0.0,
                     horiz_num_labels=2.0,
                     vert_num_labels=5.0,
                     font_name="Times-Roman",
                     font_size=0.0)

  elif (   type == "avery5263"
        or type == "avery5663"
        or type == "avery5963"
        or type == "avery8163"):
    # Big mailing labels, 10 per page.  Usually the TO address goes
    # on these.
    return SheetSpec(left_margin=48.0,
                     bottom_margin=31.0,
                     label_width=253.5,
                     label_height=145.3,
                     horiz_space=0.0,
                     vert_space=0.0,
                     horiz_num_labels=2.0,
                     vert_num_labels=5.0,
                     font_name="Times-Roman",
                     font_size=20.0)

  elif type == "avery7159":
    # Large address labels, 24 per A4 page
    # Avery-7159 3x8 A4 labels
    # Tested against a Kyocera bulk-laser printer.
    # Contributed by: Bruce Smith <Bruce.Smith {_AT_} nmmu.ac.za>
    k = 72.0/25.4             # Convert mm to points
    return SheetSpec(left_margin=(k * 0.0),
                     bottom_margin=(k * 0.0),
                     label_width=(k * 57.25),
                     label_height=(k * 32.5),
                     horiz_space=(k * 11.75),
                     vert_space=(k * 4.5),
                     horiz_num_labels=3.0,
                     vert_num_labels=8.0,
                     font_name="Times-Roman",
                     font_size=10.0)


  else:
    raise Exception("ERROR: Unknown label type '%s'.\n" % otype)


def parse_param_file(pfile):
  """Return a SheetSpec based on the contents of parameter file PFILE."""
  ctl = open(pfile, "r")
  spec = SheetSpec()
  line = ctl.readline()
  while (line):
    ### TODO: Why is it apparently optional to escape the backslash here?
    if re.match('\s*#|^\s*$', line):
      # Skip comment lines and blank lines.
      line = ctl.readline()
      continue
    key, val = line.split()
    if key[len(key) - 1] == ":":
      # Strip any trailing colon off the end of the key.  That enables
      # the output of 'labelnation -t foo --show-parameters' to be
      # used directly as the input via '--parameter-file'.
      key = key[0:len(key) - 1]
    key = normalize_string(key)
    if val:
      val = dedelimit_string(val)

    if key == "leftmargin":
      spec.left_margin = float(dedelimit_string(val))
    elif key == "bottommargin":
      spec.bottom_margin = float(dedelimit_string(val))
    elif key == "labelwidth":
      spec.label_width = float(dedelimit_string(val))
    elif key == "labelheight":
      spec.label_height = float(dedelimit_string(val))
    elif key == "horizspace":
      spec.horiz_space = float(dedelimit_string(val))
    elif key == "vertspace":
      spec.vert_space = float(dedelimit_string(val))
    elif key == "horiznumlabels":
      spec.horiz_num_labels = float(dedelimit_string(val))
    elif key == "vertnumlabels":
      spec.vert_num_labels = float(dedelimit_string(val))
    elif key == "fontname":
      spec.font_name = val
    elif key == "fontsize":
      spec.font_size = float(val)
    else:
      sys.stderr.write("ERROR: Unknown parameter line '%s'.\n" % line)
    line = ctl.readline()

  ctl.close()
  return spec


# Print version number.
def version():
  major = "1"
  minor = "$Revision: 218 $"
  minor = re.match('\S+\s+(\S+)\s+\S+', minor).group(1)
  version = major + "." + minor
  print "LabelNation, version %s" % version


# Print all predefined label types
def types():
  print '''Predefined label types:

  2 labels per page:           Avery-5444
  4 labels per page:           Avery-5168
  6 labels per page:           Avery-5264                             
  10 labels per page:          Avery-5263, 5663, 5963, 8163
  20 labels per page:          Avery-5161, 5261, 5661, 5961
  14 labels per page:          Avery-5162, 5262, 5662, 5962, 8162, 8252, 8462,
                                     15162, 18162, 18662
  30 labels per page:          Avery-5160, 5260, 5660, 5960, 5970, 5971, 5972
                                     5979, 5980, 6241, 6460, 6245, 8660
                               Brady-Lasertab-53-361
                               Maco-LL5805
  80 labels per page:          Avery-5167, 5267, 5667, 6467, 8167
                               Maco-LL8100                            
  10 business cards per page:  Avery-5371, Maco-LL8550
  45 labels per page:          Brady-Lasertab-52-361
  49 labels per page:          Cable-Labels-LSL-77 (or "-LS10-77S")
  84 35mm slides per page:     SlidePro, SlideScribe
  16 labels per page:          Avery-7162
  14 labels per page:          Avery-7163
  32 labels per page:          Avery-6571
  21 labels per A4 page:       Avery-7160
  24 labels per A4 page:       Avery-7159
  65 labels per A4 page:       Avery-2651, 7651
  8 labels per 10" page:       Avery-2160, Maverick-ST340817

Remember to include the brand when specifying a label type; for example,
say "avery-5979" not "5979".'''


# Print a general explanation of how this program works.
def explain():
  print '''LabelNation is a program for making labels: address labels,
business cards, or anything else involving regularly-arranged
rectangles on a printer-ready sheet.

Here's the basic concept: you tell LabelNation what text you want on
each label (i.e., each rectangle).  You can specify plain lines of
text, or even arbitrary PostScript code.  You also tell it what kind
(i.e., brand) of labels it should print for.  LabelNation takes all
this information and produces a PostScript file, which you then send
to your printer.

Of course, you'll need a PostScript printer (or a PostScript filter,
such as GNU GhostScript), and a sheet of special peel-off label paper
in the tray.  Such paper is widely available at office supply stores.
Two companies that offer it are Avery Dennison (www.averydennison.com)
and Maco (www.maco.com).  This is not a recommendation or an
endorsement -- Avery and Maco are simply the ones I've used.

PostScript viewing software such as Ghostview also helps, so you can
see what your labels look like before you print.

How To Use It:
==============

Let's start with return address labels.  If you wanted to print a
sheet of them using the Avery 5167 standard (80 small labels per
page), you might invoke LabelNation like this:

   prompt$ labelnation -t avery5167 -i myaddress.txt -l -o myaddress.ps

The "-t" stands for "type", followed by one of the standard predefined
label types.  The "-i" means "input file", that is, where to take the
label data from.  The "-l" stands for "lines input", meaning that the
format of the incoming data is lines of text (as opposed to PostScript
code).  The "-o" specifies the output file, which you'll print to get
the labels.

Here is a sample label lines file:

        J. Random User
        1423 W. Rootbeer Ave
        Chicago, IL 60622
        USA

Note that the indentation is significant -- the farther you indent a
line, the more whitespace will be between it and the left edge of the
label.  Three spaces is a typical indentation.  Also note that blank
lines are significant -- they are printed like any other text.

You can have as many lines as you want on a label; fonts will be
automatically scaled down if there are too many lines to fit using the
default font size.


How To Print A Variety Of Addresses:
====================================

An input file can also define many different labels (this is useful if
you're running a mailing list, for example).  In that case, instead of
iterating one label over an entire sheet, LabelNation will print each
label once, using as many sheets as necessary and leaving the unused
remainder blank.

To print many labels at once, you need to communicate all the
different label texts to LabelNation.  There are two ways to do this:

   1) Passing custom-delimited text, using "-d" to specify the delimiter.
   2) Passing comma-separated value (CSV) text, using the "--csv" option.

We'll cover each way below:

1) Passing custom-delimited text, using "-d" to specify the delimiter.

The delimiter is a special string (sequence of characters), on a line
by itself, that separates each label from the next.  For example, if
you use a delimiter of "XXXXX", then you might invoke LabelNation like so

   prompt$ labelnation -d "XXXXX" -t avery5167 -l -i addrs.txt -o addrs.ps

where the file addrs.txt contains this:

        J. Random User
        1423 W. Rootbeer Ave
        Chicago, IL 60622
        USA
   XXXXX
        William Lyon Phelps III
        27 Rue d'Agonie
        Paris, France
   XXXXX

Remember that all the examples are indented three spaces in this help
message, so the address lines above are actually indented only five
spaces in the file, while the XXXXX delimiters are not indented at all.

2) Passing comma-separated value (CSV) text, using the "--csv" option.

Use a command like this:

   prompt$ labelnation --leading-spaces 3 --csv -t avery5167 -i addrs.csv -o addrs.ps

where the file addrs.csv contains this:

   "J. Random User","1423 W. Rootbeer Ave","Chicago, IL 60622","USA"
   "William Lyon Phelps III","27 Rue d'Agonie","Paris, France"

...etc, etc.

The "--leading-spaces 3" part of the command is optional.  It's just a
way to left-pad the labels with some blank space, to better center the
text on each label.  You can adjust the number as needed, or leave off
the option entirely if your labels look fine without extra padding.

See http://en.wikipedia.org/wiki/Comma-separated_values for more about
CSV.  CSV is a fairly common text format, and most spreadsheets and
databases can easily export their data to it.  The flavor of CSV that
LabelNation expects is fairly standard:

  * There is one record per line; each record is a sequence of fields.

  * Each field is enclosed is a pair of double-quote marks ("'s).
    Within the double-quotes marks, a comma is just a comma, and two
    consecutive double-quotes marks escapes to a single quotation
    mark (see the example below).

  * Each field is separated from the next field by a single comma
    (no whitespace between the comma and the next quotation mark).

  * There is no trailing comma at the end of the line.

For example:

  "Ernest and Bertrand Muppet","123 Sesame Street","New York, NY 11123"
  "Elvis ""The King"" Presley","222 N. Danny Thomas Boulevard","Memphis, TN 37522"
  "Georgia O'Keefe","The Art Institute of Chicago","111 South Michigan Avenue","Chicago, IL 60603-6404"


How To Discover The Predefined Label Types:
===========================================

To see a list of all known label types, run

   prompt$ labelnation --list-types
   Predefined label types:
      Avery-5160 / Avery-6245 / Maco-LL5805  (30 labels per page)
      Avery-5167 / Maco-LL8100               (80 labels per page)
      [etc...]

Note that when you're specifying a label type, you can omit the
capitalization and the hyphen (or you can leave them on -- LabelNation
will recognize the type either way).

A bit farther on, you'll learn how to define your own label types, in
case none of the built-in ones are suitable.


What To Do If The Text Is A Little Bit Off From The Labels:
===========================================================

Printers vary -- the label parameters that work for me might not be
quite right for your hardware.  Correcting the problem may merely be a
matter of adjusting the bottom and/or left margin (that is, the
distance from the bottom or left edge of the page to the first row or
column, respectively).

The two options to do this are

   prompt$ labelnation --bottom-margin N --left-margin N ...

where N is a number of PostScript points, each being 1/72 of an inch.
(Of course, you don't have to use the two options together, that's
just how it is in this example.)  The N you specify does not add to
the predefined quantity, but rather replaces it.

In order to know where you're starting from, you can ask LabelNation
to show you the parameters for a given label type:

   prompt$ labelnation -t avery5167 --show-parameters
   LeftMargin      14
   BottomMargin    17
   LabelWidth      126
   LabelHeight     36
   HorizSpace      22.5
   VertSpace       0
   HorizNumLabels  4
   VertNumLabels   20
   FontName        Times-Roman
   FontSize        7

The first two parameters are usually the only ones you need to look
at, although the others may come in handy when you're defining your
own parameter files.  Which brings me to the next subject...


How To Print Labels That Aren't One Of The Predefined Standards:
================================================================

Use the -p option to tell LabelNation to use a parameter file.  A
parameter file consists of lines of the form

   PARAMETER   VALUE
   PARAMETER   VALUE
   PARAMETER   VALUE
   ...

You can see valid parameter names by running

   prompt$ labelnation -t avery5167 --show-parameters

as mentioned earlier (it doesn't have to be avery5167, it can be any
built-in type).  Keep in mind that a "parameter file" is for
specifying the dimensions and arrangement of the labels on the sheet,
*not* for specifying the content you want printed on those labels.


How To Use Arbitrary Postscript Code To Draw Labels:
====================================================

If your input file contains PostScript code to draw the label(s),
instead of lines of label text, then pass the "-c" (code) option
instead of "-l".

The PostScript code will be run in a translated coordinate space, so
0,0 is at the bottom left corner of each label in turn.  Also,
clipping will be in effect, so you can't draw past the edges of a
label.  Normally, you will have to experiment a lot to get things just
right.

You can still print multiple, different labels at
once -- delimiters work just as well in code files as in linetext
files.

One user reported that he had to do some trickery to get encapsulated
PostScript to work right:

   From: Simon Wood <Simon.Wood {_AT_} pace.co.uk>
   Subject: RE: Graphical Labels with labelnation.
   To: "'kfogel {_AT_} red-bean.com'" <kfogel {_AT_} red-bean.com>
   Date: Mon, 20 May 2002 08:54:57 +0100
   
   I managed to get some really simple graphics in last year (for a crop 
   of plum chutney). I'll send you the files from home. The image was 
   created in Dia and then exported to '.eps'.
   
   The trick was to remove the header from the '.ps', run labelnation to 
   size and position the images and then manually re-insert the header into
   the start of 'labelnation.ps'. 


How To Report A Bug:
====================

Check http://www.red-bean.com/labelnation/ to make sure you have the
latest version (perhaps your bug has been fixed).  Else, see the
instructions there for reporting bugs.

Copyright:
==========

    LabelNation: command-line label printing
    Copyright (C) 2000  Karl Fogel <kfogel {_AT_} red-bean.com>

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, write to the Free Software
    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
'''

def usage():
  version()
  print ''
  explain()
  print ''
  types()
  print ''
  print '''Options:

   -h, --help, --usage, -?     Show this usage
   --version                   Show version number
   --explain                   Show instructions (lots of output!)
   --list-types                Show all predefined label types
   -t, --type TYPE             Generate labels of type TYPE
   -p, --parameter-file FILE   Read label parameters from FILE
   -i, --infile                Take input from FILE ("-" means stdin)
   -l, --line-input            Input contains label text lines (default)
   -c, --code-input            Input contains PostScript code
   --csv, --csv-input          Input is Comma-Separated Value (CSV) format
   --leading-spaces N          Left-pad label text by N spaces (CSV & line only)
   -d, --delimiter DELIM       Labels separated by DELIM lines
   --min-label-lines N         Pad each label to N lines using blanks if needed
   --show-bounding-box         Print rectangle around each label
                               (recommended for testing only)
   --first-label N             Start printing at label number N
                               (bottom left is 1, count up each
                               column in turn, top right is last)
   --font-name NAME            Use PostScript font FONT
   --font-size SIZE            Scale font to SIZE
   -o, --outfile FILE          Output to FILE ("-" means stdout)'''

# The single quote in this comment resets Python Mode's highlighting.

def make_clipping_func(label_height, label_width, inner_margin,
                       show_bounding_box):
  """Return the code for a PostScript clipping function for the labels
  being generated, given the necessary parameters."""
  clipper = ''

  upper_bound = label_height - inner_margin
  right_bound = label_width  - inner_margin

  clipper += '\tnewpath\n'
  clipper += '\t%f %f moveto\n' % (inner_margin, inner_margin)
  clipper += '\t%f %f lineto\n' % (right_bound, inner_margin)
  clipper += '\t%f %f lineto\n' % (right_bound, upper_bound)
  clipper += '\t%f %f lineto\n' % (inner_margin, upper_bound)
  clipper += '\tclosepath\n'
  clipper += '\tclip\n'

  if show_bounding_box:
    clipper += '\tstroke\n'

  return clipper


def set_up_iso8859(output):
  output.write('''/deffont {
  findfont exch scalefont def
} bind def

/reencode_font {
  findfont reencode 2 copy definefont pop def
} bind def

% reencode the font
% <encoding-vector> <fontdict> -> <newfontdict>
/reencode { %def
  dup length 5 add dict begin
    { %forall
      1 index /FID ne
      { def }{ pop pop } ifelse
    } forall
    /Encoding exch def

    % Use the font's bounding box to determine the ascent, descent,
    % and overall height; don't forget that these values have to be
    % transformed using the font's matrix.
    % We use 'load' because sometimes BBox is executable, sometimes not.
    % Since we need 4 numbers an not an array avoid BBox from being executed
    /FontBBox load aload pop
    FontMatrix transform /Ascent exch def pop
    FontMatrix transform /Descent exch def pop
    /FontHeight Ascent Descent sub def

    % Define these in case they're not in the FontInfo (also, here
    % they're easier to get to.
    /UnderlinePosition 1 def
    /UnderlineThickness 1 def

    % Get the underline position and thickness if they're defined.
    currentdict /FontInfo known {
      FontInfo

      dup /UnderlinePosition known {
        dup /UnderlinePosition get
        0 exch FontMatrix transform exch pop
        /UnderlinePosition exch def
      } if

      dup /UnderlineThickness known {
        /UnderlineThickness get
        0 exch FontMatrix transform exch pop
        /UnderlineThickness exch def
      } if

    } if
    currentdict
  end
} bind def

/ISO-8859-1Encoding [
/.notdef /.notdef /.notdef /.notdef /.notdef /.notdef /.notdef /.notdef
/.notdef /.notdef /.notdef /.notdef /.notdef /.notdef /.notdef /.notdef
/.notdef /.notdef /.notdef /.notdef /.notdef /.notdef /.notdef /.notdef
/.notdef /.notdef /.notdef /.notdef /.notdef /.notdef /.notdef /.notdef
/space /exclam /quotedbl /numbersign /dollar /percent /ampersand /quoteright
/parenleft /parenright /asterisk /plus /comma /minus /period /slash
/zero /one /two /three /four /five /six /seven
/eight /nine /colon /semicolon /less /equal /greater /question
/at /A /B /C /D /E /F /G
/H /I /J /K /L /M /N /O
/P /Q /R /S /T /U /V /W
/X /Y /Z /bracketleft /backslash /bracketright /asciicircum /underscore
/quoteleft /a /b /c /d /e /f /g
/h /i /j /k /l /m /n /o
/p /q /r /s /t /u /v /w
/x /y /z /braceleft /bar /braceright /asciitilde /.notdef
/.notdef /.notdef /.notdef /.notdef /.notdef /.notdef /.notdef /.notdef
/.notdef /.notdef /.notdef /.notdef /.notdef /.notdef /.notdef /.notdef
/.notdef /.notdef /.notdef /.notdef /.notdef /.notdef /.notdef /.notdef
/.notdef /.notdef /.notdef /.notdef /.notdef /.notdef /.notdef /.notdef
/space /exclamdown /cent /sterling /currency /yen /brokenbar /section
/dieresis /copyright /ordfeminine /guillemotleft /logicalnot /hyphen /registered /macron
/degree /plusminus /twosuperior /threesuperior /acute /mu /paragraph /bullet
/cedilla /onesuperior /ordmasculine /guillemotright /onequarter /onehalf /threequarters /questiondown
/Agrave /Aacute /Acircumflex /Atilde /Adieresis /Aring /AE /Ccedilla
/Egrave /Eacute /Ecircumflex /Edieresis /Igrave /Iacute /Icircumflex /Idieresis
/Eth /Ntilde /Ograve /Oacute /Ocircumflex /Otilde /Odieresis /multiply
/Oslash /Ugrave /Uacute /Ucircumflex /Udieresis /Yacute /Thorn /germandbls
/agrave /aacute /acircumflex /atilde /adieresis /aring /ae /ccedilla
/egrave /eacute /ecircumflex /edieresis /igrave /iacute /icircumflex /idieresis
/eth /ntilde /ograve /oacute /ocircumflex /otilde /odieresis /divide
/oslash /ugrave /uacute /ucircumflex /udieresis /yacute /thorn /ydieresis
] def
''')

# This comment resets Emacs Python Mode's indentation.  Sigh.

def make_labels(spec, infile, input_type, delimiter, leading_spaces,
                outfile, show_bounding_box, min_label_lines=0):
  '''Using SheetSpec SPEC, read INPUT_TYPE data from INFILE
  (separated by DELIMITER if there are multiple different labels in
  INFILE, else DELIMITER is None), and write PostScript to OUTFILE.

  INPUT_TYPE is "line", "code", or "csv".

  LEADING_SPACES is number of spaces by which to left-pad each line of
  label text; use 0 (not None) to achieve no padding.

  If SHOW_BOUNDING_BOX is true, then draw a rectangle around each label.

  MIN_LABEL_LINES sets a minimum number of lines for each label: if
  the text of a label has fewer than that number of lines, add blank
  lines to pad it out to MIN_LABEL_LINES.  It defaults to 0.'''
  inner_margin = 1

  if infile == '-':
    input = sys.stdin
  else:
    input = open(infile, "r")
  if outfile == '-':
    output = sys.stdout
  else:
    output = open(outfile, "w")

  if input_type == "csv":
    csv_reader = csv.reader(input)

  # Start off with standard Postscript header
  output.write("%!PS-Adobe-3.0\n")
  output.write("\n")
    
  # Re-encode the requested font, so we can handle ISO-8859 chars.
  set_up_iso8859(output)
  output.write("/ISO%s ISO-8859-1Encoding /%s reencode_font\n"
               % (spec.font_name, spec.font_name))

  # Set up subroutines
  clipfunc = make_clipping_func(spec.label_height, spec.label_width,
                                inner_margin, show_bounding_box)
  output.write("/labelclip {\n%s\n} def\n" % clipfunc)
  output.write("\n")
  output.write("% end prologue\n")
  output.write("\n")
  output.write("% set font type and size\n")
  output.write("ISO%s %d scalefont setfont\n"
               % (spec.font_name, spec.font_size))

  # Set up some loop vars.
  label_lines = [ ]     # Used only for line and csv input
  line_idx = 0          # Used only for line input
  code_accum = ''       # Used for both line input and code input
  page_number = 1       # Do you really need a comment?

  # See the end of the while loop below for an explanation of this flag.
  iterate_over_single_page = False

  # Horiz position (by label)
  x = int((spec.first_label - 1) / spec.vert_num_labels)

  # Vertical position (by label)
  y = int((spec.first_label - 1) % spec.vert_num_labels)

  overlong_label_warning_already_issued = False
  start_new_page = True
  if input_type == "csv":
    line = csv_reader.next() # is actually an array
  else:
    line = input.readline()
  while line or iterate_over_single_page:
    if not iterate_over_single_page:
      if input_type != "csv":
        line = line.rstrip()

    if (input_type == "csv" or (delimiter is not None and line == delimiter)
        or iterate_over_single_page):
      if input_type == "csv":
        label_lines = line # cheap trick
      if input_type != "code":
        num_lines = len(label_lines)
        if num_lines < min_label_lines:
          label_lines += [''] * (min_label_lines - num_lines)
          num_lines = min_label_lines

        # Left-pad each line of text if any such padding requested.
        label_lines = [" " * leading_spaces + line for line in label_lines]

        # Sometimes people forget to pass the --delimiter flag.  When
        # they forget, labelnation naturally interprets all the lines
        # in the input as being for one label (to be iterated over the
        # entire page).  However, when any PostScript interpreter
        # tries to render that label, it will choke, usually giving an
        # incomprehensible error.  Since labelnation will be long gone
        # by then, we try to detect this situation here and warn the
        # user that they probably forgot to pass --delimiter.
        #
        # 8 lines per label on a 20-vertical-labels-per-sheet spec, or
        # 16 lines on a 10-vert spec, seems like a safe threshold at
        # which to assume the user probably goofed, and warn them.
        if num_lines >= (160 / spec.vert_num_labels):
          if not overlong_label_warning_already_issued:
            sys.stderr.write("WARNING: This label is unusually long; ")
            sys.stderr.write("it might even cause a PostScript error.\n")
            sys.stderr.write("WARNING: Did you perhaps forget to pass "
                             "the --delimiter option?\n")
            sys.stderr.write("WARNING: (See 'labelnation --help' for "
                             "more information.)\n")
            overlong_label_warning_already_issued = True

        text_margin = inner_margin + 2.0
        ### TODO: need to be more sophisticated about divining the
        # font sizes and acting accordingly, here.
        upmost_line_start = spec.label_height / (num_lines + 1.0) \
                            * float(num_lines)
        distance_down = spec.label_height / (num_lines + 2.0)
        fontsize = spec.font_size / (1.0 + ((num_lines - 4.0) / 10.0))
        
        code_accum += "newpath\n"
        code_accum += "ISO%s %d scalefont setfont\n" % (spec.font_name,
                                                        fontsize)
        for label_line in range(0, num_lines):
          this_line = upmost_line_start - (label_line * distance_down)
          code_accum += "%f %f moveto\n" % (text_margin, this_line)
          # code_accum += "moveto\n"
          code_accum += "(" + label_lines[label_line] + ") show\n"
          # code_accum += "show\n"
        code_accum += "stroke\n"

      if start_new_page:
        output.write("%%%%Page: labels %d\n\n" % page_number)
        output.write("%%BeginPageSetup\n")
        output.write("%f " % spec.left_margin)
        output.write("%f " % spec.bottom_margin)
        output.write("translate\n")
        output.write("%%EndPageSetup\n\n")
        start_new_page = False
      
      # Print the label, clipped and translated appropriately.
      this_x_step = x * (spec.label_width + spec.horiz_space)
      this_y_step = y * (spec.label_height + spec.vert_space)
      output.write("gsave\n")
      output.write("%d %d\n" % (this_x_step, this_y_step))
      output.write("translate\n")
      output.write("labelclip\n")
      output.write(code_accum)
      output.write("grestore\n")
      output.write("\n")

      # Increment, and maybe cross a column or page boundary.
      y += 1
      if y >= spec.vert_num_labels:
        y = 0
        x += 1
      if x >= spec.horiz_num_labels:
        x = 0
        page_number += 1
        output.write("showpage\n")
        start_new_page = True

      # Reset everyone.
      if (delimiter is not None) or (input_type == "csv"):
        label_lines = [ ]
      code_accum = ''

    elif input_type != "code":
      # PostScript needs (, ), and \ escaped.
      line = line.replace('\\','\\\\')
      line = line.replace('(','\\(')
      line = line.replace(')','\\)')
      label_lines.append(line)

    elif input_type == "code":
      code_accum += line
      code_accum += "\n"

    if input_type == "csv":
      try:
        line = csv_reader.next()
      except StopIteration, e:
        break
    else:
      line = input.readline()

    # You are not going to believe this... let me explain:
    # 
    # When this code was in Perl, it was written with a goto.
    # 
    # We need to handle input files containing only a single label, that
    # is, input files with no delimiter, so every line that appears in
    # the input is part of the one label text.  Then this label is
    # mapped across the whole page, so we get a single page with the
    # same label on it.  That way it's as convenient to produce return
    # address labels as to generate outgoing mailing list sheets.
    #
    # Since there's no delimiter, we just jump straight to the printing
    # part in the 'while' loop above, and let it increment x and y as it
    # normally does.  So the conditional below behaves like the guard of
    # a 'for' loop, except it's after the fact, and it shares its body
    # with the file-reading loop.  We use iterate_over_single_page to
    # stop after one page, otherwise it would go on forever.  It starts
    # out false, but is set to True within the first iteration of the
    # loop if it is going to be set at all.
    if (input_type != "csv"
        and line == ""
        and delimiter is None
        and not (y >= spec.vert_num_labels)
        and not (x >= spec.horiz_num_labels)
        and not (iterate_over_single_page and x == 0 and y == 0)):
      iterate_over_single_page = True
    else:
      iterate_over_single_page = False
  
  if not (x == 0 and y == 0):
    output.write("\nshowpage\n")
  
  output.close()


def main():
  exit_cleanly = False
  show_parameters = False
  spec = SheetSpec()

  type = None                 # A predefined label type (e.g., avery5160).
  infile = None               # Holds PostScript code or text lines.
  line_input = False          # One kind of input infile can hold.
  code_input = False          # Another kind of input infile can hold.
  csv_input = False           # Yet another kind of input infile can hold.
  leading_spaces = 0          # Left-pad each line of label text by this.
  outfile = 'labelnation.ps'  # Poor default, but kept for compatibility.
  param_file = None           # File containing label dimensions.
  delimiter = None            # Separates labels in multi-label files.
  show_bounding_box = False   # Draw boxes around the labels.
  input_type = "line"         # The default.
  min_label_lines = 0         # The default.

  # If this gets set, we encountered unknown options and will exit at
  # the end of this subroutine.
  exit_with_admonishment = False

  if len(sys.argv) < 2:
    usage()
    sys.exit(1)

  try:
    opts, args = getopt.getopt(sys.argv[1:],
                               '?ht:p:i:lcd:o:',
                               ['help', 'usage',
                                'version',
                                'list-types',
                                'explain',
                                'show-parameters',
                                'type=',
                                'parameter-file=',
                                'infile=',
                                'line-input',
                                'csv',
                                'csv-input',
                                'code-input',
                                'leading-spaces=',
                                'first-label=',
                                'delimiter=',
                                'font-name=',
                                'font-size=',
                                'show-bounding-box',
                                'left-margin=',
                                'bottom-margin=',
                                'outfile=',
                                'min-label-lines=',
                                ])
  except getopt.GetoptError, e:
    sys.stderr.write("ERROR: " + str(e) + '\n\n')
    usage()
    sys.exit(1)

  for opt, value in opts:
    if opt == '--version':
      version()
      exit_cleanly = True
    elif opt == '--help' or opt == '-h' or opt == '-?' or opt == 'usage':
      usage()
      exit_cleanly = True
    elif opt == '--list-types':
      types()
      exit_cleanly = True
    elif opt == '--explain':
      explain()
      exit_cleanly = True
    elif opt == '--show-parameters':
      show_parameters = True
    elif opt == '-t' or opt == '--type':
      type = value
    elif opt == '-p' or opt == '--parameter-file':
      param_file = value
    elif opt == '-i' or opt == '--infile':
      infile = value
    elif opt == '-l' or opt == '--line-input':
      line_input = True
    elif opt == '-c' or opt == '--code-input':
      code_input = True
    elif opt == '--csv' or opt == '--csv-input':
      csv_input = True
    elif opt == '--leading-spaces':
      leading_spaces = int(value)
    elif opt == '--first-label':
      spec.first_label = int(value)
    elif opt == '-d' or opt == '--delimiter':
      delimiter = value
    elif opt == '--font-name':
      spec.font_name = value
    elif opt == '--font-size':
      spec.font_size = float(value)
    elif opt == '--show-bounding-box':
      show_bounding_box = True
    elif opt == '--left-margin':
      spec.left_margin = float(value)
    elif opt == '--bottom-margin':
      spec.bottom_margin = float(value)
    elif opt == '-o' or opt == '--outfile':
      outfile = value
    elif opt == '--min-label-lines':
      min_label_lines = int(value)
    else:
      sys.stderr.write("ERROR: Unrecognized option '%s'.\n" % opt)
      exit_with_admonishment = True

  if exit_cleanly:
    sys.exit(0)

  # Do file parsing _after_ command line options have been processed.

  # Absorb any explicit parameters first, so they dominate built-in
  # sheet spec values.
  if param_file is not None:
    spec.absorb(parse_param_file(param_file))

  # Finally, take any values from the built-in sheet spec.
  if type is not None:
    spec.absorb(sheetspec_for_type(type))

  if code_input and line_input:
    sys.stderr.write("ERROR: Cannot use both -l and -c.\n")
    exit_with_admonishment = True

  if csv_input and line_input:
    sys.stderr.write("ERROR: Cannot use both -l and --csv.\n")
    exit_with_admonishment = True

  if csv_input and code_input:
    sys.stderr.write("ERROR: Cannot use both -c and --csv.\n")
    exit_with_admonishment = True

  if leading_spaces and code_input:
    sys.stderr.write("ERROR: Cannot use both -c and --leading-spaces.\n")
    exit_with_admonishment = True

  if (not code_input and not line_input and not csv_input
      and not show_parameters):
    sys.stderr.write("ERROR: Must use one of -l, -c, or --csv.\n")
    exit_with_admonishment = True

  if line_input:
    input_type = "line"
  elif code_input:
    input_type = "code"
  elif csv_input:
    input_type = "csv"

  if show_parameters:
    if type is None:
        sys.stderr.write("ERROR: Must specify a label type with -t.\n")
        sys.exit(1)
    print spec
    sys.exit(0)

  # Check that required parameters have been found and are sane.
  if spec.left_margin is None:
    sys.stderr.write("ERROR: Missing required left-margin parameter.\n")
    exit_with_admonishment = True

  if spec.bottom_margin is None:
    sys.stderr.write("ERROR: Missing required bottom-margin parameter.\n")
    exit_with_admonishment = True

  if spec.label_width is None:
    sys.stderr.write("ERROR: Missing required label-width parameter.\n")
    exit_with_admonishment = True

  if spec.label_height is None:
    sys.stderr.write("ERROR: Missing required label-height parameter.\n")
    exit_with_admonishment = True

  if spec.horiz_space is None:
    sys.stderr.write("ERROR: Missing required horiz-space parameter.\n")
    exit_with_admonishment = True

  if spec.vert_space is None:
    sys.stderr.write("ERROR: Missing required vert-space parameter.\n")
    exit_with_admonishment = True

  if spec.horiz_num_labels is None:
    sys.stderr.write("ERROR: Missing required horiz-num-labels parameter.\n")
    exit_with_admonishment = True

  if spec.vert_num_labels is None:
    sys.stderr.write("ERROR: Missing required vert-num-labels parameter.\n")
    exit_with_admonishment = True

  if int(spec.first_label) != spec.first_label:
    sys.stderr.write("ERROR: First label %f is not an integer.\n"
                     % spec.first_label)
    exit_with_admonishment = True
  if spec.first_label < 1:
    sys.stderr.write("ERROR: First label %d too low; "
                     "must be at least 1.\n" % spec.first_label)
    exit_with_admonishment = True
  elif spec.first_label > spec.horiz_num_labels * spec.vert_num_labels:
    sys.stderr.write("ERROR: First label %d is too high; there are only "
                     "%d * %d == %d labels available.\n" \
                     % (spec.first_label,
                        spec.horiz_num_labels, spec.vert_num_labels,
                        spec.horiz_num_labels * spec.vert_num_labels))
    exit_with_admonishment = True

  if exit_with_admonishment:
    sys.stderr.write('Run "labelnation --help" to see usage.\n')
    sys.exit(1)

  make_labels(spec, infile, input_type, delimiter, leading_spaces,
              outfile, show_bounding_box, min_label_lines)





if __name__ == '__main__':
  main()
