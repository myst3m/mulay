%dw 2.0
// 偽の SOAP サービスの応答。vars.ver ("11" / "12")、vars.mode、payload (受け取った要求の文字列) から
// {status, ct, body} を作る。ct は app.xml の choice が Content-Type に写す: xml11 / xml12 / plain / latin1 / html
import try from dw::Runtime
output application/java
var v12 = (vars.ver == '12') != (vars.mode == 'wrongver')
var envNs = if (v12) 'http://www.w3.org/2003/05/soap-envelope' else 'http://schemas.xmlsoap.org/soap/envelope/'
var ct = if (v12) 'xml12' else 'xml11'
var got = try(() -> (read(payload default '', 'application/xml')..text)[0] default '').result default ''
fun env(body: String, header: String = '') =
    '<soap:Envelope xmlns:soap="' ++ envNs ++ '">' ++ (if (header == '') '' else '<soap:Header>' ++ header ++ '</soap:Header>')
    ++ '<soap:Body>' ++ body ++ '</soap:Body></soap:Envelope>'
var echoBody = '<e:echoResponse xmlns:e="urn:mulay:echo"><text>' ++ got ++ '</text></e:echoResponse>'
var fault11 = '<soap:Fault><faultcode>soap:Server</faultcode><faultstring>Echo failed</faultstring><faultactor>urn:actor</faultactor>'
    ++ '<detail><e:echoFault xmlns:e="urn:mulay:echo"><reason>bad input</reason></e:echoFault></detail></soap:Fault>'
var fault12 = '<soap:Fault><soap:Code><soap:Value>soap:Sender</soap:Value><soap:Subcode><soap:Value xmlns:e="urn:mulay:echo">e:Invalid</soap:Value></soap:Subcode></soap:Code>'
    ++ '<soap:Reason><soap:Text xml:lang="en">Echo failed</soap:Text></soap:Reason><soap:Role>urn:actor</soap:Role>'
    ++ '<soap:Detail><e:echoFault xmlns:e="urn:mulay:echo"><reason>bad input</reason></e:echoFault></soap:Detail></soap:Fault>'
var fault = if (v12) fault12 else fault11
---
vars.mode match {
    case 'echo' -> {status: 200, ct: ct, body: env(echoBody)}
    case 'prefix' -> {status: 200, ct: ct, body: '<soap:Envelope xmlns:soap="' ++ envNs ++ '" xmlns:e="urn:mulay:echo" xmlns:unused="urn:unused"><soap:Body xmlns="urn:mulay:default">'
        ++ '<e:echoResponse><text>p</text><inner>d</inner></e:echoResponse></soap:Body></soap:Envelope>'}
    case 'multi' -> {status: 200, ct: ct, body: env(echoBody ++ '<e:extra xmlns:e="urn:mulay:echo">x</e:extra>')}
    case 'ws' -> {status: 200, ct: ct, body: '<?xml version="1.0" encoding="UTF-8"?>\n<soap:Envelope xmlns:soap="' ++ envNs ++ '">\n  <soap:Body>\n    <!-- comment -->\n    '
        ++ '<e:echoResponse xmlns:e="urn:mulay:echo">\n      <text> spaced </text>\n    </e:echoResponse>\n  </soap:Body>\n</soap:Envelope>\n'}
    case 'header' -> {status: 200, ct: ct, body: env(echoBody, '<e:trace xmlns:e="urn:mulay:echo">abc</e:trace><h:other xmlns:h="urn:other" soap:mustUnderstand="0">o</h:other>')}
    case 'latin1' -> {status: 200, ct: 'latin1', body: '<?xml version="1.0" encoding="ISO-8859-1"?>' ++ env('<e:echoResponse xmlns:e="urn:mulay:echo"><text>café ü</text></e:echoResponse>')}
    case 'fault' -> {status: 500, ct: ct, body: env(fault)}
    case 'fault200' -> {status: 200, ct: ct, body: env(fault)}
    case 'faultmin' -> {status: 500, ct: ct, body: env(if (v12) '<soap:Fault><soap:Code><soap:Value>soap:Receiver</soap:Value></soap:Code><soap:Reason><soap:Text xml:lang="en">min</soap:Text></soap:Reason></soap:Fault>'
        else '<soap:Fault><faultcode>soap:Client</faultcode><faultstring>min</faultstring></soap:Fault>')}
    case 's500' -> {status: 500, ct: 'plain', body: 'oops'}
    case 's404' -> {status: 404, ct: 'html', body: '<html><body>not found</body></html>'}
    case 's202' -> {status: 202, ct: 'plain', body: ''}
    case 'empty' -> {status: 200, ct: ct, body: ''}
    case 'notxml' -> {status: 200, ct: ct, body: 'not xml'}
    case 'noenv' -> {status: 200, ct: ct, body: '<foo xmlns="urn:foo"/>'}
    case 'emptybody' -> {status: 200, ct: ct, body: env('')}
    case 'wrongver' -> {status: 200, ct: ct, body: env(echoBody)}
    case 'html200' -> {status: 200, ct: 'html', body: '<html><body>not soap</body></html>'}
    case 'nons' -> {status: 200, ct: ct, body: '<foo/>'}
    case 's404soap' -> {status: 404, ct: ct, body: env(echoBody)}
    case 's500echo' -> {status: 500, ct: ct, body: env(echoBody)}
    case 'badbody' -> {status: 200, ct: ct, body: env('<e:x xmlns:e="urn:mulay:echo">a & b</e:x>')}
    case 'unclosed' -> {status: 200, ct: ct, body: '<soap:Envelope xmlns:soap="' ++ envNs ++ '"><soap:Body><e:echoResponse xmlns:e="urn:mulay:echo"><text>x</text></e:echoResponse>'}
    case 'badheader' -> {status: 200, ct: ct, body: env(echoBody, '<e:trace xmlns:e="urn:mulay:echo">a < b</e:trace>')}
    case 'nobody' -> {status: 200, ct: ct, body: '<soap:Envelope xmlns:soap="' ++ envNs ++ '"><soap:Header/></soap:Envelope>'}
    case 'textbody' -> {status: 200, ct: ct, body: env('just text')}
    case 'xmlcontent' -> {status: 200, ct: ct, body: env('<e:r xmlns:e="urn:mulay:echo" a=\'q"\' b="&lt;&amp;&gt;"><e:empty/><e:pair></e:pair><![CDATA[c<d]]>&#233;<?pi data?>t&gt;&apos;&quot;</e:r>')}
    case 'nested' -> {status: 200, ct: ct, body: '<soap:Envelope xmlns:soap="' ++ envNs ++ '" xmlns:a="urn:a"><soap:Body xmlns:b="urn:b"><a:r xmlns:c="urn:c"><b:x c:at="1">v</b:x><a:y xmlns:a="urn:a2"/></a:r></soap:Body></soap:Envelope>'}
    case 'nsheader' -> {status: 200, ct: ct, body: '<soap:Envelope xmlns:soap="' ++ envNs ++ '" xmlns:e="urn:mulay:echo" xmlns:z="urn:z"><soap:Header xmlns:hh="urn:hh">'
        ++ '<e:trace xmlns:own="urn:own">t</e:trace><hh:h2/></soap:Header><soap:Body>' ++ echoBody ++ '</soap:Body></soap:Envelope>'}
    case 'nsfault' -> {status: 500, ct: ct, body: '<soap:Envelope xmlns:soap="' ++ envNs ++ '" xmlns:e="urn:mulay:echo" xmlns:z="urn:z"><soap:Body>'
        ++ (if (v12) '<soap:Fault><soap:Code><soap:Value>soap:Receiver</soap:Value></soap:Code><soap:Reason><soap:Text xml:lang="en">ns</soap:Text></soap:Reason><soap:Detail><e:info>i</e:info><z:more/></soap:Detail></soap:Fault>'
            else '<soap:Fault><faultcode>e:Custom</faultcode><faultstring>ns</faultstring><detail><e:info>i</e:info><z:more/></detail></soap:Fault>')
        ++ '</soap:Body></soap:Envelope>'}
    case 'htmlct' -> {status: 200, ct: 'html', body: env(echoBody)}
    case 'xmlct404' -> {status: 404, ct: ct, body: '<foo/>'}
    case 'html500' -> {status: 500, ct: 'html', body: env(fault)}
    case 'owndecl' -> {status: 200, ct: ct, body: env('<e:r xmlns:x="urn:x" xmlns:e="urn:mulay:echo" x:a="1"><x:c/></e:r>')}
    case 'duphdr' -> {status: 200, ct: ct, body: env(echoBody, '<e:trace xmlns:e="urn:mulay:echo">1</e:trace><f:trace xmlns:f="urn:f">2</f:trace>')}
    case 'bodyextra' -> {status: 200, ct: ct, body: '<soap:Envelope xmlns:soap="' ++ envNs ++ '"><soap:Body>\n  <!-- lead -->\n  <e:a xmlns:e="urn:mulay:echo">1</e:a>\n  <e:b xmlns:e="urn:mulay:echo">2</e:b><!-- post -->\n</soap:Body></soap:Envelope>'}
    case 'subcode' -> {status: 500, ct: ct, body: env(fault12)}
    case 'rpc' -> {status: 200, ct: ct, body: env('<c:addResponse xmlns:c="urn:mulay:calc"><sum>3</sum></c:addResponse>')}
    case 'ping' -> {status: 200, ct: ct, body: env('<pong xmlns="urn:mulay:imp"><n>1</n></pong>')}
    else -> {status: 200, ct: ct, body: env(echoBody)}
}
