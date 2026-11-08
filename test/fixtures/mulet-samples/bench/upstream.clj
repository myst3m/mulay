;; Simple upstream echo server for I/O benchmarks
;; Start: cd mulet && clojure -M:dev -i samples/bench/upstream.clj
(require '[zeph.server :as server])

(def stop
  (server/run-server
    (fn [req]
      {:status 200
       :headers {"Content-Type" "application/json"}
       :body "{\"echo\":true,\"status\":\"ok\"}"})
    {:port 18099 :thread 2}))

(println "[UPSTREAM] Echo server running on port 18099")
