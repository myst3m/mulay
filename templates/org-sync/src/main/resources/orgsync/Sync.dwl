%dw 2.0

var FIELDS = ["Name", "Phone__c", "Amount__c", "Status__c", "Due__c"]

fun num(x) = if (x == null) null else x as Number

fun day(x) = if (x == null) null
  else if ((x as Number) > 100000) (|1970-01-01T00:00:00Z| + ("PT$((x as Number) / 1000)S" as Period)) as Date
  else |1970-01-01| + ("P$(x as Number)D" as Period)

fun version(x) = num(x) default -1

// 届いたイベントを相手の org にどう当てるか: "upsert" / "delete" / "skip"
fun decide(e, current) =
  if (e.Deleted__c default false)
    (if (current == null) "skip" else if (num(e.Version__c) >= version(current.Sync_Version__c)) "delete" else "skip")
  else if (current == null or num(e.Version__c) > version(current.Sync_Version__c)) "upsert"
  else "skip"

fun record(e) = {
  Sync_Key__c: e.Sync_Key__c,
  Name: e.Name__c,
  Phone__c: e.Phone__c,
  Amount__c: num(e.Amount__c),
  Status__c: e.Status__c,
  Due__c: day(e.Due__c),
  Sync_Version__c: num(e.Version__c)
}

// SOQL の行を相手に書くレコードにする (初回コピーと突き合わせ)
fun copied(r) = {
  Sync_Key__c: r.Sync_Key__c,
  Name: r.Name,
  Phone__c: r.Phone__c,
  Amount__c: num(r.Amount__c),
  Status__c: r.Status__c,
  Due__c: if (r.Due__c == null) null else r.Due__c as Date,
  Sync_Version__c: num(r.Sync_Version__c)
}

