echo "Starting 2 copies of application..."

echo "PINNING: ${PINNING}"
echo "APP_RUN: ${APP_RUN}"

echo "Starting copy 1..."
${PINNING} ${APP_RUN} > ${LOG_DIR}/app_1.log 2>&1 &

echo "Starting copy 2..."
${PINNING} ${APP_RUN} > ${LOG_DIR}/app_2.log 2>&1 &

wait

echo "All copies finished."