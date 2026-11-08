global with sharing class MulaySoap {
    webservice static String hello(String name) {
        return 'hello ' + name;
    }
    webservice static Integer add(Integer a, Integer b) {
        return a + b;
    }
    webservice static List<String> split(String s) {
        return s.split(',');
    }
}
