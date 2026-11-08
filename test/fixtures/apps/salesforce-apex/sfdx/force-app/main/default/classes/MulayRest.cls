@RestResource(urlMapping='/mulay/*')
global with sharing class MulayRest {
    @HttpGet
    global static String doGet() {
        RestRequest req = RestContext.request;
        String tail = req.requestURI.substringAfterLast('/');
        return 'hello ' + req.params.get('name') + ' ' + tail;
    }
    global class Result {
        global String name;
        global Integer twice;
        global List<Integer> items;
        global Boolean ok;
        global String none;
    }
    @HttpPost
    global static Result doPost(String name, Integer n) {
        Result r = new Result();
        r.name = name;
        r.twice = n * 2;
        r.items = new List<Integer>{1, 2, 3};
        r.ok = true;
        return r;
    }
    @HttpPut
    global static List<String> doPut(List<String> xs) {
        List<String> out = new List<String>();
        for (Integer i = xs.size() - 1; i >= 0; i--) { out.add(xs[i]); }
        return out;
    }
    @HttpDelete
    global static Long doDelete() {
        return 1234567890123L;
    }
    @HttpPatch
    global static Date doPatch(Date d) {
        return d.addDays(1);
    }
}
