# org-sync

A template for two-way record sync between two Salesforce orgs (A and B), built on Platform Events and the
Salesforce Pub/Sub API. It runs on both real Mule 4 and mulay.

The synced object is `SyncItem__c` (Name, Phone, Amount, Status, Due). Replace it with your own object and fields.

## How it works

- **Publishing (Salesforce side).** A trigger on `SyncItem__c` publishes `SyncItemChange__e` with the whole record
  (every synced field, not only the changed ones), so a lost event is repaired by the next change to the same record.
  The event is *Publish After Commit*, so rolled-back changes publish nothing. Deletes and undeletes publish too.
- **Versions and loop prevention.** Each record has `Sync_Version__c` (epoch milliseconds).
  - A user's change leaves the field untouched, so the trigger stamps the current time into it and publishes.
  - A sync write sets the field to the other org's version, so the trigger knows the change came from sync and
    publishes nothing.
  - This tells sync writes apart from manual edits even when the integration user and the human user are the same
    account.
- **Receiving (this app).** `a-to-b` / `b-to-a` subscribe with `salesforce-pub-sub:subscribe-channel-listener`.
  - An event is applied only when its version is newer than the target record's, so out-of-order events never
    roll a record back.
  - Writes are upserts by the external ID `Sync_Key__c` (a UUID set on insert), so a replayed event changes nothing.
  - A delete first marks the record with `Sync_Deleting__c` (so the delete publishes nothing), then deletes it.
- **Resuming.** After each event the flow stores its replay ID in the persistent Object Store `Replay`, and
  `replay-id-from-object-store` resumes from it after a restart. Events are kept for 72 hours; a longer outage is
  repaired by the reconcile job.
- **Failures.** An event that cannot be applied (validation rule, storage limit, ...) is kept in the Object Store
  `Failed` (see `/status`); the reconcile job repairs the record later.
- **Initial copy.** `POST /initial-copy` reads A in key order, `sync.copyChunk` records at a time, and upserts each
  chunk into B with a Bulk API 2.0 job. The next chunk is queued through VM, so memory stays flat for millions of
  records. Records copied this way carry A's version, so B's trigger publishes nothing.
- **Reconcile.** Every `sync.reconcileMinutes` (and on `POST /reconcile`) both orgs are read and, per key, the newer
  version is written to the other org. It repairs lost events, failed events and outages longer than 72 hours.

```
GET  /status          counts (upsert / delete / skip), initial-copy progress, replay IDs, failed keys
POST /initial-copy    copy every record of A to B (run once, before or after starting the event flows)
POST /reconcile       compare both orgs now
```

## Setup

1. Deploy the metadata to both orgs and give the integration user access:

   ```bash
   cd sfdx
   sf project deploy start --target-org <A> --source-dir force-app --test-level RunSpecifiedTests --tests SyncItemSyncTest
   sf project deploy start --target-org <B> --source-dir force-app --test-level RunSpecifiedTests --tests SyncItemSyncTest
   sf org assign permset --name OrgSync --target-org <A> --on-behalf-of <integration user of A>
   sf org assign permset --name OrgSync --target-org <B> --on-behalf-of <integration user of B>
   ```

2. In each org, create an app with the OAuth client credentials flow and a run-as user. Use an External Client App
   (new orgs cannot create Connected Apps), with the Client Credentials Flow enabled and the run-as user set.
3. Put the credentials in `src/main/resources/sf-secret.yaml` (git ignores this file):

   ```yaml
   a:
     clientId: "..."
     clientSecret: "..."
     tokenUrl: "https://<A my domain>.my.salesforce.com/services/oauth2/token"
   b:
     clientId: "..."
     clientSecret: "..."
     tokenUrl: "https://<B my domain>.my.salesforce.com/services/oauth2/token"
   ```

4. Run it:

   ```bash
   mulay run templates/org-sync      # port 18600 (config.yaml: http.port)
   ```

## Sizing

- Each applied event costs two API calls in the target org (a query and an upsert). 100,000 events a day are
  200,000 calls. Check the `DailyApiRequests` limit, or batch the events per `eventBatchSize`.
- Event delivery counts toward the org's `DailyDeliveredPlatformEvents` limit (each subscriber counts).
- The reconcile job reads all records with SOQL. For millions of records, narrow it to `SystemModstamp` after the
  previous run, or compare Bulk API exports.

## Limits

- A record deleted in one org and still present in the other is copied back by the reconcile job; deletes are
  carried by events only. To carry deletes through reconcile too, also read the recycle bin (`queryAll`) of each org.
- Two edits to the same record in both orgs within the event delay: the later version wins for the whole record.
