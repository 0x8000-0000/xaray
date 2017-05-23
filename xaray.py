#!/usr/bin/python

# Copyright 2017 Florin Iucha <florin@signbit.net>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys
import os
import io
import argparse
import zipfile
import hashlib

parser = argparse.ArgumentParser(description = "Report the inner structure of a Java Enterprise Application")
parser.add_argument('--verbose', '-v', action = 'count', help = "Be verbose")
parser.add_argument('--sort_checksum', '-s', action = 'store_true', help = "Sort by SHA1 checksum value")
parser.add_argument('--sort_name', '-n', action = 'store_true', help = "Sort by archive member name")
parser.add_argument('--duplicates', '-d', action = 'store_true', help = "Highlight duplicates")
parser.add_argument('input_file', help = "Input file")

args = parser.parse_args()

class Entry(object):
   def __init__(self, container, parent, name):
      self.container = container
      self.parent    = parent
      self.name      = name

      if parent is None:
         self.isZipFile = True
         self.digest = '000000000'
      else:
         self.content = io.BytesIO(self.container.read(self.name))
         self.isZipFile = zipfile.is_zipfile(self.content)

         if args.verbose > 2:
            print("%s is archive: %s" % (self.name, self.isZipFile))

         sha1 = hashlib.sha1()
         sha1.update(self.content.getvalue())
         self.digest = sha1.hexdigest()

   def isArchive(self):
      return self.isZipFile

   def getChildren(self):
      children = []

      if self.isZipFile:
         if self.parent is None:
            selfAsZip = self.container
         else:
            selfAsZip = zipfile.ZipFile(self.content, 'r')

         for name in selfAsZip.namelist():
            if not name.endswith('/'):
               entry = Entry(selfAsZip, self, name)
               children.append(entry)

      return children

   def getPath(self):
      if self.parent is None:
         return ''
      else:
         return self.parent.getPath() + self.parent.name + "/"

entries = []

jarFile = zipfile.ZipFile(args.input_file, 'r')

toProcess = [Entry(jarFile, None, '')]

while len(toProcess):

   entry = toProcess.pop(0)

   for child in entry.getChildren():
      entries.append(child)
      toProcess.append(child)

jarFile.close()

if args.duplicates:

   fileChecksums = {}
   for entry in entries:
      fileChecksums[entry.digest] = 1 + fileChecksums.get(entry.digest, 0)

if args.verbose > 2:
   print('-----------------------------------')

if args.sort_checksum:
   entries.sort(key = lambda x: x.digest)

   for entry in entries:

      if args.duplicates:
         count = fileChecksums[entry.digest]
         if count > 1:
            dup = "#%3d" % count
         else:
            dup = "    "
      else:
         dup = ""

      print("%s %s  %-40s   %s" % (entry.digest, dup, entry.getPath(), entry.name))

else: # args.sort_name:
   entries.sort(key = lambda x: (x.name + '/' + x.getPath()))

   for entry in entries:
      if args.duplicates:
         count = fileChecksums[entry.digest]
         if count > 1:
            dup = "#%3d" % count
         else:
            dup = "    "
      else:
         dup = ""

      print("%-64s %s %s %s" % (entry.name, dup, entry.getPath(), entry.digest))
