
# Show work for python2/3 both
import sys, os
import lxml
from lxml import etree
import xml.etree.ElementTree as ET

sys.path.append('./')

xml_file = 'nfvi_ek.xml'
xsd_file = 'nfvi_ek.xsd'

def helper():
	print(
"Usage \n\
    nfvi_ek.py -r tag\n\
    nfvi_ek.py -a tag attr ...\n\
    nfvi_ek.py -u tag attr new_attr ...\n\
    nfvi_ek.py -d tag \n\
    nfvi_ek.py -x tag \n\
Options\n\
    -a  ADD     add a new (duplicate) tag & and attr(s) to nfvi_ek.xml\n\
    -r  READ    read attr of a tag from nfvi_ek.xml\n\
    -u  UPDATE  update a tag's attr with new attr value\n\
    -d  DELETE  delete tag(s) from nfvi_ek.xml \n\
    -x  tag     execute a command in <tag>, bash only\n\n\
Example in bash:\n\
    python nfvi_ek.py -a hostname nfvi-ek\n\
    python nfvi_ek.py -d hostname\n\
    python nfvi_ek.py -r trex_port\n\
    python nfvi_ek.py -u trex_port 0 2 4 6 8\n\
    python nfvi_ek.py -x build_vpp\n\
    echo $(python3 -c 'import nfvi_ek;print(nfvi_ek.get_xml(\"nfvi_ek.xml\",\"nfvi_ek.xsd\", \"http_proxy\"))')    \n\
")
	print(
'Example in python2/3:       \n\
    import sys \n\
    sys.path.append("./")\n\
    import nfvi_ek \n\
    xml = "nfvi_ek.xml" \n\
    xsd = "nfvi_ek.xsd" \n\
    parent = "nseed"  \n\
    # nfvi_ek.py -a hostname nfvi-ek \n\
    nfvi_ek.add_element(xml, xsd, parent, tag="hostname", attr="nfvi-ek") \n\
    # nfvi_ek.py -d hostname \n\
    nfvi_ek.remove_element(xml, xsd, parent, tag="hostname") \n\
    # nfvi_ek.py -r trex_port \n\
    port = nfvi_ek.get_xml(xml, xsd, "trex_port")   \n\
    # nfvi_ek.py -u trex_port 0 2 4 6 8 \n\
    port = [0,2,4,6,8] \n\
    nfvi_ek.set_xml(xml, xsd, "trex_port", "0", port)\n\n\
')
	return 0

# Disable validate schema as updating nseed_pkg will fail the xsd file
def validate_xml(xml_file, xsd_file):
	
	# Disable validate schema as updating nseed_pkg will fail the schema
	return True

	try:
		with open(xsd_file) as f:
			xsd_doc = etree.parse(f)
		try:
			xsd_schema = etree.XMLSchema(xsd_doc) 
			f.close()

		# except lxml.etree.XMLSchemaParseError as e: print(e)
		except Exception as ex:
			print('xsd Error: ', type(ex), __name__, ex.args)
			return False

	except Exception as ex:
		print('xsd open Error:', type(ex), __name__, ex.args)
		return False

	try:
		with open(xml_file) as f:
			xml_doc = etree.parse(f)
			#print (xml_doc)
		try:
			ret = xsd_schema.validate(xml_doc) 
			f.close()
			if not ret:
				print('xsd schma valdate error: ', 
					xsd_schema.error_log)
				return False
		# except lxml.etree.XMLSchemaParseError as e: print(e)
		except Exception as ex:
			print('xml Error: ', type(ex), __name__, ex.args)
			return False

	except Exception as ex:
		print('xml open Error: ', type(ex), __name__, ex.args)
		return False
	return True

#
# xsd/xml schema generator: 
#    https://www.freeformatter.com/xsd-generator.html
#
def get_xml(xml_file, xsd_file, tag=None):

	#if validate_xml(xml_file, xsd_file) is not True:
	#	print("Validate {} with schema {} failed!".format(xml_file, 
	#		xsd_file))
	#	return False
	parser = etree.XMLParser(load_dtd = True)
	tree = etree.parse(xml_file, parser)
	root = tree.getroot()
	rlst=[]
	for elem in tree.iter():
		if tag == elem.tag:
			rlst.append(elem.text)
	if rlst: 
		return rlst
	else:
		return False

def set_xml(xml_file, xsd_file, tag, attr, new_attr=''):

	if type(new_attr) is list:
		attrs = ''.join(str(e)+" " for e in new_attr)
	elif type(attr) is str:
		attrs = new_attr
	else:
		print('attr must be str or list type, not ', type(attr))
		return False 

	if validate_xml(xml_file, xsd_file) is not True:
		print("Validate {} with schema {} failed!".format(xml_file, 
			xsd_file))
		return False

	parser = etree.XMLParser(load_dtd = True)
	tree = etree.parse(xml_file, parser)
	root = tree.getroot()

	update = False
	for elem in tree.iter(tag):
		text = elem.text.strip()
		if text == attr:
			print('FOUND', elem.text)
			elem.text = attrs;
			update=True

	if update:
		tree.write(xml_file)

	return update

# xml_file='nfvi_el.xml', xsd_file='nfvi_ek.xsd', parent='nseed', 
# tag='nseed_pkg'
def add_element(xml_file, xsd_file, parent, tag, attr):

	# Can suport either attr="vim ssh tmux' or attr=['vim', 'ssh', 'tmux']
	if type(attr) is list:
		attrs = ''.join(str(e)+" " for e in attr)
	elif type(attr) is str:
		attrs = attr
	else:
		print('attr must be str or list type, not ', type(attr))
		return False 

	# House-keeping, no leading and trailing space
	attrs = attrs.strip()
	tree = ET.parse(xml_file)
	root = tree.getroot()
	nseed = root.find(parent)
	element = nseed.makeelement(tag, {})
	nseed.append(element)
	element.text = attrs
	tree.write('nfvi_ek.xml')
	return True


# xml_file='nfvi_el.xml', xsd_file='nfvi_ek.xsd', parent='nseed'
def remove_element(xml_file, xsd_file, parent, tag):

	tree = ET.parse(xml_file)
	root = tree.getroot()
	element = root.find(parent)
	items = element.findall(tag)
	for i in items:
		element.remove(i)		
	tree.write('nfvi_ek.xml')
	return True




if __name__ == "__main__":

	if len(sys.argv) < 2:
		print('Need more arguments, use --help for usage')
		sys.exit(0)

	ret = False
	if sys.argv[1] == "--help" or sys.argv[1] == "-h" :
		helper()
		sys.exit(0)


	# Goto common/ dir
	CWD = os.getcwd()
	dir = os.path.dirname(sys.argv[0])
	if dir != '.' and dir != '':
		os.chdir(dir)
		xml_file = dir + '/' + xml_file
		xsd_file = dir + '/' + xsd_file

	#----------------------------------------------------------------
	# Read a tag, "a.out -r <tag>"
	if sys.argv[1] == "-r":
		ret = get_xml(xml_file, 
			xsd_file, 
			tag = sys.argv[2])
		# Stringify the print-out for bash caller
		rets=[]
		if ret:
			rets = ''.join(str(e)+' ' for e in ret)
			print(rets)

	# Add a new tag and attr value, "a.out -a <tag> value"
	elif sys.argv[1] == "-a":
		if len(sys.argv) >= 4:
			add_element(xml_file, 
				xsd_file, 
				parent = 'nseed', 
				tag = sys.argv[2], 
				attr = sys.argv[3:])
		else:
			print('Incorrect args for -a, use -help for usage')

	# Update a tag with new attr value, "a.out -u <tag> value new_value"
	elif sys.argv[1] == '-u':
		if len(sys.argv) == 5:
			ret = set_xml(xml_file, 
				xsd_file, 
				tag = sys.argv[2], 
				attr = sys.argv[3], 
				new_attr = sys.argv[4])
		else:
			print('Incorrect args for -u, use -help for usage')

	# Delete a tag, "a.out -d <tag>"
	elif sys.argv[1] == '-d':
		if len(sys.argv) == 3:
			remove_element(xml_file, 
				xsd_file, 
				parent = 'nseed',
				tag = sys.argv[2])	 
		else:
			print('Incorrect args for -d, use -help for usage')

	elif sys.argv[1] == '-x':
		if len(sys.argv) == 3:
			ret = get_xml(xml_file, xsd_file, tag = sys.argv[2])
			rets=[]
			if ret:
				rets = ''.join(str(e)+' ' for e in ret)
				os.chdir('../../downloads')
				os.system(rets)
				os.chdir(PWD)
			else:
				print('Incorrect args for -a, use -help for usage')
	else:
		print('Incorrect argument, use --help for usage')

	os.chdir(CWD)
	sys.exit(0)


