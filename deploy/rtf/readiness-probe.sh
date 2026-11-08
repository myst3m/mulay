#!/usr/bin/env sh

# Returns 0 if application is DEPLOYED, otherwise non-0, printing the detected state to stdout

MULE_NOT_STARTED=1
FAILED_TO_CONNECT=2
NON_200_HTTP_RESPONSE=3

TMP_RESPONSE_FILE=/tmp/readiness
DEFAULT_READINESS_PROBE_URL=localhost:7777/mule/healthcheck/applications/${APP_NAME}/ready
CURL_OPTS="-s --connect-timeout 5 -w %{http_code}  -o $TMP_RESPONSE_FILE"
MULE_VERSION_FILE="/opt/mule/_VERSION_"

MULE_VERSION=$(cat ${MULE_VERSION_FILE})

# clean up from previous run
rm -f ${STATE_RESPONSE_FILE}

case ${MULE_VERSION} in
    3.*) READINESS_PROBE_URL=localhost:7777/mule/rtf/probe/readiness
         ;;
    *)
esac

# Can app receive traffic?
URL=${READINESS_PROBE_URL:-${DEFAULT_READINESS_PROBE_URL}}
HTTP_CODE=$(curl $CURL_OPTS $URL)
EXIT_CODE=$?
if [ ${HTTP_CODE} -eq 0 ] || [ "${HTTP_CODE}" = "000" ]; then
    echo "Failed to connect (${EXIT_CODE})"
    exit ${FAILED_TO_CONNECT}
fi
if [ "${HTTP_CODE}" != "200" ]; then
    echo "${HTTP_CODE}: $(head -c 100 ${TMP_RESPONSE_FILE})"
    exit ${NON_200_HTTP_RESPONSE}
fi

exit 0
