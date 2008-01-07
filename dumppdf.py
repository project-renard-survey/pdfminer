#!/usr/bin/env python
#
# dumppdf.py - dump pdf contents in XML format.
#
#  usage: dumppdf.py [options] [files ...]
#  options:
#    -i objid : object id
#
import sys, re
from pdfparser import PDFDocument, PDFParser, PDFStream, \
     PDFObjRef, PSKeyword, PSLiteral
stdout = sys.stdout
stderr = sys.stderr


ESC_PAT = re.compile(r'[\000-\037&<>\042\047\134\177-\377]')
def esc(s):
  return ESC_PAT.sub(lambda m:'\\x%02x' % ord(m.group(0)), s)


# dumpxml
def dumpxml(out, obj):
  if isinstance(obj, dict):
    out.write('<dict size="%d">\n' % len(obj))
    for (k,v) in obj.iteritems():
      out.write('<key>%s</key>\n' % k)
      out.write('<value>')
      dumpxml(out, v)
      out.write('</value>\n')
    out.write('</dict>')
    return
  
  if isinstance(obj, list):
    out.write('<list size="%d">\n' % len(obj))
    for v in obj:
      dumpxml(out, v)
      out.write('\n')
    out.write('</list>')
    return
  
  if isinstance(obj, str):
    out.write('<string size="%d">%s</string>' % (len(obj), esc(obj)))
    return
  
  if isinstance(obj, PDFStream):
    props = obj.dic.copy()
    if 'Filter' in props:
      del props['Filter']
    if 'DecodeParms' in props:
      del props['DecodeParms']
    out.write('<stream>\n<props>\n')
    dumpxml(out, props)
    data = obj.get_data()
    out.write('\n</props>\n')
    out.write('<data size="%d">%s</data>\n' % (len(data), esc(data)))
    out.write('</stream>')
    return
  
  if isinstance(obj, PDFObjRef):
    out.write('<ref id="%d"/>' % obj.objid)
    return
  
  if isinstance(obj, PSKeyword):
    out.write('<keyword>%s</keyword>' % obj.name)
    return

  if isinstance(obj, PSLiteral):
    out.write('<literal>%s</literal>' % obj.name)
    return
  
  if isinstance(obj, int) or isinstance(obj, float):
    out.write('<number>%s</number>' % obj)
    return

  raise TypeError(obj)

# dumptrailers
def dumptrailers(out, doc):
  for xref in doc.xrefs:
    out.write('<trailer objid0="%d" objid1="%d">\n' %
              (xref.objid0, xref.objid1))
    dumpxml(out, xref.trailer)
    out.write('\n</trailer>\n\n')
  return

# dumpallobjs
def dumpallobjs(out, doc):
  out.write('<pdf>')
  for xref in doc.xrefs:
    for objid in xrange(xref.objid0, xref.objid1+1):
      try:
        obj = doc.getobj(objid)
        out.write('<object id="%d">\n' % objid)
        dumpxml(out, obj)
        out.write('\n</object>\n\n')
      except:
        pass
  dumptrailers(out, doc)
  out.write('</pdf>')
  return

# dumppdf
def dumppdf(outfp, fname, objids, pageids,
            dumpall=False, binary=False, debug=0):
  doc = PDFDocument(debug=debug)
  fp = file(fname)
  parser = PDFParser(doc, fp, debug=debug)
  if objids:
    for objid in objids:
      obj = doc.getobj(objid)
      if binary and isinstance(obj, PDFStream):
        outfp.write(obj.get_data())
      else:
        dumpxml(outfp, obj)
  if pageids:
    for page in doc.get_pages():
      if page.pageid in pageids:
        dumpxml(outfp, page.attrs)
  if dumpall:
    dumpallobjs(outfp, doc)
  if (not objids) and (not pageids) and (not dumpall):
    dumptrailers(outfp, doc)
  fp.close()
  outfp.write('\n')
  return


# main
def main(argv):
  import getopt
  def usage():
    print 'usage: %s [-d] [-a] [-b] [-p pageid] [-i objid] file ...' % argv[0]
    return 100
  try:
    (opts, args) = getopt.getopt(argv[1:], 'dabi:p:')
  except getopt.GetoptError:
    return usage()
  if not args: return usage()
  debug = 0
  objids = []
  pageids = set()
  binary = False
  dumpall = False
  outfp = stdout
  for (k, v) in opts:
    if k == '-d': debug += 1
    elif k == '-i': objids.append(int(v))
    elif k == '-p': pageids.add(int(v))
    elif k == '-a': dumpall = True
    elif k == '-b': binary = True
    elif k == '-o': outfp = file(v, 'w')
  #
  for fname in args:
    dumppdf(outfp, fname, objids, pageids,
            dumpall=dumpall, binary=binary, debug=debug)
  return

if __name__ == '__main__': sys.exit(main(sys.argv))
