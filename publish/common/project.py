#!/usr/local/bin/python25
"""
Classes used by the publication API clients and servers.
See bottom of file for examples

Michael DeHaan <mdehaan@lulu.com>
"""

import simplejson
import exceptions
import baseobj

class Project(baseobj.BaseData):
   """
   A project is the top level datastructure.
   It is the main unit of work for the Pub API.
   """

   def get_map(self):
      PROJECT_TYPE_CHOICES = [ "hardcover", "softcover", "ebook" ]
      ACCESS_TYPE_CHOICES = [ "private", "direct", "public" ]
      return {
          'content_id'          : [ 0,                    "int",              0],
          'allow_ratings'       : [ True,                 "boolean",          0],
          'project_type'        : [ None,                 "choice",           PROJECT_TYPE_CHOICES],
          'program_code'        : [ "",                   "string",           0],
          'access'              : [ None,                 "choice",           ACCESS_TYPE_CHOICES],
          'bibliography'        : [ Bibliography(),       Bibliography,       0],
          'isbn'                : [ Isbn(),               Isbn,               0],
          'physical_attributes' : [ PhysicalAttributes(), PhysicalAttributes, 0],
          'drm'                 : [ False,                "boolean",          0],
          'pricing'             : [ [],                   "list",             Pricing],
          'file_info'           : [ FileInfo(),           FileInfo,           0]
      }

class AuthorName(baseobj.BaseData):
   """
   Representation of an author
   """
   def get_map(self):
       return {
           "first_name"          : [ "", "string", 0 ],
           "last_name"           : [ "", "string", 0 ]
       }

class Bibliography(baseobj.BaseData):
   """
   Basic information about the Book/Project.
   """
   
   def get_map(self):
       return {
           "title"              : [ None, "string", 0],
           "authors"            : [ [],   "list",   AuthorName],
           # FIXME: we should publish a list of category numbers
           "category"           : [ None, "int",    0],
           "copyright_year"     : [ None, "int",    0],
           "description"        : [ None, "string", 0],
           "keywords"           : [ [],   "list",   "string"],
           "license"            : [ None, "string", 0],
           "copyright_citation" : [ None, "string", 0],
           "publisher"          : [ None, "string", 0],
           "edition"            : [ None, "string", 0],
           "language"           : [ None, "string", 0],
           "country_code"       : [ None, "string", 0],
       } 

class Isbn(baseobj.BaseData):

   """
   Information about the ISBN to be assigned, or intent to assign one.
   """


   def get_map(self):
      ISBN_INTENT_CHOICES = [ "provided", "assigned", "none" ]
      return {
          "intent"             : [ None,          "choice",     ISBN_INTENT_CHOICES ],
          "number"             : [ None,          "string",     0 ],
          "publisher"          : [ None,          "string",     0 ],
          "contact_info"       : [ ContactInfo(), ContactInfo,  0 ]
      }

class ContactInfo(baseobj.BaseData):
 
   """
   Who Provided The ISBN?
   """

   def get_map(self):
       return {
          "name"              : [ None, "string", 0 ],
          "street1"           : [ None, "string", 0 ],
          "street2"           : [ None, "string", 0 ],
          "city"              : [ None, "string", 0 ],
          "state"             : [ None, "string", 0 ],
          "postal_code"       : [ None, "string", 0 ],
          "country"           : [ None, "string", 0 ],
          "phone"             : [ None, "string", 0 ],
       }

class PhysicalAttributes(baseobj.BaseData):

   """
   Physical attributes of the Book, for Physical Projects...
   Not supplied for ebooks?
   """

   # FIXME: fix inconsistent casing and underscores vs hyphens in constants?
   def get_map(self):
       BINDING_TYPE_CHOICES = [ 'coil', 'perfect', 'saddle-stitch', \
                                'casewrap-hardcover', 'jacket-hardcover' ]
       TRIM_SIZE_CHOICES = [ 'US_LETTER', 'US_TRADE', 'COMIC', 'POCKET' \
                             'LANDSCAPE', 'SQUARE', 'SIZE_825x1075', \
                             'ROYAL', 'CROWN_QUARTO', 'A4', \
                             'LARGE_SQUARE', 'A5', 'DIGEST', ]
       PAPER_TYPE_CHOICES = [ 'regular', 'publisher-grade' ]
       return {
           "binding_type"    : [ None,  "choice", BINDING_TYPE_CHOICES],
           "trim_size"       : [ None,  "string", TRIM_SIZE_CHOICES],
           "paper_type"      : [ None,  "string", PAPER_TYPE_CHOICES],
           "color"           : [ False, "bool",   0],
       }

class Pricing(baseobj.BaseData):

   """
   Information about project pricing and revenue distribution
   """

   def get_map(self):
       # FIXME: add custom validators to invalidate negative pricing
       # or add a positive decimal type
       PRODUCT_CHOICES = [ 'print', 'download' ]
       return {
           "product"       : [ "print",  "string",  PRODUCT_CHOICES ],
           "currency_code" : [ "USD", "string",  0 ],
           "royalty"       : [ 0,  "currency", 0 ],
           "total_price"   : [ 0,  "currency", 0 ],
       }

class FileInfo(baseobj.BaseData):
   """
   Information about uploaded cover and source files
   """

   def get_map(self):
       return {
           "cover"        : [ [], "list", FileDetails ],
           "contents"     : [ [], "list", FileDetails ]
       }

class FileDetails(baseobj.BaseData):
   """
   Mime type and path to files
   """

   def get_map(self):
       return {
           "mimetype"   : [ "application/x-pdf", "string", 0 ],
           "filename"   : [ "",                  "string", 0 ]
       }

