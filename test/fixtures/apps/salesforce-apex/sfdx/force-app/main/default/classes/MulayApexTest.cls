@isTest
private class MulayApexTest {
    @isTest static void rest() {
        RestRequest req = new RestRequest();
        req.requestURI = '/services/apexrest/mulay/x';
        req.params.put('name', 'n');
        RestContext.request = req;
        RestContext.response = new RestResponse();
        System.assertEquals('hello n x', MulayRest.doGet());
        System.assertEquals(4, MulayRest.doPost('a', 2).twice);
        System.assertEquals('b', MulayRest.doPut(new List<String>{'a', 'b'})[0]);
        System.assertEquals(1234567890123L, MulayRest.doDelete());
        System.assertEquals(Date.newInstance(2020, 1, 2), MulayRest.doPatch(Date.newInstance(2020, 1, 1)));
    }
    @isTest static void soap() {
        System.assertEquals('hello a', MulaySoap.hello('a'));
        System.assertEquals(3, MulaySoap.add(1, 2));
        System.assertEquals(2, MulaySoap.split('a,b').size());
    }
}
