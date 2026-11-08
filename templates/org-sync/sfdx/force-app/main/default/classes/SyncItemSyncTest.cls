@IsTest
private class SyncItemSyncTest {
    @IsTest
    static void localChangesGetKeysAndVersions() {
        SyncItem__c r = new SyncItem__c(Name = 'a', Amount__c = 1);
        insert r;
        r = [SELECT Sync_Key__c, Sync_Version__c FROM SyncItem__c WHERE Id = :r.Id];
        System.assert(r.Sync_Key__c != null);
        System.assert(r.Sync_Version__c != null);
        r.Status__c = 'open';
        update r;
        delete r;
        undelete r;
    }

    @IsTest
    static void syncWritesKeepTheirVersion() {
        SyncItem__c r = new SyncItem__c(Name = 'b', Sync_Key__c = 'k-1', Sync_Version__c = 42);
        insert r;
        r.Sync_Version__c = 43;
        r.Sync_Deleting__c = true;
        update r;
        r = [SELECT Sync_Version__c FROM SyncItem__c WHERE Id = :r.Id];
        System.assertEquals(43, r.Sync_Version__c);
        delete r;
    }
}
