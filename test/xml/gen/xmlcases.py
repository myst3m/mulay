import xml.parsers.expat, sys
cases = [
 "<a/>", "<a></a>", "<a>text</a>", "<a b='1' c=\"2\"/>", "<a><b/><c>t</c></a>",
 "<a>&lt;&gt;&amp;&apos;&quot;</a>", "<a>&#65;&#x42;&#x10FFFF;</a>", "<a>&#0;</a>", "<a>&#xD800;</a>",
 "<a>\u00e9\u3042</a>", "<a x='&lt;'/>", "<a x='<'/>", "<a x='\"'/>", "<a x=\"'\"/>",
 "<a>]]></a>", "<a>]]</a>", "<a><![CDATA[x]]y]]></a>", "<a><![CDATA[]]></a>",
 "<a><!-- ok - comment --></a>", "<a><!-- bad -- comment --></a>", "<a><!---></a>", "<a><!----></a>",
 "<a><?pi?></a>", "<a><?pi  data here ?></a>", "<a><?xml bad?></a>", "<a><?XmL bad?></a>", "<?xml version='1.0'?><a/>",
 "<?xml version='1.0' encoding='UTF-8' standalone='yes'?><a/>", "<?xml version='1.0' standalone='maybe'?><a/>",
 "<?xml encoding='UTF-8'?><a/>", "<?xml version='1.0' encoding='UTF-8' version='1.0'?><a/>",
 "<a></b>", "<a>", "</a>", "<a/><b/>", "text", "<a/>text", " <a/> ", "<a/><!--c--><?p?>",
 "<a b='1' b='2'/>", "<a b='1'b='2'/>", "<a b=1/>", "<a b/>", "<1a/>", "<a:b:c/>", "<:a/>", "<a:/>",
 "<p:a xmlns:p='u'/>", "<p:a/>", "<a xmlns:p='u'><p:b p:x='1' x='2'/></a>", "<a xmlns='u'><b xmlns=''/></a>",
 "<a xmlns:p='u' xmlns:q='u' p:x='1' q:x='2'/>", "<a xmlns:p=''/>", "<a xmlns:xml='http://www.w3.org/XML/1998/namespace'/>",
 "<a xmlns:xml='u'/>", "<a xmlns:xmlns='u'/>", "<a xml:lang='en'/>", "<a xmlns:p='http://www.w3.org/XML/1998/namespace'/>",
 "<!DOCTYPE a><a/>", "<!DOCTYPE a SYSTEM 'x.dtd'><a/>", "<!DOCTYPE a PUBLIC '-//X//Y' 'x.dtd'><a/>",
 "<!DOCTYPE a [<!ENTITY e 'v'>]><a>&e;</a>", "<!DOCTYPE a [<!ENTITY e 'v'>]><a x='&e;'/>",
 "<!DOCTYPE a [<!ENTITY e '<b>x</b>'>]><a>&e;</a>", "<!DOCTYPE a [<!ENTITY e '&#60;b/>'>]><a>&e;</a>",
 "<!DOCTYPE a [<!ENTITY e '&#38;#60;'>]><a>&e;</a>", "<!DOCTYPE a [<!ENTITY e 'x&f;'><!ENTITY f 'y'>]><a>&e;</a>",
 "<!DOCTYPE a [<!ENTITY e '&e;'>]><a>&e;</a>", "<!DOCTYPE a [<!ENTITY e 'v'><!ENTITY e 'w'>]><a>&e;</a>",
 "<!DOCTYPE a [<!ELEMENT a (#PCDATA)><!ATTLIST a x CDATA 'd'><!-- c --><?p x?>]><a/>",
 "<!DOCTYPE a [<!ENTITY % p 'x'>]><a/>", "<!DOCTYPE a [<!NOTATION n SYSTEM 'x'>]><a/>",
 "<a>&undef;</a>", "<a>&amp</a>", "<a>& b</a>", "<a>&#x;</a>", "<a>&#12a;</a>",
 "<a>\n  <b>  sp  </b>\n</a>", "<a\n  x = '1'\n  y\t=\t\"2\"\n/>", "<a x='a\tb\nc'/>", "<a x='a&#9;b&#10;c'/>",
 "<a></a >", "<a></ a>", "< a/>", "<a/ >", "<a b='1'/ >",
 "<!DOCTYPE a><!DOCTYPE a><a/>", "<a/><!DOCTYPE a>", "<!-- c --><!DOCTYPE a><a/>",
 "<a>\u0001</a>", "<a x='\u0001'/>", "<a>\ufffe</a>", "<a>\t\r\n</a>",
 "<a><b><c><d><e/></d></c></b></a>", "<é/>", "<a é='1'/>", "<a>x<![CDATA[y]]>z</a>",
 "<!DOCTYPE a [<!ENTITY e SYSTEM 'x'>]><a/>", "<!DOCTYPE a [<!ENTITY e SYSTEM 'x'>]><a>&e;</a>",
 "<!DOCTYPE a [ <!ENTITY e 'v' > ]><a>&e;</a>",
 "<!DOCTYPE a [<!ATTLIST a x CDATA 'd' y CDATA #IMPLIED z CDATA #FIXED 'f'>]><a y='1'/>",
 "<!DOCTYPE a [<!ATTLIST a x NMTOKENS 'd'>]><a x='  p   q  '/>", "<!DOCTYPE a [<!ATTLIST a x CDATA 'd'>]><a x='  p   q  '/>",
 "<!DOCTYPE a [<!ATTLIST a xmlns:p CDATA 'urn:p'>]><a><p:b/></a>", "<!DOCTYPE a [<!ATTLIST a x (u|v) 'u'>]><a/>",
 "<!DOCTYPE a [<!ENTITY e 'ev'><!ATTLIST a x CDATA '&e;!'>]><a/>", "<!DOCTYPE a [<!ATTLIST a x CDATA 'd'><!ATTLIST a x CDATA 'e'>]><a/>",
 "<!DOCTYPE a [<!ATTLIST b x CDATA 'd'>]><a><b/><c/></a>", "<!DOCTYPE a [<!ENTITY e \"it's\">]><a>&e;</a>",
]
def canon(doc):
    p = xml.parsers.expat.ParserCreate('UTF-8', ' ')
    p.ordered_attributes = True
    out = []
    buf = []
    def flush():
        if buf:
            out.append('T(' + ''.join(buf) + ')'); buf.clear()
    def q(n):
        if ' ' in n:
            u, l = n.split(' ', 1); return '{' + u + '}' + l
        return n
    def start(name, attrs):
        flush()
        a = ''.join(' %s=%s' % (q(attrs[i]), attrs[i+1]) for i in range(0, len(attrs), 2))
        out.append('S(' + q(name) + a + ')')
    def end(name):
        flush(); out.append('E(' + q(name) + ')')
    def cdata(t): buf.append(t)
    indtd = [False]
    def comment(t):
        if not indtd[0]: flush(); out.append('!(' + t + ')')
    def pi(t, d):
        if not indtd[0]: flush(); out.append('?(' + t + ',' + d + ')')
    def sd(*a): indtd[0] = True
    def ed(*a): indtd[0] = False
    p.StartDoctypeDeclHandler = sd; p.EndDoctypeDeclHandler = ed
    p.StartElementHandler = start; p.EndElementHandler = end; p.CharacterDataHandler = cdata
    p.CommentHandler = comment; p.ProcessingInstructionHandler = pi
    p.SetParamEntityParsing(xml.parsers.expat.XML_PARAM_ENTITY_PARSING_NEVER)
    p.UseForeignDTD(False)
    try:
        p.Parse(doc.encode('utf-8'), True)
    except Exception as e:
        return 'ERR'
    flush()
    return ''.join(out)
def cstr(s):
    o = '"'
    for ch in s:
        c = ord(ch)
        if ch == '"': o += '\\"'
        elif ch == '\\': o += '\\\\'
        elif ch == '\n': o += '\\n'
        elif ch == '\t': o += '\\t'
        elif ch == '\r': o += '" (chr 13) "'
        elif c < 32: o += '" (chr %d) "' % c
        else: o += ch
    return '(str ' + o + '")'
print('(ns xml-expat-test (:require [mulay.lib.xml :as xml] [clay.string :as str]))')
print(open(sys.argv[1]).read())
print('(deftest expat-agreement')
for c in cases:
    print('  (is (= (canon %s) %s))' % (cstr(c), cstr(canon(c))))
print('  (is true))')
