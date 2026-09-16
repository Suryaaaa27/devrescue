import logging
import time

from opentelemetry import trace
from opentelemetry._logs import set_logger_provider
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import SimpleLogRecordProcessor
from opentelemetry.exporter.otlp.proto.http._log_exporter import (
    OTLPLogExporter,
)


resource = Resource.create(
    {
        "service.name": "devrescue-log-test",
        "service.version": "0.1.0",
        "deployment.environment": "development",
    }
)


logger_provider = LoggerProvider(
    resource=resource
)


exporter = OTLPLogExporter(
    endpoint="http://127.0.0.1:4318/v1/logs",
)


logger_provider.add_log_record_processor(
    SimpleLogRecordProcessor(exporter)
)


set_logger_provider(
    logger_provider
)


otel_handler = LoggingHandler(
    level=logging.INFO,
    logger_provider=logger_provider,
)


logger = logging.getLogger("devrescue-log-test")
logger.setLevel(logging.INFO)
logger.addHandler(otel_handler)


logger.error(
    "DIRECT_OTEL_LOG_TEST request_id=test-001 message=hello-loki"
)

print("Log emitted. Waiting for export...")

time.sleep(5)

logger_provider.shutdown()

print("Logger provider shut down.")