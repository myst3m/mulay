public with sharing class SyncItemSync {
    private static Set<String> localChanges = new Set<String>();

    public static void handle() {
        if (Trigger.isBefore && Trigger.isInsert) {
            for (SyncItem__c r : (List<SyncItem__c>) Trigger.new) {
                if (String.isBlank(r.Sync_Key__c)) {
                    r.Sync_Key__c = UUID.randomUUID().toString();
                }
                if (r.Sync_Version__c == null) {
                    r.Sync_Version__c = System.currentTimeMillis();
                    localChanges.add(r.Sync_Key__c);
                }
            }
        } else if (Trigger.isBefore && Trigger.isUpdate) {
            Map<Id, SyncItem__c> old = (Map<Id, SyncItem__c>) Trigger.oldMap;
            for (SyncItem__c r : (List<SyncItem__c>) Trigger.new) {
                if (r.Sync_Version__c == old.get(r.Id).Sync_Version__c) {
                    r.Sync_Version__c = System.currentTimeMillis();
                    localChanges.add(r.Sync_Key__c);
                }
            }
        } else if (Trigger.isAfter && (Trigger.isInsert || Trigger.isUpdate)) {
            List<SyncItemChange__e> events = new List<SyncItemChange__e>();
            for (SyncItem__c r : (List<SyncItem__c>) Trigger.new) {
                if (localChanges.remove(r.Sync_Key__c) && !r.Sync_Deleting__c) {
                    events.add(change(r, r.Sync_Version__c, false));
                }
            }
            publish(events);
        } else if (Trigger.isAfter && Trigger.isUndelete) {
            List<SyncItemChange__e> events = new List<SyncItemChange__e>();
            for (SyncItem__c r : (List<SyncItem__c>) Trigger.new) {
                events.add(change(r, System.currentTimeMillis(), false));
            }
            publish(events);
        } else if (Trigger.isAfter && Trigger.isDelete) {
            List<SyncItemChange__e> events = new List<SyncItemChange__e>();
            for (SyncItem__c r : (List<SyncItem__c>) Trigger.old) {
                if (!r.Sync_Deleting__c) {
                    events.add(change(r, System.currentTimeMillis(), true));
                }
            }
            publish(events);
        }
    }

    private static SyncItemChange__e change(SyncItem__c r, Decimal version, Boolean deleted) {
        return new SyncItemChange__e(
            Sync_Key__c = r.Sync_Key__c,
            Name__c = r.Name,
            Phone__c = r.Phone__c,
            Amount__c = r.Amount__c,
            Status__c = r.Status__c,
            Due__c = r.Due__c,
            Version__c = version,
            Deleted__c = deleted);
    }

    private static void publish(List<SyncItemChange__e> events) {
        if (!events.isEmpty()) {
            EventBus.publish(events);
        }
    }
}
