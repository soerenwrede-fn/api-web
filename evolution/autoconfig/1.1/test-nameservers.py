#!/usr/bin/python
#
# Copyright (c) 2012 Matthew Barnes <mbarnes@redhat.com>
#
# This test does the following to emulate Evolution's account
# autoconfiguration feature:
#
#  1. Extract domain names from each XML file.
#  2. Query the authoritative name server for the domain.
#  3. Verify the name server's FQDN ends with the XML file name.
#
# Example:
#
#     The yahoo.com file has '<domain>rocketmail.com</domain>'.
#
#     $ dig ns rocketmail.com
#     ...
#     rocketmail.com.           154702  IN      NS      ns1.yahoo.com.
#     ...
#
#     >>> file='yahoo.com'
#     >>> ns='ns1.yahoo.com'
#     >>> assert ns.endswith(file)
#
# This test requires the 'dns' module from http://www.dnspython.org/.
#

import dns.resolver
import operator
import os
import xml.sax

missing = {}

class ClientConfig(xml.sax.ContentHandler):
	def startDocument(self):
		self.domains = []

	def startElement(self, tag, attrs):
		self.element = tag

	def endElement(self, tag):
		self.element = None

	def characters(self, data):
		if self.element == 'domain':
			self.domains.append(data)

handler = ClientConfig()

def file_exists(ns_domain):
	tokens = ns_domain.split('.')
	for n in range(len(tokens) - 1):
		filename = '.'.join(tokens[n:])
		if os.path.exists(filename):
			return True
	return False

def resolve_ns(domain, filename):
	try:
		answer = dns.resolver.query(domain, 'NS')
		for rdata in dns.resolver.query(domain, 'NS'):
			# Trim the trailing dot
			ns_domain = str(rdata)[:-1]
			if not file_exists(ns_domain):
				missing[ns_domain] = filename
		return True
	except dns.resolver.NoAnswer:
		print filename + ':',
		print 'No answer for DOMAIN', domain
		return False
	except dns.resolver.NXDOMAIN:
		print filename + ':',
		print 'No such DOMAIN', domain
		return False

for filename in os.listdir('.'):
	# Skip symbolic links
	if os.path.islink(filename):
		continue
	try:
		xml.sax.parse(filename, handler)
	except:
		print filename + ': Skipping'
		continue
	success = True
	for domain in handler.domains:
		if not os.path.exists(domain):
			os.symlink(filename, domain)
		if not resolve_ns(domain, filename):
			success = False
	if success: print filename + ': PASS'

print
print
print 'MISSING SYMLINKS'
print '----------------'
getvalue = operator.itemgetter(1)
for ns_domain, filename in sorted(missing.iteritems(), key=getvalue):
	print '%s: NS %s' % (filename, ns_domain)
